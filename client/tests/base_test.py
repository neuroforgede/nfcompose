# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from datetime import datetime
from typing import Any, Dict, Optional, cast
import unittest

from compose_client.library.connection.client import APIClient, RequestsRestClient, Credentials
from tests.env import TEST_NF_COMPOSE_URL, TEST_USER_NAME, TEST_USER_PASSWORD
from compose_client.library.connection.read import read_paginated_generator

class BaseIntegrationTest(unittest.TestCase):
    client: RequestsRestClient

    def _clear_all_data_series(self) -> None:
        all_data_series = read_paginated_generator(
            client=self.client,
            url=self.client.url('/api/dataseries/dataseries/'),
            converter=lambda x: x
        )
        for data_series in all_data_series:
            self.client.delete(data_series['url'])

    def _clear_all_groups(self) -> None:
        all_groups = read_paginated_generator(
            client=self.client,
            url=self.client.url('/api/common/auth/group/'),
            converter=lambda x: x
        )
        for group in all_groups:
            self.client.delete(group['url'])

    def _clear_all_users(self) -> None:
        all_users = read_paginated_generator(
            client=self.client,
            url=self.client.url('/api/common/auth/user/'),
            converter=lambda x: x
        )
        for user in all_users:
            if user['username'] == self.client.credentials.user:
                continue
            self.client.delete(user['url'])
    
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
        self._clear_all_groups()
        self._clear_all_users()
        return super().setUp()

    def tearDown(self) -> None:
        self._clear_all_data_series()
        self._clear_all_groups()
        self._clear_all_users()
        
        self.client.post(
            url=self.client.url('/api/dataseries/prune/dataseries/'),
            data={
                "older_than": '2100-01-01T00:00:00.000001Z',
                "accept": True
            }
        )
        return super().tearDown()