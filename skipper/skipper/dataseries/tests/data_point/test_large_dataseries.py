# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import copy
import random

import uuid
from typing import Any, Dict

from skipper import modules
from skipper.core.tests.base import BaseViewTest, BASE_URL
from skipper.dataseries.storage.contract import StorageBackendType

DATA_SERIES_BASE_URL = BASE_URL + modules.url_representation(modules.Module.DATA_SERIES) + '/'


class BaseLargeDataSeriesDataPointFetchTest(BaseViewTest):
    # the list endpoint is disabled for datapoints if we do not select for a data series
    url_under_test = DATA_SERIES_BASE_URL + 'dataseries/'
    simulate_other_tenant = True
    maxDiff = None

    backend_key: str
    data_series: Dict[str, Any]
    dim_entries_1: Dict[int, Any]
    dim_entries_2: Dict[int, Any]
    dim_entries_3: Dict[int, Any]
    data_points: Dict[str, Dict[str, Any]]
    data_points_resolved_dimension: Dict[str, Dict[str, Any]]

    verify_payload_order: bool

    def setUp(self) -> None:
        super().setUp()
        self.data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': f'my_data_series_with_extra_keys_{self.backend_key}',
            'external_id': f'{str(uuid.uuid4()).replace("-", "_")}',
            'allow_extra_fields': False,
            'backend': self.backend_key
        }, simulate_tenant=False)

        # create a bunch of facts
        for i in range(100):
            self.create_payload(self.data_series['float_facts'], payload={
                "external_id": f"fact_{i}",
                "name": f"fact_{i}",
                "optional": False
            }, simulate_tenant=False)

        data_series_for_dim_1_and_2 = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': 'my_data_series_2',
            'external_id': 'external_id2'
        }, simulate_tenant=False)

        data_series_for_dim_3 = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': 'my_data_series_3',
            'external_id': 'external_id3'
        }, simulate_tenant=False)

        dim_1 = self.create_payload(self.data_series['dimensions'], payload={
            'name': 'dim_1',
            'reference': data_series_for_dim_1_and_2['url'],
            'external_id': 'dim_1',
            'optional': False
        })

        self.dim_entries_1 = {}
        for i in range(0, 2):
            self.dim_entries_1[i] = self.create_payload(data_series_for_dim_1_and_2['data_points'], {
                'external_id': f'1_{i}',
                'payload': {}
            })

        # we intentionally use the same dataseries for this dimension again
        # so that we can test properly if resolution still works
        dim_2 = self.create_payload(self.data_series['dimensions'], payload={
            'name': 'dim_2',
            'reference': data_series_for_dim_1_and_2['url'],
            'external_id': 'dim_2',
            'optional': False
        })

        self.dim_entries_2 = {}
        for i in range(0, 2):
            self.dim_entries_2[i] = self.create_payload(data_series_for_dim_1_and_2['data_points'], {
                'external_id': f'2_{i}',
                'payload': {}
            })

        dim_3 = self.create_payload(self.data_series['dimensions'], payload={
            'name': 'dim_3',
            'reference': data_series_for_dim_3['url'],
            'external_id': 'dim_3',
            'optional': False
        })

        self.dim_entries_3 = {}
        for i in range(0, 2):
            self.dim_entries_3[i] = self.create_payload(data_series_for_dim_3['data_points'], {
                'external_id': f'3_{i}',
                'payload': {}
            })

        self.data_points = {}
        self.data_points_resolved_dimension = {}

        # put some data in
        for dp_idx in range(20):
            dim_1_val = random.choice(list(self.dim_entries_1.values()))
            dim_2_val = random.choice(list(self.dim_entries_2.values()))
            dim_3_val = random.choice(list(self.dim_entries_3.values()))
            payload = {
                "dim_1": dim_1_val['id'],
                "dim_2": dim_2_val['id'],
                "dim_3": dim_3_val['id']
            }
            for i in range(100):
                payload[f"fact_{i}"] = random.random()

            self.data_points[f'dp_{dp_idx}'] = self.create_payload(self.data_series['data_points'], payload={
                "external_id": f'dp_{dp_idx}',
                "payload": payload
            }, simulate_tenant=False)

            self.data_points_resolved_dimension[f'dp_{dp_idx}'] = copy.deepcopy(self.data_points[f'dp_{dp_idx}'])
            self.data_points_resolved_dimension[f'dp_{dp_idx}']['payload']['dim_1'] = dim_1_val['external_id']
            self.data_points_resolved_dimension[f'dp_{dp_idx}']['payload']['dim_2'] = dim_2_val['external_id']
            self.data_points_resolved_dimension[f'dp_{dp_idx}']['payload']['dim_3'] = dim_3_val['external_id']

    def test_basic_data_point_fetch(self) -> None:
        # fetch some data from the first page, check if it is the data we expect, if yes, regular fetching works
        page_1 = self.get_payload(self.data_series['data_points'])['data']
        self.assertEqual(self.data_points[page_1[0]['external_id']], page_1[0])

    def test_basic_data_point_fetch_identify_by_external_id(self) -> None:
        # fetch some data from the first page, check if it is the data we expect, if yes, regular fetching works
        page_1 = self.get_payload(self.data_series['data_points'] + '?identify_dimensions_by_external_id')['data']
        self.assertEqual(self.data_points_resolved_dimension[page_1[0]['external_id']], page_1[0])

    def test_basic_versions_endpoint_fetch(self) -> None:
        if self.backend_key in [elem[0] for elem in StorageBackendType.choices_with_split_history()]:
            endpoint_data = self.get_payload(self.data_series['history_data_points'] + '?include_versions')['data'][0]

            expected_payload_keys = set(self.data_points_resolved_dimension[endpoint_data['external_id']]["payload"].keys())
            self.assertEqual(expected_payload_keys, set(endpoint_data["versions"]["payload"]))

            # we dont care about the versions for the basic assert
            del endpoint_data['versions']
            # fetch some data from the first page, check if it is the data we expect, if yes, regular fetching works
            self.assertEqual(self.data_points[endpoint_data['external_id']], endpoint_data)

    def test_basic_versions_endpoint_fetch_identify_by_external_id(self) -> None:
        if self.backend_key in [elem[0] for elem in StorageBackendType.choices_with_split_history()]:
            endpoint_data = self.get_payload(self.data_series['history_data_points'] + '?include_versions&identify_dimensions_by_external_id')['data'][0]


            expected_payload_keys = set(self.data_points_resolved_dimension[endpoint_data['external_id']]["payload"].keys())
            self.assertEqual(expected_payload_keys, set(endpoint_data["versions"]["payload"]))

            # we dont care about the versions for the basic assert
            del endpoint_data['versions']
            # fetch some data from the first page, check if it is the data we expect, if yes, regular fetching works
            self.assertEqual(self.data_points_resolved_dimension[endpoint_data['external_id']], endpoint_data)


class DynamicSQLNoHistoryLargeDataSeriesDataPointFetchTest(BaseLargeDataSeriesDataPointFetchTest):
    backend_key: str = StorageBackendType.DYNAMIC_SQL_NO_HISTORY.value


class DynamicSQLMaterializedFlatHistoryLargeDataSeriesDataPointFetchTest(BaseLargeDataSeriesDataPointFetchTest):
    backend_key: str = StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value

del BaseLargeDataSeriesDataPointFetchTest
