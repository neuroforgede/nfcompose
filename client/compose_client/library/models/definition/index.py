# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from copy import deepcopy
from dataclasses import dataclass
from typing import Dict, Any, List

from dataclasses_json import dataclass_json, Undefined

from compose_client.library.models.identifiable import Identifiable
from compose_client.library.models.raw.index import RawIndex, RawIndexTarget
from compose_client.library.service.url import replace_domain

REST_URL = str


@dataclass_json(undefined=Undefined.RAISE)
@dataclass
class IndexTarget:
    target_external_id: str
    target_type: str

    @staticmethod
    def from_dict(dict: Dict[str, Any]) -> 'IndexTarget': ...

@dataclass_json(undefined=Undefined.RAISE)
@dataclass
class Index(Identifiable):
    name: str
    targets: List[IndexTarget]


    @staticmethod
    def from_raw(raw: RawIndex) -> 'Index':
        return Index(
            external_id=raw.external_id,
            name=raw.name,
            targets=[IndexTarget(
                target_external_id=raw_target.target_external_id,
                target_type=raw_target.target_type
            ) for raw_target in raw.targets]
        )

    def to_dict(self) -> Any: ...

