# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from dataclasses import dataclass
from typing import Callable, Any, Dict, Union, cast

from dataclasses_json import dataclass_json, Undefined

from compose_client.library.models.identifiable import Identifiable
from compose_client.library.models.raw.facts import RawFloatFact, RawStringFact, RawTextFact, RawTimestampFact, RawImageFact, RawFileFact, \
    RawJsonFact, RawBooleanFact


@dataclass
class BaseFact(Identifiable):
    name: str
    optional: bool

    def to_dict(self) -> Any: ...


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class FloatFact(BaseFact):

    @staticmethod
    def from_raw(raw: RawFloatFact) -> 'FloatFact':
        return FloatFact(
            external_id=raw.external_id,
            name=raw.name,
            optional=raw.optional
        )


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class StringFact(BaseFact):

    @staticmethod
    def from_raw(raw: RawStringFact) -> 'StringFact':
        return StringFact(
            external_id=raw.external_id,
            name=raw.name,
            optional=raw.optional
        )


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class TextFact(BaseFact):

    @staticmethod
    def from_raw(raw: RawTextFact) -> 'TextFact':
        return TextFact(
            external_id=raw.external_id,
            name=raw.name,
            optional=raw.optional
        )


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class TimestampFact(BaseFact):

    @staticmethod
    def from_raw(raw: RawTimestampFact) -> 'TimestampFact':
        return TimestampFact(
            external_id=raw.external_id,
            name=raw.name,
            optional=raw.optional
        )


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ImageFact(BaseFact):

    @staticmethod
    def from_raw(raw: RawImageFact) -> 'ImageFact':
        return ImageFact(
            external_id=raw.external_id,
            name=raw.name,
            optional=raw.optional
        )


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class FileFact(BaseFact):

    @staticmethod
    def from_raw(raw: RawFileFact) -> 'FileFact':
        return FileFact(
            external_id=raw.external_id,
            name=raw.name,
            optional=raw.optional
        )


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class JsonFact(BaseFact):

    @staticmethod
    def from_raw(raw: RawJsonFact) -> 'JsonFact':
        return JsonFact(
            external_id=raw.external_id,
            name=raw.name,
            optional=raw.optional
        )


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class BooleanFact(BaseFact):

    @staticmethod
    def from_raw(raw: RawBooleanFact) -> 'BooleanFact':
        return BooleanFact(
            external_id=raw.external_id,
            name=raw.name,
            optional=raw.optional
        )


FactType = Union[
    FloatFact,
    StringFact,
    TextFact,
    TimestampFact,
    ImageFact,
    FileFact,
    JsonFact,
    BooleanFact
]

# TODO: enforce types when parsing!
from_dict: Callable[[str], Callable[[Dict[str, Any]], FactType]] = lambda type_key: {
    'float': lambda x: cast(FactType, FloatFact(**x)),
    'string': lambda x: StringFact(**x),
    'text': lambda x: TextFact(**x),
    'timestamp': lambda x: TimestampFact(**x),
    'image': lambda x: ImageFact(**x),
    'file': lambda x: FileFact(**x),
    'json': lambda x: JsonFact(**x),
    'boolean': lambda x: BooleanFact(**x)
}[type_key]

to_dict: Callable[[str], Callable[[FactType], Dict[str, Any]]] = lambda type_key: {
    'float': lambda x: x.to_dict(),
    'string': lambda x: x.to_dict(),
    'text': lambda x: x.to_dict(),
    'timestamp': lambda x: x.to_dict(),
    'image': lambda x: x.to_dict(),
    'file': lambda x: x.to_dict(),
    'json': lambda x: x.to_dict(),
    'boolean': lambda x: x.to_dict(),
}[type_key]
