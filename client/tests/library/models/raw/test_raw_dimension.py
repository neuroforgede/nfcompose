# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

import datetime
import unittest
import uuid

from compose_client.library.models.raw.dimension import RawDimension


class RawDimensionConversionTest(unittest.TestCase):

    def test_raw_conversion(self) -> None:
        dict = {
            "url": "http://some.url/",
            "id": str(uuid.uuid4()),
            "point_in_time": datetime.datetime.now().isoformat(),
            "last_modified_at": datetime.datetime.now().isoformat(),
            "name": "1111",
            "optional": True,
            "external_id": "111",
            "reference": "http://some.other.url/"
        }
        parsed = RawDimension.from_dict(dict)
        self.assertEqual(parsed.url, dict['url'])
        self.assertEqual(parsed.id, dict['id'])
        self.assertEqual(parsed.point_in_time, dict['point_in_time'])
        self.assertEqual(parsed.last_modified_at, dict['last_modified_at'])
        self.assertEqual(parsed.name, dict['name'])
        self.assertEqual(parsed.optional, dict['optional'])
        self.assertEqual(parsed.external_id, dict['external_id'])
        self.assertEqual(parsed.reference, dict['reference'])

    def test_extra_data_raw_conversion(self) -> None:
        dict = {
            "url": "http://some.url/",
            "id": str(uuid.uuid4()),
            "point_in_time": datetime.datetime.now().isoformat(),
            "last_modified_at": datetime.datetime.now().isoformat(),
            "name": "1111",
            "optional": True,
            "external_id": "111",
            "should": "not-be-here",
            "reference": "http://some.other.url/"
        }
        RawDimension.from_dict(dict)
