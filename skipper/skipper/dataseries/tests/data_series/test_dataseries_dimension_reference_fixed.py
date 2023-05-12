# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from rest_framework import status

from skipper import modules
from skipper.core.tests.base import BaseViewTest, BASE_URL

# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


DATA_SERIES_BASE_URL = BASE_URL + modules.url_representation(modules.Module.DATA_SERIES) + '/'


class DataSeriesTest(BaseViewTest):
    # the list endpoint is disabled for datapoints if we do not select for a data series
    url_under_test = DATA_SERIES_BASE_URL + 'dataseries/'
    simulate_other_tenant = True

    def test_cant_change(self) -> None:
        data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': 'my_data_series_1',
            'external_id': 'external_id1'
        }, simulate_tenant=False)

        data_series_for_dim_1_and_2 = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': 'my_data_series_2',
            'external_id': 'external_id2'
        }, simulate_tenant=False)

        some_other_ds = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': 'my_data_series_3',
            'external_id': 'external_id3'
        }, simulate_tenant=False)

        dim_1 = self.create_payload(data_series['dimensions'], payload={
            'name': 'my_dim_1',
            'reference': data_series_for_dim_1_and_2['url'],
            'external_id': 'my_dim_1',
            'optional': False
        })

        failed_response = self.client.put(path=dim_1['url'], data={
            'name': 'my_dim_1',
            'reference': some_other_ds['url'],
            'external_id': 'my_dim_1',
            'optional': False
        })
        self.assertEquals(status.HTTP_400_BAD_REQUEST, failed_response.status_code)

    def test_cant_delete_dataseries_if_still_referenced(self) -> None:
        data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': 'my_data_series_1',
            'external_id': 'external_id1'
        }, simulate_tenant=False)

        data_series_for_dim_1 = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': 'my_data_series_2',
            'external_id': 'external_id2'
        }, simulate_tenant=False)

        data_series_for_dim_2 = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': 'my_data_series_3',
            'external_id': 'external_id3'
        }, simulate_tenant=False)

        dim_1 = self.create_payload(data_series['dimensions'], payload={
            'name': 'my_dim_1',
            'reference': data_series_for_dim_1['url'],
            'external_id': 'my_dim_1',
            'optional': False
        })

        dim_2 = self.create_payload(data_series['dimensions'], payload={
            'name': 'my_dim_2',
            'reference': data_series_for_dim_2['url'],
            'external_id': 'my_dim_2',
            'optional': False
        })

        deletion_response = self.client.delete(path=data_series_for_dim_1['url'])
        self.assertEqual(deletion_response.status_code, status.HTTP_400_BAD_REQUEST)
        deletion_response_json = deletion_response.json()
        self.assertIn('visible_references', deletion_response_json)
        self.assertEquals(1, len(deletion_response_json['visible_references']))
        self.assertIn('data_series', deletion_response_json['visible_references'][0])
        self.assertIn('dimension', deletion_response_json['visible_references'][0])
        self.assertURLEqual(deletion_response_json['visible_references'][0]['data_series'], data_series['url'])  # type: ignore
        self.assertURLEqual(deletion_response_json['visible_references'][0]['dimension'], dim_1['url'])  # type: ignore

        # after the dimension is deleted, it should be allowed to delete the data series
        self.delete_payload(dim_1['url'])
        deletion_response = self.client.delete(path=data_series_for_dim_1['url'])
        self.assertEqual(deletion_response.status_code, status.HTTP_204_NO_CONTENT)
