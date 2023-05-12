# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


import io

import json
from PIL import Image as PIL_Image  # type: ignore
from rest_framework import status
from typing import Any, Dict

from skipper import modules
from skipper.core.tests.base import BaseViewTest, BASE_URL
from skipper.dataseries.storage.contract import StorageBackendType
from skipper.settings import AWS_S3_ENDPOINT_URL

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

    fact_type: str

    def gen_data(self) -> Any:
        raise NotImplementedError()

    def check_data(self, value: Any) -> Any:
        raise NotImplementedError()

    def add_fact(self, data_series: Dict[str, Any], optional: bool) -> None:
        self.create_payload(data_series[f'{self.fact_type}_facts'], {
            'external_id': '1',
            'optional': optional,
            'name': '1'
        })

    def _test_multipart_batch(self, idx: int, backend: str) -> None:

        data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': f'my_data_series_{idx}',
            'external_id': f'external_id{idx}',
            'backend': backend
        }, simulate_tenant=False)

        self.add_fact(data_series=data_series, optional=False)

        response = self.client.post(
            path=data_series['data_points_bulk'],
            data={
                f"batch-0.external_id": 'should_succeed',
                "batch-0.payload.1": self.gen_data(),
                "async": self._async
            }, format='multipart')
        self.assertEquals(status.HTTP_201_CREATED, response.status_code)

        dp_1 = self.get_payload(data_series['data_points'] + f'?external_id=should_succeed')['data'][0]
        self.assertTrue(
            '1' in dp_1['payload'],
            "fact should be in the second datapoint"
        )
        self.assertIsNotNone(
            dp_1['payload']['1'],
            "fact in second datapoint should not be null"
        )

        self.check_data(dp_1['payload']['1'])

    def test_multipart_batch(self) -> None:
        idx = 0
        for backend_key, backend_value in StorageBackendType.choices():
            self._test_multipart_batch(idx, backend_value)
            idx += 1


class FloatTest(Base):
    fact_type: str = 'float'
    _async: bool = False

    def gen_data(self) -> float:
        return 1.0

    def check_data(self, value: Any) -> None:
        self.assertEquals(1.0, value)


class AsyncFloatTest(FloatTest):
    _async: bool = True


class StringTest(Base):
    fact_type: str = 'string'
    _async: bool = False

    def gen_data(self) -> str:
        return "123"

    def check_data(self, value: Any) -> None:
        self.assertEquals('123', value)


class AsyncStringTest(StringTest):
    _async: bool = True


class TextTest(Base):
    fact_type: str = 'text'
    _async: bool = False

    def gen_data(self) -> str:
        return "123"

    def check_data(self, value: Any) -> None:
        self.assertEquals('123', value)


class AsyncTextTest(TextTest):
    _async: bool = True


class JSONTest(Base):
    fact_type: str = 'json'
    _async: bool = False

    def gen_data(self) -> str:
        return "\"\\\"\\\"\""

    def check_data(self, value: Any) -> None:
        self.assertEquals('\"\"', value)

    def gen_null(self) -> Any:
        return 'null'

    def _test_multipart_null_batch(self, idx: int, backend: str) -> None:
        data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': f'my_data_series_{idx}',
            'external_id': f'external_id{idx}',
            'backend': backend
        }, simulate_tenant=False)

        self.add_fact(data_series=data_series, optional=True)

        response = self.client.post(
            path=data_series['data_points_bulk'],
            data={
                f"batch-0.external_id": 'should_succeed',
                "batch-0.payload.1": self.gen_null(),
                "async": self._async
            }, format='multipart')
        self.assertEquals(status.HTTP_201_CREATED, response.status_code)

        dp_1 = self.get_payload(data_series['data_points'] + f'?external_id=should_succeed')['data'][0]
        self.assertTrue(
            '1' not in dp_1['payload'],
            "fact should not be in the datapoint"
        )

    def test_multipart_null_batch(self) -> None:
        idx = 0
        for backend_key, backend_value in StorageBackendType.choices():
            self._test_multipart_null_batch(idx, backend_value)
            idx += 1


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
        return json.dumps(self.data)

    def check_data(self, value: Any) -> None:
        self.assertEquals(self.data, value)


class AsyncJSONComplexTest(JSONComplexTest):
    _async: bool = True


class TimestampTest(Base):
    fact_type: str = 'timestamp'
    _async: bool = False

    def gen_data(self) -> str:
        return '2019-12-15T19:09:25.007985'

    def check_data(self, value: Any) -> None:
        self.assertEquals('2019-12-15T19:09:25.007985', value)


class AsyncTimestampTest(TimestampTest):
    _async: bool = True


class ImageTest(Base):
    fact_type = 'image'
    _async: bool = False

    def gen_data(self) -> Any:
        return generate_photo_file()

    def check_data(self, value: Any) -> None:
        self.assertTrue(AWS_S3_ENDPOINT_URL in str(value))

    def _test_multipart_batch_two(self, idx: int, backend: str) -> None:
        data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': f'my_data_series_{idx}',
            'external_id': f'external_id{idx}',
            'backend': backend
        }, simulate_tenant=False)

        self.add_fact(data_series=data_series, optional=True)

        response = self.client.post(
            path=data_series['data_points_bulk'],
            data={
                f"batch-0.external_id": 'should_succeed',
                f"batch-1.external_id": 'should_succeed2',
                "batch-1.payload.1": self.gen_data(),
                "async": self._async
            }, format='multipart')
        self.assertEquals(status.HTTP_201_CREATED, response.status_code)

        dp_1 = self.get_payload(data_series['data_points'] + f'?external_id=should_succeed')['data'][0]
        self.assertTrue(
            '1' not in dp_1['payload'],
            "fact should not be in the first datapoint if it was left out in batch"
        )

        dp_2 = self.get_payload(data_series['data_points'] + f'?external_id=should_succeed2')['data'][0]
        self.assertTrue(
            '1' in dp_2['payload'],
            "fact should be in the second datapoint"
        )
        self.assertIsNotNone(
            dp_2['payload']['1'],
            "fact in second datapoint should not be null"
        )

    def test_multipart_batch_two(self) -> None:
        idx = 0
        for backend_key, backend_value in StorageBackendType.choices():
            self._test_multipart_batch_two(idx, backend_value)
            idx += 1


class AsyncImageTest(ImageTest):
    _async: bool = True


class BooleanTest(Base):
    fact_type: str = 'boolean'
    _async: bool = False

    def gen_data(self) -> bool:
        return True

    def check_data(self, value: Any) -> None:
        self.assertEquals(True, value)


class AsyncBooleanTest(BooleanTest):
    _async: bool = True

# FIXME: add dimension


del Base

