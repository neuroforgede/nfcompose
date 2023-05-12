# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from rest_framework.exceptions import ValidationError
from typing import Union, Dict, List

from skipper.dataseries.models.partitions import fully_qualified_partition_table
from skipper.dataseries.raw_sql.escape import escape
from skipper.dataseries.storage.contract import StorageBackendType
from skipper.dataseries.storage.dynamic_sql.queries.select_info import SelectInfo
from skipper.dataseries.storage.static_ds_information import DataSeriesDimensionQueryInfo, \
    DataSeriesFactQueryInfo, BasicDataSeriesQueryInfo, DataSeriesQueryInfo


def can_use_materialized_table(data_series_query_info: BasicDataSeriesQueryInfo, point_in_time: bool) -> bool:
    # if locked, we are probably migrating
    return data_series_query_info.backend == StorageBackendType.DYNAMIC_SQL_NO_HISTORY.value\
           or (
            data_series_query_info.backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED_FLAT_HISTORY.value\
            and not point_in_time
           ) \
           or\
           (
               data_series_query_info.backend == StorageBackendType.DYNAMIC_SQL_MATERIALIZED.value
                and not data_series_query_info.locked
                and not point_in_time
           )


def is_timestamp_utc_fact(select_info: SelectInfo) -> bool:
    return select_info.type == 'timestamp_fact'


def render_join_part(
        data_series_child_identifiers: Union[
            Dict[str, DataSeriesFactQueryInfo], Dict[str, DataSeriesDimensionQueryInfo]
        ],
        relation_table: str,
        fact_or_dim_id: str,
        point_in_time: bool
) -> str:
    if len(data_series_child_identifiers) == 0:
        return ""
    sub_parts: List[str] = []
    for elem in data_series_child_identifiers.values():
        id = elem.id
        final_relation_table = fully_qualified_partition_table(relation_table, elem.id)
        unescaped_display_id = elem.unescaped_display_id
        relation_table_name_alias = escape(f'relation_{unescaped_display_id}')
        hist_table_name_alias = escape(f'hist_{unescaped_display_id}')
        point_in_time_part_actual = ""
        point_in_time_part_hist = ""
        if point_in_time:
            point_in_time_part_actual = f"AND {relation_table_name_alias}.point_in_time <= %(point_in_time)s"
            point_in_time_part_hist = f"AND {hist_table_name_alias}.point_in_time <= %(point_in_time)s"
        join_sub_part = f"""
LEFT OUTER JOIN {final_relation_table} {relation_table_name_alias}
ON ({relation_table_name_alias}.data_point_id = ds_dp.id
    AND {relation_table_name_alias}.{fact_or_dim_id} = '{id}'
    {point_in_time_part_actual}
)
LEFT OUTER JOIN {final_relation_table} {hist_table_name_alias}
ON ({relation_table_name_alias}.{fact_or_dim_id} = {hist_table_name_alias}.{fact_or_dim_id} AND
    {relation_table_name_alias}.data_point_id = {hist_table_name_alias}.data_point_id AND
    ({relation_table_name_alias}.point_in_time, {relation_table_name_alias}.sub_clock) < ({hist_table_name_alias}.point_in_time, {hist_table_name_alias}.sub_clock)
    {point_in_time_part_hist}
)
"""
        sub_parts.append(join_sub_part.strip())

    all_joins = '\n'.join(sub_parts)
    return all_joins


def render_wheres(data_series_child_identifiers: Union[
    Dict[str, DataSeriesFactQueryInfo], Dict[str, DataSeriesDimensionQueryInfo]]) -> str:
    if len(data_series_child_identifiers) == 0:
        return ""
    sub_parts: List[str] = []
    for elem in data_series_child_identifiers.values():
        unescaped_display_id = elem.unescaped_display_id
        hist_table_name_alias = escape(f'hist_{unescaped_display_id}')
        sub_parts.append(f"""
AND {hist_table_name_alias}.data_point_id IS NULL
""")
    comma_nl = '\n'
    return f"{comma_nl.join(sub_parts)}"


def render_main_extra_fields_columns(main_tbl_alias: str, main_extra_fields: List[str]) -> str:
    comma_nl = ',\n'
    _main_extra_fields_elems = [f'{main_tbl_alias}.{elem}' for elem in main_extra_fields]
    _main_extra_fields_sql = ''
    if len(_main_extra_fields_elems) > 0:
        _main_extra_fields_sql = f'{comma_nl.join(_main_extra_fields_elems)},\n'
    return _main_extra_fields_sql
