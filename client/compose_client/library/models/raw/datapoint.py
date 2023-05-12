# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from dataclasses import dataclass
from typing import Dict, Any

from dataclasses_json import Undefined, dataclass_json

from compose_client.library.connection.read import APIConverter

REST_URL = str


@dataclass_json(undefined=Undefined.RAISE)
@dataclass
class RawDataPoint:
    url: str
    history_url: REST_URL
    id: str
    external_id: str
    point_in_time: str
    payload: Dict[str, Any]

    @staticmethod
    def from_dict(dict: Dict[str, Any]) -> 'RawDataPoint': ...


class RawDataPointAPIConverter(APIConverter[RawDataPoint]):
    def __call__(self, json: Dict[str, Any]) -> RawDataPoint:
        return RawDataPoint.from_dict(json)
