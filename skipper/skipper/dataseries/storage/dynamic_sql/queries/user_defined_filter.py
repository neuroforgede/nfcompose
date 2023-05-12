# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from django.utils import dateparse
from rest_framework.exceptions import ValidationError
from typing import NamedTuple, Dict, Any, List, Set

from skipper.dataseries.raw_sql.escape import escape

from skipper.dataseries.storage.static_ds_information import DataSeriesQueryInfo


class UserDefinedFilter(NamedTuple):
    filter_query_str: str
    query_params: Dict[str, Any]
    used_data_series_children: DataSeriesQueryInfo


def compute_user_defined_filter_for_raw_query(
        data_series_query_info: DataSeriesQueryInfo,
        filter_params: Dict[str, Any],
        use_materialized_table: bool,
) -> UserDefinedFilter:
    query_params: Dict[str, Any] = {}
    query_parts: List[str] = []
    used_data_series_children = DataSeriesQueryInfo(
        data_series_id=data_series_query_info.data_series_id,
        backend=data_series_query_info.backend,
        locked=data_series_query_info.locked,
        schema_name=data_series_query_info.schema_name,
        main_query_table_name=data_series_query_info.main_query_table_name,
        main_extra_fields=data_series_query_info.main_extra_fields,
        materialized_flat_history_table_name=data_series_query_info.materialized_flat_history_table_name,
        float_facts={},
        string_facts={},
        text_facts={},
        timestamp_facts={},
        image_facts={},
        json_facts={},
        boolean_facts={},
        dimensions={},
        file_facts={},
        main_alive_filter='ds_dp.deleted_at IS NULL'
    )

    handled_keys: Set[str] = set()

    for i, (key, value) in enumerate(filter_params.items()):
        # JSON is not supported because of the added complexity
        # it would bring without a proper DSL
        query_param_name = f'filter_{i}'
        # image and file intentionally not here
        _handle_if_float_fact(use_materialized_table, data_series_query_info, query_parts, query_params,
                              used_data_series_children,
                              query_param_name, key, value, handled_keys)
        _handle_if_string_fact(use_materialized_table, data_series_query_info, query_parts, query_params,
                               used_data_series_children,
                               query_param_name, key, value, handled_keys)
        _handle_if_text_fact(use_materialized_table, data_series_query_info, query_parts, query_params,
                             used_data_series_children,
                             query_param_name, key, value, handled_keys)
        _handle_if_timestamp_fact(use_materialized_table, data_series_query_info, query_parts, query_params,
                                  used_data_series_children,
                                  query_param_name, key, value, handled_keys)
        _handle_if_boolean_fact(use_materialized_table, data_series_query_info, query_parts, query_params,
                                used_data_series_children,
                                query_param_name, key, value, handled_keys)
        _handle_if_dimension(use_materialized_table, data_series_query_info, query_parts, query_params,
                             used_data_series_children,
                             query_param_name, key, value, handled_keys)

    filter_keys = filter_params.keys()

    not_found = frozenset(filter_keys).difference(handled_keys)
    if len(not_found) > 0:
        raise ValidationError(f'unrecognized fields in filter query parameter: {"{"}{",".join(not_found)}{"}"}')

    handled_keys.intersection(filter_keys)

    return UserDefinedFilter(
        filter_query_str='\n'.join(query_parts),
        query_params=query_params,
        used_data_series_children=used_data_series_children
    )


def _handle_if_dimension(
        use_materialized_table: bool,
        data_series_query_info: DataSeriesQueryInfo,
        query_parts: List[str],
        query_params: Dict[str, Any],
        used_data_series_children: DataSeriesQueryInfo,
        query_param_name: str,
        key: str,
        value: Any,
        handled_keys: Set[str]
) -> None:
    if key in data_series_query_info.dimensions:
        _lhs: str
        if use_materialized_table:
            query_info = data_series_query_info.dimensions[key]
            _lhs = f'ds_dp.{query_info.value_column}'
        else:
            _tbl_name = escape(f'relation_{key}')
            _lhs = f'{_tbl_name}.value'
        if value is None:
            query_parts.append(f"AND {_lhs} IS NULL")
        else:
            if not isinstance(value, str):
                raise ValidationError(f"expected string value for field {str(key)}")
            query_parts.append(f"AND {_lhs} = %({query_param_name})s")
            query_params[query_param_name] = value

        used_data_series_children.dimensions[key] = data_series_query_info.dimensions[key]
        handled_keys.add(key)


