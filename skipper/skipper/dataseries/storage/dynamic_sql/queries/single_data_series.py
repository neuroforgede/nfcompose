# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


import re

import uuid

from rest_framework.exceptions import APIException
from typing import List, Union

from skipper.core.utils.functions import chunks
from skipper.dataseries.models.partitions import fully_qualified_partition_table
from skipper.dataseries.raw_sql.escape import escape
from skipper.dataseries.storage.contract import StorageBackendType
from skipper.dataseries.storage.dynamic_sql.queries.common import is_timestamp_utc_fact, \
    render_main_extra_fields_columns
from skipper.dataseries.storage.dynamic_sql.queries.versions import versions_render_with_join_parts, \
    versions_render_with_parts, versions_render_select
from skipper.dataseries.storage.static_ds_information import DataSeriesQueryInfo
from skipper.dataseries.storage.dynamic_sql.queries.select_info import SelectInfo

from skipper.dataseries.storage.dynamic_sql.queries.common import render_join_part, render_wheres
from skipper.core.lint import lint


def render_point_in_time(payload_as_json: bool) -> str:
    if payload_as_json:
        # actively convert to jsonb format
        # we want to be consistent with the format for timestamps
        return "to_char(ds_dp.point_in_time AT TIME ZONE 'utc', 'YYYY-MM-DD\"T\"HH24:MI:SS.US') as point_in_time"
    else:
        return "ds_dp.point_in_time AT TIME ZONE 'utc' as point_in_time"


def single_data_series_as_sql_table(
        all_select_infos: List[SelectInfo],
        data_series_query_info: DataSeriesQueryInfo,
        use_materialized: bool,
        payload_as_json: bool = False,
        point_in_time: bool = False,
        changes_since: bool = False,
        include_versions: bool = False,
        include_pagination_data: bool = False,
        filter_str: str = ''
) -> str:
    version_ds_dp = escape(f'version_ds_dp_{str(data_series_query_info.data_series_id)}')
    # if we use changes since,
    # the performance will suck extremely hard

    sql = f"""
{versions_render_with_parts(
        include_versions,
        version_ds_dp,
        data_series_query_info,
        all_select_infos
)}
SELECT "ds_dp"."id",
('{data_series_query_info.data_series_id}') as data_series_id
{render_payload_selects(use_materialized,
                        select_infos=all_select_infos, payload_as_json=payload_as_json, data_series_query_info=data_series_query_info)},
{versions_render_select(include_versions, version_ds_dp, data_series_query_info, all_select_infos)}
{render_point_in_time(payload_as_json)},
{render_pagination_data_select(include_pagination_data=include_pagination_data, use_materialized=use_materialized)}
{render_main_extra_fields_columns(main_tbl_alias='ds_dp', main_extra_fields=data_series_query_info.main_extra_fields)}
ds_dp.external_id
{render_base_sources(point_in_time, changes_since, use_materialized, data_series_query_info)}
{versions_render_with_join_parts(include_versions, version_ds_dp, data_series_query_info, all_select_infos)}
{render_where_part(point_in_time, changes_since, use_materialized, data_series_query_info.data_series_id, data_series_query_info)}
{filter_str}
"""

    compacted_sql = str(re.sub(r"([ ]+)", " ", sql)).strip()
    compacted_sql = str(re.sub(r"[\n]+", "\n", compacted_sql))
    lint(compacted_sql)
    return compacted_sql


def render_pagination_data_select(include_pagination_data: bool, use_materialized: bool) -> str:
    if not include_pagination_data:
        # only needed in payload as json
        return ''
    if use_materialized:
        return f"(jsonb_build_object('id', \"ds_dp\".\"id\", 'inserted_at', \"ds_dp\".\"inserted_at\")::jsonb) as \"pagination_data\","
    else:
        return f"(jsonb_build_object('id', ds_dp.id)::jsonb) as pagination_data,"


def render_payload_selects(use_materialized: bool, select_infos: List[SelectInfo], payload_as_json: bool, data_series_query_info: DataSeriesQueryInfo) -> str:
    # for the flat history backend, both the historical and
    # the normal table have essentially the same columns and access structure
    if use_materialized or data_series_query_info.backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value:
        return render_payload_selects_singular_table(select_infos, payload_as_json)
    else:
        return render_payload_selects_split_tables(select_infos, payload_as_json)


def render_payload_selects_singular_table(select_infos: List[SelectInfo], payload_as_json: bool) -> str:
    comma_nl = ',\n'
    if payload_as_json:
        chunk_strs = ["'{}'::jsonb"]
        select_info_chunk: List[SelectInfo]
        for select_info_chunk in chunks(select_infos, size=30):  # type: ignore
            argument_list: List[str] = []
            select_info: SelectInfo
            for select_info in select_info_chunk:
                value = f'ds_dp.{select_info.materialized_value_column}'

                if is_timestamp_utc_fact(select_info):
                    value = f"{value} AT TIME ZONE 'utc'"

                # THIS HAS TO BE ESCAPED, so we only add this outside,
                argument_list.append(f'%({select_info.payload_variable_name})s,{value}')
            chunk_strs.append(f'(jsonb_build_object({comma_nl.join(argument_list)})::jsonb)')

        return f',({"||".join(chunk_strs)}) as payload'
    else:
        if len(select_infos) == 0:
            return ""
        sub_parts: List[str] = []
        for select_info in select_infos:
            value = f'ds_dp.{select_info.materialized_value_column}'

            if is_timestamp_utc_fact(select_info):
                value = f"{value} AT TIME ZONE 'utc'"

            sub_part = f'{value} as {select_info.select_alias}'
            sub_parts.append(sub_part.strip())
        return f",{comma_nl.join(sub_parts)}"


