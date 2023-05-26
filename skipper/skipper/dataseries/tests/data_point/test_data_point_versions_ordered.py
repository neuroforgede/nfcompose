# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import copy
import random

import uuid
from typing import Dict, Any

from skipper import modules
from skipper.core.tests.base import BaseViewTest, BASE_URL
from skipper.dataseries.storage.contract import StorageBackendType

DATA_SERIES_BASE_URL = BASE_URL + modules.url_representation(modules.Module.DATA_SERIES) + '/'


class BaseHistoricalDataPointVersionsOrderedTest(BaseViewTest):

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

    data_points_resolved_dimension: Dict[str, Any]

    verify_payload_order: bool

    def setUp(self) -> None:
        super().setUp()
        self.data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': f'my_data_series_with_extra_keys_{self.backend_key}',
            'external_id': f'{str(uuid.uuid4()).replace("-", "_")}',
            'allow_extra_fields': False,
            'backend': self.backend_key
        }, simulate_tenant=False)

        # create a float fact (should be enough, all facts should be treated the same)

        self.create_payload(self.data_series['float_facts'], payload={
            "external_id": f"fact_float",
            "name": f"fact_float",
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

        def put_version_data_in() -> None:
            dim_1_val = random.choice(list(self.dim_entries_1.values()))
            dim_2_val = random.choice(list(self.dim_entries_2.values()))
            dim_3_val = random.choice(list(self.dim_entries_3.values()))
            payload = {
                "dim_1": dim_1_val['id'],
                "dim_2": dim_2_val['id'],
                "dim_3": dim_3_val['id'],
                "fact_float": 0
            }

            self.data_points['dp'] = self.create_payload(self.data_series['data_points'], payload={
                "external_id": f'dp',
                "payload": payload
            }, simulate_tenant=False)

            url = self.data_points['dp']['url']

            # put some other data in to provoke different order
            for other_idx in range(200):
                dim_1_val = random.choice(list(self.dim_entries_1.values()))
                dim_2_val = random.choice(list(self.dim_entries_2.values()))
                dim_3_val = random.choice(list(self.dim_entries_3.values()))
                payload = {
                    "dim_1": dim_1_val['id'],
                    "dim_2": dim_2_val['id'],
                    "dim_3": dim_3_val['id'],
                    "fact_float": other_idx
                }

                self.data_points[f'dp_{other_idx}'] = self.create_payload(self.data_series['data_points'], payload={
                    "external_id": f'dp_{other_idx}',
                    "payload": payload
                })

                # put some new version data in
                for dp_version_idx in range(3):
                    dim_1_val = random.choice(list(self.dim_entries_1.values()))
                    dim_2_val = random.choice(list(self.dim_entries_2.values()))
                    dim_3_val = random.choice(list(self.dim_entries_3.values()))
                    payload = {
                        "dim_1": dim_1_val['id'],
                        "dim_2": dim_2_val['id'],
                        "dim_3": dim_3_val['id'],
                        "fact_float": dp_version_idx
                    }

                    self.data_points['dp'] = self.update_payload(url, payload={
                        "external_id": f'dp',
                        "payload": payload
                    })

        put_version_data_in()

    def test_versions_properly_ordered(self) -> None:
        # fetch some data from the first page, check if it is the data we expect, if yes, regular fetching works
        page_1 = self.get_payload(self.data_series['history_data_points'] + '?include_versions')['data']

        versions = page_1[0]['versions']

        self.assertEqual(page_1[0]['external_id'], 'dp')

        versions_data_point = versions['data_point']
        sorted_versions_data_point = sorted(versions_data_point,
                                            key=lambda x: (x['point_in_time'], x['sub_clock']))
        self.assertEqual(versions_data_point, sorted_versions_data_point)

        if self.backend_key in [elem[0] for elem in StorageBackendType.choices_with_split_history()]:
            versions_payload = versions['payload']
            for fact_dim_key, versions_fact_dim in versions_payload.items():
                sorted_versions_fact_dim = sorted(versions_data_point,
                                                  key=lambda x: (x['point_in_time'], x['sub_clock']))
                self.assertEqual(versions_fact_dim, sorted_versions_fact_dim)


class DynamicSQLMaterializedFlatHistoryHistoricalDataPointVersionsOrderedTest(BaseHistoricalDataPointVersionsOrderedTest):
    backend_key: str = StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value


del BaseHistoricalDataPointVersionsOrderedTest
