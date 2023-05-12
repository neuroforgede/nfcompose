# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from rest_framework.exceptions import APIException

from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.models.partitions import fully_qualified_partition_table
from skipper.dataseries.storage.contract import StorageBackendType
from skipper.dataseries.storage.static_ds_information import DataSeriesQueryInfo
from skipper.dataseries.storage.dynamic_sql.queries.common import render_join_part, render_wheres, \
    can_use_materialized_table
from skipper.core.lint import lint


def data_series_data_point_count(
        data_series: DataSeries,
        point_in_time: bool,
        changes_since: bool,
        used_data_series_children: DataSeriesQueryInfo,
        filter_str: str = ''
) -> str:
    use_materialized = can_use_materialized_table(used_data_series_children, point_in_time)
    sql = f"""
SELECT count(ds_dp.id)
{render_base_sources(use_materialized, changes_since, point_in_time, used_data_series_children)}
{render_where_part(point_in_time, changes_since, use_materialized, data_series, used_data_series_children)}
{filter_str}
"""
    lint(sql)
    return sql


def render_base_sources(use_materialized_table: bool, changes_since: bool, point_in_time: bool, data_series_query_info: DataSeriesQueryInfo) -> str:
    if use_materialized_table:
        return render_base_sources_materialized(data_series_query_info)
    else:
        if data_series_query_info.backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value:
            return render_materialized_flat_history_base_sources(point_in_time, changes_since, data_series_query_info)
        else:
            return render_historical_split_base_sources(changes_since, point_in_time, data_series_query_info)


def render_base_sources_materialized(data_series_query_info: DataSeriesQueryInfo) -> str:
    return f"FROM {data_series_query_info.schema_name}.{data_series_query_info.main_query_table_name} ds_dp"


def render_materialized_flat_history_base_sources(point_in_time: bool, changes_since: bool, data_series_query_info: DataSeriesQueryInfo) -> str:
    def render_changes_since_ds_dp2() -> str:
        if not changes_since:
            return ""
        return f"AND ds_dp2.point_in_time > %(changes_since)s"

    point_in_time_part_ds_dp2 = ''
    if point_in_time:
        point_in_time_part_ds_dp2 = f"AND ds_dp2.point_in_time <= %(point_in_time)s"

    return f"""
    FROM {data_series_query_info.schema_name}.{data_series_query_info.materialized_flat_history_table_name} ds_dp
    LEFT OUTER JOIN {data_series_query_info.schema_name}.{data_series_query_info.materialized_flat_history_table_name} ds_dp2 ON (
    ds_dp.id = ds_dp2.id
    AND (ds_dp.point_in_time, ds_dp.sub_clock) < (ds_dp2.point_in_time, ds_dp2.sub_clock)
    {point_in_time_part_ds_dp2}
    {render_changes_since_ds_dp2()}
    )
"""


def render_historical_split_base_sources(changes_since: bool, point_in_time: bool, data_series_query_info: DataSeriesQueryInfo) -> str:
    def render_changes_since_ds_dp2() -> str:
        if not changes_since:
            return ""
        return f"AND ds_dp2.point_in_time > %(changes_since)s"
    point_in_time_part_ds_dp2 = ''
    if point_in_time:
        point_in_time_part_ds_dp2 = f"AND ds_dp2.point_in_time <= %(point_in_time)s"
    return f"""
FROM {fully_qualified_partition_table('_3_data_point', data_series_query_info.data_series_id)} ds_dp
LEFT OUTER JOIN {fully_qualified_partition_table('_3_data_point', data_series_query_info.data_series_id)} ds_dp2 ON (
    ds_dp.data_series_id = ds_dp2.data_series_id
    AND ds_dp.id = ds_dp2.id
    AND (ds_dp.point_in_time, ds_dp.sub_clock) < (ds_dp2.point_in_time, ds_dp2.sub_clock)
    {point_in_time_part_ds_dp2}
    {render_changes_since_ds_dp2()}
)
{render_join_part(data_series_query_info.dimensions, '_3_data_point_dimension', 'dimension_id', point_in_time=point_in_time)}
{render_join_part(data_series_query_info.float_facts, '_3_data_point_float_fact',
                  'fact_id', point_in_time=point_in_time)}
{render_join_part(data_series_query_info.string_facts, '_3_data_point_string_fact',
                  'fact_id', point_in_time=point_in_time)}
{render_join_part(data_series_query_info.text_facts, '_3_data_point_text_fact',
                  'fact_id', point_in_time=point_in_time)}
{render_join_part(data_series_query_info.timestamp_facts, '_3_data_point_timestamp_fact',
                  'fact_id', point_in_time=point_in_time)}
{render_join_part(data_series_query_info.image_facts, '_3_data_point_image_fact',
                  'fact_id', point_in_time=point_in_time)}
{render_join_part(data_series_query_info.file_facts, '_3_data_point_file_fact',
                  'fact_id', point_in_time=point_in_time)}
{render_join_part(data_series_query_info.json_facts, '_3_data_point_json_fact', 
                  'fact_id', point_in_time=point_in_time)}
{render_join_part(data_series_query_info.boolean_facts, '_3_data_point_boolean_fact',
                  'fact_id', point_in_time=point_in_time)}
"""


