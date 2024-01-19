# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from dataclasses_json import Undefined, dataclass_json

from compose_client.library.connection.read import APIConverter

REST_URL = str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class RawGroupPermissions:
    group_permissions: List[str]

    @staticmethod
    def from_dict(dict: Dict[str, Any]) -> 'RawGroupPermissions': ...


class RawGroupPermissionsAPIConverter(APIConverter[RawGroupPermissions]):
    def __call__(self, json: Dict[str, Any]) -> RawGroupPermissions:
        return RawGroupPermissions.from_dict(json)


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class RawGroup:
    url: REST_URL
    permissions: REST_URL
    name: str
    fully_qualified: str
    # future versions will drop this in the api
    id: Optional[int] = field(default=None)

    @staticmethod
    def from_dict(dict: Dict[str, Any]) -> 'RawGroup': ...


class RawGroupAPIConverter(APIConverter[RawGroup]):
    def __call__(self, json: Dict[str, Any]) -> RawGroup:
        return RawGroup.from_dict(json)
