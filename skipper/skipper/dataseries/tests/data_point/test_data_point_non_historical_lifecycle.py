# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


# TODO: test s3 files overwriting when inserting (old data should be deleted afterwards?
#       see skipper/skipper/dataseries/storage/dynamic_sql/serializers/modification.py
#       where we left the explanation why we dont do it in the first draft

import io

import uuid

import json
from django_multitenant.utils import set_current_tenant  # type: ignore
from typing import Tuple, Any, Dict, Callable, List, cast, Type, Optional, Union

from PIL import Image as PIL_Image  # type: ignore
from django.utils import dateparse, timezone
from rest_framework import status
from urllib.parse import quote

from django.db.models import Count

from skipper.core.models.tenant import Tenant

from skipper import modules
from skipper.core.tests.base import BaseViewTest, BASE_URL
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.raw_sql import dbtime
from skipper.dataseries.storage.contract import StorageBackendType
from skipper.dataseries.storage.dynamic_sql.models.datapoint import DisplayDataPoint
from skipper.dataseries.storage.dynamic_sql.queries.display import data_series_as_sql_table
from skipper.dataseries.storage.dynamic_sql.queries.modification_materialized.insert import insert_or_update_data_points
from skipper.dataseries.storage.dynamic_sql.queries.select_info import select_infos
from skipper.dataseries.storage.static_ds_information import compute_data_series_query_info, \
    data_point_serialization_keys
from skipper.dataseries.storage.uuid import gen_uuid
from skipper.dataseries.models.file_lookup import FileLookup

DATA_SERIES_BASE_URL = BASE_URL + modules.url_representation(modules.Module.DATA_SERIES) + '/'


def generate_photo_file() -> io.BytesIO:
    file = io.BytesIO()
    image = PIL_Image.new('RGBA', size=(100, 100), color=(155, 0, 0))
    image.save(file, 'png')
    file.name = 'test.png'
    file.seek(0)
    return file


def generate_some_other_photo_file() -> io.BytesIO:
    file = io.BytesIO()
    image = PIL_Image.new('RGBA', size=(100, 100), color=(200, 200, 0))
    image.save(file, 'png')
    file.name = 'test.png'
    file.seek(0)
    return file


