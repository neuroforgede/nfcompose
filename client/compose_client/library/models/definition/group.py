# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from dataclasses import dataclass
from typing import Dict, Any, List

from dataclasses_json import dataclass_json, Undefined

from compose_client.library.models.raw.group import RawGroupPermissions, RawGroup

REST_URL = str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class GroupPermissions:
    group_permissions: List[str]

    @staticmethod
    def from_raw(raw: RawGroupPermissions) -> 'GroupPermissions':
        return GroupPermissions(
            group_permissions=raw.group_permissions
        )

    def to_dict(self) -> Any: ...


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Group:
    name: str

    @staticmethod
    def from_raw(raw: RawGroup) -> 'Group':
        return Group(
            name=raw.name
        )

    def to_dict(self) -> Any: ...


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class GroupDefinition:
    group: Group
    group_permissions: GroupPermissions

    @staticmethod
    def from_dict(dict: Dict[str, Any]) -> 'GroupDefinition': ...

