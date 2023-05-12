# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from dataclasses import dataclass
from typing import Type, Dict, Any, cast, TypeVar

from dataclasses_json import dataclass_json, Undefined

from compose_client.library.connection.read import APIConverter

REST_URL = str


@dataclass
class _BaseRawFact:
    url: REST_URL
    id: str
    point_in_time: str
    last_modified_at: str
    name: str
    optional: bool
    external_id: str


@dataclass_json(undefined=Undefined.RAISE)
@dataclass
class RawFloatFact(_BaseRawFact):
    pass


@dataclass_json(undefined=Undefined.RAISE)
@dataclass
class RawStringFact(_BaseRawFact):
    pass


@dataclass_json(undefined=Undefined.RAISE)
@dataclass
class RawTextFact(_BaseRawFact):
    pass


@dataclass_json(undefined=Undefined.RAISE)
@dataclass
class RawTimestampFact(_BaseRawFact):
    pass


@dataclass_json(undefined=Undefined.RAISE)
@dataclass
class RawImageFact(_BaseRawFact):
    pass


@dataclass_json(undefined=Undefined.RAISE)
@dataclass
class RawFileFact(_BaseRawFact):
    pass


@dataclass_json(undefined=Undefined.RAISE)
@dataclass
class RawJsonFact(_BaseRawFact):
    pass


@dataclass_json(undefined=Undefined.RAISE)
@dataclass
class RawBooleanFact(_BaseRawFact):
    pass


__BaseRawFact = TypeVar('__BaseRawFact', bound=_BaseRawFact)


def raw_fact_api_converter(fact_type: Type[__BaseRawFact]) -> APIConverter[__BaseRawFact]:
    class ActualConverter(APIConverter[__BaseRawFact]):
        def __call__(self, json: Dict[str, Any]) -> '__BaseRawFact':
            return cast('__BaseRawFact', cast(Any, fact_type).from_dict(json))

    return ActualConverter()
