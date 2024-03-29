# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

import enum
from dataclasses import dataclass
from typing import Optional, Dict, Any

from dataclasses_json import dataclass_json, Undefined


class OperationType(enum.Enum):
    CREATE = "CREATE"
    DELETE = "DELETE"
    UPDATE = "UPDATE"


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Operation:
    operation_type: OperationType
    payload: Dict[str, Any]

    def empty(self) -> bool:
        # all operations are by definition not empty
        return False


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ExternalIdOperation:
    operation_type: OperationType
    # operations sometimes have no external_id, e.g. for EngineSecrets
    external_id: Optional[str]
    payload: Dict[str, Any]

    def empty(self) -> bool:
        # all operations are by definition not empty
        return False


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class NameOperation:
    operation_type: OperationType
    name: Optional[str]
    payload: Dict[str, Any]

    def empty(self) -> bool:
        # all operations are by definition not empty
        return False
