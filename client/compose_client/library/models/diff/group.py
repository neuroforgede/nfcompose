# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from dataclasses import dataclass
from typing import Optional, Dict, Any

from dataclasses_json import dataclass_json, Undefined

from compose_client.library.models.diff.mixin import list_empty
from compose_client.library.models.operation.general import NameOperation, Operation


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class GroupDefinitionDiff:
    """
    A complete Group Definition that we can
    instantiate on any given NF Compose instance
    """
    name: str
    group: Optional[NameOperation]
    group_permissions: Optional[Operation]

    @staticmethod
    def from_dict(dict: Dict[str, Any]) -> 'GroupDefinitionDiff': ...

    def empty(self) -> bool:
        for key, value in self.__dict__.items():
            if key != 'name':
                if isinstance(value, list):
                    if not list_empty(value):
                        return False
                elif value is not None and not value.empty():
                    return False
        return True
