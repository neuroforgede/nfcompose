# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from dataclasses import dataclass, field
from typing import Optional, List, Any, Dict

from dataclasses_json import dataclass_json, Undefined

from compose_client.library.models.diff.mixin import EmptyMixin
from compose_client.library.models.operation.general import ExternalIdOperation, NameOperation


@dataclass_json(undefined=Undefined.RAISE)
@dataclass
class DataSeriesStructureDiff:
    float_facts: List[ExternalIdOperation] = field(default_factory=list)
    string_facts: List[ExternalIdOperation] = field(default_factory=list)
    text_facts: List[ExternalIdOperation] = field(default_factory=list)
    timestamp_facts: List[ExternalIdOperation] = field(default_factory=list)
    image_facts: List[ExternalIdOperation] = field(default_factory=list)
    file_facts: List[ExternalIdOperation] = field(default_factory=list)
    json_facts: List[ExternalIdOperation] = field(default_factory=list)
    boolean_facts: List[ExternalIdOperation] = field(default_factory=list)
    dimensions: List[ExternalIdOperation] = field(default_factory=list)

    def empty(self) -> bool:
        for key, value in self.__dict__.items():
            if value is None:
                continue
            for elem in value:
                if not elem.empty():
                    return False
        return True


@dataclass_json(undefined=Undefined.RAISE)
@dataclass
class DataSeriesDefinitionDiff(EmptyMixin):
    """
    A complete DataSeries Definition that we can
    instantiate on any given NF Compose instance
    """
    external_id: str
    data_series: Optional[ExternalIdOperation]
    structure: DataSeriesStructureDiff
    group_permissions: List[NameOperation] = field(default_factory=list)
    consumers: List[ExternalIdOperation] = field(default_factory=list)
    indexes: List[ExternalIdOperation] = field(default_factory=list)


    def to_dict(self) -> Any: ...
    @staticmethod
    def from_dict(dict: Dict[str, Any]) -> 'DataSeriesDefinitionDiff': ...