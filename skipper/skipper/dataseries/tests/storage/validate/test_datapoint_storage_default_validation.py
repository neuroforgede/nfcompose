# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import uuid

import datetime
from django.http import QueryDict
from django.test import TestCase
from django.utils.dateparse import parse_datetime
from django_multitenant.utils import set_current_tenant, get_current_tenant  # type: ignore
from rest_framework.exceptions import ValidationError, APIException
from typing import Any, List, cast, Union, Optional

from skipper.core.models.tenant import Tenant
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.storage.actions import handle_create_data_series
from skipper.dataseries.storage.contract import StorageBackendType
from skipper.dataseries.storage.dynamic_sql.models.datapoint import DataPoint
from skipper.dataseries.storage.uuid import gen_uuid

from skipper.dataseries.storage.static_ds_information import DataSeriesQueryInfo, DataSeriesFactQueryInfo, \
    ReadOnlyFact, ReadOnlyBaseDataSeriesFactRelation, DataSeriesDimensionQueryInfo, ReadOnlyDimension, \
    ReadOnlyDataSeries, ReadOnlyDataSeries_Dimension
from skipper.dataseries.storage.validate.contract import ValidationRequest, DataPointAccessor, ReadOnlyDataPoint
from skipper.dataseries.storage.validate.default import validate


class Base(TestCase):
    data_series: DataSeries

    by_external_id: bool = False

    def setUp(self) -> None:
        tenant = Tenant.objects.create(
            name="test_tenant"
        )
        tenant.save()
        set_current_tenant(tenant)

        self.data_series = DataSeries.objects.create(
            tenant=tenant,
            external_id="my_data_series",
            name="my_data_series_name",
            allow_extra_fields=False
        )
        self.data_series.save()

    def tearDown(self) -> None:
        set_current_tenant(None)

    def get_data_point_accessor(self) -> DataPointAccessor:
        def accessor(
                identifier: str,
                data_series_id: Union[str, uuid.UUID]
        ) -> Optional[ReadOnlyDataPoint]:
            return None
        return accessor

    def empty_request(self) -> ValidationRequest:
        return ValidationRequest(
            # data point id is none => new datapoint
            data_point_id=None,
            data_point_relation_info=DataSeriesQueryInfo(
                data_series_id=self.data_series.id,
                backend=self.data_series.backend,
                locked=self.data_series.locked,
                schema_name='',
                main_query_table_name='',
                main_extra_fields=[],
                materialized_flat_history_table_name='',
                float_facts={},
                string_facts={},
                text_facts={},
                timestamp_facts={},
                image_facts={},
                file_facts={},
                json_facts={},
                boolean_facts={},
                dimensions={},
                main_alive_filter='ds_dp.deleted_at IS NULL'
            ),
            partial=False,
            bulk_insert=False,
            external_id_as_dimension_identifier=self.by_external_id,
            data_point_accessor=self.get_data_point_accessor()
        )


