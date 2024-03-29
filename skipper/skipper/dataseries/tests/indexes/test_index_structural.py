# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


from typing import Any, List, Union

from rest_framework import status
from skipper import modules
from skipper.core.tests.base import BaseViewTest, BASE_URL
from skipper.dataseries.storage.contract import IndexableDataSeriesChildType


DATA_SERIES_BASE_URL = BASE_URL + modules.url_representation(modules.Module.DATA_SERIES) + '/'


def _helper_corrupt_id(id: str) -> str:
    id_list: List[str] = list(id)
    if id_list[0] == '0':
        id_list[0] = '1'
    else:
        id_list[0] = '0'
    return ''.join(id_list)


def _helper_corrupt_type(type: str) -> str:
    if type == IndexableDataSeriesChildType.FLOAT_FACT.value:
        return IndexableDataSeriesChildType.STRING_FACT.value
    else:
        return IndexableDataSeriesChildType.FLOAT_FACT.value


class IndexBaseTest(BaseViewTest):

    _ds: Any
    _dim_ds: Any

    _float_fact: Any
    _string_fact: Any
    _text_fact: Any
    _timestamp_fact: Any
    _image_fact: Any
    _file_fact: Any
    _json_fact: Any
    _boolean_fact: Any
    _dimension: Any

    def setUp(self) -> None:
        super().setUp()
        self._ds = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': 'my_data_series_2',
            'external_id': 'external_id2'
        }, simulate_tenant=False)
        self._float_fact = self.create_payload(self._ds['float_facts'], payload={
            "external_id": "float_fact",
            "name": "float_fact",
            "optional": False
        })
        self._string_fact = self.create_payload(self._ds['string_facts'], payload={
            "external_id": "string_fact",
            "name": "string_fact",
            "optional": False
        })
        self._text_fact = self.create_payload(self._ds['text_facts'], payload={
            "external_id": "text_fact",
            "name": "text_fact",
            "optional": False
        })
        self._timestamp_fact = self.create_payload(self._ds['timestamp_facts'], payload={
            "external_id": "timestamp_fact",
            "name": "timestamp_fact",
            "optional": False
        })
        self._image_fact = self.create_payload(self._ds['image_facts'], payload={
            "external_id": "image_fact",
            "name": "image_fact",
            "optional": False
        })
        self._file_fact = self.create_payload(self._ds['file_facts'], payload={
            "external_id": "file_fact",
            "name": "file_fact",
            "optional": False
        })
        self._json_fact = self.create_payload(self._ds['json_facts'], payload={
            "external_id": "json_fact",
            "name": "json_fact",
            "optional": False
        })
        self._boolean_fact = self.create_payload(self._ds['boolean_facts'], payload={
            "external_id": "boolean_fact",
            "name": "boolean_fact",
            "optional": False
        })
        self._dim_ds = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': 'my_data_series_3',
            'external_id': 'external_id_3'
        }, simulate_tenant=False)
        self._dimension = self.create_payload(self._ds['dimensions'], payload={
            "external_id": "dimension",
            "name": "dimension",
            "reference": self._dim_ds['url'],
            "optional": False
        })

    def _do_test(self, payload: Any) -> None:
        raise NotImplementedError()

    def _index_payload(self, target_id: str, target_type: str) -> Any:
        raise NotImplementedError()

    def test_float(self) -> None:
        self._do_test(self._index_payload(
            target_id=self._float_fact['id'],
            target_type=IndexableDataSeriesChildType.FLOAT_FACT.value
        ))

    def test_string(self) -> None:
        self._do_test(self._index_payload(
            target_id=self._string_fact['id'],
            target_type=IndexableDataSeriesChildType.STRING_FACT.value
        ))

    def test_timestamp(self) -> None:
        self._do_test(self._index_payload(
            target_id=self._timestamp_fact['id'],
            target_type=IndexableDataSeriesChildType.TIMESTAMP_FACT.value
        ))

    def test_text(self) -> None:
        self._do_test(self._index_payload(
            target_id=self._text_fact['id'],
            target_type=IndexableDataSeriesChildType.TEXT_FACT.value
        ))

    def test_image(self) -> None:
        self._do_test(self._index_payload(
            target_id=self._image_fact['id'],
            target_type=IndexableDataSeriesChildType.IMAGE_FACT.value
        ))

    def test_file(self) -> None:
        self._do_test(self._index_payload(
            target_id=self._file_fact['id'],
            target_type=IndexableDataSeriesChildType.FILE_FACT.value
        ))

    def test_json(self) -> None:
        self._do_test(self._index_payload(
            target_id=self._json_fact['id'],
            target_type=IndexableDataSeriesChildType.JSON_FACT.value
        ))

    def test_boolean(self) -> None:
        self._do_test(self._index_payload(
            target_id=self._boolean_fact['id'],
            target_type=IndexableDataSeriesChildType.BOOLEAN_FACT.value
        ))

    def test_dimension(self) -> None:
        self._do_test(self._index_payload(
            target_id=self._dimension['id'],
            target_type=IndexableDataSeriesChildType.DIMENSION.value
        ))


class IndexCREATEBaseTest(IndexBaseTest):
    _expected_error: Union[int, None] = None
    _wrong_id: bool = False
    _wrong_type: bool = False
    _wrong_parent: bool = False

    def _index_payload(self, target_id: str, target_type: str) -> Any:
        if self._wrong_id:
            target_id = _helper_corrupt_id(target_id)
        if self._wrong_type:
            target_type = _helper_corrupt_type(target_type)
        index_name = target_id + '_INDEX'

        return {
            'name': index_name,
            'external_id': index_name.replace('-', '_') + '_ID',
            'targets': [{
                'target_id': target_id,
                'target_type': target_type
            }]
        }

    def _do_test(self, payload: Any) -> None:
        target: str
        if not self._wrong_parent:
            target = self._ds['indexes']
        else:
            target = self._dim_ds['indexes']

        if self._expected_error:
            resp = self.client.post(
                path=target,
                format='json',
                data=payload
            )
            self.assertEqual(resp.status_code, self._expected_error)
        else:
            self.create_payload(target, payload=payload)


class IndexCREATEValidTest(IndexCREATEBaseTest):
    pass


class IndexCREATEInvalidIDTest(IndexCREATEBaseTest):
    _expected_error = status.HTTP_400_BAD_REQUEST
    _wrong_id = True


class IndexCREATEWrongTargetParentTest(IndexCREATEBaseTest):
    _expected_error = status.HTTP_400_BAD_REQUEST
    _wrong_parent = True


class IndexCREATEInvalidTypeTest(IndexCREATEBaseTest):
    _expected_error = status.HTTP_400_BAD_REQUEST
    _wrong_type = True


del IndexCREATEBaseTest
del IndexBaseTest
