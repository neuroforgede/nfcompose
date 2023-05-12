# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from django.utils import timezone
from health_check.cache.backends import CacheBackend  # type: ignore
from health_check.contrib.redis.backends import RedisHealthCheck  # type: ignore
from health_check.contrib.s3boto3_storage.backends import S3Boto3StorageHealthCheck  # type: ignore
from health_check.db.backends import DatabaseBackend  # type: ignore
from health_check.storage.backends import DefaultFileStorageHealthCheck  # type: ignore

from skipper.health.contract import ServiceWarning


def database_check() -> None:
    backend = DatabaseBackend()
    backend.check_status()


def cache_check() -> None:
    backend = CacheBackend()
    backend.check_status()


def default_file_storage_check() -> None:
    backend = DefaultFileStorageHealthCheck()
    backend.check_status()


def s3boto3_check() -> None:
    backend = S3Boto3StorageHealthCheck()
    backend.check_status()


def redis_check() -> None:
    backend = RedisHealthCheck()
    backend.check_status()


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
