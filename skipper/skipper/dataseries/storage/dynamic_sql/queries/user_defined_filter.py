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


def complex_filter_to_sql_filter(filter_dict, handle_column, max_depth=10, depth=0):
    if depth > max_depth:
        raise ValueError("Maximum recursion depth exceeded")

    sql_filter = ""

    key: str
    for key, value in filter_dict.items():
        if key == "$and":
            and_clauses = [complex_filter_to_sql_filter(item, handle_column, max_depth, depth + 1) for item in value]
            sql_filter += "(" + " AND ".join(and_clauses) + ")"
        elif key == "$or":
            or_clauses = [complex_filter_to_sql_filter(item, handle_column, max_depth, depth + 1) for item in value]
            sql_filter += "(" + " OR ".join(or_clauses) + ")"
        elif key.startswith("$"):
            raise ValueError(f"Unsupported operator: {key}")
        else:
            column = key
            sql_filter += handle_column(column, value)
        

        sql_filter += " AND "

    return sql_filter[:-5]  # Remove the trailing "AND"


def compute_user_defined_filter_for_raw_query(
        data_series_query_info: DataSeriesQueryInfo,
        filter_params: Dict[str, Any],
        use_materialized_table: bool,
) -> UserDefinedFilter:
    query_params: Dict[str, Any] = {}
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

    def handle_column(column, filter, operation="$eq"):
        if isinstance(filter, dict):
            and_clauses = [handle_column(column, item[1], operation=item[0]) for item in filter.items()]
            sql_filter = " AND ".join(and_clauses)
            return sql_filter
        else:
            return primitive_filter(column, filter, operation)
        
    query_param_idx = 0


    handled_keys: Set[str] = set()
    keys_overall: Set[str] = set()

    def primitive_filter(key, value, operation):
        keys_overall.add(key)

        nonlocal query_param_idx
        query_parts: List[str] = []
        # JSON is not supported because of the added complexity
        # it would bring without a proper DSL
        query_param_name = f'filter_{query_param_idx}'
        query_param_idx += 1
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
        return '\n'.join(query_parts)

    filter_query_str = complex_filter_to_sql_filter(
        filter_dict=filter_params,
        handle_column=handle_column
    )

    not_found = frozenset(keys_overall).difference(handled_keys)
    if len(not_found) > 0:
        raise ValidationError(f'unrecognized fields in filter query parameter: {"{"}{",".join(not_found)}{"}"}')

    return UserDefinedFilter(
        filter_query_str=filter_query_str,
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
