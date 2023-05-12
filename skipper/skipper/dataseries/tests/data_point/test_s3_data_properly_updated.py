# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


import io
from typing import Any, Dict

import requests
from PIL import Image as PIL_Image  # type: ignore

from skipper import modules
from skipper.core.tests.base import BaseViewTest, BASE_URL

from rest_framework import status

from skipper.dataseries.storage.contract import StorageBackendType

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

    def test_s3_storage_updates_properly_regular_update_image(self) -> None:
        idx = 0
        for backend_key, backend_value in StorageBackendType.choices():
            self._test_s3_storage_updates_properly_regular_update(backend_value, idx, 'image_facts')
            idx += 1

    def test_s3_storage_updates_properly_upsert_image(self) -> None:
        idx = 0
        for backend_key, backend_value in StorageBackendType.choices():
            self._test_s3_storage_updates_properly_upsert(backend_value, idx, 'image_facts')
            idx += 1

    def test_s3_storage_updates_properly_regular_update_file(self) -> None:
        idx = 0
        for backend_key, backend_value in StorageBackendType.choices():
            self._test_s3_storage_updates_properly_regular_update(backend_value, idx, 'file_facts')
            idx += 1

    def test_s3_storage_updates_properly_upsert_file(self) -> None:
        idx = 0
        for backend_key, backend_value in StorageBackendType.choices():
            self._test_s3_storage_updates_properly_upsert(backend_value, idx, 'file_facts')
            idx += 1

    def _test_s3_storage_updates_properly_upsert(self, storage_backend_type: str, idx: int,
                                                         facts_type: str) -> None:
        data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': f'my_data_series{idx}',
            'external_id': f'external_id{idx}',
            'backend': storage_backend_type
        }, simulate_tenant=False)

        # check if this works with multipart data being present
        # this is required since we some multipart data hacks
        fact = self.create_payload(data_series[facts_type], payload={
            'name': 'required_fact',
            'external_id': 's3_file',
            'optional': False
        })

        with generate_photo_file() as image_file:
            payload = {
                f"batch-0.external_id": 'should_work',
                f"batch-0.payload.{fact['external_id']}": image_file,
                "async": False
            }
            initial_payload_resp = \
                self.client.post(path=data_series['data_points_bulk'],
                                 data=payload, format='multipart')
            self.assertEqual(status.HTTP_201_CREATED, initial_payload_resp.status_code)
            initial = self.get_payload(f"{data_series['data_points']}?external_id=should_work")['data'][0]

        with generate_some_other_photo_file() as some_other_image_file:
            updated_payload = {
                f"batch-0.external_id": 'should_work',
                f"batch-0.payload.{fact['external_id']}": some_other_image_file,
                "async": False
            }
            updated_payload_resp = \
                self.client.post(path=data_series['data_points_bulk'],
                                 data=updated_payload, format='multipart')
            self.assertEqual(status.HTTP_201_CREATED, updated_payload_resp.status_code)
            updated = self.get_payload(f"{data_series['data_points']}?external_id=should_work")['data'][0]


        initial_resp = requests.get(initial['payload']['s3_file'])
        self.assertEquals(status.HTTP_200_OK, initial_resp.status_code)

        initial_resp_again = requests.get(initial['payload']['s3_file'])
        self.assertEquals(status.HTTP_200_OK, initial_resp.status_code)

        # ensure the following assertion will make sense by getting the initial file twice and comparing it to itself
        self.assertEqual(ascii(initial_resp.content), ascii(initial_resp_again.content))

        updated_resp = requests.get(updated['payload']['s3_file'])
        self.assertEquals(status.HTTP_200_OK, updated_resp.status_code)

        self.assertNotEqual(ascii(initial_resp.content), ascii(updated_resp.content))

    def _test_s3_storage_updates_properly_regular_update(self, storage_backend_type: str, idx: int, facts_type: str) -> None:
        data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': f'my_data_series{idx}',
            'external_id': f'external_id{idx}',
            'backend': storage_backend_type
        }, simulate_tenant=False)

        # check if this works with multipart data being present
        # this is required since we some multipart data hacks
        fact = self.create_payload(data_series[facts_type], payload={
            'name': 'required_fact',
            'external_id': 's3_file',
            'optional': False
        })

        with generate_photo_file() as image_file:
            payload = {
                f"external_id": 'should_work',
                f"payload.{fact['external_id']}": image_file,
            }
            initial = \
                self.create_payload(url=data_series['data_points'],
                                    payload=payload, format='multipart', equality_check=False,
                                    simulate_tenant=False)

        with generate_some_other_photo_file() as some_other_image_file:
            updated_payload = {
                f"external_id": 'should_work',
                f"payload.{fact['external_id']}": some_other_image_file,
            }
            updated_payload_resp = \
                self.client.put(path=initial['url'],
                                data=updated_payload, format='multipart')
            self.assertEqual(status.HTTP_200_OK, updated_payload_resp.status_code)
            updated = updated_payload_resp.json()

        initial_resp = requests.get(initial['payload']['s3_file'])
        self.assertEquals(status.HTTP_200_OK, initial_resp.status_code)

        initial_resp_again = requests.get(initial['payload']['s3_file'])
        self.assertEquals(status.HTTP_200_OK, initial_resp.status_code)

        # ensure the following assertion will make sense by getting the initial file twice and comparing it to itself
        self.assertEqual(ascii(initial_resp.content), ascii(initial_resp_again.content))

        updated_resp = requests.get(updated['payload']['s3_file'])
        self.assertEquals(status.HTTP_200_OK, updated_resp.status_code)

        self.assertNotEqual(ascii(initial_resp.content), ascii(updated_resp.content))
