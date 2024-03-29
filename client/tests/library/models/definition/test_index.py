# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

import datetime
import unittest
import uuid

from compose_client.library.models.definition.index import Index
from compose_client.library.models.raw.index import RawIndex, RawIndexTarget


class IndexConversionTest(unittest.TestCase):
    def test_conversion(self) -> None:
        raw = RawIndex(
            external_id='idx',
            name='idxname',
            url='http://some.url',
            id=str(uuid.uuid4()),
            point_in_time=datetime.datetime.now().isoformat(),
            last_modified_at=datetime.datetime.now().isoformat(),
            targets=[
                RawIndexTarget(
                    target_id=str(uuid.uuid4()),
                    target_external_id='some_target_1',
                    target_type='FLOAT_FACT'
                ),
                RawIndexTarget(
                    target_id=str(uuid.uuid4()),
                    target_external_id='some_target_2',
                    target_type='STRING_FACT'
                )
            ]
        )
        parsed = Index.from_raw(raw)
        self.assertEqual(parsed.name, raw.name)
        self.assertEqual(parsed.external_id, raw.external_id)
        for i, target in enumerate(raw.targets):
            self.assertEqual(target.target_external_id, parsed.targets[i].target_external_id)
            self.assertEqual(target.target_type, parsed.targets[i].target_type)

