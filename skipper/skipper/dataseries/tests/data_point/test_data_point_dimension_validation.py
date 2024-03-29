# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from typing import Any, Dict

from skipper import modules
from skipper.core.tests.base import BaseViewTest, BASE_URL

from rest_framework import status

from skipper.dataseries.storage.contract import StorageBackendType

DATA_SERIES_BASE_URL = BASE_URL + modules.url_representation(modules.Module.DATA_SERIES) + '/'


class Base(BaseViewTest):
    # the list endpoint is disabled for datapoints if we do not select for a data series
    url_under_test = DATA_SERIES_BASE_URL + 'dataseries/'
    simulate_other_tenant = True

    backend: str

    data_series: Dict[str, Any]
    dim_1: Dict[str, Any] = {}
    dim_2: Dict[str, Any] = {}
    dim_entries_1: Dict[int, Any] = {}
    dim_entries_2: Dict[int, Any] = {}

    def setUp(self) -> None:
        super().setUp()
        self.data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': 'my_data_series_1',
            'external_id': 'external_id1',
            'backend': self.backend
        }, simulate_tenant=False)

        data_series_for_dim_1 = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': 'my_data_series_2',
            'external_id': 'external_id2',
            'backend': self.backend
        }, simulate_tenant=False)

        data_series_for_dim_2 = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': 'my_data_series_3',
            'external_id': 'external_id3',
            'backend': self.backend
        }, simulate_tenant=False)

        self.dim_1 = self.create_payload(self.data_series['dimensions'], payload={
            'name': 'my_dim_1',
            'reference': data_series_for_dim_1['url'],
            'external_id': 'my_dim_1',
            'optional': False
        })

        self.dim_entries_1: Dict[int, Any] = {}
        for i in range(0, 2):
            self.dim_entries_1[i] = self.create_payload(data_series_for_dim_1['data_points'], {
                'external_id': f'1_{i}',
                'payload': {}
            })

        # we intentionally use the same dataseries for this dimension again
        # so that we can test properly if resolution still works
        self.dim_2 = self.create_payload(self.data_series['dimensions'], payload={
            'name': 'my_dim_2',
            'reference': data_series_for_dim_2['url'],
            'external_id': 'my_dim_2',
            'optional': False
        })

        self.dim_entries_2: Dict[int, Any] = {}
        for i in range(0, 2):
            self.dim_entries_2[i] = self.create_payload(data_series_for_dim_2['data_points'], {
                'external_id': f'2_{i}',
                'payload': {}
            })

    def test_missing_alltogether(self) -> None:
        response = self.client.post(
            path=self.data_series['data_points'],
            data={
                f"external_id": 'no_dim_should_fail',
                "payload": {}
            }, format='json')

        self.assertEquals(status.HTTP_400_BAD_REQUEST, response.status_code)
        error_json = response.json()
        self.assertTrue('payload' in error_json)
        self.assertTrue(self.dim_1['external_id'] in error_json['payload'])
        self.assertTrue(self.dim_2['external_id'] in error_json['payload'])

    def test_both_entries_wrong_identify_by_external_id(self) -> None:
        response = self.client.post(
            path=self.data_series['data_points'],
            data={
                f"external_id": 'no_dim_should_fail',
                "payload": {
                    self.dim_1['external_id']: 'NOT_EXISTANT_1',
                    self.dim_2['external_id']: 'NOT_EXISTANT_1',
                },
                "identify_dimensions_by_external_id": False
            }, format='json')

        self.assertEquals(status.HTTP_400_BAD_REQUEST, response.status_code)

        error_json = response.json()

        self.assertTrue('payload' in error_json)
        self.assertTrue(self.dim_1['external_id'] in error_json['payload'])
        self.assertTrue(self.dim_2['external_id'] in error_json['payload'])

    def test_both_entries_wrong(self) -> None:
        response = self.client.post(
            path=self.data_series['data_points'],
            data={
                f"external_id": 'no_dim_should_fail',
                "payload": {
                    self.dim_1['external_id']: 'NOT_EXISTANT_1',
                    self.dim_2['external_id']: 'NOT_EXISTANT_1',
                },
                "identify_dimensions_by_external_id": False
            }, format='json')

        self.assertEquals(status.HTTP_400_BAD_REQUEST, response.status_code)

        error_json = response.json()

        self.assertTrue('payload' in error_json)
        self.assertTrue(self.dim_1['external_id'] in error_json['payload'])
        self.assertTrue(self.dim_2['external_id'] in error_json['payload'])

    def test_should_work_normal(self) -> None:
        response = self.client.post(
            path=self.data_series['data_points'],
            data={
                f"external_id": '1',
                "payload": {
                    self.dim_1['external_id']: self.dim_entries_1[1]['id'],
                    self.dim_2['external_id']: self.dim_entries_2[1]['id'],
                },
                "identify_dimensions_by_external_id": False
            }, format='json')
        self.assertEquals(status.HTTP_201_CREATED, response.status_code)

    def test_should_work_identify_by_external_id(self) -> None:
        response = self.client.post(
            path=self.data_series['data_points'],
            data={
                f"external_id": '1',
                "payload": {
                    self.dim_1['external_id']: self.dim_entries_1[1]['external_id'],
                    self.dim_2['external_id']: self.dim_entries_2[1]['external_id'],
                },
                "identify_dimensions_by_external_id": True
            }, format='json')
        self.assertEquals(status.HTTP_201_CREATED, response.status_code)

    def test_both_entries_wrong_and_wrong_external_id(self) -> None:
        response = self.client.post(
            path=self.data_series['data_points'],
            data={
                f"external_id": '1',
                "payload": {
                    self.dim_1['external_id']: self.dim_entries_1[1]['id'],
                    self.dim_2['external_id']: self.dim_entries_2[1]['id'],
                }
            }, format='json')
        self.assertEquals(status.HTTP_201_CREATED, response.status_code)

        response = self.client.post(
            path=self.data_series['data_points'],
            data={
                # same external id again
                f"external_id": '1',
                "payload": {
                    self.dim_1['external_id']: 'NOT_EXISTANT_1',
                    self.dim_2['external_id']: 'NOT_EXISTANT_1',
                },
                "identify_dimensions_by_external_id": True
            }, format='json')

        self.assertEquals(status.HTTP_400_BAD_REQUEST, response.status_code)

        error_json = response.json()
        self.assertTrue('external_id' in error_json)

        response = self.client.post(
            path=self.data_series['data_points'],
            data={
                # same external id again
                f"external_id": '1',
                "payload": {
                    self.dim_1['external_id']: 'NOT_EXISTANT_1',
                    self.dim_2['external_id']: 'NOT_EXISTANT_1',
                },
                "identify_dimensions_by_external_id": False
            }, format='json')

        self.assertEquals(status.HTTP_400_BAD_REQUEST, response.status_code)

        error_json = response.json()
        self.assertTrue('external_id' in error_json)

        self.assertTrue('payload' in error_json)
        self.assertTrue(self.dim_1['external_id'] in error_json['payload'])
        self.assertTrue(self.dim_2['external_id'] in error_json['payload'])


class DynamicSQLNoHistoryDimensionValidationTest(Base):
    backend = StorageBackendType.DYNAMIC_SQL_NO_HISTORY.value


del Base
