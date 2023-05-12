# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import json
from rest_framework import status
from typing import Any, Dict

from skipper import modules
from skipper.core.tests.base import BaseViewTest, BASE_URL

DATA_SERIES_BASE_URL = BASE_URL + modules.url_representation(modules.Module.DATA_SERIES) + '/'


class DataSeriesFilterByFactTest(BaseViewTest):
    # the list endpoint is disabled for datapoints if we do not select for a data series
    url_under_test = DATA_SERIES_BASE_URL + 'dataseries/'

    def test_facts_are_accessible_via_external_id_url(self) -> None:
        data_series = self.create_payload(self.url_under_test, payload={
            'name': 'my_data_series_1',
            'external_id': 'external_id1'
        }, simulate_tenant=False)

        for fact_type in ['float', 'string', 'text', 'json', 'boolean']:
            external_id_fact = f'{fact_type}_fact'
            self.client.post(path=data_series[f'{fact_type}_facts'], data={
                'name': f'{external_id_fact}_name',
                'external_id': external_id_fact,
                'optional': False
            }, format='json')

        data_point_a: Dict[str, Any] = {
                'external_id': '1',
                'payload': {
                    'float_fact': 2.0,
                    'string_fact': 'abcdef',
                    'text_fact': 'long text',
                    'json_fact': {
                        'key1': 'value1',
                        'key2': 'value2',
                    },
                    'boolean_fact': False
                }
            }
        self.client.post(path=data_series['data_points'], data=data_point_a, format='json')

        data_point_b: Dict[str, Any] = {
            'external_id': '2',
            'payload': {
                'float_fact': 3.0,
                'string_fact': 'ghijk',
                'text_fact': 'longer text',
                'json_fact': {
                    'key1': 'valuea',
                    'key2': 'valueb',
                },
                'boolean_fact': True
            }
        }
        self.client.post(path=data_series['data_points'], data=data_point_b, format='json')

        def data_equals_data_point(data: Dict[str, Any], data_point: Dict[str, Any]) -> None:
            self.assertEquals(data_point['external_id'], data['external_id'])
            self.assertEquals(data_point['payload']['float_fact'], data['payload']['float_fact'])
            self.assertEquals(data_point['payload']['string_fact'], data['payload']['string_fact'])
            self.assertEquals(data_point['payload']['text_fact'], data['payload']['text_fact'])
            self.assertEquals(data_point['payload']['boolean_fact'], data['payload']['boolean_fact'])

        payload_a = data_point_a['payload']
        for fact in payload_a:
            if fact == 'json_fact':
                pass
            else:
                response = self.client.get(path=f'{data_series["data_points"]}?filter={{ "{fact}": {json.dumps(payload_a[fact])} }}').json()
                self.assertEquals(1, len(response['data']))
                data_equals_data_point(response['data'][0], data_point_a)

        payload_b = data_point_b['payload']
        for fact in payload_b:
            if fact == 'json_fact':
                pass
            else:
                response = self.client.get(
                    path=f'{data_series["data_points"]}?filter={{ "{fact}": {json.dumps(payload_b[fact])} }}').json()
                self.assertEquals(1, len(response['data']))
                data_equals_data_point(response['data'][0], data_point_b)

