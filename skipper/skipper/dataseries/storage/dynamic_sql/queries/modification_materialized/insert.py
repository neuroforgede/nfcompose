# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


import json
import uuid

import datetime
from django.core.files.uploadedfile import InMemoryUploadedFile
from psycopg2.extras import execute_values  # type: ignore
from typing import Iterable, Dict, Any, List, Tuple, Optional, Union, Sequence

from skipper.core.models.fields import default_media_storage
from skipper.dataseries.raw_sql import escape
from skipper.dataseries.raw_sql.tenant import escaped_tenant_schema
from skipper.dataseries.storage.contract import StorageBackendType, file_registry
from skipper.dataseries.storage.contract.file_registry import HistoryDataPointIdentifier, delete_all_but_latest_for_datapoints
from skipper.dataseries.storage.dynamic_sql.materialized import materialized_column_name, materialized_table_name
from skipper.dataseries.storage.static_ds_information import DataPointSerializationKeys
from skipper.settings import DATA_SERIES_DYNAMIC_SQL_DB
from skipper.core.lint import sql_cursor
from skipper.dataseries.storage.dynamic_sql.queries.modification_materialized.history import insert_to_flat_history_query
from skipper.dataseries.storage.dynamic_sql.queries.modification_materialized.order import FACT_DIM_ORDER_IN_SQL, FACT_DIM_TYPES, add_columns_to_list, add_columns_to_types_list
from skipper.dataseries.storage.dynamic_sql.migrations.custom_v1.helpers import data_point_id_column_def, external_id_column_def

def _add_json_values_to_list(keys: Sequence[Tuple[str, Union[str, uuid.UUID]]], _validated_data: Dict[str, Any], values: List[Any]) -> None:
    for external_id, uuid in keys:
        if external_id in _validated_data['payload']:
            values.append(json.dumps(_validated_data['payload'][external_id]))
        else:
            values.append(None)


def _add_file_like_values_to_list(
        keys: Sequence[Tuple[str, Union[str, uuid.UUID]]],
        _validated_data: Dict[str, Any],
        values: List[Any],
        tenant_id: Union[str, uuid.UUID],
        data_series_id: str,
        point_in_time: datetime.datetime,
        sub_clock: int,
        backend: str
) -> None:
    _files_to_save: List[InMemoryUploadedFile] = []
    for external_id, uuid in keys:
        if external_id in _validated_data['payload']:
            _val: InMemoryUploadedFile = _validated_data['payload'][external_id]
            if _val is not None and backend in [
                    StorageBackendType.DYNAMIC_SQL_NO_HISTORY.value,
                    StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value
            ]:
                file_registry.save(
                    storage=default_media_storage,
                    tenant_id=tenant_id,
                    data_series_id=data_series_id,
                    fact_id=uuid,
                    history_data_point_identifier=HistoryDataPointIdentifier(
                        data_point_id=_validated_data['id'],
                        point_in_time=point_in_time,
                        sub_clock=sub_clock
                    ),
                    file=_val
                )
            if _val is not None:
                values.append(_val.name)
            else:
                values.append(None)
        else:
            values.append(None)


def _add_values_to_list(keys: List[Tuple[str, uuid.UUID]], _validated_data: Dict[str, Any], values: List[Any]) -> None:
    for external_id, uuid in keys:
        if external_id in _validated_data['payload']:
            values.append(_validated_data['payload'][external_id])
        else:
            values.append(None)


def _generate_set_statements_non_partial(
        keys: List[Tuple[str, uuid.UUID]],
        statements: List[Any]
) -> None:
    for external_id, uuid in keys:
        # this is non partial overwrite everything
        column_name = escape.escape(materialized_column_name(uuid, external_id))
        statements.append(f'{column_name} = EXCLUDED.{column_name}')


def _generate_set_statements_for_single(keys: List[Tuple[str, uuid.UUID]], _validated_data: Dict[str, Any], statements: List[Any]) -> None:
    for external_id, uuid in keys:
        if external_id in _validated_data['payload']:
            column_name = escape.escape(materialized_column_name(uuid, external_id))
            statements.append(f'{column_name} = EXCLUDED.{column_name}')


def _generate_history_select_non_partial(
        keys: List[Tuple[str, uuid.UUID]],
        history_select_columns: List[Any]
) -> None:
    for external_id, uuid in keys:
        # this is non partial overwrite everything
        column_name = escape.escape(materialized_column_name(uuid, external_id))
        history_select_columns.append(f'"values_to_insert".{column_name}')


