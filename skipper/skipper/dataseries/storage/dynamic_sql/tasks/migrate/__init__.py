# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from typing import Dict, Callable
from skipper.dataseries.models.task_data import MetaModelTaskData
from .v1_to_materialized import spawn_migrate_v1_to_materialized
from .materialized_to_no_history import spawn_migrate_materialized_to_no_history
from .no_history_to_flat_history import spawn_migrate_no_history_to_flat_history
from .flat_history_to_no_history import spawn_migrate_flat_history_to_no_history

def register(registry: Dict[str, Callable[[MetaModelTaskData], None]]) -> None:
    from skipper.dataseries.storage.dynamic_sql.tasks.migrate import v1_to_materialized
    from skipper.dataseries.storage.dynamic_sql.tasks.migrate import materialized_to_no_history
    from skipper.dataseries.storage.dynamic_sql.tasks.migrate import no_history_to_flat_history
    from skipper.dataseries.storage.dynamic_sql.tasks.migrate import flat_history_to_no_history
    
    v1_to_materialized.register(registry)
    materialized_to_no_history.register(registry)
    no_history_to_flat_history.register(registry)
    flat_history_to_no_history.register(registry)