def test_materialized_upsert_checks_point_in_time(
    self: 'BaseDataPointLifecycleTest',
    current_data_point: Dict[str, Any],
    data_series_id: str,
    data_series_external_id: str,
    fact_type: str,
    fact: Dict[str, Any],
    secondary_fact: Dict[str, Any],
    partial: bool,
    fact_value_that_should_not_be_set: Callable[[], Any],
    secondary_fact_value_that_should_not_be_set: Callable[[], Any],
    expected_to_be_found_at_all: bool,
    expected_fact_value: Optional[Callable[[], Any]],
    equal: Callable[[Any, Any], Any]
) -> None:
    set_current_tenant(
        Tenant.objects.get(name='default_tenant')
    )

    _data_series_obj = DataSeries.objects.get(id=data_series_id)

    _data_series_query_info = compute_data_series_query_info(
        data_series=_data_series_obj
    )

    _serialization_keys = data_point_serialization_keys(
        _data_series_query_info
    )
    set_current_tenant(None)

    _fact_value_that_should_not_be_set = fact_value_that_should_not_be_set()
    _secondary_fact_value_that_should_not_be_set = secondary_fact_value_that_should_not_be_set()

    _some_point_in_time_str = '2000-12-15T19:09:25.007985'
    _some_point_in_time = dateparse.parse_datetime(
        _some_point_in_time_str
    )
    assert _some_point_in_time is not None

    _validated_datas = [{
        'id': current_data_point['id'],
        'external_id': current_data_point['external_id'],
        'payload': {
            fact["external_id"]: _fact_value_that_should_not_be_set,
            secondary_fact["external_id"]: _secondary_fact_value_that_should_not_be_set
        }
    }]

    def mangle(value: Any) -> Any:
        class FakedFileValue:
            name: str

        class FakedFile:
            value: FakedFileValue

        if fact_type == 'image':
            faked_value = FakedFileValue()
            faked_value.name = 'should_not_be_here'
            faked_file = FakedFile()
            faked_file.value = faked_value
            return faked_file
        elif fact_type == 'file':
            faked_value = FakedFileValue()
            faked_value.name = 'should_not_be_here'
            faked_file = FakedFile()
            faked_file.value = faked_value
            return faked_file
        else:
            return value

    _django_relation_data = [{
        fact["id"]: mangle(_fact_value_that_should_not_be_set),
        secondary_fact["id"]: mangle(_secondary_fact_value_that_should_not_be_set)
    }]

    if partial:
        _validated_datas[0]['payload'].pop(secondary_fact['external_id'])
        _django_relation_data[0].pop(secondary_fact["id"])

    insert_or_update_data_points(
        tenant_id=Tenant.objects.get(name='default_tenant').id,
        tenant_name='default_tenant',
        data_series_id=data_series_id,
        data_series_external_id=data_series_external_id,
        point_in_time=_some_point_in_time,
        data_point_serialization_keys=_serialization_keys,
        validated_datas=_validated_datas,
        partial=partial,
        sub_clock=1,
        backend=_data_series_obj.backend,
        record_source="TEST",
        user_id="1"
    )

    _sql = data_series_as_sql_table(
        data_series=_data_series_obj,
        payload_as_json=True,
        point_in_time=False,
        changes_since=False,
        include_versions=False,
        filter_str='',
        resolve_dimension_external_ids=False,
        data_series_query_info=_data_series_query_info,
        use_materialized=True
    )

    query_params: Dict[str, Any] = {select_info.payload_variable_name: select_info.unescaped_display_id for
                                    select_info in
                                    select_infos(_data_series_query_info)}

    query_params['data_point_lookup_id'] = current_data_point['id']

    _display_data_points: List[DisplayDataPoint] = list(DisplayDataPoint.objects.raw(
        f"""
        {_sql}
        AND ds_dp.id = %(data_point_lookup_id)s
        """,
        query_params
    ))

    if expected_to_be_found_at_all:
        if expected_fact_value is None:
            raise AssertionError()
        self.assertEqual(1, len(_display_data_points))
        self.assertNotEqual(_display_data_points[0].point_in_time, _some_point_in_time_str)
        self.assertTrue(equal(_display_data_points[0].payload[fact['external_id']], expected_fact_value()))
        if fact_type != 'image' and fact_type != 'file':
            # TODO: check image byte by byte
            self.assertFalse(equal(_display_data_points[0].payload[fact['external_id']], _fact_value_that_should_not_be_set))
    else:
        # is deleted, should not be recreated
        if len(_display_data_points) > 0:
            print(_display_data_points[0].payload)
        self.assertEqual(0, len(_display_data_points))


def filter_query_param(fact_id: str, value: Any) -> str:
    ret = f'filter={"{"}"{fact_id}":{json.dumps(value)}{"}"}'
    return ret


