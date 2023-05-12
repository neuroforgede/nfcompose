# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from django.apps.registry import Apps
from django.db import migrations
from typing import Any, Optional, List

from skipper.dataseries.storage.dynamic_sql.migrations.custom_v1 import helpers
from skipper.modules import Module

"""
This migration exploits postgres internals.
If you need any of this ever again, make sure that all views
that depend on any of this are recreated properly afterwards.

THIS ONLY WORKS FOR VARCHARs because the layout on disk is the same
"""


def migration_widen_col_def(
        data_name: str,
        fact_name_ds_rel: str,
        fact_model_name: str,
        value_name: str = 'value',
) -> List[Any]:
    relevant_table_name = f'data_point_{data_name}'

    def tbl_name(prefix: Optional[str] = None) -> str:
        actual_prefix = ''
        if prefix is not None:
            actual_prefix = f'_{prefix}'
        return f'_{str(Module.DATA_SERIES.value)}{actual_prefix}_{relevant_table_name}'

    def widen_materialized_tables(apps: Apps, schema_editor: Any) -> Any:
        from skipper.dataseries.storage.dynamic_sql.materialized import \
            materialized_table_name, materialized_column_name
        from django.db import connections
        from skipper.dataseries.raw_sql import escape
        from skipper.settings import DATA_SERIES_DYNAMIC_SQL_DB
        from skipper.dataseries.raw_sql.tenant import escaped_tenant_schema, ensure_schema

        DataSeries = apps.get_model('dataseries', 'DataSeries')
        FactModel = apps.get_model('dataseries', fact_model_name)

        for dataseries in DataSeries.all_objects.all():
            if dataseries.backend == 'DYNAMIC_SQL_MATERIALIZED':
                table_name_unescaped = materialized_table_name(str(dataseries.id), str(dataseries.external_id))
                table_name = escape.escape(table_name_unescaped)
                schema_name = escaped_tenant_schema(dataseries.tenant.name)

                changed_one = False
                for fact in FactModel.objects.filter(
                        **{
                            f'dataseries_{fact_name_ds_rel}__data_series': dataseries
                        }
                ).all():
                    external_id = getattr(fact, f'dataseries_{fact_name_ds_rel}').external_id
                    ensure_schema(schema_name, connection_name=DATA_SERIES_DYNAMIC_SQL_DB)
                    with connections[DATA_SERIES_DYNAMIC_SQL_DB].cursor() as cursor:
                        cursor.execute(
                            f"""
                            ALTER TABLE {schema_name}.{table_name}
                            ALTER COLUMN {escape.escape(materialized_column_name(fact.id, external_id))} TYPE TEXT;
                            """
                        )
                    changed_one = True

                if changed_one:
                    # we changed a lot of things in the internal schema, so be sure to reindex the table
                    with connections[DATA_SERIES_DYNAMIC_SQL_DB].cursor() as cursor:
                        cursor.execute(f"""
                        REINDEX TABLE {schema_name}.{table_name};
                        """)

    def keep_track_of_old_views(apps: Apps, schema_editor: Any) -> Any:
        from django.db import connections
        from skipper.settings import DATA_SERIES_DYNAMIC_SQL_DB
        from skipper.dataseries.raw_sql import escape

        DataSeries = apps.get_model('dataseries', 'DataSeries')
        FactModel = apps.get_model('dataseries', fact_model_name)

        with connections[DATA_SERIES_DYNAMIC_SQL_DB].cursor() as cursor:
            cursor.execute("""
                DROP TABLE IF EXISTS _tmp_views_to_recreate;
                CREATE TABLE _tmp_views_to_recreate (
                    schemaname TEXT,
                    viewname TEXT,
                    definition TEXT
                );
                """)
            for dataseries in DataSeries.all_objects.all():
                for fact in FactModel.all_objects.filter(
                        **{
                            f'dataseries_{fact_name_ds_rel}__data_series': dataseries
                        }
                ).all():
                    # TODO: meh. we are not using proper escaped data, but the fact ids are uuids
                    cursor.execute(f"""
                        INSERT INTO _tmp_views_to_recreate(
                            schemaname, viewname, definition
                        )
                        SELECT schemaname, viewname, definition
                        FROM    pg_catalog.pg_views
                        WHERE   schemaname  LIKE '_3_tenant_%' 
                        AND     definition  LIKE'%{str(fact.id)}%';
                        """)
            cursor.execute(f"""
                SELECT schemaname, viewname, definition
                FROM    _tmp_views_to_recreate;
                """)
            views_to_recreate = cursor.fetchall()
            for elem in views_to_recreate:
                schemaname, viewname, definition = elem
                cursor.execute(
                    f"""
                    DROP VIEW {escape.escape(schemaname)}.{escape.escape(viewname)};
                    """)

    def recreate_all_views(apps: Apps, schema_editor: Any) -> Any:
        from django.db import connections
        from skipper.settings import DATA_SERIES_DYNAMIC_SQL_DB
        from skipper.dataseries.raw_sql import escape

        Tenant = apps.get_model('core', 'Tenant')
        PostgresAnalyticsUser = apps.get_model('dataseries', 'PostgresAnalyticsUser')

        with connections[DATA_SERIES_DYNAMIC_SQL_DB].cursor() as cursor:
            cursor.execute("""
                SELECT schemaname, viewname, definition
                FROM  _tmp_views_to_recreate
            """)
            views_to_recreate = cursor.fetchall()

            for elem in views_to_recreate:
                schemaname, viewname, definition = elem
                cursor.execute(f"""
                    CREATE VIEW {escape.escape(schemaname)}.{escape.escape(viewname)} AS {definition};
                """)

                tenants = list(Tenant.all_objects.filter(name=schemaname.replace('_3_tenant_', '')))

                if len(tenants) > 0:
                    for postgres_analytics_user in PostgresAnalyticsUser.objects.filter(
                            tenant=tenants[0],
                            tenant_global_read=True
                    ).all():
                        cursor.execute(
                            f"""
                            GRANT USAGE ON SCHEMA {schemaname}
                                TO {escape.escape(postgres_analytics_user.role)};
                            GRANT SELECT ON TABLE {schemaname}.{escape.escape(viewname)}
                                TO {escape.escape(postgres_analytics_user.role)};
                            """
                        )

            cursor.execute(f"""
                DROP TABLE _tmp_views_to_recreate;
            """)

    table_name = tbl_name()
    return [
        migrations.RunPython(keep_track_of_old_views),
        *helpers.drop_views_for_datapoint_data_tables(
            data_name=data_name
        ),
        migrations.RunSQL(
            f"""
            ALTER TABLE {table_name}
            ALTER COLUMN {value_name} TYPE TEXT;
            """
        ),
        migrations.RunPython(widen_materialized_tables),
        *helpers.create_views_for_datapoint_data_tables(
            data_name=data_name
        ),
        migrations.RunPython(recreate_all_views),
    ]


class Migration(migrations.Migration):
    atomic = True

    dependencies = [
        ('skipper_dataseries_storage_dynamic_sql', '0017_move_existing_partitions_to_tenant_schema'),
        ('dataseries', '0044_partitionbyuuid_child_table_schema')
    ]

    replaces = [
        ('skipper.dataseries.storage.dynamic_sql', '0018_widen_file_type_path_columns_and_recreate_dependents')
    ]

    operations = [
        *migration_widen_col_def(
            data_name='file_fact',
            fact_name_ds_rel='filefact',
            fact_model_name='FileFact'
        ),
        *migration_widen_col_def(
            data_name='image_fact',
            fact_name_ds_rel='imagefact',
            fact_model_name='ImageFact'
        )
    ]
