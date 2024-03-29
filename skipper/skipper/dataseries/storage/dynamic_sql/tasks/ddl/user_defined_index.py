# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


import uuid

from django.db import connections, transaction
from typing import Any, Dict, List, Mapping, Union
from psycopg2 import errors # type: ignore
from skipper.core.lint import sql_cursor  # type: ignore

from skipper.core.models.tenant import Tenant
from skipper.core.celery import task
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.models.metamodel.index import IndexByUUID, IndexRegistrySourceType, TargetTableType
from skipper.dataseries.raw_sql import escape, limit
from skipper.dataseries.raw_sql.tenant import escaped_tenant_schema, ensure_schema, tenant_schema_unescaped
from skipper.dataseries.storage.contract import IndexableDataSeriesChildType, StorageBackendType
from skipper.dataseries.storage.dynamic_sql.materialized import materialized_table_name, materialized_flat_history_table_name
from skipper.dataseries.storage.dynamic_sql.migrations.custom_v1.helpers import data_point_id_column_def, \
    external_id_column_def
from skipper.dataseries.storage.dynamic_sql.tasks.common import grant_permissions_for_global_analytics_users
from skipper.dataseries.storage.static_ds_information import DataSeriesDimensionQueryInfo, DataSeriesFactQueryInfo, DataSeriesQueryInfo, compute_data_series_query_info
from skipper.settings import DATA_SERIES_DYNAMIC_SQL_DB


# DO NOT CHANGE
def index_rel_name(index_id: uuid.UUID) -> str:
    return limit.limit_length('_mat_userindex_' + str(index_id))


# DO NOT CHANGE
def index_rel_name_flat_history(index_id: uuid.UUID) -> str:
    return limit.limit_length('_mfhist_userindex_' + str(index_id))


def handle_create_user_defined_index_on_materialized_or_flat_table(
    unescaped_table_name: str, target_table_type: TargetTableType, escaped_schema_name: str, index_id: uuid.UUID,
    index_rel_name: str, escaped_target_columns: List[str]
) -> None:
    targets_list_string = ','.join(escaped_target_columns)
    with sql_cursor(DATA_SERIES_DYNAMIC_SQL_DB) as cursor:
        cursor.execute(
            f"""
                CREATE INDEX IF NOT EXISTS {escape.escape(index_rel_name)}
                ON {escaped_schema_name}.{escape.escape(unescaped_table_name)} ({targets_list_string});
            """
        )
    if not IndexByUUID.objects.filter(source_id=index_id, target_table_type=target_table_type.value).exists():
        IndexByUUID.objects.create(
            source_id=index_id,
            source_type=IndexRegistrySourceType.USER_DEFINED_INDEX.value,
            db_name=index_rel_name,
            target_table=unescaped_table_name,
            target_table_type=target_table_type.value
        )


def handle_drop_user_defined_index_materialized(
    index_id: uuid.UUID, escaped_schema_name: str
) -> None:

    indexes = list(IndexByUUID.objects.filter(source_id=index_id, source_type=IndexRegistrySourceType.USER_DEFINED_INDEX.value))
    if len(indexes) != 1:
        raise AssertionError("Unexpected amount of indexes registered in IndexByUUID with is UUID: " + str(index_id))
    for index in indexes:
        with sql_cursor(DATA_SERIES_DYNAMIC_SQL_DB) as cursor:
            cursor.execute(
                f"""
                    DROP INDEX {escaped_schema_name}.{escape.escape(index.db_name)};
                """
            )
        index.delete()


def handle_drop_user_defined_index_flat_history(
    index_id: uuid.UUID, escaped_schema_name: str
) -> None:
    indexes = list(IndexByUUID.objects.filter(source_id=index_id, source_type=IndexRegistrySourceType.USER_DEFINED_INDEX.value))
    if len(indexes) != 2:
        raise AssertionError("Unexpected amount of indexes registered in IndexByUUID with this ID: " + str(index_id))
    for index in indexes:
        with sql_cursor(DATA_SERIES_DYNAMIC_SQL_DB) as cursor:
            cursor.execute(
                f"""
                    DROP INDEX {escaped_schema_name}.{escape.escape(index.db_name)};
                """
            )
        index.delete()


def handle_drop_user_defined_index_by_target_table_type(
    index_id: uuid.UUID,
    escaped_schema_name: str,
    target_table_type: TargetTableType
) -> None:
    indexes = list(IndexByUUID.objects.filter(
        target_table_type=target_table_type.value, source_id=index_id, source_type=IndexRegistrySourceType.USER_DEFINED_INDEX.value
    ))
    if len(indexes) != 1:
        raise AssertionError("Unexpected amount of indexes registered in IndexByUUID with this ID: " + str(index_id))
    for index in indexes:
        with sql_cursor(DATA_SERIES_DYNAMIC_SQL_DB) as cursor:
            cursor.execute(
                f"""
                    DROP INDEX {escaped_schema_name}.{escape.escape(index.db_name)};
                """
            )
        index.delete()


