# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

import unittest
import uuid

from faker import Faker  # type: ignore

from compose_client.library.models.definition.http_endpoint import HttpEndpoint
from compose_client.library.models.raw.http_endpoint import RawHttpEndpoint

fake = Faker()


class HttpEndpointConversionTest(unittest.TestCase):

    def test_conversion(self) -> None:
        _id = str(uuid.uuid4())
        raw = RawHttpEndpoint(
            url=f"https://localhost:6043/api/flow/httpendpoint/{_id}/",
            id=_id,
            engine=f"https://localhost:6043/api/flow/engine/{_id}/",
            external_id="http_endpoint",
            path="/api/flow/impl/mypath",
            method="GET",
            public=False,
            permission_user=f"https://localhost:6043/api/flow/httpendpoint/{_id}/permission/user/",
            permission_group=f"https://localhost:6043/api/flow/httpendpoint/{_id}/permission/group/",
        )
        converted = HttpEndpoint.from_raw(raw, {
            f"https://localhost:6043/api/flow/engine/{_id}/": 'engine_external_id'
        })
        self.assertEqual(converted.external_id, raw.external_id)
        self.assertEqual(converted.engine, 'engine_external_id')
        self.assertEqual(converted.path, raw.path)
        self.assertEqual(converted.method, raw.method)
        self.assertEqual(converted.public, raw.public)
