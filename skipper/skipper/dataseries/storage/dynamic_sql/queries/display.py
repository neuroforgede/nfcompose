# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from functools import lru_cache
from rest_framework.exceptions import APIException
from typing import Optional, Dict, List

from skipper.core.utils.functions import chunks
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.models.partitions import fully_qualified_partition_table
from skipper.dataseries.raw_sql.escape import escape
from skipper.dataseries.storage.contract import StorageBackendType
from skipper.dataseries.storage.dynamic_sql.queries.common import can_use_materialized_table, \
    render_main_extra_fields_columns
from skipper.dataseries.storage.static_ds_information import DataSeriesQueryInfo, \
    compute_data_series_query_info, compute_basic_data_series_query_info
from skipper.dataseries.storage.dynamic_sql.queries.select_info import select_infos, SelectInfo, \
    _data_series_dimension_to_select_info
from skipper.dataseries.storage.dynamic_sql.queries.single_data_series import single_data_series_as_sql_table
from skipper.core.lint import lint

_central_table = escape('__central_table')


def render_selects(unescaped_display_ids_with_order: List[SelectInfo], payload_as_json: bool, agg_dimension_select_infos: Dict[str, SelectInfo] = {}) -> str:
    comma_nl = ',\n'
    if payload_as_json:
        chunk_strs = ["'{}'::jsonb"]
        unescaped_display_id_with_order_chunk: List[SelectInfo]
        for unescaped_display_id_with_order_chunk in chunks(unescaped_display_ids_with_order, size=30):  # type: ignore
            argument_list: List[str] = []
            unescaped_display_id_with_order: SelectInfo
            for unescaped_display_id_with_order in unescaped_display_id_with_order_chunk:
                value = f'{_central_table}.{unescaped_display_id_with_order.select_alias}'

                if unescaped_display_id_with_order.actual_id in agg_dimension_select_infos:
                    value = f'{escape(f"__resolve_{unescaped_display_id_with_order.actual_id}")}.external_id'

                # THIS HAS TO BE ESCAPED, so we only add this outside,
                argument_list.append(f'%({unescaped_display_id_with_order.payload_variable_name})s,{value}')
            chunk_strs.append(f'(jsonb_build_object({comma_nl.join(argument_list)})::jsonb)')

        return f',({"||".join(chunk_strs)}) as payload'
    else:
        if len(unescaped_display_ids_with_order) == 0:
            return ""
        sub_parts: List[str] = []
        for unescaped_display_id_with_order in unescaped_display_ids_with_order:
            value = f'{_central_table}.{unescaped_display_id_with_order.select_alias}'

            if unescaped_display_id_with_order.actual_id in agg_dimension_select_infos:
                value = f'{escape(f"__resolve_{unescaped_display_id_with_order.actual_id}")}.external_id'

            sub_part = f'{value} as {unescaped_display_id_with_order.select_alias}'
            sub_parts.append(sub_part.strip())
        return f",{comma_nl.join(sub_parts)}"


def render_version_select(include_versions: bool) -> str:
    if not include_versions:
        return ""
    return f'{_central_table}.versions,'


def render_current_version_select(payload_as_json: bool) -> str:
    if payload_as_json:
        return f"to_char({_central_table}.point_in_time AT TIME ZONE 'utc', 'YYYY-MM-DD\"T\"HH24:MI:SS.US') as point_in_time,"
    else:
        return f"{_central_table}.point_in_time AT TIME ZONE 'utc' as point_in_time,"


def render_pagination_data_select(include_pagination_data: bool) -> str:
    if not include_pagination_data:
        # only needed in payload as json
        return ''
    return f'{_central_table}.pagination_data,'


