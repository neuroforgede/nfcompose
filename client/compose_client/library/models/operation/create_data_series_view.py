# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from dataclasses import dataclass
from typing import Any, Dict

from dataclasses_json import dataclass_json, Undefined


@dataclass_json(undefined=Undefined.RAISE)
@dataclass
class DataSeriesCreateViewSettings:
    view_name: str
    overwrite: bool
    cascade_if_delete: bool
    # added in 1.6.6, defaulting to False as the API does
    identify_dimensions_by_external_id: bool = False
    # added in 1.7.1, defaulting to False as the API does
    full_history: bool = False

    def to_dict(self) -> Any: ...


@dataclass_json(undefined=Undefined.RAISE)
@dataclass
class DataSeriesCreateViewOperation:
    data_series_external_id: str
    settings: DataSeriesCreateViewSettings

    def to_dict(self) -> Any: ...

    @staticmethod
    def from_dict(dict: Dict[str, Any]) -> 'DataSeriesCreateViewOperation': ...

    def empty(self) -> bool:
        # all operations are by definition not empty
        return False
