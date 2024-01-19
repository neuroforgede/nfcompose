# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from dataclasses import dataclass
from typing import Dict, Any

from dataclasses_json import dataclass_json, Undefined

from compose_client.library.models.identifiable import Identifiable
from compose_client.library.models.raw.consumer import RawConsumer
from compose_client.library.service.url import replace_domain

REST_URL = str


@dataclass_json(undefined=Undefined.RAISE)
@dataclass
class Consumer(Identifiable):
    target: REST_URL
    name: str
    mode: str
    headers: Dict[str, Any]
    timeout: float
    retry_backoff_every: int
    retry_backoff_delay: str
    retry_max: int

    @staticmethod
    def from_raw(raw: RawConsumer, domain_aliases: Dict[str, str]) -> 'Consumer':
        return Consumer(
            external_id=raw.external_id,
            target=replace_domain(raw.target, domain_aliases),
            name=raw.name,
            mode=raw.mode,
            headers=raw.headers,
            timeout=raw.timeout,
            retry_backoff_delay=raw.retry_backoff_delay,
            retry_backoff_every=raw.retry_backoff_every,
            retry_max=raw.retry_max
        )

    def to_dict(self) -> Any: ...

