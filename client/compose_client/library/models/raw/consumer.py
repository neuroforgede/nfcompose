# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from dataclasses import dataclass
from typing import Dict, Any

from dataclasses_json import dataclass_json, Undefined

from compose_client.library.connection.read import APIConverter

REST_URL = str


@dataclass_json(undefined=Undefined.RAISE)
@dataclass
class RawConsumer:
    external_id: str
    target: REST_URL
    name: str
    headers: Dict[str, Any]
    timeout: float
    retry_backoff_every: int
    retry_backoff_delay: str
    retry_max: int
    mode: str

    url: REST_URL
    id: str
    point_in_time: str
    last_modified_at: str
    health: str
    events: REST_URL

    @staticmethod
    def from_dict(dict: Dict[str, Any]) -> 'RawConsumer': ...


class ConsumerConverter(APIConverter[RawConsumer]):
    def __call__(self, json: Dict[str, Any]) -> 'RawConsumer':
        return RawConsumer.from_dict(json)