# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import datetime
import unittest
import uuid
from typing import Any

from compose_client.library.models.raw.facts import RawFloatFact, RawStringFact, RawTextFact, RawImageFact, RawFileFact, RawJsonFact, \
    RawBooleanFact, RawTimestampFact, raw_fact_api_converter


class BaseRawFactConversionTest(unittest.TestCase):
    fact_type: Any

    def test_raw_conversion_with_converter(self) -> None:
        dict = {
            "url": "http://some.url/",
            "id": str(uuid.uuid4()),
            "point_in_time": datetime.datetime.now().isoformat(),
            "last_modified_at": datetime.datetime.now().isoformat(),
            "name": "1111",
            "optional": True,
            "external_id": "111"
        }
        parsed = raw_fact_api_converter(self.fact_type)(dict)
        self.assertEqual(parsed.url, dict['url'])
        self.assertEqual(parsed.id, dict['id'])
        self.assertEqual(parsed.point_in_time, dict['point_in_time'])
        self.assertEqual(parsed.last_modified_at, dict['last_modified_at'])
        self.assertEqual(parsed.name, dict['name'])
        self.assertEqual(parsed.optional, dict['optional'])
        self.assertEqual(parsed.external_id, dict['external_id'])

    def test_raw_conversion(self) -> None:
        dict = {
            "url": "http://some.url/",
            "id": str(uuid.uuid4()),
            "point_in_time": datetime.datetime.now().isoformat(),
            "last_modified_at": datetime.datetime.now().isoformat(),
            "name": "1111",
            "optional": True,
            "external_id": "111"
        }
        parsed = self.fact_type.from_dict(dict)
        self.assertEqual(parsed.url, dict['url'])
        self.assertEqual(parsed.id, dict['id'])
        self.assertEqual(parsed.point_in_time, dict['point_in_time'])
        self.assertEqual(parsed.last_modified_at, dict['last_modified_at'])
        self.assertEqual(parsed.name, dict['name'])
        self.assertEqual(parsed.optional, dict['optional'])
        self.assertEqual(parsed.external_id, dict['external_id'])

    def test_extra_data_raw_conversion(self) -> None:
        dict = {
            "url": "http://some.url/",
            "id": uuid.uuid4(),
            "point_in_time": datetime.datetime.now().isoformat(),
            "last_modified_at": datetime.datetime.now().isoformat(),
            "name": "1111",
            "optional": True,
            "external_id": "111",
            "should": "not-be-here"
        }
        # should not raise
        self.fact_type.from_dict(dict)


class RawFloatFactConversionTest(BaseRawFactConversionTest):
    fact_type = RawFloatFact


class RawStringFactConversionTest(BaseRawFactConversionTest):
    fact_type = RawStringFact


class RawTextFactConversionTest(BaseRawFactConversionTest):
    fact_type = RawTextFact


class RawTimestampFactConversionTest(BaseRawFactConversionTest):
    fact_type = RawTimestampFact


class RawImageFactConversionTest(BaseRawFactConversionTest):
    fact_type = RawImageFact


class RawFileFactConversionTest(BaseRawFactConversionTest):
    fact_type = RawFileFact


class RawJsonFactConversionTest(BaseRawFactConversionTest):
    fact_type = RawJsonFact


class RawBooleanFactConversionTest(BaseRawFactConversionTest):
    fact_type = RawBooleanFact


del BaseRawFactConversionTest