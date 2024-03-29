# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from uuid import UUID

import datetime
from django.utils.datastructures import MultiValueDict
from rest_framework.exceptions import ValidationError, APIException, NotFound
from typing import Dict, List, Set, Tuple, Mapping, Optional, Any, cast, Union, Protocol

from skipper.dataseries.storage.uuid import gen_uuid
from skipper.dataseries.storage.static_ds_information import DataSeriesQueryInfo, DataSeriesFactQueryInfo
from skipper.dataseries.storage.validate.contract import DataPointAccessor, ReadOnlyDataPoint


def _append_error(errors: Dict[str, List[str]], key: str, error: str) -> None:
    if key not in errors:
        errors[key] = []
    errors[key].append(error)


def _validate_dim_ids(
        attrs: Dict[str, Any],
        errors: Dict[str, List[str]],
        data_point_relation_info: DataSeriesQueryInfo,
        partial: bool
) -> Dict[str, Any]:
    """
    Helper to create validation functions for dimensions. Checks if all dimensions are set
    """
    _required_dimension_ids = []
    for _elem in data_point_relation_info.dimensions.values():
        _dataseries_dim = _elem.dataseries_dimension
        _dimension = _elem.dimension
        if _dimension.reference.id != data_point_relation_info.data_series_id and not _dimension.optional:
            _required_dimension_ids.append(str(_dataseries_dim.external_id))

    difference: Set[str] = set(_required_dimension_ids).difference(set(attrs.keys()))

    if not partial:
        for element in difference:
            _append_error(errors, element, f'dimension {element} was not set, but is required')

    # there is no need for a null check on dimensions here, it is handled in _validate_dimensions

    return attrs


def _ensure_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    if 'payload' not in data:
        raise ValidationError('payload is expected to be set')
    _payload = data['payload']
    if not isinstance(_payload, dict):
        raise ValidationError('payload is expected to be an object/dictionary')
    if isinstance(_payload, MultiValueDict):
        raise APIException('payload should not be a multi-value dict')
    return cast(Dict[str, Any], data['payload'])


def _validate_dimensions(
        data: Dict[str, Any],
        data_point_relation_info: DataSeriesQueryInfo,
        partial: bool,
        use_external_id_as_dimension_identifier: bool,
        data_point_accessor: DataPointAccessor
) -> Tuple[Dict[str, List[str]], Dict[str, Any]]:
    attrs = _ensure_payload(data)
    errors: Dict[str, List[str]] = {}
    attrs = _validate_dim_ids(
        attrs=attrs,
        errors=errors,
        data_point_relation_info=data_point_relation_info,
        partial=partial
    )

    for _elem in data_point_relation_info.dimensions.values():
        _dataseries_dim = _elem.dataseries_dimension
        _dimension = _elem.dimension
        external_dimension_id = str(_dataseries_dim.external_id)
        if external_dimension_id not in attrs or attrs[external_dimension_id] is None:
            continue
        if attrs[external_dimension_id] == "":
            # an empty external id is the same as it being set to null/None
            attrs[external_dimension_id] = None
            continue

        _dimension_data_series = _dimension.reference
        _dp_id: Optional[str] = None
        _id_col_string_if_not_exists: str
        _type_error: bool

        if use_external_id_as_dimension_identifier:
            _dp_external_id = attrs[external_dimension_id]
            _id_col_string_if_not_exists = f'external id {_dp_external_id}'
            _type_error = not isinstance(attrs[external_dimension_id], str)
            if not _type_error:
                _dp_id = gen_uuid(data_series_id=_dimension_data_series.id, external_id=_dp_external_id)
                # update the validated value with the actual id if we use external ids to identify things
                attrs[external_dimension_id] = _dp_id
        else:
            _type_error = not isinstance(attrs[external_dimension_id], str)
            _dp_id = attrs[external_dimension_id]
            _id_col_string_if_not_exists = f'id {_dp_id}'

        if _type_error:
            _append_error(
                errors,
                external_dimension_id,
                f'DataPoint with {_id_col_string_if_not_exists} used in dimension {external_dimension_id} was no string'
            )
            continue

        _datapoint: Optional[ReadOnlyDataPoint] = None

        if _dp_id is not None:
            # select by data_series_id to also use the partition properly
            _datapoint = data_point_accessor(
                data_series_id=_dimension_data_series.id,
                identifier=_dp_id
            )

        if _datapoint is None:
            _append_error(
                errors,
                external_dimension_id,
                f'DataPoint with {_id_col_string_if_not_exists} used in dimension {external_dimension_id} does not exist'
            )
        elif _datapoint.data_series_id != _dimension_data_series.id:
            _append_error(
                errors,
                external_dimension_id,
                f'DataPoint with {_id_col_string_if_not_exists} used in dimension {external_dimension_id}' +
                f'does not belong to the expected DataSeries {_dimension_data_series.id}'
            )

    return errors, attrs


