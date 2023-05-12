# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


import io

from PIL import Image as PIL_Image  # type: ignore
from rest_framework import status
from typing import Any, Dict

from skipper import modules
from skipper.core.tests.base import BaseViewTest, BASE_URL
from skipper.settings import AWS_S3_TEST_OUTSIDE_BASE_URL, AWS_S3_ENDPOINT_URL

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


class Base(BaseViewTest):
    # the list endpoint is disabled for datapoints if we do not select for a data series
    url_under_test = DATA_SERIES_BASE_URL + 'dataseries/'
    simulate_other_tenant = True

    data_series: Dict[str, Any]

    fact_type: str

    def gen_data(self) -> Any:
        return generate_photo_file()

    def setUp(self) -> None:
        super().setUp()
        self.data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': 'my_data_series_1',
            'external_id': 'external_id1'
        }, simulate_tenant=False)

    def add_fact(self, optional: bool) -> None:
        self.create_payload(self.data_series[f'{self.fact_type}_facts'], {
            'external_id': '1',
            'optional': optional,
            'name': '1'
        })

    def test_private_public_detection_for_s3_urls(self) -> None:
        self.add_fact(optional=False)

        # just get the data in somehow (here, via batch)
        response = self.client.post(
            path=self.data_series['data_points_bulk'],
            data={
                f"batch-0.external_id": 'should_succeed',
                "batch-0.payload.1": self.gen_data()
            }, format='multipart')
        self.assertEquals(status.HTTP_201_CREATED, response.status_code)

        dp_1 = self.client.get(
            path=self.data_series['data_points'] + f'?external_id=should_succeed',
            format='json'
        ).json()['data'][0]

        # direct without a nginx proxy we should get the internal url
        self.assertTrue(AWS_S3_ENDPOINT_URL in str(dp_1['payload']['1']))

        dp_1 = self.client.get(
            path=self.data_series['data_points'] + f'?external_id=should_succeed',
            format='json',
            **{
                'HTTP_X_Nginx-Proxy': 'true'
            }  # type: ignore
        ).json()['data'][0]

        # with the nginx header we should get the outside url
        self.assertTrue(AWS_S3_TEST_OUTSIDE_BASE_URL in str(dp_1['payload']['1']))


class Image(Base):
    fact_type = 'image'


del Base