class GeneralTest(Base):
    def test_external_id_missing(self) -> None:
        validation_request = self.empty_request()
        try:
            validate(
                data={
                    'payload': {}
                },
                request=validation_request
            )
            self.fail('expected validation to fail if no payload is set')
        except ValidationError as e:
            pass

    def test_payload_missing(self) -> None:
        validation_request = self.empty_request()
        try:
            validate(
                data={
                    'external_id': '1'
                },
                request=validation_request
            )
            self.fail('expected validation to fail if no payload is set')
        except ValidationError as e:
            pass

    def test_payload_list(self) -> None:
        validation_request = self.empty_request()
        try:
            validate(
                data={
                    'external_id': '1',
                    'payload': []
                },
                request=validation_request
            )
            self.fail('expected validation to fail if payload is no dict')
        except ValidationError as e:
            pass

    def test_payload_string(self) -> None:
        validation_request = self.empty_request()
        try:
            validate(
                data={
                    'external_id': '1',
                    'payload': "1"
                },
                request=validation_request
            )
            self.fail('expected validation to fail if payload is no dict')
        except ValidationError as e:
            pass

    def test_payload_number(self) -> None:
        validation_request = self.empty_request()
        try:
            validate(
                data={
                    'external_id': '1',
                    'payload': "1"
                },
                request=validation_request
            )
            self.fail('expected validation to fail if payload is no dict')
        except ValidationError as e:
            pass

    def test_payload_None(self) -> None:
        validation_request = self.empty_request()
        try:
            validate(
                data={
                    'external_id': '1',
                    'payload': None
                },
                request=validation_request
            )
            self.fail('expected validation to fail if payload is None')
        except ValidationError as e:
            pass

    def test_external_id_wrong_type(self) -> None:
        validation_request = self.empty_request()
        for wrong_type in [1, 1.0, False, True, [], {}, object()]:
            try:
                validate(
                    data={
                        'external_id': wrong_type,
                        'payload': {}
                    },
                    request=validation_request
                )
                self.fail('expected validation to fail if payload has wrong type')
            except ValidationError as e:
                pass

    def test_payload_empty_dict(self) -> None:
        validation_request = self.empty_request()
        result = validate(
            data={
                'external_id': '1',
                'payload': {}
            },
            request=validation_request
        )
        self.assertTrue('external_id' in result)
        self.assertTrue('payload' in result)
        self.assertTrue(isinstance(result['payload'], dict))
        self.assertEquals(0, len(result['payload']))

    def test_payload_multi_value_dict(self) -> None:
        validation_request = self.empty_request()
        try:
            validate(
                data={
                    'external_id': '1',
                    'payload': QueryDict()
                },
                request=validation_request
            )
            self.fail('expected validation to fail if payload is is a MultiValueDict')
        except APIException as e:
            pass


class BaseFactTest(Base):
    name: str
    type: Any

    correct_values: List[Any]
    wrong_values: List[Any]

    def add_fact(self, validation_request: ValidationRequest, optional: bool) -> None:
        raise NotImplementedError()

    def fact(self, external_id: str, optional: bool) -> DataSeriesFactQueryInfo:
        fact_id = uuid.uuid4()
        _actual_fact = ReadOnlyFact(
            id=fact_id,
            name='MY_NAME',
            optional=optional
        )
        return DataSeriesFactQueryInfo(
            id=str(fact_id),
            unescaped_display_id=external_id,
            fact=_actual_fact,
            dataseries_fact=ReadOnlyBaseDataSeriesFactRelation(
                id=str(fact_id),
                external_id=external_id,
                fact=_actual_fact,
                point_in_time=parse_datetime('2020-04-24T13:31:41.508305Z')
            ),
            value_column=''
        )

    def test_payload_missing(self) -> None:
        validation_request = self.empty_request()
        self.add_fact(validation_request, False)
        try:
            validate(
                data={
                    'external_id': '1',
                    'payload': {}
                },
                request=validation_request
            )
            self.fail(f'expected validation to fail if payload is missing a required {self.name} fact')
        except ValidationError as e:
            self.assertTrue(f'{self.name} fact' in str(e.detail),
                            'error message should contain information about which type the missing fact has')
            self.assertTrue('facty_boy' in str(e.detail),
                            'error message should contain information about the missing fact')

    def test_payload_not_proper_type(self) -> None:
        validation_request = self.empty_request()
        self.add_fact(validation_request, False)
        for wrong_value in self.wrong_values:
            try:
                validate(
                    data={
                        'external_id': '1',
                        'payload': {
                            'facty_boy': wrong_value
                        }
                    },
                    request=validation_request
                )
                self.fail(
                    f'expected validation to fail if payload value is no {self.name} for wrong value {wrong_value}')
            except ValidationError as e:
                self.assertTrue('facty_boy' in str(e.detail),
                                'error message should contain information about the missing fact')

    def test_payload_proper_type(self) -> None:
        validation_request = self.empty_request()
        self.add_fact(validation_request, False)
        for correct_value in self.correct_values:
            result = validate(
                data={
                    'external_id': '1',
                    'payload': {
                        'facty_boy': correct_value
                    }
                },
                request=validation_request
            )

            self.assertTrue('external_id' in result)
            self.assertTrue('payload' in result)
            self.assertTrue(isinstance(result['payload'], dict))
            self.assertEquals(1, len(result['payload']))
            self.assertTrue(isinstance(result['payload']['facty_boy'], self.type))
            self.assertEquals(correct_value, result['payload']['facty_boy'])

    def test_optional_null(self) -> None:
        validation_request = self.empty_request()
        self.add_fact(validation_request, True)
        result = validate(
            data={
                'external_id': '1',
                'payload': {
                    'facty_boy': None
                }
            },
            request=validation_request
        )

        self.assertTrue('external_id' in result)
        self.assertTrue('payload' in result)
        self.assertTrue(isinstance(result['payload'], dict))
        self.assertEquals(1, len(result['payload']))
        self.assertEquals(None, result['payload']['facty_boy'])

    def test_optional_not_present(self) -> None:
        validation_request = self.empty_request()
        self.add_fact(validation_request, True)
        result = validate(
            data={
                'external_id': '1',
                'payload': {}
            },
            request=validation_request
        )

        self.assertTrue('external_id' in result)
        self.assertTrue('payload' in result)
        self.assertTrue(isinstance(result['payload'], dict))
        self.assertEquals(0, len(result['payload']))