def handle_create_user_defined_index(
    data_series_id: Union[uuid.UUID, str],
    data_series_external_id: str,
    tenant_name: str,
    targets: List[Dict[str, Union[uuid.UUID, str]]], backend: str, index_id: uuid.UUID
) -> None:
    """
    This function simply wraps the async task call
    """
    handle_create_user_defined_index_actual.delay(
        data_series_id=data_series_id, 
        data_series_external_id=data_series_external_id,
        tenant_name=tenant_name,
        targets=targets,
        backend=backend,
        index_id=index_id
    )


@task(
    name="_3_dynamic_sql_create_user_defined_index",
    queue='index_creation',
    autoretry_for=(errors.DeadlockDetected,),
    retry_backoff=True,  # type: ignore
    retry_kwargs={'max_retries': 3, 'countdown': 10}
)  # type: ignore
def handle_create_user_defined_index_actual(
    data_series_id: Union[uuid.UUID, str],
    data_series_external_id: str,
    tenant_name: str,
    targets: List[Dict[str, Union[uuid.UUID, str]]],
    backend: str,
    index_id: uuid.UUID
) -> None:
    # 1.: Turn fact/dim targets into schema/column targets

    parent_ds: DataSeries = DataSeries.objects.get(id=data_series_id)
    parent_ds_query_info: DataSeriesQueryInfo = compute_data_series_query_info(parent_ds)
    
    escaped_schema_target_columns: List[str] = []
    for target in targets:
        # find target in static info
        target_query_info: Mapping[str, Union[DataSeriesFactQueryInfo, DataSeriesDimensionQueryInfo]]

        _type = target['target_type']
        if _type == IndexableDataSeriesChildType.FLOAT_FACT.value:
            target_query_info = parent_ds_query_info.float_facts
        elif _type == IndexableDataSeriesChildType.STRING_FACT.value:
            target_query_info = parent_ds_query_info.string_facts
        elif _type == IndexableDataSeriesChildType.TEXT_FACT.value:
            target_query_info = parent_ds_query_info.text_facts
        elif _type == IndexableDataSeriesChildType.TIMESTAMP_FACT.value:
            target_query_info = parent_ds_query_info.timestamp_facts
        elif _type == IndexableDataSeriesChildType.IMAGE_FACT.value:
            target_query_info = parent_ds_query_info.image_facts
        elif _type == IndexableDataSeriesChildType.JSON_FACT.value:
            target_query_info = parent_ds_query_info.json_facts
        elif _type == IndexableDataSeriesChildType.BOOLEAN_FACT.value:
            target_query_info = parent_ds_query_info.boolean_facts
        elif _type == IndexableDataSeriesChildType.FILE_FACT.value:
            target_query_info = parent_ds_query_info.file_facts
        elif _type == IndexableDataSeriesChildType.DIMENSION.value:
            target_query_info = parent_ds_query_info.dimensions

        escaped_target_column_name: str = ''
        for k, v in target_query_info.items():
            if v.id == str(target['target_id']):
                escaped_target_column_name = v.value_column
        if not escaped_target_column_name:
            raise AssertionError('An Index target column was not found, aborting...')
        escaped_schema_target_columns.append(escaped_target_column_name)

    escaped_schema_name = escaped_tenant_schema(tenant_name)
    ensure_schema(escaped_schema_name, connection_name=DATA_SERIES_DYNAMIC_SQL_DB)
    
    # 2.: Create indexes
    with transaction.atomic():
        if backend in (
            StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value,
            StorageBackendType.DYNAMIC_SQL_NO_HISTORY.value
        ):
            handle_create_user_defined_index_on_materialized_or_flat_table(
                unescaped_table_name=materialized_table_name(data_series_id, data_series_external_id),
                target_table_type=TargetTableType.MATERIALIZED,
                escaped_schema_name=escaped_schema_name,
                index_rel_name=index_rel_name(index_id),
                escaped_target_columns=escaped_schema_target_columns,
                index_id=index_id
            )

        if backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value:
            handle_create_user_defined_index_on_materialized_or_flat_table(
                unescaped_table_name=materialized_flat_history_table_name(data_series_id, data_series_external_id),
                target_table_type=TargetTableType.FLAT_HISTORY,
                escaped_schema_name=escaped_schema_name,
                index_rel_name=index_rel_name_flat_history(index_id),
                escaped_target_columns=escaped_schema_target_columns,
                index_id=index_id
            )
