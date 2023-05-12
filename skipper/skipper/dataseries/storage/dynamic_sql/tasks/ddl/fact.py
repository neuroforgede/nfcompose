# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import uuid
from typing import Union, Tuple

from django.db import connections, transaction

from skipper.core.models.tenant import Tenant
from skipper.dataseries.raw_sql import escape, limit, partition
from skipper.dataseries.raw_sql.tenant import escaped_tenant_schema, ensure_schema, tenant_schema_unescaped
from skipper.dataseries.storage.contract import FactType, StorageBackendType
from skipper.dataseries.storage.dynamic_sql.materialized import materialized_column_name, materialized_table_name, \
    materialized_flat_history_table_name
from skipper.dataseries.storage.dynamic_sql.tasks.common import grant_permissions_for_global_analytics_users
from skipper.settings import DATA_SERIES_DYNAMIC_SQL_DB
from skipper.core.lint import sql_cursor


def handle_create_fact_in_materialized_table(
        escaped_table_name: str, schema_name: str, fact_id: str,
        fact_type: FactType, external_id: str
) -> None:
    value_column_def: str
    if fact_type == FactType.Float:
        value_column_def = 'double precision'
    elif fact_type == FactType.String:
        value_column_def = 'character varying(256) COLLATE "pg_catalog"."default"'
    elif fact_type == FactType.Text:
        value_column_def = "text"
    elif fact_type == FactType.Timestamp:
        value_column_def = 'timestamp with time zone'
    elif fact_type == FactType.Image:
        value_column_def = 'TEXT COLLATE "pg_catalog"."default"'
    elif fact_type == FactType.JSON:
        value_column_def = 'jsonb'
    elif fact_type == FactType.Boolean:
        value_column_def = 'BOOLEAN'
    elif fact_type == FactType.File:
        value_column_def = 'TEXT COLLATE "pg_catalog"."default"'
    else:
        raise NotImplementedError('this backend does not support fact_type ' + str(fact_type))

    column_name = escape.escape(materialized_column_name(fact_id, external_id))
    with sql_cursor(DATA_SERIES_DYNAMIC_SQL_DB) as cursor:
        cursor.execute(
            f"""
            ALTER TABLE {schema_name}.{escaped_table_name}
            ADD COLUMN IF NOT EXISTS {column_name} {value_column_def};
            """
        )


def handle_drop_fact_in_materialized_table(
        escaped_table_name: str, escaped_schema_name: str, fact_id: Union[str, uuid.UUID], external_id: str
) -> None:
    column_name = escape.escape(materialized_column_name(fact_id, external_id))
    with sql_cursor(DATA_SERIES_DYNAMIC_SQL_DB) as cursor:
        cursor.execute(
            f"""
            ALTER TABLE {escaped_schema_name}.{escaped_table_name}
            DROP COLUMN IF EXISTS {column_name};
            """
        )


def handle_drop_fact_in_materialized_flat_history_table(
        escaped_table_name: str, escaped_schema_name: str, fact_id: Union[str, uuid.UUID], external_id: str
) -> None:
    column_name = escape.escape(materialized_column_name(fact_id, external_id))
    with sql_cursor(DATA_SERIES_DYNAMIC_SQL_DB) as cursor:
        cursor.execute(
            f"""
            ALTER TABLE {escaped_schema_name}.{escaped_table_name}
            DROP COLUMN IF EXISTS {column_name};
            """
        )


def handle_create_fact_materialized(
        data_series_id: Union[str, uuid.UUID], data_series_external_id: str, fact_id: str,
        fact_type: FactType, tenant_name: str, external_id: str
) -> None:
    schema_name = escaped_tenant_schema(tenant_name)
    ensure_schema(schema_name, connection_name=DATA_SERIES_DYNAMIC_SQL_DB)
    table_name = escape.escape(materialized_table_name(data_series_id, data_series_external_id))
    handle_create_fact_in_materialized_table(escaped_table_name=table_name, schema_name=schema_name, fact_id=fact_id,
                                             fact_type=fact_type, external_id=external_id)


