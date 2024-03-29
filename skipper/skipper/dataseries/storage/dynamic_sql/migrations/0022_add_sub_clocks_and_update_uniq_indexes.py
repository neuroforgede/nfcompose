# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

import uuid
from django.apps.registry import Apps
from django.db import migrations, connections
from typing import Optional, List, Any, Union

from skipper.dataseries.raw_sql import escape
from skipper.dataseries.raw_sql.tenant import escaped_tenant_schema, ensure_schema
from skipper.dataseries.storage.dynamic_sql.materialized import materialized_table_name
from skipper.modules import Module
from skipper.settings import DATA_SERIES_DYNAMIC_SQL_DB


def add_sub_clock_to_materialized(
        data_series_id: Union[str, uuid.UUID],
        data_series_external_id: str,
        tenant_name: str
) -> None:
    schema_name = escaped_tenant_schema(tenant_name)
    ensure_schema(schema_name, connection_name=DATA_SERIES_DYNAMIC_SQL_DB)
    table_name_unescaped = materialized_table_name(data_series_id, data_series_external_id)
    table_name = escape.escape(table_name_unescaped)
    with connections[DATA_SERIES_DYNAMIC_SQL_DB].cursor() as cursor:
        queries = [
            f"""
            ALTER TABLE {schema_name}.{table_name}
            ADD COLUMN IF NOT EXISTS sub_clock bigint NULL;
            """
        ]

        for query in queries:
            cursor.execute(query)


def migrate_materialized_dataseries_indexes(apps: Apps, schema_editor: Any) -> Any:
    Tenant = apps.get_model('core', 'Tenant')
    for tenant in Tenant.all_objects.all():
        schema_name = escaped_tenant_schema(tenant.name)
        # simply ensure the schema, we create the sequences inside
        ensure_schema(schema_name, connection_name=DATA_SERIES_DYNAMIC_SQL_DB)
        DataSeries = apps.get_model('dataseries', 'DataSeries')
        for dataseries in DataSeries.all_objects.all():
            if dataseries.backend == 'DYNAMIC_SQL_NO_HISTORY':
                add_sub_clock_to_materialized(dataseries.id, dataseries.external_id, dataseries.tenant.name)


class Migration(migrations.Migration):
    atomic = True

    dependencies = [
        ('skipper_dataseries_storage_dynamic_sql', '0021_fix_sdel_triggers_for_dataseries_children'),
    ]

    operations: List[Any] = (
            [
                migrations.RunPython(migrate_materialized_dataseries_indexes)
            ]
    )
