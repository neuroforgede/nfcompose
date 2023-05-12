# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from rest_framework.exceptions import ValidationError
from typing import List

from skipper.core.utils.functions import chunks
from skipper.dataseries.models.partitions import fully_qualified_partition_table
from skipper.dataseries.storage.contract import StorageBackendType
from skipper.dataseries.storage.dynamic_sql.queries.select_info import SelectInfo
from skipper.dataseries.storage.static_ds_information import DataSeriesQueryInfo
from skipper.core.lint import lint


def versions_render_with_join_parts(include_versions: bool, version_ds_dp: str,
                                    data_series_query_info: DataSeriesQueryInfo,
                                    select_infos: List[SelectInfo]) -> str:
    if not include_versions:
        return ""
    if data_series_query_info.backend == StorageBackendType.DYNAMIC_SQL_NO_HISTORY.value:
        # in the no history backend we currently have no way to check the version
        # if we want to support this, we have to add a record source and an id to the table
        # for now, we simply do not support it
        raise ValidationError(
            detail={
                "error": 'DYNAMIC_SQL_NO_HISTORY backend does not allow for querying for versions'
            }
        )
    comma_nl = '\n'
    parts: List[str] = [f'LEFT OUTER JOIN {version_ds_dp} ON ({version_ds_dp}.id = ds_dp.id)']

    if data_series_query_info.backend != StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value:
        for select_info in select_infos:
            parts.append(
                f'LEFT OUTER JOIN {select_info.version_alias_name} ON ({select_info.version_alias_name}.data_point_id = ds_dp.id)')
    return comma_nl.join(parts)


def versions_render_with_parts(
        include_versions: bool,
        version_ds_dp: str,
        data_series_query_info: DataSeriesQueryInfo,
        _select_infos: List[SelectInfo]
) -> str:
    if not include_versions:
        return ""
    if data_series_query_info.backend == StorageBackendType.DYNAMIC_SQL_NO_HISTORY.value:
        # in the no history backend we currently have no way to check the version
        # if we want to support this, we have to add a record source and an id to the table
        # for now, we simply do not support it
        raise ValidationError(
            detail={
                "error": f'{data_series_query_info.backend} backend does not allow for querying for versions'
            }
        )

    if data_series_query_info.backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value:
        return f"""
        WITH
{version_ds_dp} AS (
    SELECT id, jsonb_agg(jsonb_build_object('point_in_time', point_in_time AT TIME ZONE 'utc', 'sub_clock', sub_clock, 'user_id', user_id, 'record_source', record_source) ORDER BY (point_in_time, sub_clock)) as data_point_versions
FROM {data_series_query_info.schema_name}.{data_series_query_info.materialized_flat_history_table_name}
GROUP BY 1
)
"""

    else:
        parts: List[str] = []
        base = f"""
WITH
{version_ds_dp} AS (
    SELECT id, jsonb_agg(jsonb_build_object('point_in_time', point_in_time AT TIME ZONE 'utc', 'sub_clock', sub_clock, 'user_id', user_id, 'record_source', record_source) ORDER BY (point_in_time, sub_clock)) as data_point_versions
FROM {fully_qualified_partition_table('_3_data_point', data_series_query_info.data_series_id)}
WHERE data_series_id='{str(data_series_query_info.data_series_id)}'
GROUP BY 1
)"""
        parts.append(base)

        comma_nl = ',\n'
        for select_info in _select_infos:
            part = f"""
{select_info.version_alias_name} AS (
SELECT data_point_id, jsonb_agg(jsonb_build_object('point_in_time', point_in_time AT TIME ZONE 'utc', 'sub_clock', sub_clock, 'user_id', user_id, 'record_source', record_source) ORDER BY (point_in_time, sub_clock)) as "versions"
FROM {fully_qualified_partition_table(select_info.actual_table_name, select_info.actual_id)}
WHERE {select_info.fact_or_dim_id}='{select_info.actual_id}'
GROUP BY 1
)"""
            parts.append(part)
        sql = comma_nl.join(parts)
        lint(sql)
        return sql


def versions_render_select(
        include_versions: bool,
        version_ds_dp: str,
        data_series_query_info: DataSeriesQueryInfo,
        select_infos: List[SelectInfo]
) -> str:
    if not include_versions:
        return ""

    if data_series_query_info.backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value:
        return f"jsonb_build_object('data_point', jsonb_strip_nulls({version_ds_dp}.data_point_versions))::jsonb as versions,"

    comma_nl = ',\n'
    chunk_strs = ["'{}'::jsonb"]
    select_info_chunk: List[SelectInfo]
    for select_info_chunk in chunks(select_infos, size=30):  # type: ignore
        argument_list: List[str] = []
        select_info: SelectInfo
        for select_info in select_info_chunk:
            value = f'{select_info.version_alias_name}.versions'
            argument_list.append(f'%({select_info.payload_variable_name})s,{value}')
        chunk_strs.append(f'(jsonb_build_object({comma_nl.join(argument_list)})::jsonb)')

    return f"jsonb_build_object('data_point', jsonb_strip_nulls({version_ds_dp}.data_point_versions), 'payload', jsonb_strip_nulls(({'||'.join(chunk_strs)})))::jsonb as versions,"