# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


from enum import Enum
from typing import Any, Tuple

from skipper import modules
from skipper.core.tests.base import BaseViewTest, BASE_URL
from skipper.dataseries.storage.contract import IndexableDataSeriesChildType


DATA_SERIES_BASE_URL = BASE_URL + modules.url_representation(modules.Module.DATA_SERIES) + '/'


class ExecutionMode(Enum):
    ID = 'id'
    EXTERNAL_ID = 'e_id'
    BOTH_IDS = 'both'


class IndexTargetBaseTest(BaseViewTest):

    mode: ExecutionMode
    _ds: Any

    def setUp(self) -> None:
        super().setUp()
        self._ds = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': 'my_data_series_2',
            'external_id': 'external_id2'
        }, simulate_tenant=False)

    def _do_test(self, url: str, payload: Any) -> None:
        raise NotImplementedError()

    def _index_payload(self, target_id: str, target_external_id: str, target_type: str) -> Tuple[str, Any]:
        raise NotImplementedError()

    def test_float(self) -> None:
        _float_fact = self.create_payload(self._ds['float_facts'], payload={
            "external_id": "float_fact",
            "name": "float_fact",
            "optional": False
        })
        url, payload = self._index_payload(
            target_id=_float_fact['id'],
            target_external_id=_float_fact['external_id'],
            target_type=IndexableDataSeriesChildType.FLOAT_FACT.value
        )
        self._do_test(url, payload)

    def test_string(self) -> None:
        _string_fact = self.create_payload(self._ds['string_facts'], payload={
            "external_id": "string_fact",
            "name": "string_fact",
            "optional": False
        })
        url, payload = self._index_payload(
            target_id=_string_fact['id'],
            target_external_id=_string_fact['external_id'],
            target_type=IndexableDataSeriesChildType.STRING_FACT.value
        )
        self._do_test(url, payload)

    def test_timestamp(self) -> None:
        _timestamp_fact = self.create_payload(self._ds['timestamp_facts'], payload={
            "external_id": "timestamp_fact",
            "name": "timestamp_fact",
            "optional": False
        })
        url, payload = self._index_payload(
            target_id=_timestamp_fact['id'],
            target_external_id=_timestamp_fact['external_id'],
            target_type=IndexableDataSeriesChildType.TIMESTAMP_FACT.value
        )
        self._do_test(url, payload)

    def test_text(self) -> None:
        _text_fact = self.create_payload(self._ds['text_facts'], payload={
            "external_id": "text_fact",
            "name": "text_fact",
            "optional": False
        })
        url, payload = self._index_payload(
            target_id=_text_fact['id'],
            target_external_id=_text_fact['external_id'],
            target_type=IndexableDataSeriesChildType.TEXT_FACT.value
        )
        self._do_test(url, payload)

    def test_image(self) -> None:
        _image_fact = self.create_payload(self._ds['image_facts'], payload={
            "external_id": "image_fact",
            "name": "image_fact",
            "optional": False
        })
        url, payload = self._index_payload(
            target_id=_image_fact['id'],
            target_external_id=_image_fact['external_id'],
            target_type=IndexableDataSeriesChildType.IMAGE_FACT.value
        )
        self._do_test(url, payload)

    def test_file(self) -> None:
        _file_fact = self.create_payload(self._ds['file_facts'], payload={
            "external_id": "file_fact",
            "name": "file_fact",
            "optional": False
        })
        url, payload = self._index_payload(
            target_id=_file_fact['id'],
            target_external_id=_file_fact['external_id'],
            target_type=IndexableDataSeriesChildType.FILE_FACT.value
        )
        self._do_test(url, payload)

    def test_json(self) -> None:
        _json_fact = self.create_payload(self._ds['json_facts'], payload={
            "external_id": "json_fact",
            "name": "json_fact",
            "optional": False
        })
        url, payload = self._index_payload(
            target_id=_json_fact['id'],
            target_external_id=_json_fact['external_id'],
            target_type=IndexableDataSeriesChildType.JSON_FACT.value
        )
        self._do_test(url, payload)

    def test_boolean(self) -> None:
        _boolean_fact = self.create_payload(self._ds['boolean_facts'], payload={
            "external_id": "boolean_fact",
            "name": "boolean_fact",
            "optional": False
        })
        url, payload = self._index_payload(
            target_id=_boolean_fact['id'],
            target_external_id=_boolean_fact['external_id'],
            target_type=IndexableDataSeriesChildType.BOOLEAN_FACT.value
        )
        self._do_test(url, payload)

    def test_dimension(self) -> None:
        _dim_ds = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': 'my_data_series_3',
            'external_id': 'external_id_3'
        }, simulate_tenant=False)
        _dimension = self.create_payload(self._ds['dimensions'], payload={
            "external_id": "dimension",
            "name": "dimension",
            "reference": _dim_ds['url'],
            "optional": False
        })
        url, payload = self._index_payload(
            target_id=_dimension['id'],
            target_external_id=_dimension['external_id'],
            target_type=IndexableDataSeriesChildType.DIMENSION.value
        )
        self._do_test(url, payload)


