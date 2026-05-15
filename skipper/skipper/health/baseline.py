# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

import asyncio

from django.conf import settings
from django.utils import timezone
from health_check.checks import Cache, Database, Storage  # type: ignore
from health_check.contrib.redis import Redis as RedisHealthCheck  # type: ignore
from redis.asyncio import Redis as RedisClient  # type: ignore

from skipper.health.contract import ServiceWarning


def database_check() -> None:
    Database().run()


def cache_check() -> None:
    asyncio.run(Cache().run())


def default_file_storage_check() -> None:
    Storage(alias='default').run()


def s3boto3_check() -> None:
    Storage(alias='default').run()


def redis_check() -> None:
    asyncio.run(
        RedisHealthCheck(
            client_factory=lambda: RedisClient.from_url(settings.REDIS_URL)
        ).run()
    )


def celery_check() -> None:
    from celery import states  # type: ignore
    from django_celery_results.models import TaskResult  # type: ignore
    task_result_failures = frozenset({states.RETRY, states.FAILURE})  # explicitly ignore REVOKED
    found_errors = TaskResult.objects.filter(
        status__in=task_result_failures,
        date_done__gt=timezone.now() - timezone.timedelta(minutes=30)
    ).exists()
    if found_errors:
        raise ServiceWarning('there were errors in the TaskResult queue in the last 30 minutes')
