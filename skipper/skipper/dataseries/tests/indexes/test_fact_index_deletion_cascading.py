# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from rest_framework import status
from skipper import modules
from skipper.core.tests.base import BaseViewTest, BASE_URL
from skipper.dataseries.storage.contract import FactType, IndexableDataSeriesChildType


DATA_SERIES_BASE_URL = BASE_URL + modules.url_representation(modules.Module.DATA_SERIES) + '/'


class DimensionIndexFactCascadeRejectionTest(BaseViewTest):

    def test_dimension_cascade_deletion_rejection(self) -> None:
        data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': 'my_data_series',
            'external_id': 'external_id'
        }, simulate_tenant=False)

        data_series_2 = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': 'my_data_series_2',
            'external_id': 'external_id2'
        }, simulate_tenant=False)

        dimension = self.create_payload(data_series['dimensions'], payload={
            "external_id": "dimension",
            "name": "dimension",
            "reference": data_series_2['url'],
            "optional": False
        })

        self.create_payload(data_series['indexes'],  payload={
            'external_id': 'idx',
            'name': 'idx',
            "targets": [
                {
                    "target_id": dimension['id'],
                    "target_type": IndexableDataSeriesChildType.DIMENSION.value
                }
            ]
        })

        response = self._client().delete(path=dimension['url'], format='json')
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)


class BaseIndexFactCascadeRejectionTest(BaseViewTest):

    _fact_name: str
    _fact_type: FactType

    def test_fact_cascade_deletion_rejection(self) -> None:
        data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': 'my_data_series_2',
            'external_id': 'external_id2'
        }, simulate_tenant=False)

        target_parent_url: str = data_series[self._fact_name]

        fact = self.create_payload(target_parent_url, payload={
            'external_id': 'fact',
            'name': 'fact',
            'optional': False
        })

        self.create_payload(data_series['indexes'],  payload={
            'external_id': 'idx',
            'name': 'idx',
            "targets": [
                {
                    "target_id": fact['id'],
                    "target_type": self._fact_type.value
                }
            ]
        })

        response = self._client().delete(path=fact['url'], format='json')
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)


class FloatIndexFactCascadeRejectionTest(BaseIndexFactCascadeRejectionTest):
    _fact_name = 'float_facts'
    _fact_type = FactType.Float


class StringIndexFactCascadeRejectionTest(BaseIndexFactCascadeRejectionTest):
    _fact_name = 'string_facts'
    _fact_type = FactType.String


class TextIndexFactCascadeRejectionTest(BaseIndexFactCascadeRejectionTest):
    _fact_name = 'text_facts'
    _fact_type = FactType.Text


class TimestampIndexFactCascadeRejectionTest(BaseIndexFactCascadeRejectionTest):
    _fact_name = 'timestamp_facts'
    _fact_type = FactType.Timestamp


class ImageIndexFactCascadeRejectionTest(BaseIndexFactCascadeRejectionTest):
    _fact_name = 'image_facts'
    _fact_type = FactType.Image


class FileIndexFactCascadeRejectionTest(BaseIndexFactCascadeRejectionTest):
    _fact_name = 'file_facts'
    _fact_type = FactType.File


class JsonIndexFactCascadeRejectionTest(BaseIndexFactCascadeRejectionTest):
    _fact_name = 'json_facts'
    _fact_type = FactType.JSON


class BooleantIndexFactCascadeRejectionTest(BaseIndexFactCascadeRejectionTest):
    _fact_name = 'boolean_facts'
    _fact_type = FactType.Boolean


del BaseIndexFactCascadeRejectionTest
