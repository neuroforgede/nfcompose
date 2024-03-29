# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


from rest_framework.exceptions import ValidationError
from typing import Dict, Any, List, Tuple, Protocol

from skipper.dataseries.storage.static_ds_information import DataSeriesQueryInfo
from skipper.dataseries.storage.uuid import gen_uuid
from skipper.dataseries.storage.validate.contract import ValidationRequest
from skipper.dataseries.storage.validate.default.internal import _validate_dimensions, _validate_external_id, \
    _validate_float_facts, _validate_string_facts, _validate_text_facts, _validate_timestamp_facts, \
    _validate_json_facts, _validate_image_facts, _validate_boolean_facts, _validate_file_facts


class FactValidation(Protocol):
    def __call__(
            self,
            data: Dict[str, Any],
            partial: bool,
            data_point_relation_info: DataSeriesQueryInfo
    ) -> Tuple[Dict[str, List[str]], Dict[str, Any]]: ...


def validate(
        data: Dict[str, Any],
        request: ValidationRequest
) -> Dict[str, Any]:
    all_errors: Dict[str, Dict[str, List[Any]]] = {}
    non_payload_errors: Dict[str, List[Any]] = {}

    def check_validation_result(
        validation_result: Tuple[Dict[str, List[str]], Dict[str, Any]]
    ) -> None:
        _errors, value = validation_result
        if len(_errors) > 0:
            if 'payload' not in all_errors:
                all_errors['payload'] = {}
            all_errors['payload'].update(_errors)
        else:
            data['payload'] = value

    def run_sub_validation(
            validation: FactValidation
    ) -> None:
        _validation_result = validation(
            data=data,
            partial=request.partial,
            data_point_relation_info=request.data_point_relation_info
        )
        check_validation_result(_validation_result)

    def validate_dimensions() -> None:
        _validation_result = _validate_dimensions(
            data=data,
            data_point_relation_info=request.data_point_relation_info,
            partial=request.partial,
            use_external_id_as_dimension_identifier=request.external_id_as_dimension_identifier,
            data_point_accessor=request.data_point_accessor
        )
        check_validation_result(_validation_result)

    validate_dimensions()

    run_sub_validation(_validate_float_facts)
    run_sub_validation(_validate_string_facts)
    run_sub_validation(_validate_text_facts)
    run_sub_validation(_validate_timestamp_facts)
    run_sub_validation(_validate_json_facts)
    run_sub_validation(_validate_image_facts)
    run_sub_validation(_validate_file_facts)
    run_sub_validation(_validate_boolean_facts)

    actual_errors: Dict[str, Any] = dict(all_errors)

    try:
        if not (request.partial and 'external_id' not in data):
            # patches may leave out the external id
            data['external_id'] = _validate_external_id(
                data=data,
                bulk_insert=request.bulk_insert,
                data_series_id=request.data_point_relation_info.data_series_id,
                data_point_id=request.data_point_id,
                data_point_accessor=request.data_point_accessor
            )
    except ValidationError as e:
        non_payload_errors['external_id'] = ['\n'.join(e.detail)]

    if len(non_payload_errors) > 0:
        actual_errors.update(non_payload_errors)

    if len(actual_errors) > 0:
        raise ValidationError(actual_errors)

    if request.data_point_id is not None:
        data['id'] = request.data_point_id
    else:
        if 'external_id' not in data:
            raise AssertionError('external_id may not be null if id does not exist already')
        data['id'] = gen_uuid(
            data_series_id=request.data_point_relation_info.data_series_id,
            external_id=data['external_id']
        )

    return data