def _generate_history_select_for_single(
    keys: List[Tuple[str, uuid.UUID]],
    _validated_data: Dict[str, Any],
    history_select_columns: List[Any]
) -> None:
    for external_id, uuid in keys:
        if external_id in _validated_data['payload']:
            column_name = escape.escape(materialized_column_name(uuid, external_id))
            history_select_columns.append(f'"values_to_insert".{column_name}')
        else:
            column_name = escape.escape(materialized_column_name(uuid, external_id))
            history_select_columns.append(f'"inserted".{column_name}')



def insert_or_update_data_points(
        tenant_id: Union[str, uuid.UUID],
        tenant_name: str,
        data_series_id: str,
        data_series_external_id: str,
        point_in_time: datetime.datetime,
        data_point_serialization_keys: DataPointSerializationKeys,
        validated_datas: Iterable[Dict[str, Any]],
        partial: bool,
        sub_clock: int,
        backend: str,
        user_id: str,
        record_source: str
) -> None:
    columns = ['id', 'external_id', 'point_in_time', 'inserted_at', 'deleted_at', 'sub_clock']
    col_types = [data_point_id_column_def, external_id_column_def, 'timestamp with time zone', 'timestamp with time zone', 'timestamp with time zone', 'bigint']
    history_select_columns = [f'"values_to_insert".{escape.escape(column)}' for column in columns]
    set_statements = [
        # keep old inserted_at if not deleted, change inserted_at to new value if was deleted
        """inserted_at = CASE 
            WHEN target_tbl.deleted_at is NULL
                THEN target_tbl.inserted_at 
                ELSE EXCLUDED.inserted_at
            END""",
        'deleted_at = EXCLUDED.deleted_at',
        'point_in_time = EXCLUDED.point_in_time',
        'sub_clock = EXCLUDED.sub_clock'
    ]

    # FIXME: determine if something is a PUT, if yes, we can use update set? or does the performance not matter
    # and a regular upsert is enough?

    if partial:
        for validated_data in validated_datas:
            for key, col_type in FACT_DIM_TYPES:
                add_columns_to_list(data_point_serialization_keys[key], columns)  # type: ignore
                _generate_set_statements_for_single(data_point_serialization_keys[key], validated_data, set_statements)  # type: ignore
                add_columns_to_types_list(data_point_serialization_keys[key], col_type, col_types)  # type: ignore
                _generate_history_select_for_single(data_point_serialization_keys[key], validated_data, history_select_columns)  # type: ignore
            # FIXME: partial is a patch, so we can actually always enforce the usage of UPDATE SET?
            # when doing a patch, we need to do a lock for update and properly do the handling of point_in_time
            _insert_or_update_data_points_impl(
                tenant_id=tenant_id,
                tenant_name=tenant_name,
                data_series_id=data_series_id,
                data_series_external_id=data_series_external_id,
                point_in_time=point_in_time,
                data_point_serialization_keys=data_point_serialization_keys,
                validated_datas=[validated_data],
                set_statements=set_statements,
                history_select_columns=history_select_columns,
                columns=columns,
                column_types=col_types,
                sub_clock=sub_clock,
                backend=backend,
                user_id=user_id,
                record_source=record_source
            )
    else:
        for key, col_type in FACT_DIM_TYPES:
            add_columns_to_list(data_point_serialization_keys[key], columns)  # type: ignore
            _generate_set_statements_non_partial(data_point_serialization_keys[key], set_statements)  # type: ignore
            add_columns_to_types_list(data_point_serialization_keys[key], col_type, col_types)  # type: ignore
            _generate_history_select_non_partial(data_point_serialization_keys[key], history_select_columns)  # type: ignore
        _insert_or_update_data_points_impl(
            tenant_id=tenant_id,
            tenant_name=tenant_name,
            data_series_id=data_series_id,
            data_series_external_id=data_series_external_id,
            point_in_time=point_in_time,
            data_point_serialization_keys=data_point_serialization_keys,
            validated_datas=validated_datas,
            set_statements=set_statements,
            history_select_columns=history_select_columns,
            columns=columns,
            column_types=col_types,
            sub_clock=sub_clock,
            backend=backend,
            user_id=user_id,
            record_source=record_source
        )