class FloatFactTest(BaseFactTest):
    name = 'float'
    type = float

    correct_values = [1, 1.0, 1.337, int(1)]
    wrong_values = [False, True, '1', '', [], {}, object(), parse_datetime('2020-04-24T13:31:41.508305Z')]

    def add_fact(self, validation_request: ValidationRequest, optional: bool) -> None:
        validation_request.data_point_relation_info.float_facts['facty_boy'] = self.fact(
            external_id='facty_boy',
            optional=optional
        )


class StringFactTest(BaseFactTest):
    name = 'string'
    type = str

    correct_values = ['', 'hello moto']
    wrong_values = [False, True, int(1), 1.337, [], {}, object(), parse_datetime('2020-04-24T13:31:41.508305Z')]

    def add_fact(self, validation_request: ValidationRequest, optional: bool) -> None:
        validation_request.data_point_relation_info.string_facts['facty_boy'] = self.fact(
            external_id='facty_boy',
            optional=optional
        )


class TextFactTest(BaseFactTest):
    name = 'text'
    type = str

    correct_values = ['', 'hello moto']
    wrong_values = [False, True, int(1), 1.337, [], {}, object(), parse_datetime('2020-04-24T13:31:41.508305Z')]

    def add_fact(self, validation_request: ValidationRequest, optional: bool) -> None:
        validation_request.data_point_relation_info.text_facts['facty_boy'] = self.fact(
            external_id='facty_boy',
            optional=optional
        )


class TimestampFactTest(BaseFactTest):
    name = 'timestamp'
    type = datetime.datetime

    correct_values = [parse_datetime('2020-04-24T13:31:41.508305Z'), parse_datetime('2020-04-24T13:31:41.508303')]
    wrong_values = [False, True, int(1), 1.337, [], {}, object(), '', 'hello moto']

    def add_fact(self, validation_request: ValidationRequest, optional: bool) -> None:
        validation_request.data_point_relation_info.timestamp_facts['facty_boy'] = self.fact(
            external_id='facty_boy',
            optional=optional
        )


class JSONFactTest(BaseFactTest):
    name = 'json'
    type = object

    correct_values = [False, True, dict(), {}, [], 1, 1.337, '', 'hello moto', {'abc': 'def'}]
    wrong_values = [parse_datetime('2020-04-24T13:31:41.508305Z'), object()]

    def add_fact(self, validation_request: ValidationRequest, optional: bool) -> None:
        validation_request.data_point_relation_info.json_facts['facty_boy'] = self.fact(
            external_id='facty_boy',
            optional=optional
        )


