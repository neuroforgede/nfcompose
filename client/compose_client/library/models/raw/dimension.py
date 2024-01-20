# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from dataclasses import dataclass
from typing import Dict, Any, cast

from dataclasses_json import dataclass_json, Undefined

from compose_client.library.connection.read import APIConverter

REST_URL = str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class RawDimension:
    url: REST_URL
    id: str
    point_in_time: str
    last_modified_at: str
    name: str
    optional: bool
    external_id: str
    reference: REST_URL

    @staticmethod
    def from_dict(dict: Dict[str, Any]) -> 'RawDimension': ...


class DimensionConverter(APIConverter[RawDimension]):
    def __call__(self, json: Dict[str, Any]) -> 'RawDimension':
        return RawDimension.from_dict(json)