def handle_create_fact_materialized_flat_history(
        data_series_id: Union[str, uuid.UUID], data_series_external_id: str, fact_id: str,
        fact_type: FactType, tenant_name: str, external_id: str
) -> None:
    schema_name = escaped_tenant_schema(tenant_name)
    ensure_schema(schema_name, connection_name=DATA_SERIES_DYNAMIC_SQL_DB)
    table_name = escape.escape(materialized_flat_history_table_name(data_series_id, data_series_external_id))
    handle_create_fact_in_materialized_table(escaped_table_name=table_name, schema_name=schema_name, fact_id=fact_id,
                                             fact_type=fact_type, external_id=external_id)


def fact_ddl_names(fact_type: FactType) -> Tuple[str, str]:
    """
    :param fact_type:
    :return: Tuple with table name, partition base name
    """
    dp_rel_table_name: str
    dp_rel_partition_base_name: str
    value_column_def: str
    if fact_type == FactType.Float:
        dp_rel_table_name = '_3_data_point_float_fact'
        dp_rel_partition_base_name = '_3_dp_float_fact'
    elif fact_type == FactType.String:
        dp_rel_table_name = '_3_data_point_string_fact'
        dp_rel_partition_base_name = '_3_dp_string_fact'
    elif fact_type == FactType.Text:
        dp_rel_table_name = '_3_data_point_text_fact'
        dp_rel_partition_base_name = '_3_dp_text_fact'
    elif fact_type == FactType.Timestamp:
        dp_rel_table_name = '_3_data_point_timestamp_fact'
        dp_rel_partition_base_name = '_3_dp_timestamp_fact'
    elif fact_type == FactType.Image:
        dp_rel_table_name = '_3_data_point_image_fact'
        dp_rel_partition_base_name = '_3_dp_image_fact'
    elif fact_type == FactType.JSON:
        dp_rel_table_name = '_3_data_point_json_fact'
        dp_rel_partition_base_name = '_3_dp_json_fact'
    elif fact_type == FactType.Boolean:
        dp_rel_table_name = '_3_data_point_boolean_fact'
        dp_rel_partition_base_name = '_3_dp_boolean_fact'
    elif fact_type == FactType.File:
        dp_rel_table_name = '_3_data_point_file_fact'
        dp_rel_partition_base_name = '_3_dp_file_fact'
    else:
        raise NotImplementedError('this backend does not support fact_type ' + str(fact_type))

    return dp_rel_table_name, dp_rel_partition_base_name


def handle_create_fact(data_series_id: Union[str, uuid.UUID], data_series_external_id: str, fact_id: str,
                       fact_type: FactType, tenant_name: str, external_id: str, backend: str, tenant_id: str) -> None:
    dp_rel_table_name, dp_rel_partition_base_name = fact_ddl_names(fact_type)
    value_column_def: str
    with transaction.atomic():
        if backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED.value or backend == StorageBackendType.DYNAMIC_SQL_V1.name:
            partition_name = partition.partition_name(
                base_name=dp_rel_partition_base_name,
                fact_or_dim_id=str(fact_id),
                tenant_name=tenant_name,
                external_id=str(external_id)
            )
            tenant = Tenant.objects.get(id=tenant_id)
            partition.partition(
                table_name=dp_rel_table_name,
                partition_name=partition_name,
                partition_key=fact_id,
                connection_name=DATA_SERIES_DYNAMIC_SQL_DB,
                tenant=tenant
            )
            grant_permissions_for_global_analytics_users(
                tenant=tenant,
                schema_escaped=escaped_tenant_schema(tenant_name),
                table=partition_name
            )

        if backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED.value or \
                backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value or \
                backend == StorageBackendType.DYNAMIC_SQL_NO_HISTORY.value:
            handle_create_fact_materialized(
                data_series_id=data_series_id,
                data_series_external_id=data_series_external_id,
                fact_id=fact_id,
                fact_type=fact_type,
                tenant_name=tenant_name,
                external_id=external_id
            )
        if backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value:
            handle_create_fact_materialized_flat_history(
                data_series_id=data_series_id,
                data_series_external_id=data_series_external_id,
                fact_id=fact_id,
                fact_type=fact_type,
                tenant_name=tenant_name,
                external_id=external_id
            )
