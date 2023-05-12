# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import datetime
import unittest
import uuid

from compose_client.library.models.definition.facts import FloatFact, StringFact, TextFact, TimestampFact, ImageFact, FileFact, JsonFact, \
    BooleanFact
from compose_client.library.models.raw.facts import RawFloatFact, RawStringFact, RawTextFact, RawTimestampFact, RawImageFact, RawFileFact, \
    RawJsonFact, RawBooleanFact


class FactConversionTest(unittest.TestCase):
    def test_float_conversion(self) -> None:
        raw = RawFloatFact(
            url='http://some.url',
            id=str(uuid.uuid4()),
            point_in_time=datetime.datetime.now().isoformat(),
            last_modified_at=datetime.datetime.now().isoformat(),
            name='my_float',
            optional=False,
            external_id='my_external_id'
        )
        parsed = FloatFact.from_raw(raw)
        self.assertEqual(parsed.name, raw.name)
        self.assertEqual(parsed.external_id, raw.external_id)
        self.assertEqual(parsed.optional, raw.optional)

    def test_string_conversion(self) -> None:
        raw = RawStringFact(
            url='http://some.url',
            id=str(uuid.uuid4()),
            point_in_time=datetime.datetime.now().isoformat(),
            last_modified_at=datetime.datetime.now().isoformat(),
            name='my_float',
            optional=False,
            external_id='my_external_id'
        )
        parsed = StringFact.from_raw(raw)
        self.assertEqual(parsed.name, raw.name)
        self.assertEqual(parsed.external_id, raw.external_id)
        self.assertEqual(parsed.optional, raw.optional)

    def test_text_conversion(self) -> None:
        raw = RawTextFact(
            url='http://some.url',
            id=str(uuid.uuid4()),
            point_in_time=datetime.datetime.now().isoformat(),
            last_modified_at=datetime.datetime.now().isoformat(),
            name='my_float',
            optional=False,
            external_id='my_external_id'
        )
        parsed = TextFact.from_raw(raw)
        self.assertEqual(parsed.name, raw.name)
        self.assertEqual(parsed.external_id, raw.external_id)
        self.assertEqual(parsed.optional, raw.optional)

    def test_timestamp_conversion(self) -> None:
        raw = RawTimestampFact(
            url='http://some.url',
            id=str(uuid.uuid4()),
            point_in_time=datetime.datetime.now().isoformat(),
            last_modified_at=datetime.datetime.now().isoformat(),
            name='my_float',
            optional=False,
            external_id='my_external_id'
        )
        parsed = TimestampFact.from_raw(raw)
        self.assertEqual(parsed.name, raw.name)
        self.assertEqual(parsed.external_id, raw.external_id)
        self.assertEqual(parsed.optional, raw.optional)

    def test_image_conversion(self) -> None:
        raw = RawImageFact(
            url='http://some.url',
            id=str(uuid.uuid4()),
            point_in_time=datetime.datetime.now().isoformat(),
            last_modified_at=datetime.datetime.now().isoformat(),
            name='my_float',
            optional=False,
            external_id='my_external_id'
        )
        parsed = ImageFact.from_raw(raw)
        self.assertEqual(parsed.name, raw.name)
        self.assertEqual(parsed.external_id, raw.external_id)
        self.assertEqual(parsed.optional, raw.optional)

    def test_file_conversion(self) -> None:
        raw = RawFileFact(
            url='http://some.url',
            id=str(uuid.uuid4()),
            point_in_time=datetime.datetime.now().isoformat(),
            last_modified_at=datetime.datetime.now().isoformat(),
            name='my_float',
            optional=False,
            external_id='my_external_id'
        )
        parsed = FileFact.from_raw(raw)
        self.assertEqual(parsed.name, raw.name)
        self.assertEqual(parsed.external_id, raw.external_id)
        self.assertEqual(parsed.optional, raw.optional)

    def test_json_conversion(self) -> None:
        raw = RawJsonFact(
            url='http://some.url',
            id=str(uuid.uuid4()),
            point_in_time=datetime.datetime.now().isoformat(),
            last_modified_at=datetime.datetime.now().isoformat(),
            name='my_float',
            optional=False,
            external_id='my_external_id'
        )
        parsed = JsonFact.from_raw(raw)
        self.assertEqual(parsed.name, raw.name)
        self.assertEqual(parsed.external_id, raw.external_id)
        self.assertEqual(parsed.optional, raw.optional)

    def test_boolean_conversion(self) -> None:
        raw = RawBooleanFact(
            url='http://some.url',
            id=str(uuid.uuid4()),
            point_in_time=datetime.datetime.now().isoformat(),
            last_modified_at=datetime.datetime.now().isoformat(),
            name='my_float',
            optional=False,
            external_id='my_external_id'
        )
        parsed = BooleanFact.from_raw(raw)
        self.assertEqual(parsed.name, raw.name)
        self.assertEqual(parsed.external_id, raw.external_id)
        self.assertEqual(parsed.optional, raw.optional)
