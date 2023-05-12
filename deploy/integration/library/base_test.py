from datetime import datetime
from typing import Any, Dict, Optional, cast
import unittest

from library.client import APIClient, RequestsRestClient, Credentials
from library.env import TEST_NF_COMPOSE_URL, TEST_USER_NAME, TEST_USER_PASSWORD
from library.read import read_paginated_generator

class BaseIntegrationTest(unittest.TestCase):
    client: APIClient

    def _clear_all_data_series(self) -> None:
        all_data_series = read_paginated_generator(
            client=self.client,
            url=self.client.url('/api/dataseries/dataseries/'),
            converter=lambda x: x
        )
        for data_series in all_data_series:
            self.client.delete(data_series['url'])
    
    def _create_data_series(self, external_id: str, name: str, backend: Optional[str] = 'DYNAMIC_SQL_NO_HISTORY', allow_extra_fields: bool = False) -> Dict[str, Any]:
        return cast(Dict[str, Any], self.client.post(
            url=self.client.url('/api/dataseries/dataseries/'),
            data={
                "external_id": external_id,
                "name": name,
                "backend": backend,
                "extra_config": {
                    "auto_clean_history_after_days": -1,
                    "auto_clean_meta_model_after_days": -1
                },
                "allow_extra_fields": allow_extra_fields
            }
        ))

    def setUp(self) -> None:
        self.client = RequestsRestClient(
            credentials=Credentials(
                base_url=TEST_NF_COMPOSE_URL,
                user=TEST_USER_NAME,
                password=TEST_USER_PASSWORD
            )
        )
        self._clear_all_data_series()
        return super().setUp()

    def tearDown(self) -> None:
        self._clear_all_data_series()
        
        self.client.post(
            url=self.client.url('/api/dataseries/prune/dataseries/'),
            data={
                "older_than": '2100-01-01T00:00:00.000001Z',
                "accept": True
            }
        )
        return super().tearDown()