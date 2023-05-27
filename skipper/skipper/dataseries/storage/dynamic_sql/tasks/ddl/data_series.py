# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import uuid

from django.db import connections, transaction
from typing import Union

from skipper.core.models.tenant import Tenant
from skipper.dataseries.raw_sql import escape
from skipper.dataseries.raw_sql.tenant import escaped_tenant_schema, ensure_schema, tenant_schema_unescaped
from skipper.dataseries.storage.contract import StorageBackendType
from skipper.dataseries.storage.dynamic_sql.materialized import materialized_table_name, \
    materialized_flat_history_table_name
from skipper.dataseries.storage.dynamic_sql.migrations.custom_v1.helpers import data_point_id_column_def, \
    external_id_column_def
from skipper.dataseries.storage.dynamic_sql.tasks.common import grant_permissions_for_global_analytics_users
from skipper.settings import DATA_SERIES_DYNAMIC_SQL_DB
from skipper.core.lint import sql_cursor


def ensure_indexes_materialized(
        data_series_id: Union[str, uuid.UUID],
        data_series_external_id: str,
        tenant_name: str,
        include_point_in_time_index: bool = True
) -> None:
    schema_name = escaped_tenant_schema(tenant_name)
    ensure_schema(schema_name, connection_name=DATA_SERIES_DYNAMIC_SQL_DB)
    table_name_unescaped = materialized_table_name(data_series_id, data_series_external_id)
    table_name = escape.escape(table_name_unescaped)
    with sql_cursor(DATA_SERIES_DYNAMIC_SQL_DB) as cursor:
        queries = [
            # for ordering
            f"""
            CREATE INDEX IF NOT EXISTS {escape.escape(f'_mat_inserted_at_id_alive_{str(data_series_id)}_{data_series_external_id}')}
            ON {schema_name}.{table_name}
            USING btree (inserted_at ASC NULLS LAST, id ASC NULLS LAST)
            WHERE deleted_at IS NULL;
            """,
#            we do not support history queries directly on the table, so dont do it
#            # for ordering in the rest api we only need an index on all dead data
#            f"""
#            CREATE INDEX IF NOT EXISTS {escape.escape(f'_mat_inserted_at_id_dead_{str(data_series_id)}_{data_series_external_id}')}
#            ON {schema_name}.{table_name}
#            USING btree (inserted_at ASC NULLS LAST, id ASC NULLS LAST)
#            WHERE deleted_at IS NOT NULL;
#            """,
            f"""
            CREATE UNIQUE INDEX IF NOT EXISTS {escape.escape(f'_mat_id_{str(data_series_id)}_{data_series_external_id}')} ON {schema_name}.{table_name} USING btree (id);
            DO $$
            BEGIN

              BEGIN
                ALTER TABLE {schema_name}.{table_name} ADD CONSTRAINT {escape.escape(f'_mat_id_pk_{str(data_series_id)}_{data_series_external_id}')} PRIMARY KEY USING INDEX {escape.escape(f'_mat_id_{str(data_series_id)}_{data_series_external_id}')};
              EXCEPTION
                WHEN duplicate_table THEN RAISE NOTICE 'Table constraint {escape.escape(f'_mat_id_pk_{str(data_series_id)}_{data_series_external_id}')} already exists';
              END;

            END $$;
            """,
            # don't use a unique index on external_id as it will break upserts
            f"""
            CREATE INDEX IF NOT EXISTS {escape.escape(f'_mat_external_id_{str(data_series_id)}_{data_series_external_id}')} ON {schema_name}.{table_name} USING btree (external_id);
            """
        ]

        if include_point_in_time_index:
            queries.append(f"""
                CREATE INDEX IF NOT EXISTS {escape.escape(f'_mat_point_in_time_{str(data_series_id)}_{data_series_external_id}')}
                ON {schema_name}.{table_name} USING btree
                (point_in_time ASC NULLS LAST)
                TABLESPACE pg_default;
            """)

        for query in queries:
            cursor.execute(query)


