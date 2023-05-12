# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

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
            if dataseries.backend == 'DYNAMIC_SQL_MATERIALIZED' \
                    or dataseries.backend == 'DYNAMIC_SQL_NO_HISTORY':
                add_sub_clock_to_materialized(dataseries.id, dataseries.external_id, dataseries.tenant.name)


def recreate_views_for_datapoint_data_tables(
        data_name: str,
        fact_or_dim_id: str = 'fact_id',
        value_name: str = 'value'
) -> List[migrations.RunSQL]:
    relevant_table_name = f'data_point_{data_name}'

    def tbl_name(prefix: Optional[str] = None) -> str:
        actual_prefix = ''
        if prefix is not None:
            actual_prefix = f'_{prefix}'
        return f'_{str(Module.DATA_SERIES.value)}{actual_prefix}_{relevant_table_name}'

    table_name = tbl_name()
    view_table_name = tbl_name('view')
    return [
        migrations.RunSQL(
            f"""
                CREATE OR REPLACE VIEW {view_table_name} AS
                SELECT tbl.data_point_id,
                    tbl.{fact_or_dim_id},
                    tbl.point_in_time,
                    tbl.{value_name},
                    tbl.user_id,
                    tbl.record_source,
                    tbl.sub_clock
                FROM {table_name} tbl
                LEFT OUTER JOIN {table_name} tbl2 ON (
                    tbl.{fact_or_dim_id} = tbl2.{fact_or_dim_id} AND
                    tbl.data_point_id = tbl2.data_point_id AND
                    (tbl.point_in_time, tbl.sub_clock) < (tbl2.point_in_time, tbl2.sub_clock)
                )
                WHERE tbl2.data_point_id IS NULL;

                CREATE OR REPLACE FUNCTION {table_name}_insert()
                RETURNS trigger AS
                $BODY$
                BEGIN
                    INSERT INTO {table_name}(
                        data_point_id,
                        {fact_or_dim_id},
                        point_in_time,
                        {value_name},
                        user_id,
                        record_source,
                        sub_clock
                    ) VALUES (
                        NEW.data_point_id,
                        NEW.{fact_or_dim_id},
                        NEW.point_in_time,
                        NEW.{value_name},
                        NEW.user_id,
                        NEW.record_source,
                        NEW.sub_clock
                    );
                    RETURN NEW;
                END;
                $BODY$
                LANGUAGE plpgsql VOLATILE;

                CREATE TRIGGER {table_name}_insert
                INSTEAD OF INSERT ON {view_table_name}
                FOR EACH ROW EXECUTE PROCEDURE {table_name}_insert();

                -- we dont need any other trigger than insert, as we only ever insert data
                CREATE UNIQUE INDEX {table_name}_data_point_uniq_fkey
                ON {table_name} USING btree
                ({fact_or_dim_id}, data_point_id COLLATE pg_catalog."default", point_in_time, sub_clock);
                
                DROP INDEX IF EXISTS {table_name}_data_point_fkey;
"""
        )
    ]


def add_subclock_migration_data_table(
        data_name: str,
        fact_or_dim_id: str = 'fact_id',
        value_name: str = 'value'
) -> List[Any]:
    relevant_table_name = f'data_point_{data_name}'

    def tbl_name(prefix: Optional[str] = None) -> str:
        actual_prefix = ''
        if prefix is not None:
            actual_prefix = f'_{prefix}'
        return f'_{str(Module.DATA_SERIES.value)}{actual_prefix}_{relevant_table_name}'

    table_name = tbl_name()
    view_table_name = tbl_name('view')
    return [
        migrations.RunSQL(f"""
            -- create the data table and partition it by dimension_id/fact_id  
            ALTER TABLE {table_name}
            -- for multi-tenancy reasons we must use manually generated serial values
            -- when inserting things
            ADD COLUMN IF NOT EXISTS sub_clock bigint NULL;
            
            DROP TRIGGER IF EXISTS {table_name}_insert ON {view_table_name};
            DROP FUNCTION IF EXISTS {table_name}_insert();

            DROP TRIGGER IF EXISTS {table_name}_delete ON {view_table_name};
            DROP FUNCTION IF EXISTS {table_name}_delete();

            DROP TRIGGER IF EXISTS {table_name}_update ON {view_table_name};
            DROP FUNCTION IF EXISTS {table_name}_update();
        """),
        *recreate_views_for_datapoint_data_tables(
            data_name=data_name,
            fact_or_dim_id=fact_or_dim_id,
            value_name=value_name
        )
    ]

