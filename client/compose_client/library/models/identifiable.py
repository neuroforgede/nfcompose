# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from dataclasses import dataclass
from typing import Any


@dataclass
class Identifiable:
    """
    base class for everything that has external_id

    We need this because Protocols and Generics dont match
    that nicely. see diff service for usage of this base class
    """
    external_id: str

    def to_dict(self) -> Any: ...
    def __eq__(self, other: Any) -> bool: ...


@dataclass
class IdentifiableByName:
    """
    base class for everything that has external_id

    We need this because Protocols and Generics dont match
    that nicely. see diff service for usage of this base class
    """
    name: str

    def to_dict(self) -> Any: ...
    def __eq__(self, other: Any) -> bool: ...

