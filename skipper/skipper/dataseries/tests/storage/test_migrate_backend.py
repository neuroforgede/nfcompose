# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


import io
from time import sleep

from PIL import Image as PIL_Image  # type: ignore
from rest_framework import status
from typing import Any, Dict, List, NamedTuple

from skipper import modules
from skipper.core.tests.base import BaseViewTest, BASE_URL
from skipper.dataseries.storage.contract import StorageBackendType
from urllib.parse import urljoin, urlparse

DATA_SERIES_BASE_URL = BASE_URL + modules.url_representation(modules.Module.DATA_SERIES) + '/'


def url_without_query(url: str) -> str:
    return urljoin(url, urlparse(url).path)


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


def to_payload_data(val: Dict[str, Any]) -> Dict[str, Any]:
    ret_val: Dict[str, Any] = {
        "external_id": val['external_id'],
        "payload": {}
    }
    for key, value in val.items():
        if 'payload' in key:
            _actual_value = value
            if 'json' in key:
                _actual_value = _actual_value.replace('"', '')
            ret_val['payload'][key.split('.')[1]] = _actual_value
    return ret_val


class Fixtures(NamedTuple):
    data_series: Dict[str, Any]

    float_fact_required: Dict[str, Any]
    float_fact_optional: Dict[str, Any]

    boolean_fact_required: Dict[str, Any]
    boolean_fact_optional: Dict[str, Any]

    string_fact_required: Dict[str, Any]
    string_fact_optional: Dict[str, Any]

    text_fact_required: Dict[str, Any]
    text_fact_optional: Dict[str, Any]

    file_fact_required: Dict[str, Any]
    file_fact_optional: Dict[str, Any]

    json_fact_required: Dict[str, Any]
    json_fact_optional: Dict[str, Any]

    timestamp_fact_required: Dict[str, Any]
    timestamp_fact_optional: Dict[str, Any]

    image_fact_required: Dict[str, Any]
    image_fact_optional: Dict[str, Any]

    dim_required: Dict[str, Any]
    values_dim_required: List[Dict[str, Any]]

    dim_optional: Dict[str, Any]
    values_dim_optional: List[Dict[str, Any]]


