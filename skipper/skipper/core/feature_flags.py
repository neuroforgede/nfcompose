# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


import os
from typing import Dict
from skipper.testing import SKIPPER_TESTING

try:
    from skipper.settings import FEATURE_FLAGS
except ImportError:
    FEATURE_FLAGS = {}

# DO NOT CHANGE DEFAULTS
FEATURE_FLAGS_DEFAULT: Dict[str, bool] = {
    "compose.structure.indexes": True,
    "compose.core.tenant.tenant_user": False,
    "compose.core.tenant": False,
    "compose.core.user": False,
}


def get_feature_flag(flag: str) -> bool:
    if SKIPPER_TESTING or os.getenv('SKIPPER_FEATURE_FLAG_ALL', 'False') in ['true', 'True']:
        return True
    if flag in FEATURE_FLAGS:
        return bool(FEATURE_FLAGS[flag])
    elif flag in FEATURE_FLAGS_DEFAULT:
        return bool(FEATURE_FLAGS_DEFAULT[flag])
    else:
        raise KeyError("Feature flag unknown: \'" + flag + "\'")