class ImageFactTest(BaseFactTest):
    name = 'image'
    type = object

    # for images we kinda have to trust django
    # FIXME: dont just rely on django here
    correct_values: List[Any] = []
    wrong_values = [False, True, dict(), {}, [], 1, 1.337, '', 'hello moto', {'abc': 'def'}]

    def add_fact(self, validation_request: ValidationRequest, optional: bool) -> None:
        validation_request.data_point_relation_info.image_facts['facty_boy'] = self.fact(
            external_id='facty_boy',
            optional=optional
        )


class FileFactTest(BaseFactTest):
    name = 'file'
    type = object

    # for images we kinda have to trust django
    # FIXME: dont just rely on django here
    correct_values: List[Any] = []
    wrong_values = [False, True, dict(), {}, [], 1, 1.337, '', 'hello moto', {'abc': 'def'}]

    def add_fact(self, validation_request: ValidationRequest, optional: bool) -> None:
        validation_request.data_point_relation_info.file_facts['facty_boy'] = self.fact(
            external_id='facty_boy',
            optional=optional
        )


class DimensionTest(Base):

    correct_values: List[str]
    wrong_values: List[str]

    def setUp(self) -> None:
        super().setUp()
        self.data_series_for_dim = DataSeries.objects.create(
            tenant=get_current_tenant(),
            external_id="my_data_series2",
            name="my_data_series_name2",
            allow_extra_fields=False
        )
        handle_create_data_series(
            data_series_id=self.data_series_for_dim.id,
            data_series_external_id=self.data_series_for_dim.external_id,
            tenant_name='hans_peter',
            external_id=self.data_series_for_dim.external_id,
            backend=StorageBackendType.DYNAMIC_SQL_MATERIALIZED.value,
            tenant_id=get_current_tenant().id
        )
        self.data_series_for_dim.save()

        self.data_point_for_dim = DataPoint.objects.create(
            id=gen_uuid(self.data_series_for_dim.id, 'some_external_id2'),
            data_series_id=self.data_series_for_dim.id,
            external_id='some_external_id2',
            deleted=False,
            point_in_time=parse_datetime('2020-04-24T13:31:41.508305Z'),
            user_id='3',
            record_source='UNIT TEST'
        )
        # if we set external and actual id as correct and wrong (and vice versa)
        # we implicitly test if checks for datapoint existance work
        if self.by_external_id:
            self.correct_values = [self.data_point_for_dim.external_id]
            self.wrong_values = [self.data_point_for_dim.id]
        else:
            self.correct_values = [self.data_point_for_dim.id]
            self.wrong_values = [self.data_point_for_dim.external_id]

    def add_dimension(self, validation_request: ValidationRequest, optional: bool) -> None:
        validation_request.data_point_relation_info.dimensions['dimmy_boy'] = self.dimension(
            external_id='dimmy_boy',
            optional=optional
        )

    def get_data_point_accessor(self) -> DataPointAccessor:
        def accessor(
                identifier: str,
                data_series_id: Union[str, uuid.UUID],
        ) -> Optional[ReadOnlyDataPoint]:
            if data_series_id != self.data_series.id:
                uuid = gen_uuid(self.data_series_for_dim.id, 'some_external_id2')
                if uuid == identifier:
                    return ReadOnlyDataPoint(
                        id=uuid,
                        data_series_id=self.data_series_for_dim.id,
                        external_id='some_external_id2'
                    )
                return None
            else:
                return None

        return accessor

    def dimension(self, external_id: str, optional: bool) -> DataSeriesDimensionQueryInfo:
        dim_id = uuid.uuid4()
        _actual_dim = ReadOnlyDimension(
            id=dim_id,
            name='MY_NAME',
            optional=optional,
            reference=ReadOnlyDataSeries(
                id=self.data_series_for_dim.id,
                schema_name='',
                main_query_table_name='',
                materialized_flat_history_table_name='',
                backend=self.data_series_for_dim.backend,
                locked=self.data_series_for_dim.locked,
                main_alive_filter='ds_dp.deleted_at IS NULL'
            )
        )
        return DataSeriesDimensionQueryInfo(
            id=str(dim_id),
            unescaped_display_id=external_id,
            dimension=_actual_dim,
            dataseries_dimension=ReadOnlyDataSeries_Dimension(
                id=str(dim_id),
                external_id=external_id,
                dimension=_actual_dim,
                point_in_time=parse_datetime('2020-04-24T13:31:41.508305Z')
            ),
            value_column=''
        )

    def test_payload_missing(self) -> None:
        validation_request = self.empty_request()
        self.add_dimension(validation_request, False)
        try:
            validate(
                data={
                    'external_id': '1',
                    'payload': {}
                },
                request=validation_request
            )
            self.fail(f'expected validation to fail if payload is missing a required dimension')
        except ValidationError as e:
            self.assertTrue(f'dimension' in str(e.detail),
                            'error message should contain information about which type the missing dimension has')
            self.assertTrue('dimmy_boy' in str(e.detail),
                            'error message should contain information about the missing dimension')

    def test_payload_not_proper_type(self) -> None:
        validation_request = self.empty_request()
        self.add_dimension(validation_request, False)
        for wrong_value in [False, True, dict(), {}, [], 1, 1.337, {'abc': 'def'}]:
            try:
                validate(
                    data={
                        'external_id': '1',
                        'payload': {
                            'dimmy_boy': wrong_value
                        }
                    },
                    request=validation_request
                )
                self.fail(
                    f'expected validation to fail if payload value can not be a dimension value for wrong value {wrong_value}')
            except ValidationError as e:
                self.assertTrue('dimmy_boy' in str(e.detail),
                                'error message should contain information about the missing dimension')

    def test_payload_not_proper_type_not_exist(self) -> None:
        validation_request = self.empty_request()
        self.add_dimension(validation_request, False)
        for wrong_value in self.wrong_values:
            try:
                validate(
                    data={
                        'external_id': '1',
                        'payload': {
                            'dimmy_boy': wrong_value
                        }
                    },
                    request=validation_request
                )
                self.fail(
                    f'expected validation to fail if payload value can not be a dimension value for wrong value {wrong_value}')
            except ValidationError as e:
                self.assertTrue('dimmy_boy' in str(e.detail),
                                'error message should contain information about the missing dimension')
                self.assertTrue('not exist' in str(e.detail))

    def test_payload_proper_type(self) -> None:
        validation_request = self.empty_request()
        self.add_dimension(validation_request, False)
        for correct_value in self.correct_values:
            result = validate(
                data={
                    'external_id': '1',
                    'payload': {
                        'dimmy_boy': correct_value
                    }
                },
                request=validation_request
            )
            self.assertTrue('external_id' in result)
            self.assertTrue('payload' in result)
            self.assertTrue(isinstance(result['payload'], dict))
            self.assertEquals(1, len(result['payload']))
            self.assertTrue(isinstance(result['payload']['dimmy_boy'], str))
            if self.by_external_id:
                self.assertEquals(self.data_point_for_dim.id, result['payload']['dimmy_boy'])
            else:
                self.assertEquals(correct_value, result['payload']['dimmy_boy'])

    def test_optional_null(self) -> None:
        validation_request = self.empty_request()
        self.add_dimension(validation_request, True)
        result = validate(
            data={
                'external_id': '1',
                'payload': {
                    'dimmy_boy': None
                }
            },
            request=validation_request
        )
        self.assertTrue('external_id' in result)
        self.assertTrue('payload' in result)
        self.assertTrue(isinstance(result['payload'], dict))
        self.assertEquals(1, len(result['payload']))
        self.assertEquals(None, result['payload']['dimmy_boy'])

    def test_optional_not_present(self) -> None:
        validation_request = self.empty_request()
        self.add_dimension(validation_request, True)
        result = validate(
            data={
                'external_id': '1',
                'payload': {}
            },
            request=validation_request
        )

        self.assertTrue('external_id' in result)
        self.assertTrue('payload' in result)
        self.assertTrue(isinstance(result['payload'], dict))
        self.assertEquals(0, len(result['payload']))


class DimensionByExternalIdTest(DimensionTest):
    by_external_id = True


del BaseFactTest

del Base
