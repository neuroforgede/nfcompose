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


def migrate_materialized_dataseries_deleted_at_data(apps: Apps, schema_editor: Any) -> Any:
    DataSeries = apps.get_model('dataseries', 'DataSeries')
    for dataseries in DataSeries.all_objects.all():
        if dataseries.backend == 'DYNAMIC_SQL_NO_HISTORY' or dataseries.backend == 'DYNAMIC_SQL_MATERIALIZED':
            if dataseries.metamodel_version == 1:
                from django.db import migrations, connections

                from skipper.dataseries.raw_sql import escape
                from skipper.dataseries.raw_sql.tenant import escaped_tenant_schema, ensure_schema, tenant_schema_unescaped
                from skipper.dataseries.storage.dynamic_sql.materialized import materialized_table_name
                from skipper.settings import DATA_SERIES_DYNAMIC_SQL_DB

                schema_name = escaped_tenant_schema(dataseries.tenant.name)
                ensure_schema(schema_name, connection_name=DATA_SERIES_DYNAMIC_SQL_DB)
                table_name_unescaped = materialized_table_name(dataseries.id, dataseries.external_id)
                table_name = escape.escape(table_name_unescaped)
                with connections[DATA_SERIES_DYNAMIC_SQL_DB].cursor() as cursor:
                    cursor.execute("""
                            SELECT count(1)
                            FROM   pg_tables 
                            WHERE  schemaname = %s
                            AND    tablename = %s
                        """, [
                        tenant_schema_unescaped(dataseries.tenant.name),
                        table_name_unescaped
                    ])
                    exists = cursor.fetchone()[0] == 1
                    if exists:
                        # welp. add it so the next thing does not die
                        # anything starting at metamodel version 2 will not have this anymore
                        cursor.execute(f"""
                            ALTER TABLE IF EXISTS {schema_name}.{table_name}
                                ADD COLUMN IF NOT EXISTS deleted_at timestamptz DEFAULT NULL
                            """)
                        helpers.ensure_indexes_materialized_v2(
                            data_series_id=dataseries.id,
                            data_series_external_id=dataseries.external_id,
                            tenant_name=dataseries.tenant.name
                        )


class Migration(migrations.Migration):
    atomic = True

    dependencies = [
        ('skipper_dataseries_storage_dynamic_sql', '0019_fix_partition_lookup_migrate_for_floatfact'),
        ('dataseries', '0063_auto_20201220_0007'),
    ]

    replaces = [
        ('skipper.dataseries.storage.dynamic_sql', '0020_migrate_all_materialized_dataseries_add_del_bool_col')
    ]

    operations = [
            RunPython(migrate_materialized_dataseries_deleted_at_data),
    ]
