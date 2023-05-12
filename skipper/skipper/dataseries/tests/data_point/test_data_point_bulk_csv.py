# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


import io

import json

import csv
from PIL import Image as PIL_Image  # type: ignore
from rest_framework import status
from typing import Any, Dict

from skipper import modules
from skipper.core.tests.base import BaseViewTest, BASE_URL
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


class Base(BaseViewTest):
    # the list endpoint is disabled for datapoints if we do not select for a data series
    url_under_test = DATA_SERIES_BASE_URL + 'dataseries/'
    simulate_other_tenant = True

    _async: bool

    should_fail: bool = False
    optional_fact: bool = False

    fact_type: str

    def gen_data(self) -> Any:
        raise NotImplementedError()

    def actual_data(self) -> Any:
        return self.gen_data()

    def add_fact(self, data_series: Dict[str, Any], optional: bool) -> None:
        self.create_payload(data_series[f'{self.fact_type}_facts'], {
            'external_id': '1',
            'optional': optional,
            'name': '1'
        })

    def _test_csv_batch(self, idx: int, backend: str) -> None:

        data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': f'my_data_series_{idx}',
            'external_id': f'external_id{idx}',
            'backend': backend
        }, simulate_tenant=False)

        self.add_fact(data_series=data_series, optional=self.optional_fact)

        idx = 0
        for csv_encoding, separator in [('text/csv-json-formencode', ','), ('text/csv-semicolon-json-formencode', ';')]:
            idx = idx + 1
            response = self.client.post(
                path=data_series['data_points_bulk'],
                data=f"""external_id{separator}payload.1
                should_succeed{idx}{separator}{self.gen_data()}""",
                content_type=csv_encoding,
                HTTP_X_BULK_DATA_POINT_ASYNC=json.dumps(self._async)
            )

            if self.should_fail:
                self.assertEquals(status.HTTP_400_BAD_REQUEST, response.status_code)
            else:
                self.assertEquals(status.HTTP_201_CREATED, response.status_code)

                dp_1 = self.get_payload(data_series['data_points'] + f'?external_id=should_succeed{idx}')['data'][0]
                self.assertTrue(
                    '1' in dp_1['payload'],
                    "fact should be in the second datapoint"
                )
                self.assertIsNotNone(
                    dp_1['payload']['1'],
                    "fact in second datapoint should not be null"
                )
                self.assertEquals(dp_1['payload']['1'], self.actual_data())

    def test_csv_batch(self) -> None:
        idx = 0
        for backend_key, backend_value in StorageBackendType.choices():
            self._test_csv_batch(idx, backend_value)
            idx += 1


class FloatTest(Base):
    fact_type: str = 'float'
    _async: bool = False

    def gen_data(self) -> float:
        return 1.0


class AsyncFloatTest(FloatTest):
    _async: bool = True


class StringTest(Base):
    fact_type: str = 'string'
    _async: bool = False

    def gen_data(self) -> str:
        return "123"


class AsyncStringTest(StringTest):
    _async: bool = True


class MultiLineStringTest(Base):
    fact_type: str = 'string'
    _async: bool = False

    def actual_data(self) -> str:
        return "123\n\n\nSOMETEXT"

    def gen_data(self) -> str:
        return "\"123\n\n\nSOMETEXT\""


class AsyncMultiLineStringTest(MultiLineStringTest):
    _async: bool = True


class TextTest(Base):
    fact_type: str = 'text'
    _async: bool = False

    def gen_data(self) -> str:
        return "123"


class AsyncTextTest(TextTest):
    _async: bool = True


class JSONTest(Base):
    fact_type: str = 'json'
    _async: bool = False

    def actual_data(self) -> str:
        return '""'

    def gen_data(self) -> str:
        return '""""""'


class AsyncJSONTest(JSONTest):
    _async: bool = True


class JSONComplexTest(Base):
    fact_type: str = 'json'
    _async: bool = False

    data = {
        'toast': True,
        'hello': [""]
    }

    def gen_data(self) -> str:
        data = json.dumps(self.data)
        mangled = data.replace('"', '""')
        return f'"{mangled}"'

    # for now, csv files upload does not support actual nested json files
    # inside columns. nested json values are defined by the csv header instead
    def actual_data(self) -> Any:
        return json.dumps(self.data)


class AsyncJSONComplexTest(JSONComplexTest):
    _async: bool = True


class TimestampTest(Base):
    fact_type: str = 'timestamp'
    _async: bool = False

    def gen_data(self) -> str:
        return '2019-12-15T19:09:25.007985'


class AsyncTimestampTest(TimestampTest):
    _async: bool = True


class ImageTest(Base):
    fact_type = 'image'

    _async: bool = False

    should_fail = True

    def gen_data(self) -> Any:
        return generate_photo_file()


class AsyncImageTest(ImageTest):
    _async: bool = True


class ImageOptionalTest(Base):
    fact_type = 'image'

    _async: bool = False

    should_fail = True
    optional_fact = True

    def gen_data(self) -> Any:
        # should fail even if we dont send a file
        return ""


class AsyncImageOptionalTest(ImageOptionalTest):
    _async: bool = True


class ImageOptionalNoneTest(Base):
    fact_type = 'image'

    _async: bool = False

    should_fail = True
    optional_fact = True

    def gen_data(self) -> Any:
        # should fail even if we dont send null
        return None


class AsyncImageOptionalNoneTest(ImageOptionalNoneTest):
    _async: bool = True


class ImageOptionalNoneAsStringTest(Base):
    fact_type = 'image'

    _async: bool = False

    should_fail = True
    optional_fact = True

    def gen_data(self) -> Any:
        # should fail even if we dont send null
        return "null"


class AsyncImageOptionalNoneAsStringTest(ImageOptionalNoneAsStringTest):
    _async: bool = True


# FIXME: add dimension tests


del Base

