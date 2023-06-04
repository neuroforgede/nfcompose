# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


import io
from urllib.parse import quote

import datetime
import requests
from PIL import Image as PIL_Image  # type: ignore
from django.db import connections, connection
from django.utils import timezone
from rest_framework import status
from typing import Any, Dict

from skipper import modules
from skipper.core.models import default_media_storage
from skipper.core.models.tenant import Tenant
from skipper.core.tests.base import BaseViewTest, BASE_URL
from skipper.dataseries.models import FileLookup
from skipper.dataseries.models.metamodel.boolean_fact import DataSeries_BooleanFact, BooleanFact
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.models.metamodel.dimension import DataSeries_Dimension, Dimension
from skipper.dataseries.models.metamodel.file_fact import DataSeries_FileFact, FileFact
from skipper.dataseries.models.metamodel.float_fact import DataSeries_FloatFact, FloatFact
from skipper.dataseries.models.metamodel.image_fact import DataSeries_ImageFact, ImageFact
from skipper.dataseries.models.metamodel.json_fact import DataSeries_JsonFact, JsonFact
from skipper.dataseries.models.metamodel.string_fact import DataSeries_StringFact, StringFact
from skipper.dataseries.models.metamodel.text_fact import DataSeries_TextFact, TextFact
from skipper.dataseries.raw_sql import dbtime
from skipper.dataseries.raw_sql.tenant import tenant_schema_unescaped
from skipper.dataseries.storage.contract import StorageBackendType
from skipper.dataseries.storage.dynamic_sql.backend_info import get_tables_in_schema
from skipper.dataseries.storage.dynamic_sql.materialized import materialized_table_name, \
    materialized_flat_history_table_name
from skipper.dataseries.storage.uuid import gen_uuid
from skipper.dataseries.tasks import file_registry
from skipper.settings import DATA_SERIES_DYNAMIC_SQL_DB
from skipper.dataseries.models.event import ConsumerEvent, ConsumerEventType

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


