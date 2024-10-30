# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


from psycopg import sql  # type: ignore
from typing import Any, List, Optional

from skipper.dataseries.raw_sql import escape
from skipper.dataseries.storage.dynamic_sql.materialized import materialized_flat_history_table_name
from skipper.dataseries.storage.static_ds_information import DataPointSerializationKeys
from skipper.dataseries.storage.dynamic_sql.queries.modification_materialized.order import FACT_DIM_ORDER_IN_SQL, add_columns_to_list


def insert_to_flat_history_query(
    data_series_id: str,
    data_series_external_id: str,
    user_id: Optional[str],
    record_source: str,
    cursor: Any,
    source_query: str,
    escaped_schema_name: str,
    data_point_serialization_keys: DataPointSerializationKeys,
    with_statement_outside: bool = False
) -> str:
    """
    :param data_series_id: the id of the dataseries the flat history belongs to
    :param data_series_external_id: The external id of the dataseries the flat history belongs to
    :param user_id: the optional user id that wrote the data.
    :param record_source: a string identifying where the data is coming from. Examples "REST PUT", "REST DELETE"
    :param cursor: the psycopg cursor to use for this query

    :param source_query: the query to use to fill the history table from. This may be an INSERT ... RETURNING * query or a simple SELECT
    as long as the table has all the necessary columns.
    Required columns are: 'id', 'external_id', 'point_in_time', 'deleted', 'user_id', 'record_source', 'sub_clock'
    Data columns must adhere to the format of materialized_column_name called on the elements of data_point_serialization_keys.

    :param escaped_schema_name: the schema name the flat history table resides in. usually this is fetched via escaped_tenant_schema(...)
    :data_point_serialization_keys: the relevant DataPointSerializationKeys.
    """
    flat_history_table_name = escape.escape(materialized_flat_history_table_name(data_series_id, data_series_external_id))

    base_flat_cols = ['id', 'external_id', 'point_in_time', 'deleted', 'user_id', 'record_source', 'sub_clock']
    flat_data_cols: List[str] = []
    for key in FACT_DIM_ORDER_IN_SQL:
        add_columns_to_list(data_point_serialization_keys[key], flat_data_cols)  # type: ignore
    all_flat_cols = base_flat_cols + flat_data_cols

    user_id_and_record_source = sql.SQL(', ').join([sql.Literal(user_id) if user_id is not None else sql.NULL, sql.Literal(record_source)]).as_string(cursor.cursor)

    data_col_string = ''
    if len(flat_data_cols) > 0:
        data_col_string = f""", {','.join([f"rows.{elem}" for elem in flat_data_cols])}"""

    return f"""
            {'WITH' if not with_statement_outside else ''} rows AS (
            {source_query}
            )
            INSERT INTO {escaped_schema_name}.{flat_history_table_name}(
            {','.join(all_flat_cols)}
            )
            SELECT 
                rows.id,
                rows.external_id,
                CASE 
                    WHEN rows.deleted_at IS NULL THEN rows.point_in_time
                    ELSE rows.deleted_at
                END,
                CASE
                    WHEN rows.deleted_at IS NULL THEN false
                    ELSE true
                END,
                {user_id_and_record_source},
                rows.sub_clock {data_col_string}
            FROM rows
    """