# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


import io
from typing import Tuple, Any, Dict, Callable, List, cast

from PIL import Image as PIL_Image  # type: ignore
from django.utils import dateparse
from rest_framework import status

from skipper import modules
from skipper.core.tests.base import BaseViewTest, BASE_URL

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

    def test_setup_data_series(self) -> Dict[str, Any]:
        data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': 'my_data_series',
            'external_id': 'external_id1'
        }, simulate_tenant=False)
        self.assertEqual('my_data_series', data_series['name'])
        self.assertEqual('external_id1', data_series['external_id'])

        _accessed_unauthorized = self.unauthorizedClient.get(path=data_series['url'])
        self.assertEqual(status.HTTP_403_FORBIDDEN, _accessed_unauthorized.status_code)

        _accessed_from_other_tenant = self.client2.get(path=data_series['url'])
        self.assertEqual(status.HTTP_404_NOT_FOUND, _accessed_from_other_tenant.status_code)

        # assert that we can not create a dataseries with the same id for the same tenant
        _failed_response_duplicate = self.client.post(path=DATA_SERIES_BASE_URL + 'dataseries/', data={
            'name': 'my_data_series',
            'external_id': 'external_id1'
        })
        self.assertEqual(status.HTTP_400_BAD_REQUEST, _failed_response_duplicate.status_code)

        data_series_2 = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': 'my_data_series_2',
            'external_id': 'external_id2'
        }, simulate_tenant=False)
        self.assertEqual('my_data_series_2', data_series_2['name'])
        self.assertEqual('external_id2', data_series_2['external_id'])

        data_series_3 = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': 'my_data_series_3',
            'external_id': 'external_id3'
        }, simulate_tenant=False)
        self.assertEqual('my_data_series_3', data_series_3['name'])
        self.assertEqual('external_id3', data_series_3['external_id'])

        # create enum dimensions with some enum entries for each

        dim_1 = self.create_payload(data_series['dimensions'], payload={
            'name': 'my_dim_1',
            'reference': data_series_2['url'],
            'external_id': 'my_dim_1_id',
            'optional': False
        })
        self.assertEqual('my_dim_1', dim_1['name'])
        self.assertEqual('my_dim_1_id', dim_1['external_id'])

        dim_1_entries: Dict[int, Any] = {}
        for i in range(0, 2):
            dim_1_entries[i] = self.create_payload(data_series_2['data_points'], {
                'external_id': f'{i}',
                'payload': {}
            })

        self.assertEqual(2, self.get_payload(data_series_2['data_points'] + '?count')['count'])

        dim_2 = self.create_payload(data_series['dimensions'], payload={
            'name': 'my_dim_2',
            'reference': data_series_3['url'],
            'external_id': 'my_dim_2_id',
            'optional': False
        })
        self.assertEqual('my_dim_2', dim_2['name'])
        self.assertEqual('my_dim_2_id', dim_2['external_id'])

        dim_2_entries: Dict[int, Any] = {}
        for i in range(0, 2):
            dim_2_entries[i] = self.create_payload(data_series_3['data_points'], {
                'external_id': f'{i}',
                'payload': {}
            })

        self.assertEqual(2, self.get_payload(data_series_3['data_points'] + '?count')['count'])

        # float fact creation

        required_float_fact = self.create_payload(data_series['float_facts'], payload={
            'name': 'required_float_fact',
            'external_id': 'fact_1',
            'optional': False
        })
        self.assertEqual('required_float_fact', required_float_fact['name'])
        self.assertEqual(False, required_float_fact['optional'])

        optional_float_fact = self.create_payload(data_series['float_facts'], payload={
            'name': 'optional_float_fact',
            'external_id': 'fact_2',
            'optional': True
        })
        self.assertEqual('optional_float_fact', optional_float_fact['name'])
        self.assertEqual(True, optional_float_fact['optional'])

        # image fact creation

        required_image_fact = self.create_payload(data_series['image_facts'], payload={
            'name': 'required_image_fact',
            'external_id': 'fact_3',
            'optional': False
        })
        self.assertEqual('required_image_fact', required_image_fact['name'])
        self.assertEqual(False, required_image_fact['optional'])

        optional_image_fact = self.create_payload(data_series['image_facts'], payload={
            'name': 'optional_image_fact',
            'external_id': 'fact_4',
            'optional': True
        })
        self.assertEqual('optional_image_fact', optional_image_fact['name'])
        self.assertEqual(True, optional_image_fact['optional'])

        required_json_fact = self.create_payload(data_series['json_facts'], payload={
            'name': 'required_json_fact',
            'external_id': 'fact_5',
            'optional': False
        })
        self.assertEqual('required_json_fact', required_json_fact['name'])
        self.assertEqual(False, required_json_fact['optional'])

        optional_json_fact = self.create_payload(data_series['json_facts'], payload={
            'name': 'optional_json_fact',
            'external_id': 'fact_6',
            'optional': True
        })
        self.assertEqual('optional_json_fact', optional_json_fact['name'])
        self.assertEqual(True, optional_json_fact['optional'])

        return {
            'data_series': data_series,
            'dimensions': [dim_1, dim_2],
            'dimension_entries': {
                dim_1['id']: dim_1_entries,
                dim_2['id']: dim_2_entries
            },
            'required_float_fact': required_float_fact,
            'optional_float_fact': optional_float_fact,
            'required_image_fact': required_image_fact,
            'optional_image_fact': optional_image_fact,
            'required_json_fact': required_json_fact,
            'optional_json_fact': optional_json_fact
        }

    def test_write_and_query_data_points(self) -> None:
        setup_data = self.test_setup_data_series()

        data_series = setup_data['data_series']
        dim_1 = setup_data['dimensions'][0]
        dim_2 = setup_data['dimensions'][1]

        with generate_photo_file() as image_file_1:
            with generate_some_other_photo_file() as image_file_2:
                data_point_everything_set_payload = {
                    f'identify_dimensions_by_external_id': True,
                    f"external_id": '1',
                    f"payload.{dim_1['external_id']}": setup_data['dimension_entries'][dim_1['id']][0]['external_id'],
                    f"payload.{dim_2['external_id']}": setup_data['dimension_entries'][dim_2['id']][1]['external_id'],
                    f"payload.{setup_data['required_float_fact']['external_id']}": 1.0,
                    f"payload.{setup_data['optional_float_fact']['external_id']}": 2.0,
                    f"payload.{setup_data['required_image_fact']['external_id']}": image_file_1,
                    f"payload.{setup_data['optional_image_fact']['external_id']}": image_file_2,
                    f"payload.{setup_data['required_json_fact']['external_id']}": "{}"
                }
                data_point_everything_set = \
                    self.create_payload(url=data_series['data_points'],
                                        payload=data_point_everything_set_payload, format='multipart', equality_check=False,
                                        simulate_tenant=False)

        with generate_photo_file() as image_file_1:
            data_point_only_required_set_payload = {
                f'identify_dimensions_by_external_id': True,
                f"external_id": '2',
                f"payload.{dim_1['external_id']}": setup_data['dimension_entries'][dim_1['id']][0]['external_id'],
                f"payload.{dim_2['external_id']}": setup_data['dimension_entries'][dim_2['id']][1]['external_id'],
                f"payload.{setup_data['required_float_fact']['external_id']}": 1.0,
                f"payload.{setup_data['required_image_fact']['external_id']}": image_file_1,
                f"payload.{setup_data['required_json_fact']['external_id']}": "{}"
            }
            data_point_only_required_set = \
                self.create_payload(url=data_series['data_points'],
                                    payload=data_point_only_required_set_payload, format='multipart', equality_check=False,
                                    simulate_tenant=False
                                    )

        no_facts_set_payload = {
            f"payload.{dim_1['external_id']}": setup_data['dimension_entries'][dim_1['id']][0]['external_id'],
            f"payload.{dim_2['external_id']}": setup_data['dimension_entries'][dim_2['id']][1]['external_id'],
        }
        no_data_set_response = \
            self.client.post(path=data_series['data_points'], data=no_facts_set_payload,
                             format='multipart')
        self.assertEqual(status.HTTP_400_BAD_REQUEST, no_data_set_response.status_code)

        with generate_photo_file() as image_file_1:
            with generate_some_other_photo_file() as image_file_2:
                no_dims_set_payload = {
                    f'identify_dimensions_by_external_id': True,
                    f"payload.{setup_data['required_float_fact']['external_id']}": 1.0,
                    f"payload.{setup_data['optional_float_fact']['external_id']}": 2.0,
                    f"payload.{setup_data['required_image_fact']['external_id']}": image_file_1,
                    f"payload.{setup_data['optional_image_fact']['external_id']}": image_file_2
                }
                no_dims_set_response = \
                    self.client.post(path=data_series['data_points'], data=no_dims_set_payload,
                                     format='multipart')
                self.assertEqual(status.HTTP_400_BAD_REQUEST, no_dims_set_response.status_code)

        data_points = {
            'data_point_everything_set': data_point_everything_set,
            'data_point_only_required_set': data_point_only_required_set
        }

        _all = self.get_payload(url=data_series['data_points'] + '?count')
        self.assertEqual(2, _all['count'])
        self.assertEqual(2, len(_all['data']))

        filtered_by_external_id = self.get_payload(url=f'{data_series["data_points"]}?external_id={data_point_everything_set["external_id"]}&count')
        self.assertEqual(1, filtered_by_external_id['count'])
        self.assertEqual(1, len(filtered_by_external_id['data']))