def _insert_or_update_data_points_impl(
        tenant_id: Union[str, uuid.UUID],
        tenant_name: str,
        data_series_id: str,
        data_series_external_id: str,
        point_in_time: datetime.datetime,
        data_point_serialization_keys: DataPointSerializationKeys,
        validated_datas: Iterable[Dict[str, Any]],
        set_statements: List[str],
        history_select_columns: List[str],
        columns: List[str],
        column_types: List[str],
        sub_clock: Optional[int],
        backend: str,
        user_id: str,
        record_source: str
) -> None:
    schema_name = escaped_tenant_schema(tenant_name)
    table_name = escape.escape(materialized_table_name(data_series_id, data_series_external_id))

    all_values = []

    for validated_data in validated_datas:
        values = [
            validated_data['id'],
            validated_data['external_id'],
            point_in_time,  # point_in_time
            point_in_time,  # inserted_at, upsert will take care of this
            None,  # deleted_at,
            sub_clock
        ]

        for key in FACT_DIM_ORDER_IN_SQL:
            # for images we have to get the value from the object that we already persisted earlier
            # and then extract the filename out of it.
            if key == 'image_facts':
                _add_file_like_values_to_list(
                    data_point_serialization_keys['image_facts'],
                    validated_data,
                    values,
                    tenant_id=tenant_id,
                    data_series_id=data_series_id,
                    point_in_time=point_in_time,
                    sub_clock=sub_clock,
                    backend=backend
                )
            elif key == 'file_facts':
                _add_file_like_values_to_list(
                    data_point_serialization_keys['file_facts'],
                    validated_data,
                    values,
                    tenant_id=tenant_id,
                    data_series_id=data_series_id,
                    point_in_time=point_in_time,
                    sub_clock=sub_clock,
                    backend=backend
                )
            elif key == 'json_facts':
                _add_json_values_to_list(data_point_serialization_keys['json_facts'], validated_data, values)
            else:
                _add_values_to_list(data_point_serialization_keys[key], validated_data, values)  # type: ignore

        all_values.append(values)

    with sql_cursor(DATA_SERIES_DYNAMIC_SQL_DB) as cursor:
        with_statement = f"""
        WITH "values_to_insert" AS (
            SELECT {','.join(map(lambda x: f'{x[0]}::{x[1]}', zip(columns, column_types)))} FROM (
                VALUES %s
            ) AS "t" ({','.join(columns)})
        )
        """

        # for concurrent updates, only upsert if current date is newer
        # than already existing one
        central_insert = f"""
            INSERT INTO {schema_name}.{table_name} AS target_tbl (
                {','.join(columns)}
            )
            SELECT * FROM "values_to_insert"
            ON CONFLICT (id) DO 
                UPDATE SET {','.join(set_statements)}
                WHERE
                    (
                        target_tbl.sub_clock IS NULL AND (
                                target_tbl.point_in_time < EXCLUDED.point_in_time AND target_tbl.deleted_at IS NULL
                            OR  target_tbl.deleted_at < EXCLUDED.point_in_time AND target_tbl.deleted_at IS NOT NULL
                        )
                    ) OR (
                        target_tbl.sub_clock IS NOT NULL AND (
                                (target_tbl.point_in_time, target_tbl.sub_clock) < (EXCLUDED.point_in_time, EXCLUDED.sub_clock) AND target_tbl.deleted_at IS NULL
                            OR  (target_tbl.deleted_at, target_tbl.sub_clock) < (EXCLUDED.point_in_time, EXCLUDED.sub_clock) AND target_tbl.deleted_at IS NOT NULL
                        )
                    )
            """
        
        if backend == StorageBackendType.DYNAMIC_SQL_NO_HISTORY.value:
            data_point_ids = [elem['id'] for elem in validated_datas]
            delete_all_but_latest_for_datapoints(
                tenant_id=tenant_id,
                data_series_id=data_series_id,
                data_point_ids=data_point_ids,
                point_in_time=point_in_time
            )

        # FIXME: join the RETURNING * with the original values to construct the actual historical value
        # IDEA: put the original values into a virtual table with WITH, then read from it to insert
        if backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value:
            _insert = insert_to_flat_history_query(
                data_series_id=data_series_id,
                data_series_external_id=data_series_external_id,
                user_id=user_id,
                record_source=record_source,
                cursor=cursor,
                source_query=f"""
                SELECT {','.join(history_select_columns)}
                FROM "values_to_insert"
                JOIN "inserted" ON (
                    "values_to_insert"."id" = "inserted"."id"
                )
                """,
                escaped_schema_name=schema_name,
                data_point_serialization_keys=data_point_serialization_keys,
                with_statement_outside=True
            )
            final_insert_sql = f"""
            {with_statement},
            "inserted" AS (
                {central_insert}
                RETURNING *
            ),
            {_insert}
            """
        else:
            final_insert_sql = f"""
            {with_statement}
            {central_insert}
            """

        execute_values(
            cursor,
            final_insert_sql,
            all_values
        )

