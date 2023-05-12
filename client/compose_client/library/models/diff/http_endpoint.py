# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

from dataclasses_json import dataclass_json, Undefined

from compose_client.library.models.diff.mixin import EmptyMixin
from compose_client.library.models.operation.general import ExternalIdOperation, NameOperation


@dataclass_json(undefined=Undefined.RAISE)
@dataclass
class HttpEndpointDefinitionDiff(EmptyMixin):
    """
    A complete DataSeries Definition that we can
    instantiate on any given NF Compose instance
    """
    external_id: str
    http_endpoint: Optional[ExternalIdOperation]
    group_permissions: List[NameOperation] = field(default_factory=list)

    @staticmethod
    def from_dict(dict: Dict[str, Any]) -> 'HttpEndpointDefinitionDiff': ...

