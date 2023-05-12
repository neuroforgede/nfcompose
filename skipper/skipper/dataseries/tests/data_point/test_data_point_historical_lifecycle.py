# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


import io

import uuid

import json
from django_multitenant.utils import set_current_tenant  # type: ignore
from typing import Tuple, Any, Dict, Callable, List, cast, Type, Optional, Union

from PIL import Image as PIL_Image  # type: ignore
from django.utils import dateparse, timezone
from rest_framework import status
from urllib.parse import quote

from skipper.core.models.tenant import Tenant

from skipper import modules
from skipper.core.tests.base import BaseViewTest, BASE_URL
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.raw_sql import dbtime
from skipper.dataseries.storage.contract import StorageBackendType
from skipper.dataseries.storage.dynamic_sql.models.base_relation import BaseDataPointFactRelation
from skipper.dataseries.storage.dynamic_sql.models.datapoint import WritableDataPoint, DisplayDataPoint
from skipper.dataseries.storage.dynamic_sql.models.dimension import WritableDataPoint_Dimension, BaseDataPoint_Dimension
from skipper.dataseries.storage.dynamic_sql.models.facts.boolean_fact import WritableDataPoint_BooleanFact
from skipper.dataseries.storage.dynamic_sql.models.facts.file_fact import WritableDataPoint_FileFact
from skipper.dataseries.storage.dynamic_sql.models.facts.float_fact import WritableDataPoint_FloatFact
from skipper.dataseries.storage.dynamic_sql.models.facts.image_fact import WritableDataPoint_ImageFact
from skipper.dataseries.storage.dynamic_sql.models.facts.json_fact import WritableDataPoint_JsonFact
from skipper.dataseries.storage.dynamic_sql.models.facts.string_fact import WritableDataPoint_StringFact
from skipper.dataseries.storage.dynamic_sql.models.facts.text_fact import WritableDataPoint_TextFact
from skipper.dataseries.storage.dynamic_sql.models.facts.timestamp_fact import WritableDataPoint_TimestampFact
from skipper.dataseries.storage.dynamic_sql.queries.display import data_series_as_sql_table
from skipper.dataseries.storage.dynamic_sql.queries.modification_materialized.insert import insert_or_update_data_points
from skipper.dataseries.storage.dynamic_sql.queries.select_info import select_infos
from skipper.dataseries.storage.static_ds_information import compute_data_series_query_info, \
    data_point_serialization_keys
