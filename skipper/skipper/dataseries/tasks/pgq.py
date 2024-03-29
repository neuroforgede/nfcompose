# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

import logging

from pgq.exceptions import PgqException
from typing import Callable, Set, Any, Optional, Tuple, Dict

from skipper.core.models.postgres_jobs import BaseTenantQueue, TenantAtLeastOnceQueue, TenantPostgresQueueJob, TenantAtMostOnceQueue
from skipper.core.models.tenant import Tenant

logger = logging.getLogger(__name__)


def get_queue_name(var_key: str, queue_base_name: str) -> str:
    queue_name = f'{var_key}_{queue_base_name}'
    assert len(queue_name) <= 1024
    return queue_name


def get_queue(
    tenant: Tenant,
    var_key: str,
    queue_base_name: str, 
    tasks: Dict[str, Callable[[BaseTenantQueue, TenantPostgresQueueJob], Any]],
    heartbeat: bool,
    at_most_once: bool
) -> BaseTenantQueue:
    # use the at most once queue so we get proper internal behaviour if delivery of events
    # has worked but just the task died
    if at_most_once:
        return TenantAtMostOnceQueue(
            tasks=tasks,
            queue=get_queue_name(var_key, queue_base_name),
            tenant=tenant,
            heartbeat=heartbeat
        )
    else:
        return TenantAtLeastOnceQueue(
            tasks=tasks,
            queue=get_queue_name(var_key, queue_base_name),
            tenant=tenant,
            heartbeat=heartbeat
        )


def try_run_all(queue: BaseTenantQueue) -> None:
    failed_ids: Set[Any] = set()

    def try_run() -> Optional[Tuple[TenantPostgresQueueJob, Any]]:
        try:
            return queue.run_once(exclude_ids=failed_ids)
        except PgqException as e:
            import traceback
            traceback.print_exc()
            logger.warn(e)
            if e.job is not None:
                failed_ids.add(e.job.id)
            return None

    job = try_run()
    while job is not None:
        job = try_run()