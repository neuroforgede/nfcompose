# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from rest_framework import status

from skipper import modules
from skipper.core.tests.base import BaseViewTest, BASE_URL

DATA_SERIES_BASE_URL = BASE_URL + modules.url_representation(modules.Module.DATA_SERIES) + '/'


class BrokenPayloadValidationTest(BaseViewTest):
    # the list endpoint is disabled for datapoints if we do not select for a data series
    url_under_test = DATA_SERIES_BASE_URL + 'dataseries/'
    simulate_other_tenant = True

    def test_payload_no_json(self) -> None:
        data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': 'my_data_series',
            'external_id': 'external_id',
        }, simulate_tenant=False)
        response = self.client.post(
            path=data_series['data_points'],
            data={
                "external_id": "123123",
                "payload": 1
            },
            format='json'
        )
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_payload_null(self) -> None:
        data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': 'my_data_series',
            'external_id': 'external_id',
        }, simulate_tenant=False)
        response = self.client.post(
            path=data_series['data_points'],
            data={
                "external_id": "123123",
                "payload": None
            },
            format='json'
        )
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_payload_string(self) -> None:
        data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': 'my_data_series',
            'external_id': 'external_id',
        }, simulate_tenant=False)
        response = self.client.post(
            path=data_series['data_points'],
            data={
                "external_id": "123123",
                "payload": ''
            },
            format='json'
        )
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
