# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List

from dataclasses_json import dataclass_json, Undefined

from compose_client.library.connection.read import APIConverter

REST_URL = str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class RawDataSeriesGroupPermissions:
    url: REST_URL
    name: str
    fully_qualified: str
    group_permissions: List[str]

    @staticmethod
    def from_dict(dict: Dict[str, Any]) -> 'RawDataSeriesGroupPermissions': ...


class RawDataSeriesPermissionsAPIConverter(APIConverter[RawDataSeriesGroupPermissions]):
    def __call__(self, json: Dict[str, Any]) -> RawDataSeriesGroupPermissions:
        return RawDataSeriesGroupPermissions.from_dict(json)


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class RawDataSeries:
    url: str
    id: str
    external_id: str
    point_in_time: str
    last_modified_at: str
    name: str
    locked: bool
    backend: str
    allow_extra_fields: bool

    dimensions: REST_URL

    float_facts: REST_URL
    string_facts: REST_URL
    text_facts: REST_URL
    timestamp_facts: REST_URL
    image_facts: REST_URL
    file_facts: REST_URL
    json_facts: REST_URL
    boolean_facts: REST_URL

    consumers: REST_URL

    data_points: REST_URL
    history_data_points: REST_URL
    data_points_bulk: REST_URL
    data_point_validate_external_ids: REST_URL
    cube_sql: REST_URL
    create_view: REST_URL
    prune_history: REST_URL

    truncate: REST_URL
    permission_user: REST_URL
    permission_group: REST_URL

    data_point_structure: Dict[str, Any]


    prune_meta_model: Optional[REST_URL] = None
    # not all compose versions have this
    indexes: Optional[REST_URL] = None
    extra_config: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def from_dict(dict: Dict[str, Any]) -> 'RawDataSeries': ...


class RawDataSeriesAPIConverter(APIConverter[RawDataSeries]):
    def __call__(self, json: Dict[str, Any]) -> RawDataSeries:
        return RawDataSeries.from_dict(json)
