# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import unittest
from typing import Any, Dict, cast

from compose_client.library.connection.client import Credentials, MockRestClient
from compose_client.library.connection.read import read_paginated_all, APIConverter, read_list

test_credentials = Credentials(
    base_url='http://some.mock.url',
    user='user',
    password='password'
)
test_path = '/my/list/paginated/'
test_path_simple = '/my/simple/list'
test_client = MockRestClient(test_credentials, {
    "user": {
        "get": {
            f'http://some.mock.url{test_path}': {
                "next": f'http://some.mock.url{test_path}1',
                "results": [
                    {
                        "external_id": "1"
                    }
                ]
            },
            f'http://some.mock.url{test_path}1': {
                "next": None,
                "results": [
                    {
                        "external_id": "2"
                    }
                ]
            },
            f'http://some.mock.url{test_path_simple}': [
                {
                    "external_id": "1"
                },
                {
                    "external_id": "2"
                }
            ]
        }
    }
})


class ConnectionReadTest(unittest.TestCase):
    def test_paginated_scrolls_all_pages(self) -> None:
        class IdentityConverter(APIConverter[Any]):
            def __call__(self, json: Dict[str, Any]) -> Dict[str, Any]:
                return json

        data = list(read_paginated_all(test_client, test_client.url(test_path), IdentityConverter()))

        self.assertEqual(2, len(data))
        self.assertEqual("1", data[0]['external_id'])
        self.assertEqual("2", data[1]['external_id'])

    def test_paginated_calls_converter(self) -> None:
        class IdentityConverter(APIConverter[Any]):
            def __call__(self, json: Dict[str, Any]) -> Dict[str, Any]:
                return cast(Dict[str, Any], json['external_id'])

        data = list(read_paginated_all(test_client, test_client.url(test_path), IdentityConverter()))

        self.assertEqual(2, len(data))
        self.assertEqual("1", data[0])
        self.assertEqual("2", data[1])

    def test_list_fetches_all(self) -> None:
        class IdentityConverter(APIConverter[Any]):
            def __call__(self, json: Dict[str, Any]) -> Dict[str, Any]:
                return json

        data = list(read_list(test_client, test_client.url(test_path_simple), IdentityConverter()))

        self.assertEqual(2, len(data))
        self.assertEqual("1", data[0]['external_id'])
        self.assertEqual("2", data[1]['external_id'])

    def test_list_calls_converter(self) -> None:
        class IdentityConverter(APIConverter[Any]):
            def __call__(self, json: Dict[str, Any]) -> Dict[str, Any]:
                return cast(Dict[str, Any], json['external_id'])

        data = list(read_list(test_client, test_client.url(test_path_simple), IdentityConverter()))

        self.assertEqual(2, len(data))
        self.assertEqual("1", data[0])
        self.assertEqual("2", data[1])




