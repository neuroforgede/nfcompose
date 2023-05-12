# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from datetime import datetime
from rest_framework import status
from typing import Any, List, Dict, Type

from skipper import modules
from skipper.core.tests.base import BaseViewTest, BASE_URL
from skipper.dataseries.storage.contract import StorageBackendType

DATA_SERIES_BASE_URL = BASE_URL + modules.url_representation(modules.Module.DATA_SERIES) + '/'


class BasicBehaviourBulkTest(BaseViewTest):
    # the list endpoint is disabled for datapoints if we do not select for a data series
    url_under_test = DATA_SERIES_BASE_URL + 'dataseries/'
    simulate_other_tenant = True

    def _test_bulk_insert_external_id_behaviour(self, idx: int, backend: str) -> None:
        data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': f'my_data_series_{idx}',
            'external_id': f'external_id{idx}',
            'backend': backend
        }, simulate_tenant=False)

        def initial_request() -> Any:
            return self.client.post(path=data_series['data_points_bulk'], data={
                'batch': [{
                    'external_id': '1',
                    'payload': {}
                }, {
                    'external_id': '2',
                    'payload': {}
                }]
            }, format='json')

        initial_response = initial_request()
        self.assertEqual(initial_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(initial_response.json()['created_external_ids'], ['1', '2'])

        same_external_id_twice_in_request = self.client.post(path=data_series['data_points_bulk'], data={
            'batch': [{
                'external_id': '1',
                'payload': {}
            }, {
                'external_id': '1',
                'payload': {}
            }]
        }, format='json')
        self.assertEqual(same_external_id_twice_in_request.status_code, status.HTTP_400_BAD_REQUEST)

        # POST endpoint should behave just like a bulk upsert
        initial_request_again = initial_request()
        self.assertEqual(initial_request_again.status_code, status.HTTP_201_CREATED)
        self.assertEqual(initial_request_again.json()['created_external_ids'], ['1', '2'])

    def test_bulk_insert_external_id_behaviour(self) -> None:
        idx = 0
        for backend_key, backend_value in StorageBackendType.choices():
            self._test_bulk_insert_external_id_behaviour(idx, backend_value)
            idx += 1

    def _test_bulk_behaves_like_upsert_put(self, idx: int, backend: str) -> None:
        data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': f'my_data_series_{idx}',
            'external_id': f'external_id{idx}',
            'backend': backend
        }, simulate_tenant=False)

        self.create_payload(data_series[f'float_facts'], payload={
            'name': 'fact',
            'external_id': 'fact',
            'optional': True
        }, simulate_tenant=False)

        initial_response = self.client.post(path=data_series['data_points_bulk'], data={
                'batch': [{
                    'external_id': '1',
                    'payload': {
                        'fact': 1
                    }
                }, {
                    'external_id': '2',
                    'payload': {}
                }]
            }, format='json')
        self.assertEqual(initial_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(initial_response.json()['created_external_ids'], ['1', '2'])

        self.client.post(path=data_series['data_points_bulk'], data={
            'batch': [{
                'external_id': '1',
                'payload': {}
            }, {
                'external_id': '2',
                'payload': {
                    'fact': 2
                }
            }]
        }, format='json')

        dp_1 = self.client.get(path=data_series['data_points'] + f'?external_id=1').json()
        self.assertTrue('fact' not in dp_1['data'][0]['payload'], 'for an existing data point, a fact should be deleted in a bulk call if it was left out')

        dp_2 = self.client.get(path=data_series['data_points'] + f'?external_id=2').json()
        self.assertTrue('fact' in dp_2['data'][0]['payload'], 'for an existing data point, a fact should be added if it was added in a second call')

    def test_bulk_behaves_like_upsert_put(self) -> None:
        idx = 0
        for backend_key, backend_value in StorageBackendType.choices():
            self._test_bulk_behaves_like_upsert_put(idx, backend_value)
            idx += 1


class BaseFactRelevantBulkInsertTest(BaseViewTest):
    # the list endpoint is disabled for datapoints if we do not select for a data series
    url_under_test = DATA_SERIES_BASE_URL + 'dataseries/'
    simulate_other_tenant = True

    fact_type: str
    insert_batch_values: List[Dict[str, Any]]

    def _test_async_request(self, idx: int, backend: str) -> None:
        data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': f'my_data_series_{idx}',
            'external_id': f'external_id{idx}',
            'backend': backend
        }, simulate_tenant=False)

        fact = self.create_payload(data_series[f'{self.fact_type}_facts'], payload={
            'name': 'fact',
            'external_id': 'fact',
            'optional': True
        }, simulate_tenant=False)

        def async_request() -> Any:
            return self.client.post(path=data_series['data_points_bulk'], data={
                'batch': self.insert_batch_values,
                'async': True
            }, format='json')

        initial_request_again = async_request()
        self.assertEqual(initial_request_again.status_code, status.HTTP_201_CREATED)
        self.assertEqual(initial_request_again.json()['created_external_ids'], ['1', '2'])

    def test_async_request(self) -> None:
        idx = 0
        for backend_key, backend_value in StorageBackendType.choices():
            self._test_async_request(idx, backend_value)
            idx += 1


class FloatFactAsyncBulkInsertTest(BaseFactRelevantBulkInsertTest):
    fact_type: str = 'float'
    insert_batch_values = [{
        'external_id': '1',
        'payload': {
            'fact': 1
        }
    }, {
        'external_id': '2',
        'payload': {
            'fact': 2
        }
    }]


class StringFactAsyncBulkInsertTest(BaseFactRelevantBulkInsertTest):
    fact_type: str = 'string'
    insert_batch_values = [{
        'external_id': '1',
        'payload': {
            'fact': '11'
        }
    }, {
        'external_id': '2',
        'payload': {
            'fact': '11'
        }
    }]


class TextFactAsyncBulkInsertTest(BaseFactRelevantBulkInsertTest):
    fact_type: str = 'text'
    insert_batch_values = [{
        'external_id': '1',
        'payload': {
            'fact': '11'
        }
    }, {
        'external_id': '2',
        'payload': {
            'fact': '11'
        }
    }]


class TimestampFactAsyncBulkInsertTest(BaseFactRelevantBulkInsertTest):
    fact_type: str = 'timestamp'
    insert_batch_values = [{
        'external_id': '1',
        'payload': {
            'fact': datetime(year=2020, month=12, day=29, hour=14, minute=40, second=0, microsecond=88888)
        }
    }, {
        'external_id': '2',
        'payload': {
            'fact': datetime(year=2021, month=12, day=29, hour=14, minute=40, second=0, microsecond=99999)
        }
    }]


class BooleanFactAsyncBulkInsertTest(BaseFactRelevantBulkInsertTest):
    fact_type: str = 'boolean'
    insert_batch_values = [{
        'external_id': '1',
        'payload': {
            'fact': True
        }
    }, {
        'external_id': '2',
        'payload': {
            'fact': False
        }
    }]


class JSONFactAsyncBulkInsertTest(BaseFactRelevantBulkInsertTest):
    fact_type: str = 'json'
    insert_batch_values = [{
        'external_id': '1',
        'payload': {
            'fact': {
                "test": "a"
            }
        }
    }, {
        'external_id': '2',
        'payload': {
            'fact': {
                "test": "b"
            }
        }
    }]


# TODO: test value is the same as we passed in

# FIXME: add dimension test

del BaseFactRelevantBulkInsertTest
