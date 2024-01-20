# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from dataclasses import dataclass
from typing import Dict, Any, List

from dataclasses_json import dataclass_json, Undefined

from compose_client.library.connection.read import APIConverter

REST_URL = str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class RawIndexTarget:
    target_id: str
    target_external_id: str
    target_type: str

    @staticmethod
    def from_dict(dict: Dict[str, Any]) -> 'RawIndexTarget': ...

@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class RawIndex:
    external_id: str
    name: str

    url: REST_URL
    id: str
    point_in_time: str
    last_modified_at: str

    targets: List[RawIndexTarget]

    @staticmethod
    def from_dict(dict: Dict[str, Any]) -> 'RawIndex': ...


class IndexConverter(APIConverter[RawIndex]):
    def __call__(self, json: Dict[str, Any]) -> 'RawIndex':
        return RawIndex.from_dict(json)