def ensure_indexes_materialized_flat_history(
        data_series_id: Union[str, uuid.UUID],
        data_series_external_id: str,
        tenant_name: str
) -> None:
    schema_name = escaped_tenant_schema(tenant_name)
    ensure_schema(schema_name, connection_name=DATA_SERIES_DYNAMIC_SQL_DB)
    table_name_unescaped = materialized_flat_history_table_name(data_series_id, data_series_external_id)
    table_name = escape.escape(table_name_unescaped)
    with sql_cursor(DATA_SERIES_DYNAMIC_SQL_DB) as cursor:
        queries = [
            # for changes since
            f"""
            CREATE INDEX IF NOT EXISTS {escape.escape(f'_mfhist_point_in_time_{str(data_series_id)}_{data_series_external_id}')}
            ON {schema_name}.{table_name} USING btree
            (point_in_time ASC NULLS LAST)
            TABLESPACE pg_default;
            """,
            f"""
            CREATE INDEX IF NOT EXISTS {escape.escape(f'_mfhist_external_id_{str(data_series_id)}_{data_series_external_id}')}
            ON {schema_name}.{table_name} USING btree
            (external_id)
            TABLESPACE pg_default;
            """,
            f"""
            CREATE UNIQUE INDEX IF NOT EXISTS {escape.escape(f'_mfhist_uniq_{str(data_series_id)}_{data_series_external_id}')} ON {schema_name}.{table_name} USING btree (
                id COLLATE "pg_catalog"."default" ASC NULLS LAST,
                point_in_time ASC NULLS LAST,
                sub_clock ASC NULLS LAST
            );
            DO $$
            BEGIN

              BEGIN
                ALTER TABLE {schema_name}.{table_name} ADD CONSTRAINT {escape.escape(f'_mfhist_uniq_c_{str(data_series_id)}_{data_series_external_id}')} PRIMARY KEY USING INDEX {escape.escape(f'_mfhist_uniq_{str(data_series_id)}_{data_series_external_id}')};
              EXCEPTION
                WHEN duplicate_table THEN RAISE NOTICE 'Table constraint {escape.escape(f'_mfhist_uniq_c_{str(data_series_id)}_{data_series_external_id}')} already exists';
              END;

            END $$;
            """,
        ]

        for query in queries:
            cursor.execute(query)


def handle_create_data_series_materialized_flat_history(
        data_series_id: Union[str, uuid.UUID],
        data_series_external_id: str,
        tenant_name: str,
        tenant: Tenant
) -> None:
    schema_name = escaped_tenant_schema(tenant_name)
    ensure_schema(schema_name, connection_name=DATA_SERIES_DYNAMIC_SQL_DB)
    table_name_unescaped = materialized_flat_history_table_name(data_series_id, data_series_external_id)
    table_name = escape.escape(table_name_unescaped)
    with sql_cursor(DATA_SERIES_DYNAMIC_SQL_DB) as cursor:
        queries = [
            f"""
                CREATE TABLE IF NOT EXISTS {schema_name}.{table_name} (
                    id {data_point_id_column_def} NOT NULL,
                    external_id {external_id_column_def} NOT NULL,
                    point_in_time timestamp with time zone NOT NULL,
                    deleted boolean NOT NULL,
                    user_id varchar(256),
                    record_source varchar(256),
                    sub_clock bigint NULL
                )
                """
        ]

        for query in queries:
            cursor.execute(query)

        grant_permissions_for_global_analytics_users(
            tenant=tenant,
            schema_escaped=schema_name,
            table=table_name_unescaped
        )

    ensure_indexes_materialized(
        data_series_id=data_series_id,
        data_series_external_id=data_series_external_id,
        tenant_name=tenant_name,
        # TODO: this might be stupid for HOT updates see #4684, for now include it
        include_point_in_time_index=True
    )

    ensure_indexes_materialized_flat_history(
        data_series_id=data_series_id,
        data_series_external_id=data_series_external_id,
        tenant_name=tenant_name
    )


def handle_create_data_series_materialized(
        data_series_id: Union[str, uuid.UUID],
        data_series_external_id: str,
        tenant_name: str,
        tenant: Tenant
) -> None:
    schema_name = escaped_tenant_schema(tenant_name)
    ensure_schema(schema_name, connection_name=DATA_SERIES_DYNAMIC_SQL_DB)
    table_name_unescaped = materialized_table_name(data_series_id, data_series_external_id)
    table_name = escape.escape(table_name_unescaped)
    with sql_cursor(DATA_SERIES_DYNAMIC_SQL_DB) as cursor:
        queries = [
            f"""
            CREATE TABLE IF NOT EXISTS {schema_name}.{table_name} (
                id {data_point_id_column_def} NOT NULL,
                external_id {external_id_column_def} NOT NULL,
                point_in_time timestamp with time zone NOT NULL,
                inserted_at timestamp with time zone NOT NULL,
                deleted_at timestamp with time zone,
                sub_clock bigint NULL
            )
            """
        ]

        for query in queries:
            cursor.execute(query)

        grant_permissions_for_global_analytics_users(
            tenant=tenant,
            schema_escaped=schema_name,
            table=table_name_unescaped
        )

    ensure_indexes_materialized(
        data_series_id=data_series_id,
        data_series_external_id=data_series_external_id,
        tenant_name=tenant_name
    )


def handle_create_data_series(data_series_id: Union[str, uuid.UUID], data_series_external_id: str, tenant_name: str,
                              external_id: str, backend: str, tenant_id: str) -> None:
    with transaction.atomic():
        tenant = Tenant.objects.get(id=tenant_id)

        if backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value or \
                backend == StorageBackendType.DYNAMIC_SQL_NO_HISTORY.value:
            handle_create_data_series_materialized(
                data_series_id=data_series_id,
                data_series_external_id=data_series_external_id,
                tenant_name=tenant_name,
                tenant=tenant
            )

        if backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.name:
            handle_create_data_series_materialized_flat_history(
                data_series_id=data_series_id,
                data_series_external_id=data_series_external_id,
                tenant_name=tenant_name,
                tenant=tenant
            )
