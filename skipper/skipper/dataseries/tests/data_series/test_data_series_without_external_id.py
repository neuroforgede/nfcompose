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


class DataSeriesWithoutExternalIDTest(BaseViewTest):
    # the list endpoint is disabled for datapoints if we do not select for a data series
    url_under_test = DATA_SERIES_BASE_URL + 'dataseries/'
    simulate_other_tenant = True

    def test_should_fail(self) -> None:
        response = self.client.post(path=DATA_SERIES_BASE_URL + 'dataseries/', data={
            'name': f'my_data_series_with_extra_keys',
            'allow_extra_fields': True
        })

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)


