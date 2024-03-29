# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

import json
from typing import Dict, Optional


def invert_dict(d: Dict[str, str]) -> Optional[Dict[str, str]]:
    out = dict()
    for k, v in d.items():
        if v in out:
            return None
        out[v] = k
    return out


def parse_domain_aliases(domain_aliases_str: str) -> Dict[str, str]:
    domain_aliases_obj = {}
    if domain_aliases_str is not None:
        domain_aliases_obj = json.loads(domain_aliases_str)

        if not isinstance(domain_aliases_obj, Dict):
            raise AssertionError('domain_aliases was no dictionary')

        for _, v in domain_aliases_obj.items():
            if not isinstance(v, str):
                raise AssertionError('domain_aliases must be a mapping from str to str')

    return domain_aliases_obj
