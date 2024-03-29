# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from skipper.dataseries.storage.contract import StorageBackendType
from skipper.dataseries.storage.contract.repository import Repository

from skipper.dataseries.storage.dynamic_sql import repository as dynamic_sql_repository


def repository(backend: StorageBackendType) -> Repository:
    return dynamic_sql_repository.DynamicSQLRepository()