def _validate_fact_ids(
        partial: bool,
        data: Dict[str, Any],
        name: str,
        facts: Mapping[str, DataSeriesFactQueryInfo]
) -> Tuple[Dict[str, List[str]], Dict[str, Any]]:
    """
    Helper to create validation functions for facts. Checks if all required facts are set as well as if any
    extra facts exist for the data series
    """
    attrs = _ensure_payload(data)

    errors: Dict[str, List[str]] = {}

    _required_fact_ids = []
    _possible_fact_ids = []
    _facts_with_wrong_null = []

    for elem in facts.values():
        _dataseries_fact = elem.dataseries_fact
        _fact = elem.fact
        _fact_id = str(_dataseries_fact.external_id)
        if _fact_id in attrs:
            if not _fact.optional and (_fact_id not in attrs or attrs[_fact_id] is None):
                _facts_with_wrong_null.append(_fact_id)
        if not _fact.optional:
            _required_fact_ids.append(_fact_id)
        _possible_fact_ids.append(_fact_id)

    difference: Set[str] = set(_required_fact_ids).difference(set(attrs.keys()))

    if not partial:
        for element in difference:
            _append_error(errors, element, f'{name} {element} was not set, but is required')

    for element in _facts_with_wrong_null:
        _append_error(errors, element, f'{name} {element} was set to null, but is required')

    return errors, attrs


class FactTypeValidation(Protocol):
    def __call__(
        self,
        value: Any
    ) -> Tuple[List[str], Optional[Any]]: ...


def _validate_fact(
        facts: Mapping[str, DataSeriesFactQueryInfo],
        fact_type_validation: FactTypeValidation,
        name: str,
        data: Dict[str, Any],
        partial: bool
) -> Tuple[Dict[str, List[str]], Dict[str, Any]]:
    errors, attrs = _validate_fact_ids(
        partial=partial,
        data=data,
        name=name,
        facts=facts
    )

    for _elem in facts.values():
        _dataseries_fact = _elem.dataseries_fact
        _fact = _elem.fact
        external_fact_id = str(_dataseries_fact.external_id)
        if external_fact_id not in attrs or attrs[external_fact_id] is None:
            continue

        additional_errors, value = fact_type_validation(attrs[external_fact_id])
        if len(additional_errors) > 0:
            for error in additional_errors:
                _append_error(errors, str(_dataseries_fact.external_id), error)
        else:
            attrs[external_fact_id] = value

    return errors, attrs


def _validate_external_id(
        data: Dict[str, Any],
        bulk_insert: bool,
        data_series_id: Union[str, UUID],
        data_point_id: Optional[str],
        data_point_accessor: DataPointAccessor
) -> str:
    if 'external_id' not in data:
        raise ValidationError('external_id is not set')
    external_id = data['external_id']
    if not isinstance(external_id, str):
        raise ValidationError('external_id is no string')
    if data_point_id is None:
        # we are creating a new one
        if not bulk_insert:
            # in bulk inserts, we generally want to overwrite data that already exists
            # any guarantees regarding permissions are also not checked
            if data_point_accessor(
                    data_series_id=data_series_id,
                    identifier=gen_uuid(data_series_id=data_series_id, external_id=external_id),
            ) is not None:
                raise ValidationError(
                    f'external id \'{external_id}\' is already in use by a another data_point in this dataseries')
    else:
        _data_point = data_point_accessor(
            data_series_id=data_series_id,
            identifier=data_point_id,
        )
        if _data_point is None:
            raise NotFound('did not find datapoint')
        if external_id != _data_point.external_id:
            raise ValidationError('changing of external_id for DataPoints is not supported!')
    return external_id


def _validate_float_facts(
        data: Dict[str, float],
        partial: bool,
        data_point_relation_info: DataSeriesQueryInfo
) -> Tuple[Dict[str, List[str]], Dict[str, Any]]:
    def is_float(value: Any) -> Tuple[List[str], Optional[float]]:
        if isinstance(value, bool):
            # booleans are integers
            return ['value is no float'], None

        if isinstance(value, float) or isinstance(value, int):
            return [], float(value)
        else:
            return ['value is no float'], None

    return _validate_fact(
        facts=data_point_relation_info.float_facts,
        fact_type_validation=is_float,
        name='float fact',
        data=data,
        partial=partial
    )


