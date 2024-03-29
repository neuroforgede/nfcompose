# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


import io

from PIL import Image as PIL_Image  # type: ignore

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

    def test_json_internal_null_not_stripped(self) -> None:
        data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': 'my_data_series_1',
            'external_id': 'external_id1'
        }, simulate_tenant=False)

        json_fact = self.create_payload(data_series['json_facts'], payload={
            'name': 'json_fact',
            'external_id': 'json_fact',
            'optional': False
        })

        after_creation = self.create_payload(data_series['data_points'], payload={
            'external_id': '1',
            'payload': {
                json_fact['external_id']: {'abc': None}
            }
        })
        self.assertTrue('abc' in after_creation['payload'][json_fact['external_id']])
        self.assertIsNone(after_creation['payload'][json_fact['external_id']]['abc'])

        fetched_again = self.get_payload(after_creation['url'])
        self.assertTrue('abc' in fetched_again['payload'][json_fact['external_id']])
        self.assertIsNone(fetched_again['payload'][json_fact['external_id']]['abc'])
