# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from dataclasses import dataclass, field
from typing import List, Dict, Any

from dataclasses_json import dataclass_json, Undefined

from compose_client.library.models.definition.consumer import Consumer
from compose_client.library.models.definition.data_series import DataSeries
from compose_client.library.models.definition.dimension import Dimension
from compose_client.library.models.definition.facts import FloatFact, StringFact, TextFact, TimestampFact, ImageFact, FileFact, JsonFact, \
    BooleanFact
from compose_client.library.models.definition.index import Index
from compose_client.library.models.identifiable import IdentifiableByName
from compose_client.library.models.raw.data_series import RawDataSeriesGroupPermissions


@dataclass_json(undefined=Undefined.RAISE)
# not frozen to be not annoying to write tests for
@dataclass
class DataSeriesStructure:
    float_facts: List[FloatFact] = field(default_factory=list)
    string_facts: List[StringFact] = field(default_factory=list)
    text_facts: List[TextFact] = field(default_factory=list)
    timestamp_facts: List[TimestampFact] = field(default_factory=list)
    image_facts: List[ImageFact] = field(default_factory=list)
    file_facts: List[FileFact] = field(default_factory=list)
    json_facts: List[JsonFact] = field(default_factory=list)
    boolean_facts: List[BooleanFact] = field(default_factory=list)
    dimensions: List[Dimension] = field(default_factory=list)


@dataclass_json(undefined=Undefined.RAISE)
@dataclass
class DataSeriesGroupPermissions(IdentifiableByName):
    name: str
    group_permissions: List[str]

    @staticmethod
    def from_raw(raw: RawDataSeriesGroupPermissions) -> 'DataSeriesGroupPermissions':
        return DataSeriesGroupPermissions(
            name=raw.name,
            group_permissions=raw.group_permissions
        )


@dataclass_json(undefined=Undefined.RAISE)
@dataclass
class DataSeriesDefinition:
    """
    A complete DataSeries Definition that we can
    instantiate on any given NF Compose instance
    """
    data_series: DataSeries
    structure: DataSeriesStructure
    consumers: List[Consumer] = field(default_factory=list)
    indexes: List[Index] = field(default_factory=list)
    group_permissions: List[DataSeriesGroupPermissions] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]: ...
    @staticmethod
    def from_dict(dict: Dict[str, Any]) -> 'DataSeriesDefinition': ...

