# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from dataclasses import dataclass, field
from typing import Dict, Any, List

from dataclasses_json import dataclass_json, Undefined

from compose_client.library.models.identifiable import Identifiable, IdentifiableByName
from compose_client.library.models.raw.engine import RawEngine, RawEngineSecret, RawEngineGroupPermissions
from compose_client.library.service.url import replace_domain

REST_URL = str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Engine(Identifiable):
    upstream: REST_URL

    @staticmethod
    def from_raw(raw: RawEngine, domain_aliases: Dict[str, str]) -> 'Engine':
        return Engine(
            external_id=raw.external_id,
            upstream=replace_domain(raw.upstream, domain_aliases)
        )

    def to_dict(self) -> Any: ...


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class EngineSecret:
    secret: str

    @staticmethod
    def from_raw(raw: RawEngineSecret) -> 'EngineSecret':
        return EngineSecret(
            secret=raw.secret
        )

    def to_dict(self) -> Any: ...


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class EngineGroupPermissions(IdentifiableByName):
    name: str
    group_permissions: List[str]

    @staticmethod
    def from_raw(raw: RawEngineGroupPermissions) -> 'EngineGroupPermissions':
        return EngineGroupPermissions(
            name=raw.name,
            group_permissions=raw.group_permissions
        )


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class EngineDefinition:
    engine: Engine
    secret: EngineSecret
    group_permissions: List[EngineGroupPermissions] = field(default_factory=list)

    @staticmethod
    def from_dict(dict: Dict[str, Any]) -> 'EngineDefinition': ...

