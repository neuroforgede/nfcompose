# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


from django.apps import AppConfig


class DynamicSQLAppConfig(AppConfig):
    name = 'skipper.dataseries.storage.dynamic_sql'
    label = 'skipper_dataseries_storage_dynamic_sql'
    verbose_name = 'Dynamic SQL DataSeries backend'

    def ready(self) -> None:
        from skipper.dataseries.tasks.metamodel import meta_model_task_registry
        from skipper.dataseries.storage.dynamic_sql.tasks import migrate

        migrate.register(meta_model_task_registry)