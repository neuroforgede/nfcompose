# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from typing import Any

from celery.signals import task_prerun, worker_process_init  # type: ignore
from django_multitenant.utils import set_current_tenant  # type: ignore


@task_prerun.connect  # type: ignore
def clear_tenant(*args: Any, **kwargs: Any) -> None:
    # reset the current tenant just to be 100% sure
    set_current_tenant(None)


@worker_process_init.connect(weak=False)  # type: ignore
def init_celery_telemetry(*args: Any, **kwargs: Any) -> None:
    from skipper import telemetry
    telemetry.setup_telemetry_celery()