def _validate_string_facts(
        data: Dict[str, str],
        partial: bool,
        data_point_relation_info: DataSeriesQueryInfo
) -> Tuple[Dict[str, List[str]], Dict[str, Any]]:
    # FIXME: should we validate length here?
    def is_string(value: Any) -> Tuple[List[str], Optional[str]]:
        if isinstance(value, str):
            return [], str(value)
        else:
            return ['value is no string'], None

    return _validate_fact(
        facts=data_point_relation_info.string_facts,
        fact_type_validation=is_string,
        name='string fact',
        data=data,
        partial=partial
    )


def _validate_text_facts(
        data: Dict[str, str],
        partial: bool,
        data_point_relation_info: DataSeriesQueryInfo
) -> Tuple[Dict[str, List[str]], Dict[str, Any]]:
    def is_text(value: Any) -> Tuple[List[str], Optional[str]]:
        if isinstance(value, str):
            return [], str(value)
        else:
            return ['value is no text'], None

    return _validate_fact(
        facts=data_point_relation_info.text_facts,
        fact_type_validation=is_text,
        name='text fact',
        data=data,
        partial=partial
    )


def _validate_timestamp_facts(
        data: Dict[str, str],
        partial: bool,
        data_point_relation_info: DataSeriesQueryInfo
) -> Tuple[Dict[str, List[str]], Dict[str, Any]]:
    def is_timestamp(value: Any) -> Tuple[List[str], Optional[datetime.datetime]]:
        if isinstance(value, datetime.datetime):
            return [], value
        else:
            return ['value is no timestamp'], None

    return _validate_fact(
        facts=data_point_relation_info.timestamp_facts,
        fact_type_validation=is_timestamp,
        name='timestamp fact',
        data=data,
        partial=partial
    )


def _validate_json_facts(
        data: Dict[str, str],
        partial: bool,
        data_point_relation_info: DataSeriesQueryInfo
) -> Tuple[Dict[str, List[str]], Dict[str, Any]]:
    def is_json(value: Any) -> Tuple[List[str], Optional[Any]]:
        if isinstance(value, bool):
            return [], value
        if isinstance(value, int):
            return [], value
        if isinstance(value, float):
            return [], value
        if isinstance(value, list):
            return [], value
        if isinstance(value, dict):
            return [], value
        if isinstance(value, str):
            return [], value
        else:
            return ['value is no json'], None

    return _validate_fact(
        facts=data_point_relation_info.json_facts,
        fact_type_validation=is_json,
        name='json fact',
        data=data,
        partial=partial
    )


def _validate_image_facts(
        data: Dict[str, Any],
        partial: bool,
        data_point_relation_info: DataSeriesQueryInfo
) -> Tuple[Dict[str, List[str]], Dict[str, Any]]:
    def is_image(value: Any) -> Tuple[List[str], Optional[Any]]:
        error = (['value is no image'], None)
        if isinstance(value, bool):
            return error
        if isinstance(value, int):
            return error
        if isinstance(value, float):
            return error
        if isinstance(value, list):
            return error
        if isinstance(value, dict):
            return error
        if isinstance(value, str):
            return error
        # best effort, FIXME: dont just rely on django here
        return [], value

    return _validate_fact(
        facts=data_point_relation_info.image_facts,
        fact_type_validation=is_image,
        name='image fact',
        data=data,
        partial=partial
    )


def _validate_file_facts(
        data: Dict[str, Any],
        partial: bool,
        data_point_relation_info: DataSeriesQueryInfo
) -> Tuple[Dict[str, List[str]], Dict[str, Any]]:
    def is_file(value: Any) -> Tuple[List[str], Optional[Any]]:
        error = (['value is no file'], None)
        if isinstance(value, bool):
            return error
        if isinstance(value, int):
            return error
        if isinstance(value, float):
            return error
        if isinstance(value, list):
            return error
        if isinstance(value, dict):
            return error
        if isinstance(value, str):
            return error
        # best effort, FIXME: dont just rely on django here
        return [], value

    return _validate_fact(
        facts=data_point_relation_info.file_facts,
        fact_type_validation=is_file,
        name='file fact',
        data=data,
        partial=partial
    )


def _validate_boolean_facts(
        data: Dict[str, bool],
        partial: bool,
        data_point_relation_info: DataSeriesQueryInfo
) -> Tuple[Dict[str, List[str]], Dict[str, Any]]:
    def is_boolean(value: Any) -> Tuple[List[str], Optional[bool]]:
        if isinstance(value, bool):
            return [], value
        else:
            return ['value is no bool'], None

    return _validate_fact(
        facts=data_point_relation_info.boolean_facts,
        fact_type_validation=is_boolean,
        name='boolean fact',
        data=data,
        partial=partial
    )
