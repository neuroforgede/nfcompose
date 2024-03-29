# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


import uuid

from typing import Any, Dict

from skipper.dataseries.storage.contract import StorageBackendType
from skipper.dataseries.storage.contract.view import StorageViewAdapter
from skipper.dataseries.storage.dynamic_sql import storage_view_adapter as dynamic_sql_views, backend_info


def storage_view_adapter(backend: StorageBackendType) -> StorageViewAdapter:
    return dynamic_sql_views.adapter()


def storage_backend_info(backend: StorageBackendType) -> Dict[str, Any]:
    return backend_info.get_backend_info()
