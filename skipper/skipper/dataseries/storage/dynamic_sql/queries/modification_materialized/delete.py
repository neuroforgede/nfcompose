# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


import uuid
from typing import List, Tuple, Dict, Any

import datetime
from django.db import connections, transaction
from psycopg2 import sql  # type: ignore

from skipper.core.models.tenant import Tenant
from skipper.dataseries.raw_sql import escape
from skipper.dataseries.raw_sql.tenant import escaped_tenant_schema
from skipper.dataseries.storage.contract import StorageBackendType
from skipper.dataseries.storage.dynamic_sql.materialized import materialized_column_name, materialized_table_name
from skipper.dataseries.storage.dynamic_sql.queries.modification_materialized.history import insert_to_flat_history_query
from skipper.dataseries.storage.static_ds_information import DataPointSerializationKeys
from skipper.settings import DATA_SERIES_DYNAMIC_SQL_DB
from skipper.core.lint import sql_cursor
from skipper.dataseries.storage.dynamic_sql.queries.modification_materialized.order import FACT_DIM_ORDER_IN_SQL

def _generate_history_select_for_delete(
    keys: List[Tuple[str, uuid.UUID]],
    history_select_columns: List[Any]
) -> None:
    for external_id, uuid in keys:
        column_name = escape.escape(materialized_column_name(uuid, external_id))
        history_select_columns.append(f'"deleted".{column_name}')


def delete_datapoint(
        tenant: Tenant,
        data_series_id: str,
        data_series_external_id: str,
        backend: str,
        datapoint_id: str,
        datapoint_external_id: str,
        point_in_time: datetime.datetime,
        sub_clock: int,
        user_id: str,
        record_source: str,
        data_point_serialization_keys: DataPointSerializationKeys,
) -> None:
    schema_name = escaped_tenant_schema(tenant.name)
    table_name = escape.escape(materialized_table_name(data_series_id, data_series_external_id))

    history_select_columns = [
        '"deleted".id',
        '"deleted".external_id',
        '"deleted".point_in_time',
        '"deleted".inserted_at',
        '%(point_in_time)s AS "deleted_at"',
        '%(sub_clock)s AS "sub_clock"'
    ]

    for key in FACT_DIM_ORDER_IN_SQL:
        _generate_history_select_for_delete(data_point_serialization_keys[key], history_select_columns)  # type: ignore

    with transaction.atomic():
        with sql_cursor(DATA_SERIES_DYNAMIC_SQL_DB) as cursor:
            # Note: if we want to do a bulk delete at some point, we
            # only have to feed data in with a with statement similar to what we do
            # in the insert

            # default to inserting a deleted entry, but use upsert for actual delete if it exists
            # this ensures that we always return rows from this query without requiring a
            # second SQL statement therefore removing possible race conditions completely
            central_update_query = f"""
                INSERT INTO {schema_name}.{table_name} as target_tbl (
                    "id",
                    "external_id",
                    "point_in_time",
                    "inserted_at",
                    "deleted_at",
                    "sub_clock"
                )
                VALUES (
                    %(id)s,
                    %(external_id)s,
                    %(point_in_time)s,
                    %(point_in_time)s,
                    %(point_in_time)s,
                    %(sub_clock)s
                )
                ON CONFLICT (id) DO 
                    UPDATE
                    SET deleted_at = %(point_in_time)s,
                        sub_clock = %(sub_clock)s
                    WHERE (
                        (
                            target_tbl.sub_clock IS NULL AND (
                                target_tbl.point_in_time < %(point_in_time)s
                            )
                        ) OR (
                            target_tbl.sub_clock IS NOT NULL AND (
                                (target_tbl.point_in_time, target_tbl.sub_clock) < (%(point_in_time)s, %(sub_clock)s)
                            )
                        )
                    )
                """

            if backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value:
                _insert = insert_to_flat_history_query(
                    data_series_id=data_series_id,
                    data_series_external_id=data_series_external_id,
                    user_id=user_id,
                    record_source=record_source,
                    cursor=cursor,
                    source_query=f"""
                    SELECT {','.join(history_select_columns)}
                    FROM "deleted"
                    """,
                    escaped_schema_name=schema_name,
                    data_point_serialization_keys=data_point_serialization_keys,
                    with_statement_outside=True
                )
                final_update_query = f"""
                WITH "deleted" AS (
                    {central_update_query}
                    RETURNING *
                ),
                {_insert}
                """
            else:
                final_update_query = central_update_query

            cursor.execute(
                final_update_query,
                {
                    "id": datapoint_id,
                    "external_id": datapoint_external_id,
                    "point_in_time": point_in_time,
                    "sub_clock": sub_clock
                }
            )
