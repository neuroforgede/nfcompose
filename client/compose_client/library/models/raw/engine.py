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
class RawEngineGroupPermissions:
    url: REST_URL
    name: str
    fully_qualified: str
    group_permissions: List[str]

    @staticmethod
    def from_dict(dict: Dict[str, Any]) -> 'RawEngineGroupPermissions': ...


class RawEngineGroupPermissionsAPIConverter(APIConverter[RawEngineGroupPermissions]):
    def __call__(self, json: Dict[str, Any]) -> RawEngineGroupPermissions:
        return RawEngineGroupPermissions.from_dict(json)


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class RawEngineSecret:
    secret: str

    @staticmethod
    def from_dict(dict: Dict[str, Any]) -> 'RawEngineSecret': ...


class RawEngineSecretAPIConverter(APIConverter[RawEngineSecret]):
    def __call__(self, json: Dict[str, Any]) -> RawEngineSecret:
        return RawEngineSecret.from_dict(json)


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class RawEngine:
    url: REST_URL
    id: str
    external_id: str
    upstream: REST_URL
    access: REST_URL
    permission_user: REST_URL
    permission_group: REST_URL
    secret: REST_URL

    @staticmethod
    def from_dict(dict: Dict[str, Any]) -> 'RawEngine': ...


class RawEngineAPIConverter(APIConverter[RawEngine]):
    def __call__(self, json: Dict[str, Any]) -> RawEngine:
        return RawEngine.from_dict(json)
