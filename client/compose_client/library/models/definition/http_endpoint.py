# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from dataclasses import dataclass, field
from typing import Dict, Any, List

from dataclasses_json import dataclass_json, Undefined

from compose_client.library.models.identifiable import Identifiable, IdentifiableByName
from compose_client.library.models.raw.engine import RawEngine, RawEngineSecret
from compose_client.library.models.raw.http_endpoint import RawHttpEndpoint, RawHttpEndpointGroupPermissions

REST_URL = str

EXTERNAL_ID = str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class HttpEndpoint:
    engine: EXTERNAL_ID
    external_id: str
    path: str
    method: str
    public: bool

    @staticmethod
    def from_dict(dict: Dict[str, Any]) -> 'HttpEndpoint': ...

    def to_dict(self) -> Any: ...

    @staticmethod
    def from_raw(raw: RawHttpEndpoint, engine_lookup: Dict[REST_URL, EXTERNAL_ID]) -> 'HttpEndpoint':
        return HttpEndpoint(
            engine=engine_lookup[raw.engine],
            external_id=raw.external_id,
            path=raw.path,
            method=raw.method,
            public=raw.public
        )


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class HttpEndpointGroupPermissions(IdentifiableByName):
    name: str
    group_permissions: List[str]

    @staticmethod
    def from_raw(raw: RawHttpEndpointGroupPermissions) -> 'HttpEndpointGroupPermissions':
        return HttpEndpointGroupPermissions(
            name=raw.name,
            group_permissions=raw.group_permissions
        )


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class HttpEndpointDefinition:
    http_endpoint: HttpEndpoint
    group_permissions: List[HttpEndpointGroupPermissions] = field(default_factory=list)

    @staticmethod
    def from_dict(dict: Dict[str, Any]) -> 'HttpEndpointDefinition': ...