class IndexTargetCREATEBaseTest(IndexTargetBaseTest):

    def _index_payload(self, target_id: str, target_external_id: str, target_type: str) -> Tuple[str, Any]:

        index_name = target_id.replace('-', '_') + '_INDEX'

        target = {'target_type': target_type}
        if self.mode in (ExecutionMode.BOTH_IDS, ExecutionMode.ID):
            target['target_id'] = target_id
        if self.mode in (ExecutionMode.BOTH_IDS, ExecutionMode.EXTERNAL_ID):
            target['target_external_id'] = target_external_id

        return ('', {
            'name': index_name,
            'external_id': index_name + '_ID',
            'targets': [target]
        })

    def _do_test(self, url: str, payload: Any) -> None:
        self.create_payload(url=self._ds['indexes'], payload=payload)


class IndexTargetCREATEExtIDTest(IndexTargetCREATEBaseTest):
    mode = ExecutionMode.EXTERNAL_ID


class IndexTargetCREATEIDTest(IndexTargetCREATEBaseTest):
    mode = ExecutionMode.ID


class IndexTargetCREATEFullTest(IndexTargetCREATEBaseTest):
    mode = ExecutionMode.BOTH_IDS


class IndexTargetUPDATEBaseTest(IndexTargetBaseTest):

    def _index_payload(self, target_id: str, target_external_id: str, target_type: str) -> Tuple[str, Any]:
        index_name = target_id.replace('-', '_') + '_INDEX'
        index_old_json = self.create_payload(
            url=self._ds['indexes'],
            payload={
                'name': index_name,
                'external_id': index_name + '_ID',
                'targets': [{
                    'target_type': target_type,
                    'target_id': target_id,
                    'target_external_id': target_external_id
                }]
            }
        )

        target = {'target_type': target_type}
        if self.mode in (ExecutionMode.BOTH_IDS, ExecutionMode.ID):
            target['target_id'] = target_id
        if self.mode in (ExecutionMode.BOTH_IDS, ExecutionMode.EXTERNAL_ID):
            target['target_external_id'] = target_external_id

        index_old_json['targets'] = [target]
        return (index_old_json['url'], index_old_json)

    def _do_test(self, url: str, payload: Any) -> None:
        self.update_payload(url=url, payload=payload)


class IndexTargetUPDATEExtIDTest(IndexTargetUPDATEBaseTest):
    mode = ExecutionMode.EXTERNAL_ID


class IndexTargetUPDATEIDTest(IndexTargetUPDATEBaseTest):
    mode = ExecutionMode.ID


class IndexTargetUPDATEFullTest(IndexTargetUPDATEBaseTest):
    mode = ExecutionMode.BOTH_IDS


class IndexTargetPATCHBaseTest(IndexTargetBaseTest):

    def _index_payload(self, target_id: str, target_external_id: str, target_type: str) -> Tuple[str, Any]:
        index_name = target_id.replace('-', '_') + '_INDEX'
        index_old_json = self.create_payload(
            url=self._ds['indexes'],
            payload={
                'name': index_name,
                'external_id': index_name + '_ID',
                'targets': [{
                    'target_type': target_type,
                    'target_id': target_id,
                    'target_external_id': target_external_id
                }]
            }
        )

        target = {'target_type': target_type}
        if self.mode in (ExecutionMode.BOTH_IDS, ExecutionMode.ID):
            target['target_id'] = target_id
        if self.mode in (ExecutionMode.BOTH_IDS, ExecutionMode.EXTERNAL_ID):
            target['target_external_id'] = target_external_id

        return (index_old_json['url'], {'targets': [target]})

    def _do_test(self, url: str, payload: Any) -> None:
        self.patch_payload(url=url, payload=payload)


class IndexTargetPATCHExtIDTest(IndexTargetPATCHBaseTest):
    mode = ExecutionMode.EXTERNAL_ID


class IndexTargetPATCHIDTest(IndexTargetPATCHBaseTest):
    mode = ExecutionMode.ID


class IndexTargetPATCHFullTest(IndexTargetPATCHBaseTest):
    mode = ExecutionMode.BOTH_IDS


del IndexTargetCREATEBaseTest
del IndexTargetUPDATEBaseTest
del IndexTargetPATCHBaseTest
del IndexTargetBaseTest