from skipper.dataseries.storage.uuid import gen_uuid

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
        _some_point_in_time_str,
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
        # subclock does not matter here, so just get one
        sub_clock=dbtime.dp_sub_clock(Tenant.objects.get(name='default_tenant')),
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

    # prune should not delete datapoints if there is exactly one there
    # now delete everything by choosing a date in the future
    prune_response = self.client.post(
        path=data_series['prune_history'],
        data={
            'older_than': dbtime.now() + timezone.timedelta(days=30)
        },
        format='json'
    )
    self.assertEqual(prune_response.status_code, status.HTTP_200_OK)
    _data_points_after_prune_on_deleted_via_api = self.get_payload(
        url=data_series['history_data_points'] + f'?count'
    )['data']
    self.assertEqual(1, len(_data_points_after_prune_on_deleted_via_api))

    if test_filtering:
        fact_id = fact['external_id']
        original_list = self.get_payload(
            url=data_series['data_points'] + f'?count&{filter_query_param(fact_id, _initial_value())}')
        self.assertEqual(1, original_list['count'])
        self.assertEqual(1, len(original_list['data']))
    else:
        original_list = self.get_payload(
            url=data_series['data_points'] + f'?count')
        self.assertEqual(1, original_list['count'])
        self.assertEqual(1, len(original_list['data']))

    # end prune intermezzo

    original_version = initial['point_in_time']
    original_version_date_time = dateparse.parse_datetime(original_version)
    original_version = quote(str(original_version))
    self.assertTrue(equal(_initial_value(), initial['payload'][fact['external_id']]))

    query_as_point_in_time_but_current = self.get_payload(initial['history_url'] + f'?point_in_time={original_version}')
    self.assertTrue(equal(_initial_value(), query_as_point_in_time_but_current['payload'][fact['external_id']]))
    self.assertTrue(equal(_secondary_initial_value(),
                          query_as_point_in_time_but_current['payload'][secondary_fact['external_id']]))

    all_original_versions = self._query_versions(initial['history_url'])
    original_fact_versions = self._versions_for_fact(fact, all_original_versions)
    original_secondary_fact_versions = self._versions_for_fact(secondary_fact, all_original_versions)
    self.assertEqual(1, len(all_original_versions['data_point']))
    self.assertEqual(1, len(original_fact_versions))
    self.assertEqual(1, len(original_secondary_fact_versions))
    self.assertEqual(1, len(set(self._point_in_time_from_versions(
        all_original_versions['data_point'] + original_fact_versions + original_secondary_fact_versions))))

    self.assertEqual(original_version_date_time,
                     dateparse.parse_datetime(all_original_versions['data_point'][0]['point_in_time']))
    self.assertEqual(original_version_date_time,
                     dateparse.parse_datetime(original_fact_versions[0]['point_in_time']))
    self.assertEqual(original_version_date_time,
                     dateparse.parse_datetime(original_secondary_fact_versions[0]['point_in_time']))

    if backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED.value:
        test_materialized_upsert_checks_point_in_time(
            self=self,
            current_data_point=initial,
            data_series_id=data_series['id'],
            data_series_external_id=data_series['external_id'],
            fact=fact,
            secondary_fact=secondary_fact,
            partial=partial,
            fact_value_that_should_not_be_set=_updated_value,
            secondary_fact_value_that_should_not_be_set=_secondary_updated_value,
            expected_to_be_found_at_all=True,
            expected_fact_value=_initial_value,
            fact_type=fact_type,
            equal=equal
        )

    if partial:
        updated = self.patch_payload(
            url=initial['url'], payload=lambda: {
                f'payload.{fact["external_id"]}': _updated_value()
            }, format='multipart'
        )
        self.assertTrue(equal(_updated_value(), updated['payload'][fact['external_id']]))
        # secondary fact should stay the same if we patch without it
        self.assertTrue(equal(_secondary_initial_value(), updated['payload'][secondary_fact['external_id']]))

        all_partial_updated_versions = self._query_versions(updated['history_url'])
        updated_fact_versions = self._versions_for_fact(fact, all_partial_updated_versions)
        updated_secondary_fact_versions = self._versions_for_fact(secondary_fact, all_partial_updated_versions)
        # 2020-03-05: Martin: PUT/PATCH should now also add a new version to the datapoint, this will improve queries
        self.assertEqual(2, len(all_partial_updated_versions['data_point']))
        self.assertEqual(2, len(updated_fact_versions))
        self.assertEqual(1, len(updated_secondary_fact_versions))
        self.assertEqual(2, len(set(self._point_in_time_from_versions((all_partial_updated_versions[
                                                                           'data_point'] + updated_fact_versions + updated_secondary_fact_versions)))))

        updated_query_as_point_in_time_but_current = self.get_payload(
            initial['history_url'] + f'?point_in_time=2119-12-16T22:03:38.415363Z')
        self.assertTrue(
            equal(_updated_value(), updated_query_as_point_in_time_but_current['payload'][fact['external_id']]))
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

        all_put_updated_versions = self._query_versions(updated['history_url'])
        updated_fact_versions = self._versions_for_fact(fact, all_put_updated_versions)
        updated_secondary_fact_versions = self._versions_for_fact(secondary_fact, all_put_updated_versions)
        # 2020-03-05: Martin: PUT/PATCH should now also add a new version to the datapoint, this will improve queries
        self.assertEqual(2, len(all_put_updated_versions['data_point']))
        self.assertEqual(2, len(updated_fact_versions))
        self.assertEqual(2, len(updated_secondary_fact_versions))
        self.assertEqual(2, len(set(self._point_in_time_from_versions(
            all_put_updated_versions['data_point'] + updated_fact_versions + updated_secondary_fact_versions))))

        updated_query_as_point_in_time_but_current = self.get_payload(
            initial['history_url'] + f'?point_in_time=2119-12-16T22:03:38.415363Z')
        self.assertTrue(
            equal(_updated_value(), updated_query_as_point_in_time_but_current['payload'][fact['external_id']]))

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

        original_list_time_travel = self.get_payload(
            url=data_series[
                    'history_data_points'] + f'?point_in_time={original_version}&count&{filter_query_param(fact_id, _initial_value())}')
        self.assertEqual(1, original_list_time_travel['count'])
        self.assertEqual(1, len(original_list_time_travel['data']))

    # after we have updated the payload, we should still have the same payload value if we query
    # for the old version
    older_version = self.get_payload(initial['history_url'] + f'?point_in_time={original_version}')
    self.assertTrue(equal(_initial_value(), older_version['payload'][fact['external_id']]))
    self.assertTrue(equal(_secondary_initial_value(), older_version['payload'][secondary_fact['external_id']]))
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
    # also hit the detail endpoint, count does not make sense here, but will just be ignored
    _internal_same_as(self.get_payload(url=f"{json_list['data'][0]['history_url']}{query_str}"))


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

    def _query_versions(self, data_point_history_url: str) -> Any:
        dp = self.get_payload(url=f'{data_point_history_url}?include_versions')
        return dp['versions']

    def _versions_for_fact(self, fact: Dict[str, Any], versions: Dict[str, Any]) -> List[Dict[str, Any]]:
        return cast(List[Dict[str, Any]], versions['payload'][fact['external_id']])

    def _point_in_time_from_versions(self, versions: List[Dict[str, Any]]) -> List[str]:
        return [elem['point_in_time'] for elem in versions]

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
            writable_type: Union[Type[BaseDataPointFactRelation], Type[BaseDataPoint_Dimension]],
            debug: bool = False,
            reference_1: Optional[Dict[str, Any]] = None,
            reference_2: Optional[Dict[str, Any]] = None
    ) -> None:
        initial_value = _initial_value()
        secondary_initial_value = _secondary_initial_value()

        data_series = self._setup_data_series_for_test(backend, fact_type)
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
            url=data_series['history_data_points'],
            query_str=f'?count&point_in_time={quote(_initial["point_in_time"])}',
            expected=_initial
        )
        same_as(
            self=self,
            equal=equal,
            fact=fact,
            url=data_series['history_data_points'],
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

        # but we can still get the old un-deleted values:

        same_as(url=data_series['history_data_points'], query_str=f'?count&point_in_time={quote(_initial["point_in_time"])}',
                expected=_initial, equal=equal, self=self, fact=fact)

        undeleted_payloads = self.get_payload(url=data_series['history_data_points'] + f'?count&point_in_time={quote(_initial["point_in_time"])}&include_versions')
        versions_after_delete = undeleted_payloads['data'][0]['versions']

        # we should find the original version and the deleted version in here
        # 2020-03-05: Martin: PUT/PATCH should now also add a new version to the datapoint, this will improve queries
        self.assertEqual(3, len(versions_after_delete['data_point']))

        __url = undeleted_payloads['data'][0]['history_url']
        initial_after_delete = self.get_payload(__url, payload={
            'point_in_time': versions_after_delete["data_point"][0]['point_in_time']})
        self.assertTrue(equal(initial_value, initial_after_delete['payload'][fact['external_id']]))
        self.assertTrue(equal(secondary_initial_value, initial_after_delete['payload'][secondary_fact['external_id']]))

        # TODO: check if we can get back all different versions of this data point, we do not know the timestamp of
        # the updated value, this has to be added to the rest api, as it is not supported at the moment

        # PRUNE TESTING

        # prune history, but keep
        _versions_before_prune = self.get_payload(
            url=data_series['history_data_points'] + f'?count&point_in_time={quote(_timestamp_before_delete.isoformat())}&include_versions'
        )['data'][0]['versions']
        _fact_versions_before_prune = self._versions_for_fact(fact, _versions_before_prune)
        _secondary_versions_before_prune = self._versions_for_fact(secondary_fact, _versions_before_prune)
        if partial:
            self.assertEqual(3, len(_versions_before_prune['data_point']))
            # delete does not write new data to facts/dims
            self.assertEqual(2, len(_fact_versions_before_prune))
            self.assertEqual(1, len(_secondary_versions_before_prune))
            self.assertEqual(3, len(set(self._point_in_time_from_versions(
                _versions_before_prune['data_point'] + _fact_versions_before_prune + _secondary_versions_before_prune))))
        else:
            self.assertEqual(3, len(_versions_before_prune['data_point']))
            # delete does not write new data to facts/dims
            self.assertEqual(2, len(_fact_versions_before_prune))
            self.assertEqual(2, len(_secondary_versions_before_prune))
            self.assertEqual(3, len(set(self._point_in_time_from_versions(
                _versions_before_prune[
                    'data_point'] + _fact_versions_before_prune + _secondary_versions_before_prune))))

        if backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED.value:
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

        # by default it should only try to delete everything that is older than a while
        prune_response = self.client.post(
            path=data_series['prune_history'],
            data={},
            format='json'
        )
        self.assertEqual(prune_response.status_code, status.HTTP_200_OK)
        # use history endpoint at point in time before deletion
        _versions_after_prune_with_default_date = self.get_payload(
            url=data_series['history_data_points'] + f'?count&point_in_time={quote(_timestamp_before_delete.isoformat())}&include_versions'
        )['data'][0]['versions']
        self.assertEqual(len(_versions_before_prune['data_point']), len(_versions_after_prune_with_default_date['data_point']))

        # now delete everything until time of delete
        prune_response = self.client.post(
            path=data_series['prune_history'],
            data={
                'older_than': _timestamp_before_delete
            },
            format='json'
        )
        self.assertEqual(prune_response.status_code, status.HTTP_200_OK)
        _data_points_after_prune_on_deleted_via_api = self.get_payload(
            url=data_series['history_data_points'] + f'?count&point_in_time={quote(dbtime.now().isoformat())}&include_versions'
        )['data']
        # should not be available via REST API since only a deleted one is there
        self.assertEqual(0, len(_data_points_after_prune_on_deleted_via_api))

        # after pruning everything data should only exist for the current ones
        self.assertEqual(1, WritableDataPoint.objects.filter(
            data_series_id=data_series['id']
        ).all().count())

        # TODO: test that materialized data is still there

        # should be zero since we only tagged as deleted in the delete operation, so the data is actually gone
        if fact_type != 'dimension':
            self.assertEqual(0, writable_type.objects.filter(
                fact_id=fact['id']
            ).all().count())
            self.assertEqual(0, writable_type.objects.filter(
                fact_id=secondary_fact['id']
            ).all().count())
        else:
            self.assertEqual(0, writable_type.objects.filter(
                dimension_id=fact['id']
            ).all().count())
            self.assertEqual(0, writable_type.objects.filter(
                dimension_id=secondary_fact['id']
            ).all().count())

        # now delete everything by choosing a date in the future
        prune_response = self.client.post(
            path=data_series['prune_history'],
            data={
                'older_than': dbtime.now() + timezone.timedelta(days=30)
            },
            format='json'
        )
        self.assertEqual(prune_response.status_code, status.HTTP_200_OK)
        _data_points_after_prune_on_deleted_via_api = self.get_payload(
            url=data_series['history_data_points'] + f'?count&point_in_time={quote(dbtime.now().isoformat())}&include_versions'
        )['data']
        self.assertEqual(0, len(_data_points_after_prune_on_deleted_via_api))

        # after pruning everything data should only exist for the current ones

        self.assertEqual(0, WritableDataPoint.objects.filter(
            data_series_id=data_series['id']
        ).all().count())

        if fact_type != 'dimension':
            self.assertEqual(0, writable_type.objects.filter(
                fact_id=fact['id']
            ).all().count())
            self.assertEqual(0, writable_type.objects.filter(
                fact_id=secondary_fact['id']
            ).all().count())
        else:
            self.assertEqual(0, writable_type.objects.filter(
                dimension_id=fact['id']
            ).all().count())
            self.assertEqual(0, writable_type.objects.filter(
                dimension_id=secondary_fact['id']
            ).all().count())


        # FIXME: this does not really test anything anymore. separate into different test!
        # FIXME: test prune should also prune facts properly (and not lose data if prune works!)
        # truncate
        truncate_response = self.client.post(
            path=data_series['truncate'],
            data={},
            format='json'
        )
        self.assertEqual(truncate_response.status_code, status.HTTP_200_OK)

        self.assertEqual(0, WritableDataPoint.objects.filter(
            data_series_id=data_series['id']
        ).all().count())

        if fact_type != 'dimension':
            self.assertEqual(0, writable_type.objects.filter(
                fact_id=fact['id']
            ).all().count())
            self.assertEqual(0, writable_type.objects.filter(
                fact_id=secondary_fact['id']
            ).all().count())
        else:
            self.assertEqual(0, writable_type.objects.filter(
                dimension_id=fact['id']
            ).all().count())
            self.assertEqual(0, writable_type.objects.filter(
                dimension_id=secondary_fact['id']
            ).all().count())


class FloatFactLifecycleTest(BaseDataPointLifecycleTest):
    def test_float_facts(self) -> None:
        for backend_key, backend_value in StorageBackendType.choices_with_split_history():
            for optional in [False, True]:
                for partial in [False, True]:
                    self._test_data_point_lifecycle(True, 'float', backend_key, optional, lambda: 1, lambda: 1,
                                                    lambda: 2, lambda x, y: x == y, partial,
                                                    WritableDataPoint_FloatFact)


class BooleanFactLifecycleTest(BaseDataPointLifecycleTest):
    def test_boolean_facts(self) -> None:
        for backend_key, backend_value in StorageBackendType.choices_with_split_history():
            for optional in [False, True]:
                for partial in [False, True]:
                    self._test_data_point_lifecycle(True, 'boolean', backend_key, optional, lambda: True, lambda: True,
                                                    lambda: False, lambda x, y: x == y, partial,
                                                    WritableDataPoint_BooleanFact)


class StringFactLifecycleTest(BaseDataPointLifecycleTest):
    def test_string_facts(self) -> None:
        for backend_key, backend_value in StorageBackendType.choices_with_split_history():
            for optional in [False, True]:
                for partial in [False, True]:
                    self._test_data_point_lifecycle(True, 'string', backend_key, optional, lambda: '1', lambda: '1',
                                                    lambda: '2', lambda x, y: x == y, partial,
                                                    WritableDataPoint_StringFact)


class TextFactLifecycleTest(BaseDataPointLifecycleTest):
    def test_text_facts(self) -> None:
        for backend_key, backend_value in StorageBackendType.choices_with_split_history():
            for optional in [False, True]:
                for partial in [False, True]:
                    self._test_data_point_lifecycle(True, 'text', backend_key, optional, lambda: '1', lambda: '1',
                                                    lambda: '2', lambda x, y: x == y, partial,
                                                    WritableDataPoint_TextFact)


class JsonFactLifecycleTest(BaseDataPointLifecycleTest):
    def test_json_facts(self) -> None:
        for backend_key, backend_value in StorageBackendType.choices_with_split_history():
            for optional in [False, True]:
                for partial in [False, True]:
                    # numbers are valid json as well. we just want to check if everything works properly
                    # and we use multipart in the function so only numbers work here
                    self._test_data_point_lifecycle(False, 'json', backend_key, optional, lambda: 1, lambda: 1,
                                                    lambda: 2, lambda x, y: x == y, partial, WritableDataPoint_JsonFact)


class TimestampFactLifecycleTest(BaseDataPointLifecycleTest):
    def test_timestamp_facts(self) -> None:
        _1 = '2019-12-15T19:09:25.007985'  # format from postgres!
        _2 = '2019-12-15T19:09:26.007985'

        def equal(x: Any, y: Any) -> bool:
            return str(x) == str(y)

        for backend_key, backend_value in StorageBackendType.choices_with_split_history():
            for optional in [False, True]:
                for partial in [False, True]:
                    self._test_data_point_lifecycle(True, 'timestamp', backend_key, optional, lambda: _1, lambda: _1,
                                                    lambda: _2, equal,
                                                    partial, WritableDataPoint_TimestampFact)


class ImageFactLifecycleTest(BaseDataPointLifecycleTest):
    def test_image_facts(self) -> None:
        for backend_key, backend_value in StorageBackendType.choices_with_split_history():
            for optional in [False, True]:
                for partial in [False, True]:
                    # FIXME: check image is actually the same byte by byte
                    self._test_data_point_lifecycle(False, 'image', backend_key, optional, generate_photo_file,
                                                    generate_photo_file, generate_some_other_photo_file,
                                                    lambda x, y: True, partial, WritableDataPoint_ImageFact)

class FileFactLifecycleTest(BaseDataPointLifecycleTest):
    def test_file_facts(self) -> None:
        for backend_key, backend_value in StorageBackendType.choices_with_split_history():
            for optional in [False, True]:
                for partial in [False, True]:
                    # FIXME: check file is actually the same byte by byte
                    self._test_data_point_lifecycle(False, 'file', backend_key, optional, generate_photo_file,
                                                    generate_photo_file, generate_some_other_photo_file,
                                                    lambda x, y: True, partial, WritableDataPoint_FileFact)


class DimensionLifecycleTest(BaseDataPointLifecycleTest):
    def test_dimensions(self) -> None:
        for backend_key, backend_value in StorageBackendType.choices_with_split_history():
            def equal(x: Any, y: Any) -> bool:
                return str(x) == str(y)

            data_series_for_dim_1 = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
                'name': f'my_data_series_dim_1_{backend_key}',
                'external_id': f'_dim_ds_1_{backend_key}',
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
                'external_id': f'_dim_ds_2_{backend_key}',
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
                        WritableDataPoint_Dimension,
                        reference_1=data_series_for_dim_1,
                        reference_2=data_series_for_dim_2
                    )


del BaseDataPointLifecycleTest