class BaseMigrationTest(BaseViewTest):
    # the list endpoint is disabled for datapoints if we do not select for a data series
    url_under_test = DATA_SERIES_BASE_URL + 'dataseries/'
    simulate_other_tenant = True

    initial_backend: StorageBackendType
    migrate_to_backend: StorageBackendType

    counter = 0

    def __setup_fixtures(self) -> Fixtures:
        data_series = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': f'my_data_series',
            'external_id': f'_external_id',
            'backend': self.initial_backend.value
        }, simulate_tenant=False)

        def add_data_point_for_dim(data_series_for_dim: Dict[str, Any]) -> Any:
            idx = self.counter
            dp = self.create_payload(
                url=data_series_for_dim['data_points'],
                payload={
                    'external_id': f'dp_{idx}',
                    'payload': {}
                }
            )
            self.counter = self.counter + 1
            return dp

        def create_fact(fact_type: str, optional: bool) -> Dict[str, Any]:
            idx = self.counter
            fact: Dict[str, Any] = self.create_payload(data_series[f'{fact_type}_facts'], payload={
                'name': f'{fact_type}_fact_{idx}_A',
                'external_id': f'{fact_type}_fact_{idx}_B',
                'optional': optional
            })
            self.counter = self.counter + 1
            return fact

        def create_dim(referenced_data_series: Dict[str, Any], optional: bool) -> Dict[str, Any]:
            idx = self.counter
            dim: Dict[str, Any] = self.create_payload(data_series[f'dimensions'], payload={
                'name': f'dim_{idx}_A',
                'external_id': f'dim_{idx}_B',
                'reference': referenced_data_series['url'],
                'optional': optional
            })
            self.counter = self.counter + 1
            return dim

        data_series_for_required_dim = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': f'ds_dim_1',
            'external_id': f'_external_id_1',
            'backend': self.initial_backend.value
        }, simulate_tenant=False)
        values_dim_required = [add_data_point_for_dim(data_series_for_required_dim),
                               add_data_point_for_dim(data_series_for_required_dim)]

        data_series_for_optional_dim = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': f'ds_dim_2',
            'external_id': f'_external_id_2',
            'backend': self.migrate_to_backend.value
        }, simulate_tenant=False)
        values_dim_optional = [add_data_point_for_dim(data_series_for_optional_dim),
                               add_data_point_for_dim(data_series_for_optional_dim)]

        dim_required = create_dim(data_series_for_required_dim, False)
        dim_optional = create_dim(data_series_for_optional_dim, True)

        return Fixtures(
            data_series=data_series,
            float_fact_required=create_fact('float', False),
            float_fact_optional=create_fact('float', True),
            boolean_fact_required=create_fact('boolean', False),
            boolean_fact_optional=create_fact('boolean', True),
            string_fact_required=create_fact('string', False),
            string_fact_optional=create_fact('string', True),
            text_fact_required=create_fact('text', False),
            text_fact_optional=create_fact('text', True),
            file_fact_required=create_fact('file', False),
            file_fact_optional=create_fact('file', True),
            json_fact_required=create_fact('json', False),
            json_fact_optional=create_fact('json', True),
            timestamp_fact_required=create_fact('timestamp', False),
            timestamp_fact_optional=create_fact('timestamp', True),
            image_fact_required=create_fact('image', False),
            image_fact_optional=create_fact('image', True),
            dim_required=dim_required,
            dim_optional=dim_optional,
            values_dim_optional=values_dim_optional,
            values_dim_required=values_dim_required
        )

    def _ensure_unlocked(self, data_series: Dict[str, Any]) -> Dict[str, Any]:
        # busy wait for the data_series unlocked again
        # this might not be required because of the way we handle
        # celery tasks during unit testing, but it does not hurt either
        max_wait = 100
        while max_wait > 0 and data_series['locked']:
            data_series = self.get_payload(data_series['url'])
            sleep(0.1)
            max_wait -= 1

        if max_wait == 0:
            self.fail('data_series was not unlocked after 100 tries. materialization seems broken')

        return data_series

    def initial_payloads(self, fixtures: Fixtures) -> List[Dict[str, Any]]:
        first = {
            'external_id': 'some',
            f'payload.{fixtures.float_fact_required["external_id"]}': 1.337,
            f'payload.{fixtures.boolean_fact_required["external_id"]}': True,
            f'payload.{fixtures.string_fact_required["external_id"]}': 'MY_STRING_1',
            f'payload.{fixtures.text_fact_required["external_id"]}': 'MY_TEXT_1',
            f'payload.{fixtures.file_fact_required["external_id"]}': generate_photo_file(),
            f'payload.{fixtures.json_fact_required["external_id"]}': '"MY_JSON"',
            f'payload.{fixtures.timestamp_fact_required["external_id"]}': '2019-12-15T19:09:25.007985',
            f'payload.{fixtures.image_fact_required["external_id"]}': generate_photo_file(),
            f'payload.{fixtures.dim_required["external_id"]}': fixtures.values_dim_required[0]['id']
        }
        second = {
            'external_id': 'some_other',
            f'payload.{fixtures.float_fact_required["external_id"]}': 3.337,
            f'payload.{fixtures.boolean_fact_required["external_id"]}': True,
            f'payload.{fixtures.string_fact_required["external_id"]}': '3_MY_STRING_1',
            f'payload.{fixtures.text_fact_required["external_id"]}': '3_MY_TEXT_1',
            f'payload.{fixtures.file_fact_required["external_id"]}': generate_some_other_photo_file(),
            f'payload.{fixtures.json_fact_required["external_id"]}': '"3_MY_JSON"',
            f'payload.{fixtures.timestamp_fact_required["external_id"]}': '2019-12-17T19:09:25.007985',
            f'payload.{fixtures.image_fact_required["external_id"]}': generate_some_other_photo_file(),
            f'payload.{fixtures.dim_required["external_id"]}': fixtures.values_dim_required[1]['id'],

            f'payload.{fixtures.float_fact_optional["external_id"]}': 2.337,
            f'payload.{fixtures.boolean_fact_optional["external_id"]}': False,
            f'payload.{fixtures.string_fact_optional["external_id"]}': '2_MY_STRING_1',
            f'payload.{fixtures.text_fact_optional["external_id"]}': '2_MY_TEXT_1',
            f'payload.{fixtures.file_fact_optional["external_id"]}': generate_photo_file(),
            f'payload.{fixtures.json_fact_optional["external_id"]}': '"2_MY_JSON"',
            f'payload.{fixtures.timestamp_fact_optional["external_id"]}': '2019-12-16T19:09:25.007985',
            f'payload.{fixtures.image_fact_optional["external_id"]}': generate_photo_file(),
            f'payload.{fixtures.dim_optional["external_id"]}': fixtures.values_dim_optional[1]['id'],
        }
        ret = [
            first,
            second
        ]
        return ret

    def insert_data(self, payloads: List[Dict[str, Any]], fixtures: Fixtures) -> List[Dict[str, Any]]:
        return [
            self.create_payload(
                url=fixtures.data_series['data_points'],
                payload=elem,
                format='multipart',
                # simulate tenant = False because we are using an image
                # and we don't want to get an error when sending
                simulate_tenant=False,
                equality_check=False
            )
            for elem in payloads
        ]

    def compare_data(
            self,
            expected_data: List[Dict[str, Any]],
            actual_data: List[Dict[str, Any]],
            fixtures: Fixtures
    ) -> None:
        for expected, actual in zip(expected_data, actual_data):
            expected_payload = expected['payload']
            actual_payload = actual['payload']
            for fixture_data_type, fixture_data in fixtures._asdict().items():
                if 'fact' in fixture_data_type or 'dim' in fixture_data_type and 'value' not in fixture_data_type:
                    if 'optional' in fixture_data_type:
                        if fixture_data['external_id'] in expected_payload:
                            if 'image' in fixture_data_type or 'file' in fixture_data_type:
                                self.assertIsNotNone(expected_payload[fixture_data['external_id']])
                            else:
                                self.assertEqual(
                                    expected_payload[fixture_data['external_id']],
                                    actual_payload[fixture_data['external_id']]
                                )
                    else:
                        if 'image' in fixture_data_type or 'file' in fixture_data_type:
                            self.assertIsNotNone(expected_payload[fixture_data['external_id']])
                        else:
                            self.assertEqual(
                                expected_payload[fixture_data['external_id']],
                                actual_payload[fixture_data['external_id']]
                            )

    def compare_migrated_data(
            self,
            initial_data: List[Dict[str, Any]],
            created_payloads: List[Dict[str, Any]],
            migrated_payloads: List[Dict[str, Any]],
            fixtures: Fixtures
    ) -> None:
        self.compare_data(
            list(map(to_payload_data, initial_data)),
            migrated_payloads,
            fixtures=fixtures
        )

        # validate image link is still pointing to the same data
        image_fact_required = fixtures.image_fact_required
        image_fact_optional = fixtures.image_fact_optional

        file_fact_required = fixtures.file_fact_required
        file_fact_optional = fixtures.file_fact_optional

        for migrated_payload, original_payload in zip(migrated_payloads, created_payloads):
            self.assertEqual(
                url_without_query(migrated_payload['payload'][image_fact_required['external_id']]),
                url_without_query(original_payload['payload'][image_fact_required['external_id']])
            )
            if image_fact_optional['external_id'] in original_payload['payload']:
                self.assertEqual(
                    url_without_query(migrated_payload['payload'][image_fact_optional['external_id']]),
                    url_without_query(original_payload['payload'][image_fact_optional['external_id']])
                )
            self.assertEqual(
                url_without_query(migrated_payload['payload'][file_fact_required['external_id']]),
                url_without_query(original_payload['payload'][file_fact_required['external_id']])
            )
            if file_fact_optional['external_id'] in original_payload['payload']:
                self.assertEqual(
                    url_without_query(migrated_payload['payload'][file_fact_optional['external_id']]),
                    url_without_query(original_payload['payload'][file_fact_optional['external_id']])
                )

    def migrate(self, fixtures: Fixtures) -> Dict[str, Any]:
        data_series = self.patch_payload(
            url=fixtures.data_series['url'],
            payload={
                'backend': self.migrate_to_backend.value
            }
        )
        return self._ensure_unlocked(data_series)

    def test_immediately_materialize(self) -> None:
        fixtures = self.__setup_fixtures()

        data_series = self.migrate(fixtures)

        initial_data = self.initial_payloads(fixtures)

        created_payloads = self.insert_data(initial_data, fixtures)

        self.compare_data(
            list(map(to_payload_data, initial_data)),
            created_payloads,
            fixtures=fixtures
        )

    def test_migrate_after_data(self) -> None:
        fixtures = self.__setup_fixtures()

        initial_data = self.initial_payloads(fixtures)

        created_payloads = self.insert_data(initial_data, fixtures)

        self.compare_data(
            list(map(to_payload_data, initial_data)),
            created_payloads,
            fixtures=fixtures
        )

        data_series = self.migrate(fixtures)

        migrated_payloads = [self.get_payload(url=elem['url']) for elem in created_payloads]

        self.compare_migrated_data(
            initial_data=initial_data,
            created_payloads=created_payloads,
            migrated_payloads=migrated_payloads,
            fixtures=fixtures
        )

    def test_migrate_after_delete_one(self) -> None:
        fixtures = self.__setup_fixtures()

        initial_data = self.initial_payloads(fixtures)

        created_payloads = self.insert_data(initial_data, fixtures)

        self.compare_data(
            list(map(to_payload_data, initial_data)),
            created_payloads,
            fixtures=fixtures
        )

        self.delete_payload(
            url=created_payloads[1]['url']
        )

        data_series = self.migrate(fixtures)

        remaining_payloads = [created_payloads[0]]
        remaining_initial = [initial_data[0]]
        migrated_payloads = [self.get_payload(url=elem['url']) for elem in remaining_payloads]

        self.compare_migrated_data(
            initial_data=remaining_initial,
            created_payloads=remaining_payloads,
            migrated_payloads=migrated_payloads,
            fixtures=fixtures
        )

        non_existent_response = self.client.get(
            path=created_payloads[1]['url']
        )
        self.assertEqual(status.HTTP_404_NOT_FOUND, non_existent_response.status_code)

# if you want to add migrations that migrate the history from one format into another, the base test is not enough
# as it only cares about the active data

class FlatHistoryToNoHistoryMigrationTest(BaseMigrationTest):
    initial_backend = StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY
    migrate_to_backend = StorageBackendType.DYNAMIC_SQL_NO_HISTORY


del BaseMigrationTest