# TODO: recreate the unique index in a subsequent migration and concurrently (so that the app is still working while the index is being created)


class Migration(migrations.Migration):
    atomic = True

    dependencies = [
        ('skipper_dataseries_storage_dynamic_sql', '0021_fix_sdel_triggers_for_dataseries_children'),
    ]

    operations: List[Any] = (
            [
                migrations.RunSQL(f"""
                ALTER TABLE _{str(Module.DATA_SERIES.value)}_data_point
                -- for multi-tenancy reasons we must use manually generated serial values
                -- when inserting things
                ADD COLUMN IF NOT EXISTS sub_clock bigint NULL;
    
                -- drop unnecessary triggers, we do insert only
                DROP TRIGGER IF EXISTS _{str(Module.DATA_SERIES.value)}_view_data_point_delete ON _{str(Module.DATA_SERIES.value)}_view_data_point;
                DROP FUNCTION IF EXISTS _{str(Module.DATA_SERIES.value)}_delete_data_point();
    
                DROP TRIGGER IF EXISTS _{str(Module.DATA_SERIES.value)}_view_data_point_update ON _{str(Module.DATA_SERIES.value)}_view_data_point;
                DROP FUNCTION IF EXISTS _{str(Module.DATA_SERIES.value)}_update_data_point();
                
                -- update view with new columns
                CREATE OR REPLACE VIEW _{str(Module.DATA_SERIES.value)}_view_data_point AS
                SELECT tbl.id,
                    tbl.data_series_id,
                    tbl.external_id,
                    tbl.point_in_time,
                    tbl.deleted,
                    tbl.user_id,
                    tbl.record_source,
                    tbl.sub_clock
                FROM _{str(Module.DATA_SERIES.value)}_data_point tbl
                LEFT OUTER JOIN _{str(Module.DATA_SERIES.value)}_data_point tbl2 ON (
                    tbl.data_series_id = tbl2.data_series_id AND
                    tbl.id = tbl2.id AND
                    (tbl.point_in_time, tbl.sub_clock) < (tbl2.point_in_time, tbl2.sub_clock)
                )
                WHERE tbl2.id IS NULL
                AND tbl.deleted = false;

                -- inserting into the view
                CREATE OR REPLACE FUNCTION _{str(Module.DATA_SERIES.value)}_insert_data_point()
                RETURNS trigger AS
                $BODY$
                BEGIN
                    INSERT INTO _{str(Module.DATA_SERIES.value)}_data_point(
                        id,
                        data_series_id,
                        external_id,
                        point_in_time,
                        deleted,
                        user_id,
                        record_source,
                        sub_clock
                    ) VALUES (
                        NEW.id,
                        NEW.data_series_id,
                        NEW.external_id,
                        NEW.point_in_time,
                        NEW.deleted,
                        NEW.user_id,
                        NEW.record_source,
                        NEW.sub_clock
                    );
                    RETURN NEW;
                END;
                $BODY$
                LANGUAGE plpgsql VOLATILE;
                
                CREATE UNIQUE INDEX _{str(Module.DATA_SERIES.value)}_data_point_uniq_pkey
                ON _{str(Module.DATA_SERIES.value)}_data_point USING btree
                (data_series_id, id COLLATE pg_catalog."default", point_in_time, sub_clock);

                DROP INDEX IF EXISTS _{str(Module.DATA_SERIES.value)}_data_point_pkey;
                -- we only need inserts
                """),
                migrations.RunPython(migrate_materialized_dataseries_indexes)
            ] +
            add_subclock_migration_data_table(data_name='dimension', fact_or_dim_id='dimension_id') +
            add_subclock_migration_data_table(data_name='float_fact', fact_or_dim_id='fact_id') +
            add_subclock_migration_data_table(data_name='string_fact', fact_or_dim_id='fact_id') +
            add_subclock_migration_data_table(data_name='text_fact', fact_or_dim_id='fact_id') +
            add_subclock_migration_data_table(data_name='timestamp_fact', fact_or_dim_id='fact_id') +
            add_subclock_migration_data_table(data_name='image_fact', fact_or_dim_id='fact_id') +
            add_subclock_migration_data_table(data_name='file_fact', fact_or_dim_id='fact_id') +
            add_subclock_migration_data_table(data_name='json_fact', fact_or_dim_id='fact_id') +
            add_subclock_migration_data_table(data_name='boolean_fact', fact_or_dim_id='fact_id')
    )
