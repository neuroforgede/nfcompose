# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from django.conf import settings
from typing import Dict


def sanitize_cookies(cookies: Dict[str, str]) -> str:
    return "; ".join([
        str(x) + "=" + str(y) for x, y in cookies.items() if x not in [
            settings.SESSION_COOKIE_NAME
        ]
    ])
