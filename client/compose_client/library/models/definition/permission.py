# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from dataclasses import dataclass
from typing import Dict, Any

from dataclasses_json import dataclass_json


@dataclass
@dataclass_json
class UserPermission:
    username: str
    user_permissions: Dict[str, Any]


@dataclass
@dataclass_json
class GroupPermission:
    name: str
    group_permissions: Dict[str, Any]