# hide the base classes inside another class so they dont get picked up as their own tests
class BaseClasses:
    class Base(BaseViewTest):
        # the list endpoint is disabled for datapoints if we do not select for a data series
        url_under_test = DATA_SERIES_BASE_URL + 'dataseries/'
        simulate_other_tenant = True

        fact_type: str
        data_series_relation_type: Any
        fact_model_type: Any

        def gen_data(self, external_id: str = '1') -> Any:
            raise NotImplementedError()

        def add_fact(self, data_series: Dict[str, Any], optional: bool, external_id: str = '1') -> Any:
            return self.create_payload(data_series[f'{self.fact_type}_facts'], {
                'external_id': external_id,
                'optional': optional,
                'name': external_id
            })['id']

        def add_consumer(self, data_series: Dict[str, Any], external_id: str = '1') -> Any:
            return self.create_payload(data_series['consumers'], {
                'target': 'http://should.not.matter.local/',
                'headers': {},
                'name': external_id,
                'external_id': external_id
            })['id']

        def delete_fact(self, data_series: Dict[str, Any], fact_id: str) -> None:
            self.client.delete(path=f"{data_series[f'{self.fact_type}_facts']}{fact_id}/")

        def write_data_once(self, data_series: Dict[str, Any], external_id: str) -> None:
            # just get the data in somehow (here, via batch)
            response = self.client.post(
                path=data_series['data_points_bulk'],
                data={
                    f"batch-0.external_id": external_id,
                    "batch-0.payload.1": self.gen_data()
                }, format='multipart')
            self.assertEquals(status.HTTP_201_CREATED, response.status_code)

        def assert_entity_count_db(
                self,
                data_series: Dict[str, Any],
                fact_id: str,
                external_id: str,
                count: int,
                fact_count: int,
        ) -> None:
            if data_series['backend'] == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value:
                # TODO: check in materialized table also, if it is deleted it should not be there
                return

        def assert_meta_model_count(
                self,
                data_series: Dict[str, Any],
                fact_id: str,
                ds_count: int,
                rel_count: int,
                fact_count: int
        ) -> None:
            self.assertEqual(ds_count, len(DataSeries.all_objects.filter(id=data_series['id'])))
            self.assertEqual(rel_count, len(self.data_series_relation_type.all_objects.filter(fact_id=fact_id)))
            self.assertEqual(fact_count, len(self.fact_model_type.all_objects.filter(id=fact_id)))

        def assert_count(
                self,
                data_series: Dict[str, Any],
                fact_id: str,
                external_id: str,
                count: int,
                fact_count: int,
                should_find_in_rest_api: bool,
                point_in_time: datetime.datetime,
                should_find_fact_in_rest_api: bool = True
        ) -> None:
            # TODO: For backends that do not version count and fact_count differently, simply check only count as that
            #       is the proper value in that case
            # TODO: the way this test is implemented only works for historical backends and not for flat backends
            # so once we implement a flat backend this will fail, but this is fine
            history_per_external_id = {
                elem['external_id']: elem['versions']
                for elem in self.get_payload(
                    url=data_series['history_data_points'] + f'?count&include_versions&point_in_time={quote(point_in_time.isoformat())}'
                )['data']
            }
            if should_find_in_rest_api:
                self.assertEqual(count, len(history_per_external_id[external_id]['data_point']))
                if data_series['backend'] != StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value:
                    # flat history backend does not generate payload versions
                    if should_find_fact_in_rest_api:
                        # always 1 in our tests
                        self.assertEqual(fact_count, len(history_per_external_id[external_id]['payload']['1']))
                    else:
                        self.assertTrue('1' not in history_per_external_id[external_id]['payload'])
            else:
                self.assertTrue(external_id not in history_per_external_id)

            self.assert_entity_count_db(
                data_series=data_series,
                fact_id=fact_id,
                external_id=external_id,
                count=count,
                fact_count=fact_count,
            )

        def _test_truncate(self, storage_backend_type: str, idx: int) -> None:
            other_data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
                'name': f'_my_other_data_series_1{idx}',
                'external_id': f'_other_external_id{idx}',
                'backend': storage_backend_type
            }, simulate_tenant=False)

            other_fact_id = self.add_fact(other_data_series, optional=False)
            other_consumer = self.add_consumer(other_data_series)

            for i in range(0, 10):
                self.write_data_once(other_data_series, 'other_dp_1')
                self.write_data_once(other_data_series, 'other_dp_2')

            data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
                'name': f'_my_data_series_1{idx}',
                'external_id': f'_external_id{idx}',
                'backend': storage_backend_type
            }, simulate_tenant=False)

            fact_id = self.add_fact(data_series, optional=False)
            consumer = self.add_consumer(data_series)

            self.write_data_once(data_series, 'dp_1')

            for i in range(0, 10):
                self.write_data_once(data_series, 'dp_1')
                self.write_data_once(data_series, 'dp_2')

            _should_definitely_find_all_in_history_timestamp = dbtime.now()

            self.assert_count(other_data_series, other_fact_id, 'other_dp_1', 10, 10, True, _should_definitely_find_all_in_history_timestamp)
            self.assert_count(other_data_series, other_fact_id, 'other_dp_1', 10, 10, True, _should_definitely_find_all_in_history_timestamp)
            other_consumer_before_count = ConsumerEvent.objects.filter(
                consumer_id=other_consumer
            ).count()
            self.assertGreater(other_consumer_before_count, 1)

            self.assert_count(data_series, fact_id, 'dp_1', 11, 11, True, _should_definitely_find_all_in_history_timestamp)
            self.assert_count(data_series, fact_id, 'dp_2', 10, 10, True, _should_definitely_find_all_in_history_timestamp)
            self.assertGreater(ConsumerEvent.objects.filter(
                consumer_id=consumer
            ).count(), 1)


            self.client.post(
                path=data_series['truncate'],
                data={},
                format='json'
            )

            # other dataseries should be unaffected
            self.assert_count(other_data_series, other_fact_id, 'other_dp_1', 10, 10, True, _should_definitely_find_all_in_history_timestamp)
            self.assert_count(other_data_series, other_fact_id, 'other_dp_1', 10, 10, True, _should_definitely_find_all_in_history_timestamp)
            self.assertEqual(ConsumerEvent.objects.filter(
                consumer_id=other_consumer
            ).count(), other_consumer_before_count)
            self.assertEqual(ConsumerEvent.objects.filter(
                consumer_id=other_consumer,
                event_type=ConsumerEventType.DATA_SERIES_TRUNCATED.value
            ).count(), 0)

            self.assert_count(data_series, fact_id, 'dp_1', 0, 0, False, _should_definitely_find_all_in_history_timestamp)
            self.assert_count(data_series, fact_id, 'dp_2', 0, 0, False, _should_definitely_find_all_in_history_timestamp)
            self.assertEqual(ConsumerEvent.objects.filter(
                consumer_id=consumer
            ).count(), 1)
            self.assertEqual(ConsumerEvent.objects.filter(
                consumer_id=consumer,
                event_type=ConsumerEventType.DATA_SERIES_TRUNCATED.value
            ).count(), 1)

        def test_truncate(self) -> None:
            idx = 0
            for backend_key, backend_value in StorageBackendType.choices_with_history():
                self._test_truncate(backend_value, idx)
                idx += 1

        def _test_prune_meta_model(self, storage_backend_type: str, idx: int) -> None:
            data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
                'name': f'_my_data_series_1{idx}',
                'external_id': f'_external_id{idx}',
                'backend': storage_backend_type
            }, simulate_tenant=False)

            fact_id = self.add_fact(data_series, optional=False)

            self.write_data_once(data_series, 'dp_1')

            for i in range(0, 10):
                self.write_data_once(data_series, 'dp_1')
                self.write_data_once(data_series, 'dp_2')

            _should_definitely_find_all_in_history_timestamp = dbtime.now()

            self.assert_count(data_series, fact_id, 'dp_1', 11, 11, True, _should_definitely_find_all_in_history_timestamp)
            self.assert_count(data_series, fact_id, 'dp_2', 10, 10, True, _should_definitely_find_all_in_history_timestamp)

            self.assert_meta_model_count(data_series=data_series, fact_id=fact_id, ds_count=1, rel_count=1, fact_count=1)

            before_delete = dbtime.now()
            self.delete_fact(data_series=data_series, fact_id=fact_id)
            after_delete = dbtime.now()

            self.assert_count(data_series, fact_id, 'dp_1', 11, 11, True,
                              _should_definitely_find_all_in_history_timestamp, should_find_fact_in_rest_api=False)
            self.assert_count(data_series, fact_id, 'dp_2', 10, 10, True,
                              _should_definitely_find_all_in_history_timestamp, should_find_fact_in_rest_api=False)

            self.assert_meta_model_count(data_series=data_series, fact_id=fact_id, ds_count=1, rel_count=1, fact_count=1)

            self.client.post(
                path=data_series['prune_meta_model'],
                data={
                    'older_than': before_delete
                },
                format='json'
            )

            self.assert_count(data_series, fact_id, 'dp_1', 11, 11, True,
                              _should_definitely_find_all_in_history_timestamp, should_find_fact_in_rest_api=False)
            self.assert_count(data_series, fact_id, 'dp_2', 10, 10, True,
                              _should_definitely_find_all_in_history_timestamp, should_find_fact_in_rest_api=False)

            self.assert_meta_model_count(data_series=data_series, fact_id=fact_id, ds_count=1, rel_count=1, fact_count=1)

            self.client.post(
                path=data_series['prune_meta_model'],
                data={
                    'older_than': after_delete + datetime.timedelta(days=30)
                },
                format='json'
            )

            self.assert_count(data_series, fact_id, 'dp_1', 11, 0, True,
                              _should_definitely_find_all_in_history_timestamp, should_find_fact_in_rest_api=False)
            self.assert_count(data_series, fact_id, 'dp_2', 10, 0, True,
                              _should_definitely_find_all_in_history_timestamp, should_find_fact_in_rest_api=False)

            self.assert_meta_model_count(data_series=data_series, fact_id=fact_id, ds_count=1, rel_count=0, fact_count=0)

        def test_prune_meta_model(self) -> None:
            idx = 0
            for backend_key, backend_value in StorageBackendType.choices_with_history():
                self._test_prune_meta_model(backend_value, idx)
                idx += 1

        def _test_prune_whole_data_series(
                self,
                storage_backend_type: str,
                idx: int,
                delete_fact_before: bool
        ) -> None:
            data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
                'name': f'_my_data_series_1{idx}',
                'external_id': f'_external_id{idx}',
                'backend': storage_backend_type
            }, simulate_tenant=False)

            _materialized_table_name = materialized_table_name(id=data_series['id'], external_id=data_series['external_id'])

            tenant = DataSeries.objects.get(id=data_series['id']).tenant

            fact_id = self.add_fact(data_series, optional=False)

            self.write_data_once(data_series, 'dp_1')

            for i in range(0, 10):
                self.write_data_once(data_series, 'dp_1')
                self.write_data_once(data_series, 'dp_2')

            _should_definitely_find_all_in_history_timestamp = dbtime.now()

            self.assert_count(data_series, fact_id, 'dp_1', 11, 11, True, _should_definitely_find_all_in_history_timestamp)
            self.assert_count(data_series, fact_id, 'dp_2', 10, 10, True, _should_definitely_find_all_in_history_timestamp)

            def assert_dps_still_there() -> None:
                self.assert_entity_count_db(
                    data_series=data_series,
                    fact_id=fact_id,
                    external_id='dp_1',
                    count=11,
                    fact_count=11
                )
                self.assert_entity_count_db(
                    data_series=data_series,
                    fact_id=fact_id,
                    external_id='dp_2',
                    count=10,
                    fact_count=10
                )

            if delete_fact_before:
                self.delete_fact(data_series=data_series, fact_id=fact_id)
            after_fact_delete = dbtime.now()

            response = self.client.post(
                path=DATA_SERIES_BASE_URL + 'prune/dataseries/',
                data={
                    'older_than': after_fact_delete,
                    'accept': False
                },
                format='json'
            )
            # should return a http 200 if no accepted
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            assert_dps_still_there()

            response = self.client.post(
                path=DATA_SERIES_BASE_URL + 'prune/dataseries/',
                data={
                    'older_than': after_fact_delete,
                    'accept': True
                },
                format='json'
            )
            # should return a http 202 if accepted
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

            # should not prune meta_model even if data_series itself is not deleted
            self.assert_meta_model_count(data_series=data_series, fact_id=fact_id, ds_count=1, rel_count=1, fact_count=1)
            assert_dps_still_there()

            self.client.delete(data_series['url'])
            after_data_series_delete = dbtime.now()

            self.assert_meta_model_count(data_series=data_series, fact_id=fact_id, ds_count=1, rel_count=1, fact_count=1)
            assert_dps_still_there()

            # try to delete but data_series was deleted later
            self.client.post(
                path=DATA_SERIES_BASE_URL + 'prune/dataseries/',
                data={
                    'older_than': _should_definitely_find_all_in_history_timestamp,
                    'accept': True
                },
                format='json'
            )

            self.assert_meta_model_count(data_series=data_series, fact_id=fact_id, ds_count=1, rel_count=1, fact_count=1)
            assert_dps_still_there()

            # actual prune
            self.client.post(
                path=DATA_SERIES_BASE_URL + 'prune/dataseries/',
                data={
                    'older_than': after_data_series_delete,
                    'accept': True
                },
                format='json'
            )
            self.assert_meta_model_count(data_series=data_series, fact_id=fact_id, ds_count=0, rel_count=0, fact_count=0)

            # TODO: only do this for SQL backends (and only those that have the columnar history)
            self.assert_entity_count_db(data_series=data_series, fact_id=fact_id,
                                        external_id=data_series['external_id'], count=0, fact_count=0)

        def test_prune_whole_data_series_with_deleted_fact(self) -> None:
            idx = 0
            for backend_key, backend_value in StorageBackendType.choices_with_history():
                self._test_prune_whole_data_series(backend_value, idx, True)
                idx += 1

        def test_prune_whole_data_series_with_not_deleted_fact(self) -> None:
            idx = 0
            for backend_key, backend_value in StorageBackendType.choices_with_history():
                self._test_prune_whole_data_series(backend_value, idx, False)
                idx += 1

        def _test_prune_historical(self, storage_backend_type: str, idx: int) -> None:
            data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
                'name': f'__my_data_series_{idx}',
                'external_id': f'__external_id{idx}',
                'backend': storage_backend_type
            }, simulate_tenant=False)

            fact_id = self.add_fact(data_series, optional=False)

            self.write_data_once(data_series, 'dp_1')

            initial_timestamp = dbtime.now()

            after_timestamps = []
            for i in range(0, 10):
                self.write_data_once(data_series, 'dp_1')
                self.write_data_once(data_series, 'dp_2')
                after_timestamps.append(dbtime.now())

            _should_definitely_find_all_in_history_timestamp = dbtime.now()

            self.assert_count(data_series, fact_id, 'dp_1', 11, 11, True, _should_definitely_find_all_in_history_timestamp)
            self.assert_count(data_series, fact_id, 'dp_2', 10, 10, True, _should_definitely_find_all_in_history_timestamp)

            # now delete the initial data for dp_1
            self.client.post(
                path=data_series['prune_history'],
                data={
                    'older_than': initial_timestamp
                },
                format='json'
            )

            self.assert_count(data_series, fact_id, 'dp_1', 10, 10, True, _should_definitely_find_all_in_history_timestamp)
            self.assert_count(data_series, fact_id, 'dp_2', 10, 10, True, _should_definitely_find_all_in_history_timestamp)

            # delete the earliest
            self.client.post(
                path=data_series['prune_history'],
                data={
                    'older_than': after_timestamps[0]
                },
                format='json'
            )

            self.assert_count(data_series, fact_id, 'dp_1', 9, 9, True, _should_definitely_find_all_in_history_timestamp)
            self.assert_count(data_series, fact_id, 'dp_2', 9, 9, True, _should_definitely_find_all_in_history_timestamp)

            self.client.delete(
                path=f"{data_series['data_points']}{gen_uuid(data_series['id'], 'dp_1')}/"
            )
            after_delete = dbtime.now()

            self.assert_count(data_series, fact_id, 'dp_1', 10, 9, True, _should_definitely_find_all_in_history_timestamp)
            self.assert_count(data_series, fact_id, 'dp_2', 9, 9, True, _should_definitely_find_all_in_history_timestamp)

            self.client.post(
                path=data_series['prune_history'],
                data={
                    'older_than': after_timestamps[8]
                },
                format='json'
            )

            self.assert_count(data_series, fact_id, 'dp_1', 2, 1, True, _should_definitely_find_all_in_history_timestamp)
            self.assert_count(data_series, fact_id, 'dp_2', 1, 1, True, _should_definitely_find_all_in_history_timestamp)

            self.client.post(
                path=data_series['prune_history'],
                data={
                    'older_than': after_timestamps[9]
                },
                format='json'
            )
            self.assert_count(data_series, fact_id, 'dp_1', 1, 0, False, _should_definitely_find_all_in_history_timestamp)
            self.assert_count(data_series, fact_id, 'dp_2', 1, 1, True, _should_definitely_find_all_in_history_timestamp)

            self.client.post(
                path=data_series['prune_history'],
                data={
                    'older_than': after_delete
                },
                format='json'
            )
            self.assert_count(data_series, fact_id, 'dp_1', 0, 0, False, _should_definitely_find_all_in_history_timestamp)
            self.assert_count(data_series, fact_id, 'dp_2', 1, 1, True, _should_definitely_find_all_in_history_timestamp)

        def test_prune_historical(self) -> None:
            idx = 0
            for backend_key, backend_value in StorageBackendType.choices_with_history():
                self._test_prune_historical(backend_value, idx)
                idx += 1

        def _test_prune_meta_model_should_not_delete_active_data(self, storage_backend_type: str, idx: int) -> None:
            data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
                'name': f'_my_data_series_1{idx}',
                'external_id': f'_external_id{idx}',
                'backend': storage_backend_type
            }, simulate_tenant=False)

            fact_id_1 = self.add_fact(data_series, optional=False, external_id='1')
            fact_id_2 = self.add_fact(data_series, optional=False, external_id='2')

            dp_1 = self.create_payload(
                url=data_series['data_points'],
                payload={
                    "external_id": 'dp_1',
                    "payload.1": self.gen_data('1'),
                    "payload.2": self.gen_data('2')
                },
                format='multipart',
                equality_check=False,
                simulate_tenant=False
            )

            dp_2 = self.create_payload(
                url=data_series['data_points'],
                payload={
                    "external_id": 'dp_2',
                    "payload.1": self.gen_data('1'),
                    "payload.2": self.gen_data('2')
                },
                format='multipart',
                simulate_tenant=False,
                equality_check=False
            )

            before_delete = dbtime.now()
            self.delete_fact(data_series=data_series, fact_id=fact_id_1)
            after_delete = dbtime.now()

            self.client.post(
                path=data_series['prune_meta_model'],
                data={
                    'older_than': before_delete
                },
                format='json'
            )

            data_points = self.get_payload(url=data_series['data_points'])['data']
            self.assertEqual(2, len(data_points))
            for dp in data_points:
                self.assertTrue('1' not in dp['payload'])
                self.assertTrue('2' in dp['payload'])

            self.client.post(
                path=data_series['prune_meta_model'],
                data={
                    'older_than': after_delete
                },
                format='json'
            )

            data_points = self.get_payload(url=data_series['data_points'])['data']
            self.assertEqual(2, len(data_points))
            for dp in data_points:
                self.assertTrue('1' not in dp['payload'])
                self.assertTrue('2' in dp['payload'])

        def test_prune_meta_model_should_not_delete_active_data(self) -> None:
            idx = 0
            for backend_key, backend_value in StorageBackendType.choices():
                self._test_prune_meta_model_should_not_delete_active_data(backend_value, idx)
                idx += 1

        def _test_prune_should_not_delete_active_data(self, storage_backend_type: str, idx: int) -> None:
            data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
                'name': f'__my_data_series_s3_prune_{idx}',
                'external_id': f'__external_id_s3_prune_{idx}',
                'backend': storage_backend_type
            }, simulate_tenant=False)

            fact_id = self.add_fact(data_series, optional=False)

            dp_1 = self.create_payload(
                url=data_series['data_points'],
                payload={
                    "external_id": 'dp_1',
                    "payload.1": self.gen_data()
                },
                format='multipart',
                equality_check=False,
                simulate_tenant=False
            )

            dp_2 = self.create_payload(
                url=data_series['data_points'],
                payload={
                    "external_id": 'dp_2',
                    "payload.1": self.gen_data()
                },
                format='multipart',
                simulate_tenant=False,
                equality_check=False
            )

            # data that was not deleted should still be there after prune
            data_points = self.get_payload(url=data_series['data_points'])['data']
            self.assertEqual(2, len(data_points))

            before_delete = dbtime.now()

            self.delete_payload(url=dp_1['url'])

            after_delete = dbtime.now()

            self.client.post(
                path=data_series['prune_history'],
                data={
                    'older_than': before_delete
                },
                format='json'
            )

            # data that was not deleted should still be there after prune that should not do things
            data_points = self.get_payload(url=data_series['data_points'])['data']
            self.assertEqual(1, len(data_points))

            self.client.post(
                path=data_series['prune_history'],
                data={
                    'older_than': after_delete
                },
                format='json'
            )
            # data that was not deleted should still be there after prune that definitely does things
            data_points = self.get_payload(url=data_series['data_points'])['data']
            self.assertEqual(1, len(data_points))

        def test_prune_should_not_delete_active_data(self) -> None:
            idx = 0
            for backend_key, backend_value in StorageBackendType.choices():
                self._test_prune_should_not_delete_active_data(backend_value, idx)
                idx += 1

        def test_prune_whole_data_series_basic_delete_before(self) -> None:
            idx = 0
            for backend_key, backend_value in StorageBackendType.choices():
                self._test_prune_whole_data_series_basic(backend_value, idx, True)
                idx += 1

        def test_prune_whole_data_series_basic_not_delete_before(self) -> None:
            idx = 0
            for backend_key, backend_value in StorageBackendType.choices():
                self._test_prune_whole_data_series_basic(backend_value, idx, False)
                idx += 1

        def custom_data_check_there_prune_whole_data_series_basic(self, dp: Dict[str, Any], be_there: bool) -> None:
            pass

        def _test_prune_whole_data_series_basic(
                self,
                storage_backend_type: str,
                idx: int,
                delete_fact_before: bool
        ) -> None:
            data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
                'name': f'_my_data_series_1{idx}',
                'external_id': f'_external_id{idx}',
                'backend': storage_backend_type
            }, simulate_tenant=False)

            _materialized_table_name = materialized_table_name(id=data_series['id'], external_id=data_series['external_id'])
            _materialized_flat_history_table_name = materialized_flat_history_table_name(
                id=data_series['id'],
                external_id=data_series['external_id']
            )

            tenant = DataSeries.objects.get(id=data_series['id']).tenant

            fact_id = self.add_fact(data_series, optional=False)

            dp_1 = self.create_payload(
                url=data_series['data_points'],
                payload={
                    "external_id": 'dp_1',
                    "payload.1": self.gen_data()
                },
                format='multipart',
                equality_check=False,
                simulate_tenant=False
            )

            dp_2 = self.create_payload(
                url=data_series['data_points'],
                payload={
                    "external_id": 'dp_2',
                    "payload.1": self.gen_data()
                },
                format='multipart',
                simulate_tenant=False,
                equality_check=False
            )

            if delete_fact_before:
                self.delete_fact(data_series=data_series, fact_id=fact_id)
            after_fact_delete = dbtime.now()

            response = self.client.post(
                path=DATA_SERIES_BASE_URL + 'prune/dataseries/',
                data={
                    'older_than': after_fact_delete,
                    'accept': False
                },
                format='json'
            )
            # should return a http 200 if no accepted
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            response = self.client.post(
                path=DATA_SERIES_BASE_URL + 'prune/dataseries/',
                data={
                    'older_than': after_fact_delete,
                    'accept': True
                },
                format='json'
            )
            # should return a http 202 if accepted
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

            # should not prune meta_model even if data_series itself is not deleted
            self.assert_meta_model_count(data_series=data_series, fact_id=fact_id, ds_count=1, rel_count=1, fact_count=1)

            if storage_backend_type != StorageBackendType.DYNAMIC_SQL_V1.value:
                self.assertIn(_materialized_table_name, get_tables_in_schema(
                    connection=connections[DATA_SERIES_DYNAMIC_SQL_DB],
                    schema=tenant_schema_unescaped(tenant.name)
                ))

            if storage_backend_type == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value:
                self.assertIn(_materialized_flat_history_table_name, get_tables_in_schema(
                    connection=connections[DATA_SERIES_DYNAMIC_SQL_DB],
                    schema=tenant_schema_unescaped(tenant.name)
                ))

            self.custom_data_check_there_prune_whole_data_series_basic(dp_1, True)
            self.custom_data_check_there_prune_whole_data_series_basic(dp_2, True)

            _should_definitely_find_all_in_history_timestamp = dbtime.now()
            self.client.delete(data_series['url'])
            after_data_series_delete = dbtime.now()

            self.assert_meta_model_count(data_series=data_series, fact_id=fact_id, ds_count=1, rel_count=1, fact_count=1)

            # try to delete but data_series was deleted later
            self.client.post(
                path=DATA_SERIES_BASE_URL + 'prune/dataseries/',
                data={
                    'older_than': _should_definitely_find_all_in_history_timestamp,
                    'accept': True
                },
                format='json'
            )

            self.assert_meta_model_count(data_series=data_series, fact_id=fact_id, ds_count=1, rel_count=1, fact_count=1)

            if storage_backend_type != StorageBackendType.DYNAMIC_SQL_V1.value:
                self.assertIn(_materialized_table_name, get_tables_in_schema(
                    connection=connections[DATA_SERIES_DYNAMIC_SQL_DB],
                    schema=tenant_schema_unescaped(tenant.name)
                ))

            if storage_backend_type == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value:
                self.assertIn(_materialized_flat_history_table_name, get_tables_in_schema(
                    connection=connections[DATA_SERIES_DYNAMIC_SQL_DB],
                    schema=tenant_schema_unescaped(tenant.name)
                ))

            # actual prune
            self.client.post(
                path=DATA_SERIES_BASE_URL + 'prune/dataseries/',
                data={
                    'older_than': after_data_series_delete,
                    'accept': True
                },
                format='json'
            )
            self.assert_meta_model_count(data_series=data_series, fact_id=fact_id, ds_count=0, rel_count=0, fact_count=0)

            after_prune = dbtime.now()

            if storage_backend_type != StorageBackendType.DYNAMIC_SQL_V1.value:
                self.assertNotIn(_materialized_table_name, get_tables_in_schema(
                    connection=connections[DATA_SERIES_DYNAMIC_SQL_DB],
                    schema=tenant_schema_unescaped(tenant.name)
                ))

            if storage_backend_type == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value:
                self.assertNotIn(_materialized_flat_history_table_name, get_tables_in_schema(
                    connection=connections[DATA_SERIES_DYNAMIC_SQL_DB],
                    schema=tenant_schema_unescaped(tenant.name)
                ))

            self.custom_data_check_there_prune_whole_data_series_basic(dp_1, True)
            self.custom_data_check_there_prune_whole_data_series_basic(dp_2, True)

            file_registry.garbage_collect(
                storage=default_media_storage,
                older_than=after_prune
            )

            self.custom_data_check_there_prune_whole_data_series_basic(dp_1, False)
            self.custom_data_check_there_prune_whole_data_series_basic(dp_2, False)

    class BaseFileLikeTest(Base):
        def custom_data_check_there_prune_whole_data_series_basic(self, dp: Dict[str, Any], be_there: bool) -> None:
            if be_there:
                self.ensure_200(dp['payload']['1'])
            else:
                self.ensure_404(dp['payload']['1'])

        def ensure_200(self, url: str) -> None:
            response = requests.get(url=url)
            self.assertEqual(status.HTTP_200_OK, response.status_code)

        def ensure_404(self, url: str) -> None:
            response = requests.get(url=url)
            self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

        def gen_data(self, external_id: str = '1') -> Any:
            return generate_photo_file()

        def test_s3_prune_meta_model_deletion(self) -> None:
            idx = 0
            # this constraint works for all backends
            for backend_key, backend_value in StorageBackendType.choices():
                self._test_s3_prune_meta_model_deletion(backend_value, idx)
                idx += 1

        def _test_s3_prune_meta_model_deletion(self, storage_backend_type: str, idx: int) -> None:
            data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
                'name': f'_my_data_series_1{idx}',
                'external_id': f'_external_id{idx}',
                'backend': storage_backend_type
            }, simulate_tenant=False)

            fact_id_1 = self.add_fact(data_series, optional=False, external_id='1')
            fact_id_2 = self.add_fact(data_series, optional=False, external_id='2')

            dp_1 = self.create_payload(
                url=data_series['data_points'],
                payload={
                    "external_id": 'dp_1',
                    "payload.1": self.gen_data(),
                    "payload.2": self.gen_data()
                },
                format='multipart',
                equality_check=False,
                simulate_tenant=False
            )

            dp_2 = self.create_payload(
                url=data_series['data_points'],
                payload={
                    "external_id": 'dp_2',
                    "payload.1": self.gen_data(),
                    "payload.2": self.gen_data()
                },
                format='multipart',
                simulate_tenant=False,
                equality_check=False
            )

            before_delete = dbtime.now()
            self.delete_fact(data_series=data_series, fact_id=fact_id_1)
            after_delete = dbtime.now()

            self.client.post(
                path=data_series['prune_meta_model'],
                data={
                    'older_than': before_delete
                },
                format='json'
            )

            # data should still be there before pruning
            self.ensure_200(dp_1['payload']['1'])
            self.ensure_200(dp_1['payload']['2'])
            self.ensure_200(dp_2['payload']['1'])
            self.ensure_200(dp_2['payload']['2'])

            self.client.post(
                path=data_series['prune_meta_model'],
                data={
                    'older_than': after_delete
                },
                format='json'
            )

            after_prune = dbtime.now()

            self.ensure_200(dp_1['payload']['1'])
            self.ensure_200(dp_1['payload']['2'])
            self.ensure_200(dp_2['payload']['1'])
            self.ensure_200(dp_2['payload']['2'])

            file_registry.garbage_collect(
                storage=default_media_storage,
                older_than=before_delete
            )

            # should still be here because we used a timestamp before deletion

            self.ensure_200(dp_1['payload']['1'])
            self.ensure_200(dp_1['payload']['2'])
            self.ensure_200(dp_2['payload']['1'])
            self.ensure_200(dp_2['payload']['2'])

            file_registry.garbage_collect(
                storage=default_media_storage,
                older_than=after_prune
            )

            # run garbage collection now it should be dead
            self.ensure_404(dp_1['payload']['1'])
            self.ensure_200(dp_1['payload']['2'])
            self.ensure_404(dp_2['payload']['1'])
            self.ensure_200(dp_2['payload']['2'])

        def test_s3_truncate(self) -> None:
            idx = 0
            # this constraint works for all backends
            for backend_key, backend_value in StorageBackendType.choices():
                self._test_s3_truncate(backend_value, idx)
                idx += 1

        def _test_s3_truncate(self, storage_backend_type: str, idx: int) -> None:
            other_data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
                'name': f'_my_other_data_series_1{idx}',
                'external_id': f'_other_external_id{idx}',
                'backend': storage_backend_type
            }, simulate_tenant=False)

            other_fact_id_1 = self.add_fact(other_data_series, optional=False, external_id='1')
            other_fact_id_2 = self.add_fact(other_data_series, optional=False, external_id='2')

            other_dp_1 = self.create_payload(
                url=other_data_series['data_points'],
                payload={
                    "external_id": 'dp_1',
                    "payload.1": self.gen_data(),
                    "payload.2": self.gen_data()
                },
                format='multipart',
                equality_check=False,
                simulate_tenant=False
            )

            other_dp_2 = self.create_payload(
                url=other_data_series['data_points'],
                payload={
                    "external_id": 'dp_2',
                    "payload.1": self.gen_data(),
                    "payload.2": self.gen_data()
                },
                format='multipart',
                simulate_tenant=False,
                equality_check=False
            )

            data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
                'name': f'_my_data_series_1{idx}',
                'external_id': f'_external_id{idx}',
                'backend': storage_backend_type
            }, simulate_tenant=False)

            fact_id_1 = self.add_fact(data_series, optional=False, external_id='1')
            fact_id_2 = self.add_fact(data_series, optional=False, external_id='2')

            dp_1 = self.create_payload(
                url=data_series['data_points'],
                payload={
                    "external_id": 'dp_1',
                    "payload.1": self.gen_data(),
                    "payload.2": self.gen_data()
                },
                format='multipart',
                equality_check=False,
                simulate_tenant=False
            )

            dp_2 = self.create_payload(
                url=data_series['data_points'],
                payload={
                    "external_id": 'dp_2',
                    "payload.1": self.gen_data(),
                    "payload.2": self.gen_data()
                },
                format='multipart',
                simulate_tenant=False,
                equality_check=False
            )

            # s3 data should be there before truncating
            self.ensure_200(dp_1['payload']['1'])
            self.ensure_200(dp_1['payload']['2'])
            self.ensure_200(dp_2['payload']['1'])
            self.ensure_200(dp_2['payload']['2'])

            self.ensure_200(other_dp_1['payload']['1'])
            self.ensure_200(other_dp_1['payload']['2'])
            self.ensure_200(other_dp_2['payload']['1'])
            self.ensure_200(other_dp_2['payload']['2'])

            other_data_points = self.get_payload(url=other_data_series['data_points'])['data']
            self.assertEqual(2, len(other_data_points))

            data_points = self.get_payload(url=data_series['data_points'])['data']
            self.assertEqual(2, len(data_points))

            self.client.post(
                path=data_series['truncate'],
                data={},
                format='json'
            )

            # s3 data should be be there after truncating, because we did not run garbage collection
            self.ensure_200(dp_1['payload']['1'])
            self.ensure_200(dp_1['payload']['2'])
            self.ensure_200(dp_2['payload']['1'])
            self.ensure_200(dp_2['payload']['2'])

            self.ensure_200(other_dp_1['payload']['1'])
            self.ensure_200(other_dp_1['payload']['2'])
            self.ensure_200(other_dp_2['payload']['1'])
            self.ensure_200(other_dp_2['payload']['2'])

            file_registry.garbage_collect(
                storage=default_media_storage,
                older_than=dbtime.now() + timezone.timedelta(days=1)
            )

            self.ensure_404(dp_1['payload']['1'])
            self.ensure_404(dp_1['payload']['2'])
            self.ensure_404(dp_2['payload']['1'])
            self.ensure_404(dp_2['payload']['2'])

            self.ensure_200(other_dp_1['payload']['1'])
            self.ensure_200(other_dp_1['payload']['2'])
            self.ensure_200(other_dp_2['payload']['1'])
            self.ensure_200(other_dp_2['payload']['2'])

            other_data_points = self.get_payload(url=other_data_series['data_points'])['data']
            self.assertEqual(2, len(other_data_points))

            data_points = self.get_payload(url=data_series['data_points'])['data']
            self.assertEqual(0, len(data_points))

        def test_s3_prune_only_deleted_pruned(self) -> None:
            idx = 0
            # this constraint works for all backends
            for backend_key, backend_value in StorageBackendType.choices():
                self._test_s3_prune_only_deleted_pruned(backend_value, idx)
                idx += 1

        def _test_s3_prune_only_deleted_pruned(self, storage_backend_type: str, idx: int) -> None:
            data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
                'name': f'__my_data_series_s3_prune_{idx}',
                'external_id': f'__external_id_s3_prune_{idx}',
                'backend': storage_backend_type
            }, simulate_tenant=False)

            fact_id = self.add_fact(data_series, optional=False)

            with generate_photo_file() as image_file:
                dp_1 = self.create_payload(
                    url=data_series['data_points'],
                    payload={
                        "external_id": 'dp_1',
                        "payload.1": image_file
                    },
                    format='multipart',
                    equality_check=False,
                    simulate_tenant=False
                )

            with generate_photo_file() as image_file:
                dp_2 = self.create_payload(
                    url=data_series['data_points'],
                    payload={
                        "external_id": 'dp_2',
                        "payload.1": image_file
                    },
                    format='multipart',
                    simulate_tenant=False,
                    equality_check=False
                )

            s3_data_dp_1_resp = requests.get(dp_1['payload']['1'])
            self.assertEquals(status.HTTP_200_OK, s3_data_dp_1_resp.status_code)

            s3_data_dp_2_resp = requests.get(dp_2['payload']['1'])
            self.assertEquals(status.HTTP_200_OK, s3_data_dp_2_resp.status_code)

            before_delete = dbtime.now()

            self.delete_payload(url=dp_1['url'])

            after_delete = dbtime.now()

            response = self.client.post(
                path=data_series['prune_history'],
                data={
                    'older_than': after_delete
                },
                format='json'
            )

            after_prune = dbtime.now()
            self.assertEqual(status.HTTP_200_OK, response.status_code)

            # even for the no history backend this must be true
            # since we actually deleted the datapoint
            self.assertTrue(FileLookup.all_objects.filter(deleted_at__isnull=False).count() > 0,
                            'prune history should properly prune s3 files ' + str(data_series['backend']))

            file_registry.garbage_collect(
                storage=default_media_storage,
                older_than=before_delete
            )

            s3_data_dp_1_resp = requests.get(dp_1['payload']['1'])
            self.assertEquals(status.HTTP_200_OK, s3_data_dp_1_resp.status_code)

            s3_data_dp_2_resp = requests.get(dp_2['payload']['1'])
            self.assertEquals(status.HTTP_200_OK, s3_data_dp_2_resp.status_code)

            file_registry.garbage_collect(
                storage=default_media_storage,
                older_than=after_prune
            )

            s3_data_dp_1_resp = requests.get(dp_1['payload']['1'])
            self.assertEquals(status.HTTP_404_NOT_FOUND, s3_data_dp_1_resp.status_code,
                              's3 data should be pruned for dataseries ' + str(data_series))

            s3_data_dp_2_resp = requests.get(dp_2['payload']['1'])
            self.assertEquals(status.HTTP_200_OK, s3_data_dp_2_resp.status_code)


