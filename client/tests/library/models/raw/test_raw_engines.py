# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import unittest
import uuid
from faker import Faker  # type: ignore

from compose_client.library.models.raw.engine import RawEngine, RawEngineSecret

fake = Faker()


class RawEngineSecretConversionTest(unittest.TestCase):

    def test_raw_conversion(self) -> None:
        dict = {
            "secret": fake.password()
        }
        parsed = RawEngineSecret.from_dict(dict)
        self.assertEqual(parsed.secret, dict['secret'])

    def test_extra_data_raw_conversion(self) -> None:
        dict = {
            "secret": fake.password(),
            "should": "not-be-here"
        }
        with self.assertRaises(Exception) as e:
            RawEngineSecret.from_dict(dict)


class RawEngineConversionTest(unittest.TestCase):

    def test_raw_conversion(self) -> None:
        dict = {
            "url": "http://localhost:7044/api/flow/engine/5d71d940-ca3f-408b-8f50-920cc68974ed/",
            "id": str(uuid.uuid4()),
            "external_id": "engine",
            "upstream": "http://nodered.dev.local:2800",
            "access": "http://localhost:7044/api/flow/engine/5d71d940-ca3f-408b-8f50-920cc68974ed/access/",
            "permission_user": "http://localhost:7044/api/flow/engine/5d71d940-ca3f-408b-8f50-920cc68974ed/permission/user/",
            "permission_group": "http://localhost:7044/api/flow/engine/5d71d940-ca3f-408b-8f50-920cc68974ed/permission/group/",
            "secret": "http://localhost:7044/api/flow/engine/5d71d940-ca3f-408b-8f50-920cc68974ed/secret/"
        }
        parsed = RawEngine.from_dict(dict)
        self.assertEqual(parsed.url, dict['url'])
        self.assertEqual(parsed.id, dict['id'])
        self.assertEqual(parsed.external_id, dict['external_id'])
        self.assertEqual(parsed.upstream, dict['upstream'])
        self.assertEqual(parsed.access, dict['access'])
        self.assertEqual(parsed.permission_user, dict['permission_user'])
        self.assertEqual(parsed.permission_group, dict['permission_group'])

    def test_extra_data_raw_conversion(self) -> None:
        dict = {
            "url": "http://localhost:7044/api/flow/engine/5d71d940-ca3f-408b-8f50-920cc68974ed/",
            "id": str(uuid.uuid4()),
            "external_id": "engine",
            "upstream": "http://nodered.dev.local:2800",
            "access": "http://localhost:7044/api/flow/engine/5d71d940-ca3f-408b-8f50-920cc68974ed/access/",
            "permission_user": "http://localhost:7044/api/flow/engine/5d71d940-ca3f-408b-8f50-920cc68974ed/permission/user/",
            "permission_group": "http://localhost:7044/api/flow/engine/5d71d940-ca3f-408b-8f50-920cc68974ed/permission/group/",
            "secret": "http://localhost:7044/api/flow/engine/5d71d940-ca3f-408b-8f50-920cc68974ed/secret/",
            "should": "not-be-here"
        }
        with self.assertRaises(Exception) as e:
            RawEngine.from_dict(dict)
