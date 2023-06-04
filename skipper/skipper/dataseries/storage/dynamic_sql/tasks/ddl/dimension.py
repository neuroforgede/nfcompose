# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import uuid
from typing import Union

from django.db import connections, transaction

from skipper.core.models.tenant import Tenant
from skipper.dataseries.raw_sql import escape, limit
from skipper.dataseries.raw_sql.tenant import escaped_tenant_schema, ensure_schema, tenant_schema_unescaped
from skipper.dataseries.storage.contract import StorageBackendType
from skipper.dataseries.storage.dynamic_sql.materialized import materialized_column_name, materialized_table_name, \
    materialized_flat_history_table_name
from skipper.dataseries.storage.dynamic_sql.migrations.custom_v1.helpers import data_point_id_column_def
from skipper.dataseries.storage.dynamic_sql.tasks.common import grant_permissions_for_global_analytics_users
from skipper.settings import DATA_SERIES_DYNAMIC_SQL_DB
from skipper.core.lint import sql_cursor


def handle_create_dimension_in_materialized_table(
        table_name: str, schema_name: str, dimension_id: str, external_id: str
) -> None:
    column_name = escape.escape(materialized_column_name(dimension_id, external_id))
    with sql_cursor(DATA_SERIES_DYNAMIC_SQL_DB) as cursor:
        cursor.execute(
            f"""
            ALTER TABLE {schema_name}.{table_name}
            ADD COLUMN IF NOT EXISTS {column_name} {data_point_id_column_def};
            """
        )


def handle_drop_dimension_in_materialized_table(
    escaped_table_name: str, escaped_schema_name: str, dimension_id: Union[str, uuid.UUID], external_id: str
) -> None:
    column_name = escape.escape(materialized_column_name(dimension_id, external_id))
    with sql_cursor(DATA_SERIES_DYNAMIC_SQL_DB) as cursor:
        cursor.execute(
            f"""
            ALTER TABLE {escaped_schema_name}.{escaped_table_name}
            DROP COLUMN IF EXISTS {column_name};
            """
        )


def handle_drop_dimension_in_materialized_flat_history_table(
    escaped_table_name: str, escaped_schema_name: str, dimension_id: Union[str, uuid.UUID], external_id: str
) -> None:
    column_name = escape.escape(materialized_column_name(dimension_id, external_id))
    with sql_cursor(DATA_SERIES_DYNAMIC_SQL_DB) as cursor:
        cursor.execute(
            f"""
            ALTER TABLE {escaped_schema_name}.{escaped_table_name}
            DROP COLUMN IF EXISTS {column_name};
            """
        )



def handle_create_dimension_materialized(
        data_series_id: Union[str, uuid.UUID], data_series_external_id: str,
        dimension_id: str, tenant_name: str, external_id: str
) -> None:
    schema_name = escaped_tenant_schema(tenant_name)
    ensure_schema(schema_name, connection_name=DATA_SERIES_DYNAMIC_SQL_DB)
    table_name = escape.escape(materialized_table_name(data_series_id, data_series_external_id))
    handle_create_dimension_in_materialized_table(
        table_name=table_name, schema_name=schema_name, dimension_id=dimension_id, external_id=external_id
    )


def handle_create_dimension_materialized_flat_history(
        data_series_id: Union[str, uuid.UUID], data_series_external_id: str,
        dimension_id: str, tenant_name: str, external_id: str
) -> None:
    schema_name = escaped_tenant_schema(tenant_name)
    ensure_schema(schema_name, connection_name=DATA_SERIES_DYNAMIC_SQL_DB)
    table_name = escape.escape(materialized_flat_history_table_name(data_series_id, data_series_external_id))
    handle_create_dimension_in_materialized_table(
        table_name=table_name, schema_name=schema_name, dimension_id=dimension_id, external_id=external_id
    )


def dim_partition_name(
        dp_rel_partition_base_name: str,
        fact_id: str,
        tenant_name: str,
        external_id: str
) -> str:
    return limit.limit_length(f'{dp_rel_partition_base_name}_{str(fact_id)}_{tenant_name}_{str(external_id)}')


def handle_create_dimension(data_series_id: Union[str, uuid.UUID], data_series_external_id: str,
                            dimension_id: str, tenant_name: str, external_id: str, backend: str, tenant_id: str) -> None:
    with transaction.atomic():

        if backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value or \
                backend == StorageBackendType.DYNAMIC_SQL_NO_HISTORY.value:
            handle_create_dimension_materialized(
                data_series_id=data_series_id,
                data_series_external_id=data_series_external_id,
                dimension_id=dimension_id,
                tenant_name=tenant_name,
                external_id=external_id
            )

        if backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.name:
            handle_create_dimension_materialized_flat_history(
                data_series_id=data_series_id,
                data_series_external_id=data_series_external_id,
                dimension_id=dimension_id,
                tenant_name=tenant_name,
                external_id=external_id
            )