def test_all_set(
    self: 'BaseDataPointLifecycleTest',
    data_series: Dict[str, Any],
    fact: Dict[str, Any],
    secondary_fact: Dict[str, Any],
    test_filtering: bool,
    backend: str,
    _initial_value: Callable[[], Any],
    _secondary_initial_value: Callable[[], Any],
    _updated_value: Callable[[], Any],
    _secondary_updated_value: Callable[[], Any],
    equal: Callable[[Any, Any], Any],
    partial: bool,
    fact_type: str,
    debug: bool = False
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    _initial_list_json = self.get_payload(url=data_series['data_points'] + '?count')
    # we start off with an empty list, ensure this is correct
    self.assertEqual(0, _initial_list_json['count'])
    self.assertEqual([], _initial_list_json['data'])

    initial = self.create_payload(url=data_series['data_points'], payload=lambda: {
        'id': gen_uuid(data_series['id'], external_id='1'),
        'external_id': '1',
        f'payload.{fact["external_id"]}': _initial_value(),
        f'payload.{secondary_fact["external_id"]}': _secondary_initial_value()
    }, format='multipart', debug=debug, equality_check=False)

    if test_filtering:
        fact_id = fact['external_id']
        original_list = self.get_payload(
            url=data_series['data_points'] + f'?count&{filter_query_param(fact_id, _initial_value())}')
        self.assertEqual(1, original_list['count'])
        self.assertEqual(1, len(original_list['data']))

        when_updated_list = self.get_payload(
            url=data_series['data_points'] + f'?count&{filter_query_param(fact_id, _updated_value())}')
        self.assertEqual(0, when_updated_list['count'])
        self.assertEqual(0, len(when_updated_list['data']))

    if partial:
        updated = self.patch_payload(
            url=initial['url'], payload=lambda: {
                f'payload.{fact["external_id"]}': _updated_value()
            }, format='multipart'
        )
        self.assertTrue(equal(_updated_value(), updated['payload'][fact['external_id']]))
        # secondary fact should stay the same if we patch without it
        self.assertTrue(equal(_secondary_initial_value(), updated['payload'][secondary_fact['external_id']]))
    else:
        updated = self.update_payload(
            url=initial['url'], payload=lambda: {
                'external_id': '1',
                f'payload.{fact["external_id"]}': _updated_value()
            }, format='multipart', debug=debug, equality_check=False
        )
        self.assertTrue(equal(_updated_value(), updated['payload'][fact['external_id']]))
        # secondary fact should be removed when we put without it
        self.assertTrue(secondary_fact['external_id'] not in updated['payload'])

    if test_filtering:
        fact_id = fact['external_id']
        original_list = self.get_payload(
            url=data_series['data_points'] + f'?count&{filter_query_param(fact_id, _initial_value())}')
        self.assertEqual(0, original_list['count'])
        self.assertEqual(0, len(original_list['data']))

        when_updated_list = self.get_payload(
            url=data_series['data_points'] + f'?count&{filter_query_param(fact_id, _updated_value())}')
        self.assertEqual(1, when_updated_list['count'])
        self.assertEqual(1, len(when_updated_list['data']))

    return initial, updated


def same_as(
        self: 'BaseDataPointLifecycleTest',
        equal: Callable[[Any, Any], Any],
        fact: Dict[str, Any],
        url: str,
        query_str: str,
        expected: Dict[str, Any]
) -> None:
    json_list = self.get_payload(url=f'{url}{query_str}')
    self.assertEqual(1, json_list['count'])
    self.assertEqual(1, len(json_list['data']))

    def _internal_same_as(to_check: Dict[str, Any]) -> None:
        self.assertEqual(expected['id'], to_check['id'])
        self.assertEqual(expected['url'], to_check['url'])
        self.assertEqual(expected['external_id'], to_check['external_id'])
        # the data point itself should not change, only the attributes
        self.assertEqual(expected['point_in_time'], to_check['point_in_time'])
        self.assertTrue(
            equal(expected['payload'][fact['external_id']], to_check['payload'][fact['external_id']]))

    _internal_same_as(json_list['data'][0])


class BaseDataPointLifecycleTest(BaseViewTest):
    # the list endpoint is disabled for datapoints if we do not select for a data series
    url_under_test = DATA_SERIES_BASE_URL + 'dataseries/'
    simulate_other_tenant = True

    counter = 0

    def _setup_fact_or_dim(self, data_series: Dict[str, Any], fact_type: str, optional: bool,
                           reference: Optional[str]) -> Any:
        idx = self.counter
        if fact_type != 'dimension':
            fact = self.create_payload(data_series[f'{fact_type}_facts'], payload={
                'name': f'{fact_type}_fact_{idx}_A',
                # test with upper case to check if sql queries are properly escaped
                'external_id': f'{fact_type}_fact_{idx}',
                'optional': optional,
            })
        else:
            fact = self.create_payload(data_series[f'dimensions'], payload={
                'name': f'{fact_type}_{idx}_A',
                # test with upper case to check if sql queries are properly escaped
                'external_id': f'{fact_type}_{idx}',
                'optional': optional,
                'reference': reference
            })
        self.counter = self.counter + 1
        return fact

    def _setup_data_series_for_test(self, backend: str, fact_type: str) -> Any:
        idx = self.counter
        data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': f'my_data_series_{fact_type}_{idx}',
            'external_id': f'_external_id_{fact_type}_{idx}',
            'backend': backend
        }, simulate_tenant=False)
        return data_series

    def _test_data_point_lifecycle(
            self,
            test_filtering: bool,
            fact_type: str,
            backend: str,
            optional: bool,
            _initial_value: Callable[[], Any],
            _secondary_initial_value: Callable[[], Any],
            _updated_value: Callable[[], Any],
            equal: Callable[[Any, Any], Any],
            partial: bool,
            debug: bool = False,
            reference_1: Optional[Dict[str, Any]] = None,
            reference_2: Optional[Dict[str, Any]] = None
    ) -> None:
        data_series = self._setup_data_series_for_test(backend, fact_type)

        resp = self.client.get(data_series['history_data_points'])
        self.assertEqual(status.HTTP_400_BAD_REQUEST, resp.status_code)

        fact = self._setup_fact_or_dim(data_series, fact_type, optional,
                                       reference_1['url'] if reference_1 is not None else None)
        secondary_fact = self._setup_fact_or_dim(data_series, fact_type, True,
                                                 reference_2['url'] if reference_2 is not None else None)

        _initial, _updated = test_all_set(
            self=self,
            data_series=data_series,
            fact=fact,
            secondary_fact=secondary_fact,
            test_filtering=test_filtering,
            backend=backend,
            _initial_value=_initial_value,
            _secondary_initial_value=_secondary_initial_value,
            _updated_value=_updated_value,
            # works, but is not pretty
            _secondary_updated_value=_initial_value,
            equal=equal,
            partial=partial,
            debug=debug,
            fact_type=fact_type
        )

        same_as(
            self=self,
            equal=equal,
            fact=fact,
            url=data_series['data_points'],
            query_str='?count',
            expected=_updated
        )

        if optional:
            # TODO:
            # test removal
            # then put back

            # test create empty, put into
            pass

        _timestamp_before_delete = dbtime.now()

        # finally delete the data point
        self.delete_payload(url=_updated['url'])

        _current_list_json = self.get_payload(url=data_series['data_points'] + '?count')
        # we start off with an empty list, ensure this is correct
        self.assertEqual(0, _current_list_json['count'])
        self.assertEqual([], _current_list_json['data'])

        if backend == StorageBackendType.DYNAMIC_SQL_NO_HISTORY.value:
            test_materialized_upsert_checks_point_in_time(
                self=self,
                current_data_point=_updated,
                data_series_id=data_series['id'],
                data_series_external_id=data_series['external_id'],
                fact=fact,
                secondary_fact=secondary_fact,
                partial=partial,
                fact_value_that_should_not_be_set=_initial_value,
                secondary_fact_value_that_should_not_be_set=_secondary_initial_value,
                expected_to_be_found_at_all=False,
                expected_fact_value=None,
                fact_type=fact_type,
                equal=equal
            )

            if fact_type in ['image', 'file']:
                with_deleted = FileLookup.all_objects.values(
                    'tenant_id',
                    'data_series_id',
                    'data_point_id',
                    'fact_id'
                ).filter(
                    data_series_id=data_series['id']
                ).annotate(
                    cnt=Count('data_point_id')
                ).order_by()
                self.assertGreater(len(with_deleted), 0)

                for elem in with_deleted:
                    if partial and str(elem['fact_id']) == secondary_fact['id']:
                        # noop
                        pass
                    else:
                        self.assertGreater(elem['cnt'], 1)
                
                without_deleted = FileLookup.objects.values(
                    'tenant_id',
                    'data_series_id',
                    'data_point_id',
                    'fact_id'
                ).filter(
                    data_series_id=data_series['id']
                ).annotate(
                    cnt=Count('data_point_id')
                ).order_by()
                self.assertGreater(len(with_deleted), 0)
                for elem in without_deleted:
                    self.assertEqual(elem['cnt'], 1)

