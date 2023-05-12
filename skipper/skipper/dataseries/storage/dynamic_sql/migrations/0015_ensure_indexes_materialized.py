# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from django.apps.registry import Apps
from django.db import migrations
from django.db.migrations import RunPython
from typing import Any

from skipper.dataseries.storage.dynamic_sql.migrations.custom_v1 import helpers


def migrate_materialized_dataseries_indexes(apps: Apps, schema_editor: Any) -> Any:
    DataSeries = apps.get_model('dataseries', 'DataSeries')
    for dataseries in DataSeries.all_objects.all():
        if dataseries.backend == 'DYNAMIC_SQL_MATERIALIZED':
            helpers.ensure_indexes_materialized_old(
                data_series_id=dataseries.id,
                data_series_external_id=dataseries.external_id,
                tenant_name=dataseries.tenant.name
            )


class Migration(migrations.Migration):
    atomic = True

    dependencies = [
        ('skipper_dataseries_storage_dynamic_sql', '0014_consumer'),
        ('dataseries', '0023_consumerevent'),
    ]

    replaces = [
        ('skipper.dataseries.storage.dynamic_sql', '0015_ensure_indexes_materialized')
    ]

    operations = [
            RunPython(migrate_materialized_dataseries_indexes),
    ]
