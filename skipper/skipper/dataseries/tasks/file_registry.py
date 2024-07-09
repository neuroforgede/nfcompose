# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

import datetime
from django.utils import timezone
from django_multitenant.utils import set_current_tenant  # type: ignore

from skipper.environment import SKIPPER_CELERY_FILE_REGISTRY_CLEANUP_MAX_AGE_HOURS
from skipper.core.celery import task
from skipper.core.models import default_media_storage
from skipper.core.models.tenant import Tenant
from skipper.dataseries.storage.contract import file_registry


@task(name='_3_actual_file_registry_cleanup', queue='file_registry_cleanup', ignore_result=True)  # type: ignore
def actual_file_registry_cleanup() -> None:
    file_registry.garbage_collect(
        storage=default_media_storage,
        older_than=datetime.datetime.now() - timezone.timedelta(hours=SKIPPER_CELERY_FILE_REGISTRY_CLEANUP_MAX_AGE_HOURS)
    )


@task(name="_3_wake_up_file_registry_cleanup", queue='file_registry_cleanup', ignore_result=True)  # type: ignore
def wake_up_file_registry_cleanup() -> None:
    actual_file_registry_cleanup.delay()
