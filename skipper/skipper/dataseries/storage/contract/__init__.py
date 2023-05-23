# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from itertools import chain
from enum import Enum, unique
from typing import Tuple, Set
from skipper.testing import SKIPPER_CELERY_TESTING


class StorageBackendType(Enum):
    # default should always be the first, so DRF displays it by default in the UI
    DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY = "DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY"
    DYNAMIC_SQL_NO_HISTORY = "DYNAMIC_SQL_NO_HISTORY"
    DYNAMIC_SQL_MATERIALIZED = "DYNAMIC_SQL_MATERIALIZED"
    DYNAMIC_SQL_V1 = 'DYNAMIC_SQL_V1'

    @classmethod
    def choices(cls) -> Tuple[Tuple[str, str], ...]:
        return tuple((i.name, i.value) for i in cls)

    @classmethod
    def choices_with_history(cls) -> Tuple[Tuple[str, str], ...]:
        return tuple(x for x in cls.choices() if x[0] != 'DYNAMIC_SQL_NO_HISTORY')

    @classmethod
    def choices_with_split_history(cls) -> Tuple[Tuple[str, str], ...]:
        return tuple(x for x in cls.choices() if x[0] != 'DYNAMIC_SQL_NO_HISTORY'
                     and x[0] != 'DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY')

    @classmethod
    def choices_without_history(cls) -> Tuple[Tuple[str, str], ...]:
        return tuple((i.name, i.value) for i in [
            cls.DYNAMIC_SQL_NO_HISTORY
        ])

    def has_history(self) -> bool:
        return self.value != StorageBackendType.DYNAMIC_SQL_NO_HISTORY.value

    @staticmethod
    def from_string(string: str) -> 'StorageBackendType':
        if string == "DYNAMIC_SQL_MATERIALIZED":
            return StorageBackendType.DYNAMIC_SQL_MATERIALIZED
        elif string == "DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY":
            return StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY
        elif string == "DYNAMIC_SQL_V1":
            return StorageBackendType.DYNAMIC_SQL_V1
        elif string == "DYNAMIC_SQL_NO_HISTORY":
            return StorageBackendType.DYNAMIC_SQL_NO_HISTORY
        else:
            raise AssertionError('unrecognized StorageBackendType: ' + string)


deprecated_backend_strings: Set[str] = {
    StorageBackendType.DYNAMIC_SQL_V1.name,
    StorageBackendType.DYNAMIC_SQL_MATERIALIZED.name
}

# if we are testing, we should still be allowed to create the deprecated backends
# when the test requires it
if SKIPPER_CELERY_TESTING:
    deprecated_backend_strings = set()


def backend_is_deprecated(backend: str) -> bool:
    return backend in deprecated_backend_strings


selectable_storage_backend_types: Tuple[Tuple[str, str], ...] = \
    tuple([elem for elem in StorageBackendType.choices() if not backend_is_deprecated(elem[0])])
default_backend: StorageBackendType = StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY

@unique
class FactType(Enum):
    Float = "FLOAT_FACT"
    String = "STRING_FACT"
    Text = "TEXT_FACT"
    Timestamp = "TIMESTAMP_FACT"
    Image = "IMAGE_FACT"
    JSON = "JSON_FACT"
    Boolean = "BOOLEAN_FACT"
    File = "FILE_FACT"

@unique
class IndexableDataSeriesChildType(Enum):
    FLOAT_FACT = "FLOAT_FACT"
    STRING_FACT = "STRING_FACT"
    TEXT_FACT = "TEXT_FACT"
    TIMESTAMP_FACT = "TIMESTAMP_FACT"
    IMAGE_FACT = "IMAGE_FACT"
    JSON_FACT = "JSON_FACT"
    BOOLEAN_FACT = "BOOLEAN_FACT"
    FILE_FACT = "FILE_FACT"

    DIMENSION = "DIMENSION"

    @classmethod
    def choices(cls) -> Tuple[Tuple[str, str], ...]:
        return tuple((i.name, i.value) for i in cls)


if __name__ == "__main__":
    print(FactType(1))
