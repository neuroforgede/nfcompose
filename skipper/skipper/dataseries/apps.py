# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from django.apps import AppConfig


class DataSeriesConfig(AppConfig):
    name = 'skipper.dataseries'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self) -> None:
        from skipper.dataseries import healthcheck
        healthcheck.register_health_checks()
