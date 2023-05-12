# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from typing import Optional
import datetime
from django.utils import timezone
from django_multitenant.utils import set_current_tenant  # type: ignore

from skipper.core.celery import task
from skipper.core.models import default_media_storage
from skipper.core.models.tenant import Tenant
from skipper.dataseries.storage.contract import file_registry


@task(name='_3_actual_file_registry_cleanup', queue='file_registry_cleanup', ignore_result=True)  # type: ignore
def actual_file_registry_cleanup() -> None:
    file_registry.garbage_collect(
        storage=default_media_storage,
        older_than=datetime.datetime.now() - timezone.timedelta(days=7)
    )


@task(name="_3_wake_up_file_registry_cleanup", queue='file_registry_cleanup', ignore_result=True)  # type: ignore
def wake_up_file_registry_cleanup() -> None:
    actual_file_registry_cleanup.delay()
