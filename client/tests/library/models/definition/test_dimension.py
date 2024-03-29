# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

import datetime
import unittest
import uuid

from compose_client.library.models.definition.dimension import Dimension
from compose_client.library.models.raw.dimension import RawDimension


class DimensionConversionTest(unittest.TestCase):
    def test_conversion(self) -> None:
        raw = RawDimension(
            url='http://some.url',
            id=str(uuid.uuid4()),
            point_in_time=datetime.datetime.now().isoformat(),
            last_modified_at=datetime.datetime.now().isoformat(),
            name='my_float',
            optional=False,
            external_id='my_external_id',
            reference='http://my.fancy.ds.url/'
        )
        parsed = Dimension.from_raw(raw, {'http://my.fancy.ds.url/': 'data_series_external_id'})
        self.assertEqual(parsed.name, raw.name)
        self.assertEqual(parsed.external_id, raw.external_id)
        self.assertEqual(parsed.optional, raw.optional)
        self.assertEqual(parsed.reference, 'data_series_external_id')
