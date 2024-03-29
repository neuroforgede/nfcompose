# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from typing import Dict, Callable, cast

from skipper import settings
from skipper.health import contract
import requests


def get_nodered_instances() -> Dict[str, Dict[str, str]]:
    return cast(Dict[str, Dict[str, str]], getattr(settings, 'SKIPPER_NODE_RED_UPSTREAMS', {}))


def nodered_health_check(url: str) -> Callable[[], None]:
    def _check() -> None:
        try:
            # small timeout, this is not a big task to ask
            response = requests.get(url, timeout=15)
            response.raise_for_status()
        except:
            raise contract.ServiceUnavailable('could not get a HTTP 200 from the default Node-RED upstream')
    return _check


def register_health_checks() -> None:
    for key, nr_config in get_nodered_instances().items():
        contract.register_health_check(f'flow.nodered.{key}.reachable', nodered_health_check(nr_config['internal_url']))
