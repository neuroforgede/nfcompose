# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from skipper.dataseries.models.partitions import fully_qualified_partition_table
from skipper.dataseries.storage.contract import StorageBackendType
from skipper.dataseries.storage.dynamic_sql.queries.common import can_use_materialized_table
from skipper.dataseries.storage.static_ds_information import BasicDataSeriesQueryInfo
from skipper.core.lint import lint, sql_cursor


def read_only_datapoint_by_id_query(
        data_series_query_info: BasicDataSeriesQueryInfo
) -> str:
    """
    constructs a query returning ds_dp.id, ds_dp.external_id in this order
    """
    # always check in the materialized table if possible
    # this makes the handling for materialized and flat history backend essentially the same
    use_materialized = can_use_materialized_table(data_series_query_info, False)
    sql = f"""
SELECT ds_dp.id, ds_dp.external_id
{render_base_sources(use_materialized, data_series_query_info)}
{render_where_part(use_materialized, data_series_query_info)}
AND ds_dp.id = %(data_point_id)s
"""
    lint(sql)
    return sql


def render_base_sources(use_materialized_table: bool, data_series_query_info: BasicDataSeriesQueryInfo) -> str:
    if use_materialized_table:
        return render_base_sources_materialized(data_series_query_info)
    else:
        return render_base_sources_point_in_time(data_series_query_info)


def render_base_sources_materialized(data_series_query_info: BasicDataSeriesQueryInfo) -> str:
    return f"FROM {data_series_query_info.schema_name}.{data_series_query_info.main_query_table_name} ds_dp"


def render_base_sources_point_in_time(data_series_query_info: BasicDataSeriesQueryInfo) -> str:
    return f"""
FROM {fully_qualified_partition_table('_3_data_point', data_series_query_info.data_series_id)} ds_dp
LEFT OUTER JOIN {fully_qualified_partition_table('_3_data_point', data_series_query_info.data_series_id)} ds_dp2 ON (
    ds_dp.data_series_id = ds_dp2.data_series_id
    AND ds_dp.id = ds_dp2.id
    AND (ds_dp.point_in_time, ds_dp.sub_clock) < (ds_dp2.point_in_time, ds_dp2.sub_clock)
)
"""


def render_where_part(use_materialized_table: bool, data_series_query_info: BasicDataSeriesQueryInfo) -> str:
    if use_materialized_table:
        return render_where_part_materialized(data_series_query_info)
    else:
        return render_where_part_point_in_time(data_series_query_info)


def render_where_part_materialized(data_series_query_info: BasicDataSeriesQueryInfo) -> str:
    return f"""
WHERE {data_series_query_info.main_alive_filter}
"""


def render_where_part_point_in_time(data_series_query_info: BasicDataSeriesQueryInfo) -> str:
    if data_series_query_info.backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value:
        return f"""
"""
    else:
        return f"""
WHERE ds_dp.data_series_id='{str(data_series_query_info.data_series_id)}'
AND ds_dp2.id IS NULL
AND ds_dp.deleted = false
"""
