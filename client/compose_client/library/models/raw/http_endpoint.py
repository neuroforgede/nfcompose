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
class RawHttpEndpointGroupPermissions:
    url: REST_URL
    name: str
    fully_qualified: str
    group_permissions: List[str]

    @staticmethod
    def from_dict(dict: Dict[str, Any]) -> 'RawHttpEndpointGroupPermissions': ...


class RawHttpEndpointGroupPermissionsAPIConverter(APIConverter[RawHttpEndpointGroupPermissions]):
    def __call__(self, json: Dict[str, Any]) -> RawHttpEndpointGroupPermissions:
        return RawHttpEndpointGroupPermissions.from_dict(json)


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class RawHttpEndpoint:
    url: REST_URL
    id: str
    engine: REST_URL
    external_id: str
    path: str
    method: str
    public: bool
    permission_user: REST_URL
    permission_group: REST_URL

    @staticmethod
    def from_dict(dict: Dict[str, Any]) -> 'RawHttpEndpoint': ...


class RawHttpEndpointAPIConverter(APIConverter[RawHttpEndpoint]):
    def __call__(self, json: Dict[str, Any]) -> RawHttpEndpoint:
        return RawHttpEndpoint.from_dict(json)