def _data_series_as_sql_table(
        include_in_payload: Optional[List[str]],
        payload_as_json: bool,
        point_in_time: bool,
        changes_since: bool,
        include_versions: bool,
        filter_str: str,
        resolve_dimension_external_ids: bool,
        data_series_query_info: DataSeriesQueryInfo,
        use_materialized: Optional[bool]
) -> str:
    include_pagination_data = payload_as_json
    _data_series_query_info = data_series_query_info

    _use_materialized = can_use_materialized_table(_data_series_query_info, point_in_time)
    if use_materialized is not None:
        _use_materialized = use_materialized

    _data_series_query_info.dimensions.keys()
    actually_resolve_dimension_external_ids: bool = resolve_dimension_external_ids \
                                                    and len(_data_series_query_info.dimensions.keys()) > 0

    all_select_infos = select_infos(_data_series_query_info)
    if include_in_payload is not None:
        all_select_infos = [select_info for select_info in all_select_infos if select_info.unescaped_display_id in include_in_payload]

    central_table_sql = single_data_series_as_sql_table(
        all_select_infos=all_select_infos,
        data_series_query_info=_data_series_query_info,
        use_materialized=_use_materialized,
        # if we resolve dimensions, we always use non json here because
        # the central table will only be used in a with clause
        payload_as_json=payload_as_json and not actually_resolve_dimension_external_ids,
        include_pagination_data=include_pagination_data,
        point_in_time=point_in_time,
        changes_since=changes_since,
        include_versions=include_versions,
        filter_str=filter_str
    )
    if not actually_resolve_dimension_external_ids:
        return central_table_sql
    else:
        _agg_dimension_select_infos: Dict[str, SelectInfo] = {}
        dimension_resolution_sql: List[str] = []
        join_parts: List[str] = []

        # TODO: move this into a separate function, this is ugly to read inline here
        for _dim_external_id, _dimension_query_info in _data_series_query_info.dimensions.items():
            _select_info = _data_series_dimension_to_select_info(_dimension_query_info.dataseries_dimension)
            _agg_dimension_select_infos[str(_dimension_query_info.dimension.id)] = _select_info
            point_in_time_part_ds_dp = ''
            point_in_time_part_ds_dp2 = ''
            if point_in_time:
                point_in_time_part_ds_dp = f"AND ds_dp.point_in_time <= %(point_in_time)s"
                point_in_time_part_ds_dp2 = f"AND ds_dp2.point_in_time <= %(point_in_time)s"

            if _use_materialized:
                __dim_filter: str
                if point_in_time:
                    # unsure if this would ever happen, but guard against it nonetheless
                    raise APIException({"detail": "materialized table is not allowed to be queried for historical data directly!"})
                else:
                    __dim_filter = f'''
                            WHERE {_dimension_query_info.dimension.reference.main_alive_filter}
                        '''
                _sql = f"""
                    {escape(f'__resolve_{_select_info.actual_id}')} AS (
                        SELECT ds_dp.id as data_point_id, ds_dp.external_id as external_id
                        FROM {_dimension_query_info.dimension.reference.schema_name}.{_dimension_query_info.dimension.reference.main_query_table_name} ds_dp
                        {__dim_filter}
                    )
                """
            else:
                if _dimension_query_info.dimension.reference.backend == StorageBackendType.DYNAMIC_SQL_NO_HISTORY.value:
                    # lets do our best, either we did not delete it or we deleted it after that point in time
                    # also make sure we did exist at that point in time already
                    _sql = f"""
                    {escape(f'__resolve_{_select_info.actual_id}')} AS (
                        SELECT ds_dp.id as data_point_id, ds_dp.external_id as external_id
                        FROM {_dimension_query_info.dimension.reference.schema_name}.{_dimension_query_info.dimension.reference.main_query_table_name} ds_dp
                        WHERE ds_dp.deleted_at IS NULL OR ds_dp.deleted_at >= %(point_in_time)s
                        AND ds_dp.inserted_at <= %(point_in_time)s
                    )
                    """
                elif _dimension_query_info.dimension.reference.backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value:
                    _sql = f"""
                        {escape(f'__resolve_{_select_info.actual_id}')} AS (
                            SELECT ds_dp.id as data_point_id, ds_dp.external_id as external_id
                            FROM {_dimension_query_info.dimension.reference.schema_name}.{_dimension_query_info.dimension.reference.materialized_flat_history_table_name} ds_dp
                            LEFT OUTER JOIN {_dimension_query_info.dimension.reference.schema_name}.{_dimension_query_info.dimension.reference.materialized_flat_history_table_name} ds_dp2 ON (
                                ds_dp.id = ds_dp2.id
                                AND (ds_dp.point_in_time, ds_dp.sub_clock) < (ds_dp2.point_in_time, ds_dp2.sub_clock)
                                {point_in_time_part_ds_dp2}
                            )
                            WHERE ds_dp2.id IS NULL
                            AND ds_dp.deleted = false
                            {point_in_time_part_ds_dp}
                        )
                    """
                else:
                    _sql = f"""
                        {escape(f'__resolve_{_select_info.actual_id}')} AS (
                            SELECT ds_dp.id as data_point_id, ds_dp.external_id as external_id
                            FROM {fully_qualified_partition_table('_3_data_point', _dimension_query_info.dimension.reference.id)} ds_dp
                            LEFT OUTER JOIN {fully_qualified_partition_table('_3_data_point', _dimension_query_info.dimension.reference.id)} ds_dp2 ON (
                                ds_dp.data_series_id = ds_dp2.data_series_id
                                AND ds_dp.id = ds_dp2.id
                                AND (ds_dp.point_in_time, ds_dp.sub_clock) < (ds_dp2.point_in_time, ds_dp2.sub_clock)
                                {point_in_time_part_ds_dp2}
                            )
                            WHERE ds_dp.data_series_id='{str(_dimension_query_info.dimension.reference.id)}'
                            AND ds_dp2.id IS NULL
                            AND ds_dp.deleted = false
                            {point_in_time_part_ds_dp}
                        )
                    """
            dimension_resolution_sql.append(_sql)

            _join_sql = f"""
            LEFT OUTER JOIN {escape(f'__resolve_{_select_info.actual_id}')} ON (
                {escape('__central_table')}.{_select_info.select_alias} = {escape(f'__resolve_{_select_info.actual_id}')}.data_point_id
            )
            """
            join_parts.append(_join_sql)

        # continue, we gathered all required joins for resolution of dimensions
        # build up the central query and return the sql string
        all_with_parts = ',\n'.join([f'WITH {_central_table} AS ({central_table_sql})', *dimension_resolution_sql])
        all_join_parts = '\n'.join(join_parts)
        final_sql = f"""
{all_with_parts}
SELECT {_central_table}.id,
{_central_table}.data_series_id
{render_selects(all_select_infos, agg_dimension_select_infos=_agg_dimension_select_infos, payload_as_json=payload_as_json)},
{render_version_select(include_versions)}
{render_current_version_select(payload_as_json=payload_as_json)}
{render_pagination_data_select(include_pagination_data=include_pagination_data)}
{render_main_extra_fields_columns(main_tbl_alias=_central_table, main_extra_fields=data_series_query_info.main_extra_fields)}
{_central_table}.external_id
FROM {_central_table}
{all_join_parts}
"""
        return final_sql


def data_series_as_sql_table(
        data_series: DataSeries,
        include_in_payload: List[str],
        payload_as_json: bool = False,
        point_in_time: bool = False,
        changes_since: bool = False,
        include_versions: bool = False,
        filter_str: str = '',
        resolve_dimension_external_ids: bool = False,
        data_series_query_info: Optional[DataSeriesQueryInfo] = None,
        use_materialized: Optional[bool] = None,
) -> str:
    _data_series_query_info: DataSeriesQueryInfo
    if data_series_query_info is None:
        _data_series_query_info = compute_data_series_query_info(data_series)
    else:
        _data_series_query_info = data_series_query_info

    sql = _data_series_as_sql_table(
        include_in_payload=include_in_payload,
        payload_as_json=payload_as_json,
        point_in_time=point_in_time,
        changes_since=changes_since,
        include_versions=include_versions,
        filter_str=filter_str,
        resolve_dimension_external_ids=resolve_dimension_external_ids,
        data_series_query_info=_data_series_query_info,
        use_materialized=use_materialized
    )
    lint(sql)
    return sql