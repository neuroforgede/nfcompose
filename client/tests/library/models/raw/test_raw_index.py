# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

import datetime
from typing import Dict, List
import unittest
import uuid

from compose_client.library.models.raw.index import RawIndex


class RawDimensionConversionTest(unittest.TestCase):

    def test_raw_conversion(self) -> None:
        targets: List[Dict[str, str]] = [
                {
                    'target_id': str(uuid.uuid4()),
                    'target_external_id': 'some_target_1',
                    'target_type': 'FLOAT_FACT'
                },
                {
                    'target_id': str(uuid.uuid4()),
                    'target_external_id': 'some_target_2',
                    'target_type': 'STRING_FACT'
                }
            ]
        dict = {
            "url": "http://some.url/",
            "id": str(uuid.uuid4()),
            "point_in_time": datetime.datetime.now().isoformat(),
            "last_modified_at": datetime.datetime.now().isoformat(),
            "name": "1111",
            "external_id": "111",
            'targets': targets
        }
        parsed = RawIndex.from_dict(dict)
        self.assertEqual(parsed.url, dict['url'])
        self.assertEqual(parsed.id, dict['id'])
        self.assertEqual(parsed.point_in_time, dict['point_in_time'])
        self.assertEqual(parsed.last_modified_at, dict['last_modified_at'])
        self.assertEqual(parsed.name, dict['name'])
        self.assertEqual(parsed.external_id, dict['external_id'])
        for i, target in enumerate(parsed.targets):
            self.assertEqual(target.target_type, targets[i]['target_type'])
            self.assertEqual(target.target_external_id, targets[i]['target_external_id'])
            self.assertEqual(target.target_id, targets[i]['target_id'])

    def test_extra_data_raw_conversion(self) -> None:
        dict = {
            "url": "http://some.url/",
            "id": str(uuid.uuid4()),
            "point_in_time": datetime.datetime.now().isoformat(),
            "last_modified_at": datetime.datetime.now().isoformat(),
            "name": "1111",
            "external_id": "111",
            "should": "not-be-here",
            'targets': [
                {
                    'target_id': str(uuid.uuid4()),
                    'target_external_id': 'some_target_1',
                    'target_type': 'FLOAT_FACT'
                },
                {
                    'target_id': str(uuid.uuid4()),
                    'target_external_id': 'some_target_2',
                    'target_type': 'STRING_FACT'
                }
            ]
        }
        # should not raise
        RawIndex.from_dict(dict)
