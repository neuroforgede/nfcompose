# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import unittest
import uuid
from faker import Faker  # type: ignore

from compose_client.library.models.raw.http_endpoint import RawHttpEndpoint

fake = Faker()


class RawHttpEndpointConversionTest(unittest.TestCase):

    def test_raw_conversion(self) -> None:
        _id = str(uuid.uuid4())
        dict = {
                "url": f"https://localhost:6043/api/flow/httpendpoint/{_id}/",
                "id": _id,
                "engine": f"https://localhost:6043/api/flow/httpendpoint/{_id}/",
                "external_id": "http_endpoint",
                "path": "/api/flow/impl/mypath",
                "method": "GET",
                "public": False,
                "permission_user": f"https://localhost:6043/api/flow/httpendpoint/{_id}/permission/user/",
                "permission_group": f"https://localhost:6043/api/flow/httpendpoint/{_id}/permission/group/"
        }
        parsed = RawHttpEndpoint.from_dict(dict)
        self.assertEqual(parsed.url, dict['url'])
        self.assertEqual(parsed.id, dict['id'])
        self.assertEqual(parsed.external_id, dict['external_id'])
        self.assertEqual(parsed.engine, dict['engine'])
        self.assertEqual(parsed.path, dict['path'])
        self.assertEqual(parsed.public, dict['public'])
        self.assertEqual(parsed.permission_user, dict['permission_user'])
        self.assertEqual(parsed.permission_group, dict['permission_group'])

    def test_extra_data_raw_conversion(self) -> None:
        _id = str(uuid.uuid4())
        dict = {
            "url": f"https://localhost:6043/api/flow/httpendpoint/{_id}/",
            "id": _id,
            "engine": f"https://localhost:6043/api/flow/httpendpoint/{_id}/",
            "external_id": "http_endpoint",
            "path": "/api/flow/impl/mypath",
            "method": "GET",
            "public": False,
            "permission_user": f"https://localhost:6043/api/flow/httpendpoint/{_id}/permission/user/",
            "permission_group": f"https://localhost:6043/api/flow/httpendpoint/{_id}/permission/group/",
            "should": "not-be-here"
        }
        # should not raise
        RawHttpEndpoint.from_dict(dict)
