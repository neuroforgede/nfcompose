# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Dict

from dataclasses_json import dataclass_json, Undefined

from compose_client.library.models.identifiable import Identifiable
from compose_client.library.models.raw.data_series import RawDataSeries


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class DataSeries(Identifiable):
    name: str
    backend: str
    extra_config: Dict[str, Any]
    allow_extra_fields: bool

    @staticmethod
    def from_raw(raw: RawDataSeries) -> 'DataSeries':
        return DataSeries(
            external_id=raw.external_id,
            name=raw.name,
            backend=raw.backend,
            extra_config=deepcopy(raw.extra_config),
            allow_extra_fields=raw.allow_extra_fields
        )

    def to_dict(self) -> Any: ...