class ImageFactTest(BaseClasses.BaseFileLikeTest):
    fact_type = 'image'
    data_series_relation_type = DataSeries_ImageFact
    fact_model_type = ImageFact


class FileFactTest(BaseClasses.BaseFileLikeTest):
    fact_type = 'file'
    data_series_relation_type = DataSeries_FileFact
    fact_model_type = FileFact


class FloatFactTest(BaseClasses.Base):
    fact_type = 'float'
    data_series_relation_type = DataSeries_FloatFact
    fact_model_type = FloatFact

    def gen_data(self, external_id: str = '1') -> Any:
        return 1.0


class BooleanFactTest(BaseClasses.Base):
    fact_type = 'boolean'
    data_series_relation_type = DataSeries_BooleanFact
    fact_model_type = BooleanFact

    def gen_data(self, external_id: str = '1') -> Any:
        return False


class StringFactTest(BaseClasses.Base):
    fact_type = 'string'
    data_series_relation_type = DataSeries_StringFact
    fact_model_type = StringFact

    def gen_data(self, external_id: str = '1') -> Any:
        return 'string'


class TextFactTest(BaseClasses.Base):
    fact_type = 'text'
    data_series_relation_type = DataSeries_TextFact
    fact_model_type = TextFact

    def gen_data(self, external_id: str = '1') -> Any:
        return 'text'