class FloatFactLifecycleTest(BaseDataPointLifecycleTest):
    def test_float_facts(self) -> None:
        for backend_key, backend_value in StorageBackendType.choices_without_history():
            for optional in [False, True]:
                for partial in [False, True]:
                    self._test_data_point_lifecycle(True, 'float', backend_key, optional, lambda: 1, lambda: 1,
                                                    lambda: 2, lambda x, y: x == y, partial)


class BooleanFactLifecycleTest(BaseDataPointLifecycleTest):
    def test_boolean_facts(self) -> None:
        for backend_key, backend_value in StorageBackendType.choices_without_history():
            for optional in [False, True]:
                for partial in [False, True]:
                    self._test_data_point_lifecycle(True, 'boolean', backend_key, optional, lambda: True, lambda: True,
                                                    lambda: False, lambda x, y: x == y, partial)


class StringFactLifecycleTest(BaseDataPointLifecycleTest):
    def test_string_facts(self) -> None:
        for backend_key, backend_value in StorageBackendType.choices_without_history():
            for optional in [False, True]:
                for partial in [False, True]:
                    self._test_data_point_lifecycle(True, 'string', backend_key, optional, lambda: '1', lambda: '1',
                                                    lambda: '2', lambda x, y: x == y, partial)


class TextFactLifecycleTest(BaseDataPointLifecycleTest):
    def test_text_facts(self) -> None:
        for backend_key, backend_value in StorageBackendType.choices_without_history():
            for optional in [False, True]:
                for partial in [False, True]:
                    self._test_data_point_lifecycle(True, 'text', backend_key, optional, lambda: '1', lambda: '1',
                                                    lambda: '2', lambda x, y: x == y, partial)


