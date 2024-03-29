# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from dataclasses import dataclass
from typing import Dict

from dataclasses_json import dataclass_json, Undefined

from compose_client.library.models.identifiable import Identifiable
from compose_client.library.models.raw.dimension import RawDimension

REST_URL = str
DATA_SERIES_EXTERNAL_ID = str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Dimension(Identifiable):
    name: str
    optional: bool
    reference: DATA_SERIES_EXTERNAL_ID

    @staticmethod
    def from_raw(raw: RawDimension, ds_lookup: Dict[REST_URL, DATA_SERIES_EXTERNAL_ID]) -> 'Dimension':
        return Dimension(
            external_id=raw.external_id,
            name=raw.name,
            optional=raw.optional,
            reference=ds_lookup[raw.reference]
        )
