# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import unittest
import uuid

from faker import Faker  # type: ignore

from compose_client.library.models.definition.engine import Engine, EngineSecret
from compose_client.library.models.raw.engine import RawEngine, RawEngineSecret

fake = Faker()


class EngineConversionTest(unittest.TestCase):

    def test_conversion(self) -> None:
        raw = RawEngine(
            url="http://localhost:7044/api/flow/engine/5d71d940-ca3f-408b-8f50-920cc68974ed/",
            id=str(uuid.uuid4()),
            external_id="engine",
            upstream="http://nodered.dev.local:2800",
            access="http://localhost:7044/api/flow/engine/5d71d940-ca3f-408b-8f50-920cc68974ed/access/",
            permission_user="http://localhost:7044/api/flow/engine/5d71d940-ca3f-408b-8f50-920cc68974ed/permission/user/",
            permission_group="http://localhost:7044/api/flow/engine/5d71d940-ca3f-408b-8f50-920cc68974ed/permission/group/",
            secret="http://localhost:7044/api/flow/engine/5d71d940-ca3f-408b-8f50-920cc68974ed/secret/"
        )
        converted = Engine.from_raw(raw, {})
        self.assertEqual(converted.upstream, raw.upstream)
        self.assertEqual(converted.external_id, raw.external_id)

    def test_conversion_aliased(self) -> None:
        raw = RawEngine(
            url="http://localhost:7044/api/flow/engine/5d71d940-ca3f-408b-8f50-920cc68974ed/",
            id=str(uuid.uuid4()),
            external_id="engine",
            upstream="http://nodered.dev.local:2800",
            access="http://localhost:7044/api/flow/engine/5d71d940-ca3f-408b-8f50-920cc68974ed/access/",
            permission_user="http://localhost:7044/api/flow/engine/5d71d940-ca3f-408b-8f50-920cc68974ed/permission/user/",
            permission_group="http://localhost:7044/api/flow/engine/5d71d940-ca3f-408b-8f50-920cc68974ed/permission/group/",
            secret="http://localhost:7044/api/flow/engine/5d71d940-ca3f-408b-8f50-920cc68974ed/secret/"
        )
        converted = Engine.from_raw(raw, {"nodered.dev.local:2800": "nodered.dev.nonlocal:2800"})
        self.assertEqual(converted.upstream, "http://nodered.dev.nonlocal:2800")
        self.assertEqual(converted.external_id, raw.external_id)



class EngineSecretConversionTest(unittest.TestCase):

    def test_conversion(self) -> None:
        raw = RawEngineSecret(
            secret=fake.password()
        )
        converted = EngineSecret.from_raw(raw)
        self.assertEqual(converted.secret, raw.secret)