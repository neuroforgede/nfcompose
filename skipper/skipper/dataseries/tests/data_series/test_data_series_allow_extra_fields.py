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
from django.utils.http import urlencode
from urllib.parse import quote

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


class DataPointWithExtraFieldsTest(BaseViewTest):
    # the list endpoint is disabled for datapoints if we do not select for a data series
    url_under_test = DATA_SERIES_BASE_URL + 'dataseries/'
    simulate_other_tenant = True

    def test_allowed(self) -> None:
        data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': f'my_data_series_with_extra_keys',
            'external_id': f'_external_id_1',
            'allow_extra_fields': True
        }, simulate_tenant=False)

        created = self.create_payload(url=data_series['data_points'], payload=lambda: {
            'external_id': '1',
            f'payload.blurb': '1',
        }, format='multipart', equality_check=False)

        self.assertEqual(created['external_id'], '1')
        self.assertFalse('blurb' in created['payload'])

    def test_not_allowed(self) -> None:
        data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': f'my_data_series_without_extra_keys',
            'external_id': f'_external_id_2',
            'allow_extra_fields': False
        }, simulate_tenant=False)

        response = self.client.post(path=data_series['data_points'], data={
            'external_id': '1',
            f'payload.blurb': '1',
        }, format='multipart')

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_allowed_bulk(self) -> None:
        data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': f'my_data_series_with_extra_keys',
            'external_id': f'_external_id_1',
            'allow_extra_fields': True
        }, simulate_tenant=False)

        response = self.client.post(path=data_series['data_points_bulk'], data={
            'batch-0.external_id': '1',
            'batch-0.payload.blurb': '1',
        }, format='multipart')

        self.assertEqual(1, len(response.json()['created_external_ids']))
        self.assertEqual('1', response.json()['created_external_ids'][0])

    def test_not_allowed_bulk(self) -> None:
        data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': f'my_data_series_without_extra_keys',
            'external_id': f'_external_id_2',
            'allow_extra_fields': False
        }, simulate_tenant=False)

        response = self.client.post(path=data_series['data_points_bulk'], data={
            'batch-0.external_id': '1',
            'batch-0.payload.blurb': '1',
        }, format='multipart')

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)


