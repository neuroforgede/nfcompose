# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from typing import NamedTuple, Any, List, Iterable, Dict, Union

from skipper.dataseries.models.metamodel.dimension import DataSeries_Dimension
from skipper.dataseries.raw_sql.escape import escape
from skipper.dataseries.storage.dynamic_sql.materialized import materialized_column_name
from skipper.dataseries.storage.static_ds_information import DataSeriesQueryInfo, \
    DataSeriesFactQueryInfo, ReadOnlyBaseDataSeriesFactRelation, ReadOnlyDataSeries_Dimension


class SelectInfo(NamedTuple):
    point_in_time: Any
    unescaped_display_id: str
    actual_id: str
    select_alias: str
    fact_or_dim_id: str
    value_column: str
    # this is the column name for both the flat history tables as well as the materialized table
    materialized_value_column: str
    payload_variable_name: str
    actual_table_name: str
    version_alias_name: str
    type: str


def select_infos(data_series_child_identifiers: 'DataSeriesQueryInfo') -> List[SelectInfo]:
    select_infos: List[SelectInfo] = [*_unsorted_dimension_select_infos(data_series_child_identifiers)]

    def fact_relations(_dict: Dict[str, 'DataSeriesFactQueryInfo']) -> Iterable[ReadOnlyBaseDataSeriesFactRelation]:
        return [elem.dataseries_fact for elem in _dict.values()]

    _handle_facts(select_infos, fact_relations(data_series_child_identifiers.float_facts), 'float_fact')
    _handle_facts(select_infos, fact_relations(data_series_child_identifiers.string_facts), 'string_fact')
    _handle_facts(select_infos, fact_relations(data_series_child_identifiers.text_facts), 'text_fact')
    _handle_facts(select_infos, fact_relations(data_series_child_identifiers.json_facts), 'json_fact')
    _handle_facts(select_infos, fact_relations(data_series_child_identifiers.timestamp_facts), 'timestamp_fact')
    _handle_facts(select_infos, fact_relations(data_series_child_identifiers.image_facts), 'image_fact')
    _handle_facts(select_infos, fact_relations(data_series_child_identifiers.file_facts), 'file_fact')
    _handle_facts(select_infos, fact_relations(data_series_child_identifiers.boolean_facts), 'boolean_fact')


    def sort_key(x: SelectInfo) -> Any:
        return x.point_in_time, x.unescaped_display_id

    select_infos.sort(key=sort_key)
    return select_infos


def _data_series_dimension_to_select_info(
        _dataseries_dimension: Union[ReadOnlyDataSeries_Dimension, DataSeries_Dimension]
) -> SelectInfo:
    return SelectInfo(
        point_in_time=_dataseries_dimension.point_in_time,
        unescaped_display_id=str(_dataseries_dimension.external_id),
        actual_id=str(_dataseries_dimension.dimension.id),
        select_alias=escape(f'dim_{str(_dataseries_dimension.external_id)}'),
        fact_or_dim_id='dimension_id',
        value_column='value',
        materialized_value_column=escape(materialized_column_name(str(_dataseries_dimension.dimension.id), str(_dataseries_dimension.external_id))),
        payload_variable_name=f'payload_elem_{str(_dataseries_dimension.id).replace("-", "_")}',
        actual_table_name='_3_data_point_dimension',
        version_alias_name=escape(f'version_{str(_dataseries_dimension.external_id)}'),
        type='dimension'
    )


def _unsorted_dimension_select_infos(data_series_child_identifiers: 'DataSeriesQueryInfo') -> List[SelectInfo]:
    select_infos: List[SelectInfo] = []
    for elem in data_series_child_identifiers.dimensions.values():
        select_info = _data_series_dimension_to_select_info(elem.dataseries_dimension)
        select_infos.append(select_info)
    return select_infos


def _handle_facts(
        select_infos: List[SelectInfo],
        dataseries_fact_set: Iterable[ReadOnlyBaseDataSeriesFactRelation],
        alias_prefix: str
) -> None:
    for _dataseries_fact in dataseries_fact_set:
        select_info = SelectInfo(
            point_in_time=_dataseries_fact.point_in_time,
            unescaped_display_id=_dataseries_fact.external_id,
            actual_id=str(_dataseries_fact.fact.id),
            select_alias=escape(f'{alias_prefix}_{_dataseries_fact.external_id}'),
            fact_or_dim_id='fact_id',
            value_column='value',
            materialized_value_column=escape(materialized_column_name(_dataseries_fact.fact.id,
                                                               _dataseries_fact.external_id)),
            payload_variable_name=f'payload_elem_{str(_dataseries_fact.id).replace("-", "_")}',
            actual_table_name=f'_3_data_point_{alias_prefix}',
            version_alias_name=escape(f'version_{str(_dataseries_fact.external_id)}'),
            type=alias_prefix
        )
        select_infos.append(select_info)
