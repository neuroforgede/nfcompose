# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


import os
from typing import Dict

FEATURE_FLAGS: Dict[str, bool] = {
    "compose.structure.indexes": os.getenv('SKIPPER_FEATURE_FLAG_DATA_SERIES_INDEX', 'True') in ['true', 'True'],
    "compose.core.tenant.tenant_user": os.getenv('SKIPPER_FEATURE_FLAG_CORE_TENANT_USER', 'False') in ['true', 'True'],
    "compose.core.tenant": os.getenv('SKIPPER_FEATURE_FLAG_CORE_TENANT', 'False') in ['true', 'True'],
    "compose.core.user": os.getenv('SKIPPER_FEATURE_FLAG_CORE_USER', 'False') in ['true', 'True'],
}

