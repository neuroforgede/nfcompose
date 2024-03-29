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

    def test_omit_dimension_or_image(self) -> None:
        data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': 'my_data_series',
            'external_id': 'external_id1'
        }, simulate_tenant=False)

        data_series_for_dim = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': 'my_data_series',
            'external_id': 'external_id2'
        }, simulate_tenant=False)

        dim = self.create_payload(data_series['dimensions'], payload={
            'name': 'my_dim_2',
            'reference': data_series_for_dim['url'],
            'external_id': 'my_dim',
            'optional': False
        })

        # check if this works with multipart data being present
        # this is required since we some multipart data hacks
        image_fact = self.create_payload(data_series['image_facts'], payload={
            'name': 'required_image_fact',
            'external_id': 'fact_3',
            'optional': False
        })

        dim_entries: Dict[int, Any] = {}
        for i in range(0, 2):
            dim_entries[i] = self.create_payload(data_series_for_dim['data_points'], {
                'external_id': f'{i}',
                'payload': {}
            })

        with generate_photo_file() as image_file:
            should_work_payload = {
                f'identify_dimensions_by_external_id': True,
                f"external_id": 'should_work',
                f"payload.{dim['external_id']}": dim_entries[0]['external_id'],
                f"payload.{image_fact['external_id']}": image_file,
            }
            dp_should_work = \
                self.create_payload(url=data_series['data_points'],
                                    payload=should_work_payload, format='multipart', equality_check=False,
                                    simulate_tenant=False)

        with generate_photo_file() as image_file:
            should_not_work_payload = {
                f'identify_dimensions_by_external_id': True,
                f"external_id": 'should_not_work',
                f"payload.{image_fact['external_id']}": image_file
            }
            response = self.create_payload_unchecked(url=data_series['data_points'],
                                payload=should_not_work_payload, format='multipart')
            self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

        with generate_photo_file() as image_file:
            should_not_work_payload = {
                f'identify_dimensions_by_external_id': True,
                f"external_id": 'should_not_work',
                f"payload.{dim['external_id']}": '',
                f"payload.{image_fact['external_id']}": image_file
            }
            response = self.create_payload_unchecked(url=data_series['data_points'],
                                payload=should_not_work_payload, format='multipart')
            self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

        # omitting the image should not work either

        should_not_work_payload = {
            f'identify_dimensions_by_external_id': True,
            f"external_id": 'should_not_work',
            f"payload.{dim['external_id']}": dim_entries[0]['external_id']
        }
        response = self.create_payload_unchecked(url=data_series['data_points'],
                            payload=should_not_work_payload, format='multipart')
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
