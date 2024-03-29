# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


import io

from PIL import Image as PIL_Image  # type: ignore
from rest_framework import status
from typing import Any

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


SYMBOLS = ['`', '~', '!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '-', '+', '=', '{', '[', '}', '}', '|',
                   '\\', ':', ';', ',', "'", '<', '>', '.', '?', '/', u'\u2190', u'\u2191', u'\u00AC', '±', '§',
                   u'\u2524', u'\u2588', u'\u2302', '¾', 'É', 'Õ', 'Æ', '¥', 'Ä', 'µ', '€', '²³']


class DataSeriesWithForbiddenCharacters(BaseViewTest):
    # the list endpoint is disabled for datapoints if we do not select for a data series
    url_under_test = DATA_SERIES_BASE_URL + 'dataseries/'
    simulate_other_tenant = True

    def test_illegal_chars_dataseries(self) -> None:

        for s in SYMBOLS:
            response = self.client.post(path=DATA_SERIES_BASE_URL + 'dataseries/', data={
                'name': f'my_data_series_with_extra_keys',
                'allow_extra_fields': True,
                'external_id': f'external_id{s}'
            })
            self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

        for s in SYMBOLS:
            response = self.client.post(path=DATA_SERIES_BASE_URL + 'dataseries/', data={
                'name': f'my_data_series_with_extra_keys',
                'allow_extra_fields': True,
                'external_id': f'{s}_external_id'
            })
            self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

        for s in SYMBOLS:
            response = self.client.post(path=DATA_SERIES_BASE_URL + 'dataseries/', data={
                'name': f'my_data_series_with_extra_keys',
                'allow_extra_fields': True,
                'external_id': f'external_id_{s}_external_id'
            })
            self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)


class DataSeriesStructureElementsWithForbiddenCharacters(BaseViewTest):
    # the list endpoint is disabled for datapoints if we do not select for a data series
    url_under_test = DATA_SERIES_BASE_URL + 'dataseries/'
    simulate_other_tenant = True

    counter = 0

    def __setup_data_series(self, fact_type: str) -> Any:
        idx = self.counter
        data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': f'my_data_series_{fact_type}_{idx}',
            'external_id': f'_external_id_{fact_type}_{idx}'
        }, simulate_tenant=False)
        return data_series

    def _test_for_fact(
        self,
        fact_type: str,
        optional: bool
    ) -> None:
        data_series = self.__setup_data_series(fact_type)

        idx = self.counter

        for s in SYMBOLS:
            failed_request = self.client.post(path=data_series[f'{fact_type}_facts'], data={
                'name': f'{fact_type}_fact_{idx}_A',  # test with upper case to check if sql queries are properly escaped
                'external_id': f'{fact_type}_fact_{s}_{idx}',
                'optional': optional
            }, format='json')
            self.assertEqual(status.HTTP_400_BAD_REQUEST, failed_request.status_code)

        successful_request = self.client.post(path=data_series[f'{fact_type}_facts'], data={
            'name': f'{fact_type}_fact_{idx}_A',  # test with upper case to check if sql queries are properly escaped
            'external_id': f'{fact_type}_fact_{idx}',
            'optional': optional
        }, format='json')
        self.assertEqual(status.HTTP_201_CREATED, successful_request.status_code)

        self.counter = self.counter + 1

    def test_float_facts(self) -> None:
        for optional in [False, True]:
            self._test_for_fact('float', optional)

    def test_string_facts(self) -> None:
        for optional in [False, True]:
            self._test_for_fact('string', optional)

    def test_text_facts(self) -> None:
        for optional in [False, True]:
            self._test_for_fact('text', optional)

    def test_json_facts(self) -> None:
        for optional in [False, True]:
            self._test_for_fact('json', optional)

    def test_timestamp_facts(self) -> None:
        _1 = '2019-12-15T19:09:25.007985+00:00'  # format from postgres!
        _2 = '2019-12-15T19:09:26.007985+00:00'
        for optional in [False, True]:
            self._test_for_fact('timestamp', optional)

    def test_image_facts(self) -> None:
        for optional in [False, True]:
            self._test_for_fact('image', optional)

    def test_boolean_facts(self) -> None:
        for optional in [False, True]:
            self._test_for_fact('boolean', optional)
            
    def test_dimension(self) -> None:
        for optional in [False, True]:
            data_series = self.__setup_data_series('data_series')
            data_series_for_dim = self.__setup_data_series('data_series_2')

            idx = self.counter

            for s in SYMBOLS:
                failed_request = self.client.post(path=data_series[f'dimensions'], data={
                    'name': f'dim_A',  # test with upper case to check if sql queries are properly escaped
                    'external_id': f'dim_{s}{idx}',
                    'reference': data_series_for_dim['url'],
                    'optional': optional
                }, format='json')
                self.assertEqual(status.HTTP_400_BAD_REQUEST, failed_request.status_code)

            successful_request = self.client.post(path=data_series[f'dimensions'], data={
                'name': f'dim_A',  # test with upper case to check if sql queries are properly escaped
                'external_id': f'dim_{idx}',
                'reference': data_series_for_dim['url'],
                'optional': optional
            }, format='json')
            self.assertEqual(status.HTTP_201_CREATED, successful_request.status_code)

            self.counter = self.counter + 1
