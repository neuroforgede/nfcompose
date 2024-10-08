# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from dataclasses import dataclass, field
from typing import Any, List, Dict, Union, BinaryIO, TYPE_CHECKING

from dataclasses_json import dataclass_json, Undefined

from compose_client.library.models.definition.data_series_definition import DataSeriesDefinition
from compose_client.library.models.identifiable import Identifiable
from compose_client.library.models.raw.datapoint import RawDataPoint


# explicitly no dataclass so we dont forget to implement a proper serializer
class FileTypeContent:
    url: str

    def __init__(self, url: str):
        self.url = url


# typing below the first level is subpar, but this is the best we can do for now
Primitive = Union[str, float, int, bool, Dict[str, Any], List[Any]]

if TYPE_CHECKING:
    PayloadType = Dict[str, Union[Primitive, FileTypeContent, BinaryIO]]
else:
    PayloadType = dict


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class DataPoint(Identifiable):
    external_id: str
    payload: PayloadType = field(default_factory=dict)
    identify_dimensions_by_external_id: bool = field(default=True)

    @staticmethod
    def from_raw(raw: RawDataPoint, definition: DataSeriesDefinition) -> 'DataPoint':
        payload = raw.payload.copy()
        for file_like_fact in [*definition.structure.file_facts, *definition.structure.image_facts]:
            if file_like_fact.external_id in payload:
                payload[file_like_fact.external_id] = FileTypeContent(url=payload[file_like_fact.external_id])
        return DataPoint(
            external_id=raw.external_id,
            payload=payload
        )

    def to_dict(self) -> Any: ...

    @staticmethod
    def from_dict(dict: Dict[str, Any]) -> 'DataPoint': ...