class JSONFactTest(BaseClasses.Base):
    fact_type = 'json'
    data_series_relation_type = DataSeries_JsonFact
    fact_model_type = JsonFact

    def gen_data(self, external_id: str = '1') -> Any:
        return '{"json": "value"}'


# dimensions are just like facts, but because of the difference in name, we have to
# handle them a bit different
class DimensionTest(BaseClasses.Base):
    fact_type = 'dimension'
    data_series_relation_type = DataSeries_Dimension
    fact_model_type = Dimension

    dimension_dp: Dict[str, Any] = {}

    def gen_data(self, external_id: str = '1') -> Any:
        return self.dimension_dp[external_id]['id']

    def assert_meta_model_count(
            self,
            data_series: Dict[str, Any],
            fact_id: str,
            ds_count: int,
            rel_count: int,
            fact_count: int
    ) -> None:
        self.assertEqual(ds_count, len(DataSeries.all_objects.filter(id=data_series['id'])))
        self.assertEqual(rel_count, len(self.data_series_relation_type.all_objects.filter(dimension=fact_id)))  # type: ignore
        self.assertEqual(fact_count, len(self.fact_model_type.all_objects.filter(id=fact_id)))

    def assert_entity_count_db(
            self,
            data_series: Dict[str, Any],
            fact_id: str,
            external_id: str,
            count: int,
            fact_count: int,
    ) -> None:
        if data_series['backend'] == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value:
            # TODO: check in materialized table also, if it is deleted it should not be there
            return

    idx_hack = 0

    def delete_fact(self, data_series: Dict[str, Any], fact_id: str) -> None:
        self.client.delete(path=f"{data_series[f'dimensions']}{fact_id}/")

    def setUp(self) -> None:
        super().setUp()
        self.dimension_dp = {}

    def add_fact(self, data_series: Dict[str, Any], optional: bool, external_id: str = '1') -> Any:
        dim_ds = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': f'my_data_series___{self.idx_hack}',
            'external_id': f'external_id__{self.idx_hack}'
        }, simulate_tenant=False)
        self.idx_hack += 1
        self.dimension_dp[external_id] = self.create_payload(dim_ds['data_points'], payload={
            'external_id': 'my_dim_dp',
            'payload': {}
        })
        return self.create_payload(data_series['dimensions'], {
            'external_id': external_id,
            'optional': optional,
            'reference': dim_ds['url'],
            'name': external_id
        })['id']