# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from django.apps import AppConfig


class HealthCheckConfig(AppConfig):
    name = 'skipper.health'

    def ready(self) -> None:
        pass
        # from skipper.health import baseline
        # from skipper.health.contract import register_health_check
        # # register base line healthchecks
        # register_health_check(
        #     'core.cache', baseline.cache_check
        # )
        # register_health_check(
        #     'core.database', baseline.database_check
        # )
        # register_health_check(
        #     'core.default_file_storage', baseline.default_file_storage_check
        # )
        # register_health_check(
        #     'core.redis', baseline.redis_check
        # )
        # register_health_check(
        #     'core.s3boto3', baseline.s3boto3_check
        # )
        # register_health_check(
        #     'core.celery', baseline.celery_check
        # )
