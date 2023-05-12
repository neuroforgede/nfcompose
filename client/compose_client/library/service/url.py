# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from typing import Dict
from urllib.parse import urlparse, urlunparse


def replace_domain(url: str, domain_aliases: Dict[str, str]) -> str:
    upstream = url
    parsed_upstream = urlparse(upstream)
    if parsed_upstream.netloc in domain_aliases:
        return urlunparse(parsed_upstream._replace(netloc=domain_aliases[parsed_upstream.netloc]))
    return url
