# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


import io
from typing import Any, Dict

from PIL import Image as PIL_Image  # type: ignore

from skipper import modules
from skipper.core.tests.base import BaseViewTest, BASE_URL

from rest_framework import status


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


class DataPointTest(BaseViewTest):
    # the list endpoint is disabled for datapoints if we do not select for a data series
    url_under_test = DATA_SERIES_BASE_URL + 'dataseries/'
    simulate_other_tenant = True

    def test_optional_dimension(self) -> None:
        data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': 'my_data_series_1',
            'external_id': 'external_id1'
        }, simulate_tenant=False)

        data_series_for_dim_1_and_2 = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': 'my_data_series_2',
            'external_id': 'external_id2'
        }, simulate_tenant=False)

        data_series_for_dim_3 = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': 'my_data_series_3',
            'external_id': 'external_id3'
        }, simulate_tenant=False)

        dim_1 = self.create_payload(data_series['dimensions'], payload={
            'name': 'my_dim_1',
            'reference': data_series_for_dim_1_and_2['url'],
            'external_id': 'my_dim_1',
            'optional': False
        })

        dim_entries_1: Dict[int, Any] = {}
        for i in range(0, 2):
            dim_entries_1[i] = self.create_payload(data_series_for_dim_1_and_2['data_points'], {
                'external_id': f'1_{i}',
                'payload': {}
            })

        # we intentionally use the same dataseries for this dimension again
        # so that we can test properly if resolution still works
        dim_2 = self.create_payload(data_series['dimensions'], payload={
            'name': 'my_dim_2',
            'reference': data_series_for_dim_1_and_2['url'],
            'external_id': 'my_dim_2',
            'optional': True
        })

        dim_entries_2: Dict[int, Any] = {}
        for i in range(0, 2):
            dim_entries_2[i] = self.create_payload(data_series_for_dim_1_and_2['data_points'], {
                'external_id': f'2_{i}',
                'payload': {}
            })

        dim_3 = self.create_payload(data_series['dimensions'], payload={
            'name': 'my_dim_3',
            'reference': data_series_for_dim_3['url'],
            'external_id': 'my_dim_3',
            'optional': True
        })

        dim_entries_3: Dict[int, Any] = {}
        for i in range(0, 2):
            dim_entries_3[i] = self.create_payload(data_series_for_dim_3['data_points'], {
                'external_id': f'3_{i}',
                'payload': {}
            })

        def test_optional_dimension() -> None:
            no_dim_should_fail = self.client.post(
                path=data_series['data_points'],
                data={
                    f"external_id": 'no_dim_should_fail',
                    "payload": {}
                },
                format='json'
            )
            self.assertEqual(status.HTTP_400_BAD_REQUEST, no_dim_should_fail.status_code)

            only_required = {
                f"external_id": 'only_required',
                "payload": {
                    f"{dim_1['external_id']}": dim_entries_1[0]['id']
                }
            }
            dp_only_required = \
                self.create_payload(url=data_series['data_points'],
                                    payload=only_required, format='json', equality_check=False,
                                    simulate_tenant=False)
            self.assertEqual(1, len(dp_only_required['payload'].keys()))
            self.assertEqual(dim_entries_1[0]['id'], dp_only_required['payload'][dim_1['external_id']])

            together_with_one_optional = {
                f"external_id": 'together_with_one_optional',
                "payload": {
                    f"{dim_1['external_id']}": dim_entries_1[0]['id'],
                    f"{dim_2['external_id']}": dim_entries_2[0]['id']
                }
            }
            dp_together_with_one_optional = \
                self.create_payload(url=data_series['data_points'],
                                    payload=together_with_one_optional, format='json', equality_check=False,
                                    simulate_tenant=False)
            self.assertEqual(2, len(dp_together_with_one_optional['payload'].keys()))
            self.assertEqual(dim_entries_1[0]['id'], dp_together_with_one_optional['payload'][dim_1['external_id']])
            self.assertEqual(dim_entries_2[0]['id'], dp_together_with_one_optional['payload'][dim_2['external_id']])

        test_optional_dimension()

        def test_optional_dimension_empty_string() -> None:
            no_dim_should_fail = self.client.post(
                path=data_series['data_points'],
                data={
                    f"external_id": 'no_dim_should_fail_empty_string',
                    "payload": {
                        f"{dim_1['external_id']}": ""
                    }
                },
                format='json'
            )
            self.assertEqual(status.HTTP_400_BAD_REQUEST, no_dim_should_fail.status_code)

            only_required = {
                f"external_id": 'only_required_empty_string',
                "payload": {
                    f"{dim_1['external_id']}": dim_entries_1[0]['id'],
                    f"{dim_2['external_id']}": ""
                }
            }
            dp_only_required = \
                self.create_payload(url=data_series['data_points'],
                                    payload=only_required, format='json', equality_check=False,
                                    simulate_tenant=False)
            self.assertEqual(1, len(dp_only_required['payload'].keys()))
            self.assertEqual(dim_entries_1[0]['id'], dp_only_required['payload'][dim_1['external_id']])

            together_with_one_optional = {
                f"external_id": 'together_with_one_optional_empty_string',
                "payload": {
                    f"{dim_1['external_id']}": dim_entries_1[0]['id'],
                    f"{dim_2['external_id']}": dim_entries_2[0]['id'],
                    f"{dim_3['external_id']}": ""
                }
            }
            dp_together_with_one_optional = \
                self.create_payload(url=data_series['data_points'],
                                    payload=together_with_one_optional, format='json', equality_check=False,
                                    simulate_tenant=False)
            self.assertEqual(2, len(dp_together_with_one_optional['payload'].keys()))
            self.assertEqual(dim_entries_1[0]['id'], dp_together_with_one_optional['payload'][dim_1['external_id']])
            self.assertEqual(dim_entries_2[0]['id'], dp_together_with_one_optional['payload'][dim_2['external_id']])

        test_optional_dimension_empty_string()

        def test_identification_by_regular_vs_external_id() -> None:
            identified_by_regular_id = {
                f"external_id": 'identified_by_regular_id',
                'identify_dimensions_by_external_id': False,
                "payload": {
                    f"{dim_1['external_id']}": dim_entries_1[0]['id'],
                    f"{dim_2['external_id']}": dim_entries_2[0]['id'],
                    f"{dim_3['external_id']}": dim_entries_3[0]['id']
                }
            }
            dp_identified_by_regular_id = \
                self.create_payload(url=data_series['data_points'],
                                    payload=identified_by_regular_id, format='json', equality_check=False,
                                    simulate_tenant=False)
            self.assertEqual(3, len(dp_identified_by_regular_id['payload'].keys()))
            self.assertEqual(dim_entries_1[0]['id'], dp_identified_by_regular_id['payload'][dim_1['external_id']])
            self.assertEqual(dim_entries_2[0]['id'], dp_identified_by_regular_id['payload'][dim_2['external_id']])
            self.assertEqual(dim_entries_3[0]['id'], dp_identified_by_regular_id['payload'][dim_3['external_id']])

            dp_identified_by_regular_id_fetched_regular = self.get_payload(url=dp_identified_by_regular_id['url'])
            self.assertEqual(dp_identified_by_regular_id, dp_identified_by_regular_id_fetched_regular)

            dp_identified_by_regular_id_fetched_resolved = self.get_payload(url=dp_identified_by_regular_id['url'] + '?identify_dimensions_by_external_id')
            self.assertEqual(dim_entries_1[0]['external_id'], dp_identified_by_regular_id_fetched_resolved['payload'][dim_1['external_id']])
            self.assertEqual(dim_entries_2[0]['external_id'], dp_identified_by_regular_id_fetched_resolved['payload'][dim_2['external_id']])
            self.assertEqual(dim_entries_3[0]['external_id'], dp_identified_by_regular_id_fetched_resolved['payload'][dim_3['external_id']])

            identified_by_external_id = {
                f"external_id": 'identified_by_external_id',
                'identify_dimensions_by_external_id': True,
                "payload": {
                    f"{dim_1['external_id']}": dim_entries_1[0]['external_id'],
                    f"{dim_2['external_id']}": dim_entries_2[0]['external_id'],
                    f"{dim_3['external_id']}": dim_entries_3[0]['external_id']
                }
            }
            dp_identified_by_external_id = \
                self.create_payload(url=data_series['data_points'],
                                    payload=identified_by_external_id, format='json', equality_check=False,
                                    simulate_tenant=False)
            self.assertEqual(3, len(dp_identified_by_external_id['payload'].keys()))
            self.assertEqual(dim_entries_1[0]['external_id'], dp_identified_by_external_id['payload'][dim_1['external_id']])
            self.assertEqual(dim_entries_2[0]['external_id'], dp_identified_by_external_id['payload'][dim_2['external_id']])
            self.assertEqual(dim_entries_3[0]['external_id'], dp_identified_by_external_id['payload'][dim_3['external_id']])

            dp_identified_by_external_id_fetched_resolved = self.get_payload(url=dp_identified_by_external_id['url'] + '?identify_dimensions_by_external_id')
            self.assertEqual(dp_identified_by_external_id, dp_identified_by_external_id_fetched_resolved)

            dp_identified_by_external_id_fetched_regular = self.get_payload(url=dp_identified_by_external_id['url'])
            self.assertEqual(dim_entries_1[0]['id'], dp_identified_by_external_id_fetched_regular['payload'][dim_1['external_id']])
            self.assertEqual(dim_entries_2[0]['id'], dp_identified_by_external_id_fetched_regular['payload'][dim_2['external_id']])
            self.assertEqual(dim_entries_3[0]['id'], dp_identified_by_external_id_fetched_regular['payload'][dim_3['external_id']])

        test_identification_by_regular_vs_external_id()