class JsonFactLifecycleTest(BaseDataPointLifecycleTest):
    def test_json_facts(self) -> None:
        for backend_key, backend_value in StorageBackendType.choices_without_history():
            for optional in [False, True]:
                for partial in [False, True]:
                    # numbers are valid json as well. we just want to check if everything works properly
                    # and we use multipart in the function so only numbers work here
                    self._test_data_point_lifecycle(False, 'json', backend_key, optional, lambda: 1, lambda: 1,
                                                    lambda: 2, lambda x, y: x == y, partial)


class TimestampFactLifecycleTest(BaseDataPointLifecycleTest):
    def test_timestamp_facts(self) -> None:
        _1 = '2019-12-15T19:09:25.007985'  # format from postgres!
        _2 = '2019-12-15T19:09:26.007985'

        def equal(x: Any, y: Any) -> bool:
            return str(x) == str(y)

        for backend_key, backend_value in StorageBackendType.choices_without_history():
            for optional in [False, True]:
                for partial in [False, True]:
                    self._test_data_point_lifecycle(True, 'timestamp', backend_key, optional, lambda: _1, lambda: _1,
                                                    lambda: _2, equal,
                                                    partial)


class ImageFactLifecycleTest(BaseDataPointLifecycleTest):
    def test_image_facts(self) -> None:
        for backend_key, backend_value in StorageBackendType.choices_without_history():
            for optional in [False, True]:
                for partial in [False, True]:
                    # FIXME: check image is actually the same byte by byte
                    self._test_data_point_lifecycle(False, 'image', backend_key, optional, generate_photo_file,
                                                    generate_photo_file, generate_some_other_photo_file,
                                                    lambda x, y: True, partial)


class FileFactLifecycleTest(BaseDataPointLifecycleTest):
    def test_file_facts(self) -> None:
        for backend_key, backend_value in StorageBackendType.choices_without_history():
            for optional in [False, True]:
                for partial in [False, True]:
                    # FIXME: check file is actually the same byte by byte
                    self._test_data_point_lifecycle(False, 'file', backend_key, optional, generate_photo_file,
                                                    generate_photo_file, generate_some_other_photo_file,
                                                    lambda x, y: True, partial)


class DimensionLifecycleTest(BaseDataPointLifecycleTest):
    def test_dimensions(self) -> None:
        for backend_key, backend_value in StorageBackendType.choices_without_history():
            def equal(x: Any, y: Any) -> bool:
                return str(x) == str(y)

            data_series_for_dim_1 = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
                'name': f'my_data_series_dim_1_{backend_key}',
                'external_id': f'_ds_external_id_1_{backend_key}',
                'backend': backend_key
            }, simulate_tenant=False)

            _1_1 = self.create_payload(
                url=data_series_for_dim_1['data_points'],
                payload={
                    'external_id': '_1_1',
                    'payload': {}
                }
            )
            _1_2 = self.create_payload(
                url=data_series_for_dim_1['data_points'],
                payload={
                    'external_id': '_1_2',
                    'payload': {}
                }
            )

            data_series_for_dim_2 = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
                'name': f'my_data_series_dim_2_{backend_key}',
                'external_id': f'_ds_external_id_2_{backend_key}',
                'backend': backend_key
            }, simulate_tenant=False)

            _2_1 = self.create_payload(
                url=data_series_for_dim_2['data_points'],
                payload={
                    'external_id': '_2_1',
                    'payload': {}
                }
            )
            for optional in [False, True]:
                for partial in [False, True]:
                    self._test_data_point_lifecycle(
                        False, 'dimension',
                        backend_key,
                        optional,
                        lambda: _1_1['id'],
                        lambda: _2_1['id'],
                        lambda: _1_2['id'],
                        equal,
                        partial,
                        reference_1=data_series_for_dim_1,
                        reference_2=data_series_for_dim_2
                    )


del BaseDataPointLifecycleTest