def _handle_if_timestamp_fact(
        use_materialized_table: bool,
        data_series_query_info: DataSeriesQueryInfo,
        query_parts: List[str],
        query_params: Dict[str, Any],
        used_data_series_children: DataSeriesQueryInfo,
        query_param_name: str,
        key: str,
        value: Any,
        handled_keys: Set[str]
) -> None:
    if key in data_series_query_info.timestamp_facts:
        _lhs: str
        if use_materialized_table:
            query_info = data_series_query_info.timestamp_facts[key]
            _lhs = f'ds_dp.{query_info.value_column}'
        else:
            _tbl_name = escape(f'relation_{key}')
            _lhs = f'{_tbl_name}.value'
        if value is None:
            query_parts.append(f"AND {_lhs} IS NULL")
        else:
            try:
                parsed_date_time = dateparse.parse_datetime(str(value))
                if parsed_date_time is None:
                    raise ValidationError(f'{value} is no valid datetime')
            except ValueError:
                raise ValidationError(f'{value} is no valid datetime')
            query_parts.append(f"AND {_lhs} = %({query_param_name})s")
            query_params[query_param_name] = parsed_date_time

        used_data_series_children.timestamp_facts[key] = data_series_query_info.timestamp_facts[key]
        handled_keys.add(key)


def _handle_if_text_fact(
        use_materialized_table: bool,
        data_series_query_info: DataSeriesQueryInfo,
        query_parts: List[str],
        query_params: Dict[str, Any],
        used_data_series_children: DataSeriesQueryInfo,
        query_param_name: str,
        key: str,
        value: Any,
        handled_keys: Set[str]
) -> None:
    if key in data_series_query_info.text_facts:
        _lhs: str
        if use_materialized_table:
            query_info = data_series_query_info.text_facts[key]
            _lhs = f'ds_dp.{query_info.value_column}'
        else:
            _tbl_name = escape(f'relation_{key}')
            _lhs = f'{_tbl_name}.value'
        if value is None:
            query_parts.append(f"AND {_lhs} IS NULL")
        else:
            if not isinstance(value, str):
                raise ValidationError(f"expected string value for field {str(key)}")
            query_parts.append(f"AND {_lhs} = %({query_param_name})s::text")
            query_params[query_param_name] = value

        used_data_series_children.text_facts[key] = data_series_query_info.text_facts[key]
        handled_keys.add(key)


def _handle_if_string_fact(
        use_materialized_table: bool,
        data_series_query_info: DataSeriesQueryInfo,
        query_parts: List[str],
        query_params: Dict[str, Any],
        used_data_series_children: DataSeriesQueryInfo,
        query_param_name: str,
        key: str,
        value: Any,
        handled_keys: Set[str]
) -> None:
    if key in data_series_query_info.string_facts:
        _lhs: str
        if use_materialized_table:
            query_info = data_series_query_info.string_facts[key]
            _lhs = f'ds_dp.{query_info.value_column}'
        else:
            _tbl_name = escape(f'relation_{key}')
            _lhs = f'{_tbl_name}.value'
        if value is None:
            query_parts.append(f"AND {_lhs} IS NULL")
        else:
            if not isinstance(value, str):
                raise ValidationError(f"expected string value for field {str(key)}")
            query_parts.append(f"AND {_lhs} = %({query_param_name})s")
            query_params[query_param_name] = value

        used_data_series_children.string_facts[key] = data_series_query_info.string_facts[key]
        handled_keys.add(key)


def _handle_if_float_fact(
        use_materialized_table: bool,
        data_series_query_info: DataSeriesQueryInfo,
        query_parts: List[str],
        query_params: Dict[str, Any],
        used_data_series_children: DataSeriesQueryInfo,
        query_param_name: str,
        key: str,
        value: Any,
        handled_keys: Set[str]
) -> None:
    if key in data_series_query_info.float_facts:
        _lhs: str
        if use_materialized_table:
            query_info = data_series_query_info.float_facts[key]
            _lhs = f'ds_dp.{query_info.value_column}'
        else:
            _tbl_name = escape(f'relation_{key}')
            _lhs = f'{_tbl_name}.value'
        if value is None:
            query_parts.append(f"AND {_lhs} IS NULL")
        else:
            if not isinstance(value, float) and not isinstance(value, int):
                raise ValidationError(f"expected numeric value for field {str(key)}")
            query_parts.append(f"AND {_lhs} = %({query_param_name})s::double precision")
            query_params[query_param_name] = value

        used_data_series_children.float_facts[key] = data_series_query_info.float_facts[key]
        handled_keys.add(key)


def _handle_if_boolean_fact(
        use_materialized_table: bool,
        data_series_query_info: DataSeriesQueryInfo,
        query_parts: List[str],
        query_params: Dict[str, Any],
        used_data_series_children: DataSeriesQueryInfo,
        query_param_name: str,
        key: str,
        value: Any,
        handled_keys: Set[str]
) -> None:
    if key in data_series_query_info.boolean_facts:
        _lhs: str
        if use_materialized_table:
            query_info = data_series_query_info.boolean_facts[key]
            _lhs = f'ds_dp.{query_info.value_column}'
        else:
            _tbl_name = escape(f'relation_{key}')
            _lhs = f'{_tbl_name}.value'
        if value is None:
            query_parts.append(f"AND {_lhs} IS NULL")
        else:
            if not isinstance(value, bool):
                raise ValidationError(f"expected boolean value for field {str(key)}")
            query_parts.append(f"AND {_lhs} = %({query_param_name})s")
            query_params[query_param_name] = value

        used_data_series_children.boolean_facts[key] = data_series_query_info.boolean_facts[key]
        handled_keys.add(key)