def render_payload_selects_split_tables(select_infos: List[SelectInfo], payload_as_json: bool) -> str:
    comma_nl = ',\n'
    if payload_as_json:
        chunk_strs = ["'{}'::jsonb"]
        select_info_chunk: List[SelectInfo]
        for select_info_chunk in chunks(select_infos, size=30):  # type: ignore
            argument_list: List[str] = []
            select_info: SelectInfo
            for select_info in select_info_chunk:
                relation_table_name_alias = escape(f'relation_{select_info.unescaped_display_id}')

                value = f'{relation_table_name_alias}.{select_info.value_column}'

                if is_timestamp_utc_fact(select_info):
                    value = f"{value} AT TIME ZONE 'utc'"

                # THIS HAS TO BE ESCAPED, so we only add this outside,
                argument_list.append(f'%({select_info.payload_variable_name})s,{value}')

            chunk_strs.append(f'(jsonb_build_object({comma_nl.join(argument_list)})::jsonb)')

        return f',({"||".join(chunk_strs)}) as payload'
    else:
        if len(select_infos) == 0:
            return ""
        sub_parts: List[str] = []
        for select_info in select_infos:
            relation_table_name_alias = escape(f'relation_{select_info.unescaped_display_id}')

            value = f'{relation_table_name_alias}.{select_info.value_column}'

            if is_timestamp_utc_fact(select_info):
                value = f"{value} AT TIME ZONE 'utc'"

            sub_part = f'{value} as {select_info.select_alias}'
            sub_parts.append(sub_part.strip())
        return f",{comma_nl.join(sub_parts)}"


def render_where_part(
        point_in_time: bool,
        changes_since: bool,
        use_materialized_table: bool,
        data_series_id: Union[str, uuid.UUID],
        data_series_query_info: DataSeriesQueryInfo
) -> str:
    if use_materialized_table:
        return render_where_part_materialized(point_in_time, changes_since, data_series_query_info)
    else:
        if data_series_query_info.backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value:
            return render_where_part_flat_history(point_in_time, changes_since)
        else:
            return render_where_part_split(point_in_time, changes_since, data_series_id, data_series_query_info)


def render_where_part_materialized(
        point_in_time: bool,
        changes_since: bool,
        data_series_query_info: DataSeriesQueryInfo
) -> str:
    def render_changes_since_ds_dp() -> str:
        if not changes_since:
            return ""
        return f"AND ds_dp.point_in_time > %(changes_since)s"

    # if we use the materialized table in point_in_time queries (as in the no history backend, we still
    # have to be able to filter by insert date)
    _filter: str
    if point_in_time:
        # should not really happen, but be sure to throw a 500 error
        raise APIException({"detail": "materialized table is not allowed to be queried for historical data directly!"})
    else:
        _filter = f'''
            WHERE {data_series_query_info.main_alive_filter}
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


def render_where_part_split(point_in_time: bool, changes_since: bool, data_series_id: Union[str, uuid.UUID], data_series_query_info: DataSeriesQueryInfo) -> str:
    def render_changes_since_ds_dp() -> str:
        if not changes_since:
            return ""
        return f"AND ds_dp.point_in_time > %(changes_since)s"

    point_in_time_part_ds_dp = ''
    if point_in_time:
        point_in_time_part_ds_dp = f"AND ds_dp.point_in_time <= %(point_in_time)s"

    return f"""
WHERE ds_dp.data_series_id='{str(data_series_id)}'
{point_in_time_part_ds_dp}
AND ds_dp2.id IS NULL
AND ds_dp.deleted = false
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


def render_base_sources(point_in_time: bool, changes_since: bool, use_materialized_table: bool, data_series_query_info: DataSeriesQueryInfo) -> str:
    if use_materialized_table:
        return render_materialized_base_sources(data_series_query_info)
    else:
        if data_series_query_info.backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value:
            return render_materialized_flat_history_base_sources(point_in_time, changes_since, data_series_query_info)
        else:
            return render_historical_split_base_sources(point_in_time, changes_since, data_series_query_info)


def render_materialized_base_sources(data_series_query_info: DataSeriesQueryInfo) -> str:
    return f"""
FROM {data_series_query_info.schema_name}.{data_series_query_info.main_query_table_name} ds_dp
"""


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


def render_historical_split_base_sources(point_in_time: bool, changes_since: bool, data_series_query_info: DataSeriesQueryInfo) -> str:
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