def render_where_part(point_in_time: bool, changes_since: bool, use_materialized_table: bool, data_series: DataSeries, data_series_query_info: DataSeriesQueryInfo) -> str:
    if use_materialized_table:
        return render_where_part_materialized(point_in_time, changes_since)
    else:
        if data_series_query_info.backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value:
            return render_where_part_flat_history(point_in_time, changes_since)
        else:
            return render_where_part_split(point_in_time, changes_since, data_series, data_series_query_info)


def render_where_part_materialized(point_in_time: bool, changes_since: bool) -> str:
    def render_changes_since_ds_dp() -> str:
        if not changes_since:
            return ""
        return f"AND ds_dp.point_in_time > %(changes_since)s"

    # if we use the materialized table in point_in_time queries (as in the no history backend, we still
    # have to be able to filter by insert date)
    _filter: str
    if point_in_time:
        raise APIException(
            {"detail": "materialized table is not allowed to be queried for historical data directly!"})
        # _filter = f'''
        #     WHERE (ds_dp.deleted_at IS NULL or ds_dp.deleted_at > %(point_in_time)s)
        #     AND ds_dp.point_in_time <= %(point_in_time)s
        # '''
    else:
        _filter = f'''
            WHERE ds_dp.deleted_at IS NULL
        '''
    return f"""
{_filter}
{render_changes_since_ds_dp()}
"""


def render_where_part_flat_history(point_in_time: bool, changes_since: bool) -> str:
    def render_changes_since_ds_dp() -> str:
        if not changes_since:
            return ""
        return f"AND ds_dp.point_in_time > %(changes_since)s"

    point_in_time_part_ds_dp = ''
    if point_in_time:
        point_in_time_part_ds_dp = f"AND ds_dp.point_in_time <= %(point_in_time)s"

    return f"""
WHERE
ds_dp2.id IS NULL
AND ds_dp.deleted = false
{point_in_time_part_ds_dp}
{render_changes_since_ds_dp()}
"""


def render_where_part_split(point_in_time: bool, changes_since: bool, data_series: DataSeries, data_series_query_info: DataSeriesQueryInfo) -> str:
    def render_changes_since_ds_dp() -> str:
        if not changes_since:
            return ""
        return f"AND ds_dp.point_in_time > %(changes_since)s"

    point_in_time_part_ds_dp = ''
    if point_in_time:
        point_in_time_part_ds_dp = f"AND ds_dp.point_in_time <= %(point_in_time)s"
    return f"""
WHERE ds_dp.data_series_id='{str(data_series.id)}'
AND ds_dp2.id IS NULL
AND ds_dp.deleted = false
{point_in_time_part_ds_dp}
{render_wheres(data_series_query_info.dimensions)}
{render_wheres(data_series_query_info.float_facts)}
{render_wheres(data_series_query_info.string_facts)}
{render_wheres(data_series_query_info.text_facts)}
{render_wheres(data_series_query_info.timestamp_facts)}
{render_wheres(data_series_query_info.image_facts)}
{render_wheres(data_series_query_info.file_facts)}
{render_wheres(data_series_query_info.json_facts)}
{render_wheres(data_series_query_info.boolean_facts)}
{render_changes_since_ds_dp()}
"""
