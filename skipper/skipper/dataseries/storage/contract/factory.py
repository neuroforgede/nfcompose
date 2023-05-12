# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


import uuid

import datetime
from django.utils.encoding import force_str
from rest_framework import serializers
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.settings import api_settings
from rest_framework.utils.serializer_helpers import NestedBoundField, BoundField, JSONBoundField
from typing import Optional, Type, Dict, Any, Mapping, cast

from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.storage.contract.base import BaseDataPointModificationSerializer
from skipper.dataseries.storage.contract.file_storage import file_based_fact_dir
from skipper.dataseries.storage.static_ds_information import DataSeriesQueryInfo, \
    compute_data_series_query_info, ReadOnlyDataSeries, data_point_serialization_keys
from skipper.dataseries.storage.uuid import gen_uuid


class CustomImageField(serializers.ImageField):
    storage_base_path: str

    def __init__(self, *args: Any, **kwargs: Any):
        self.storage_base_path = kwargs.pop('storage_base_path', '')
        super().__init__(*args, **kwargs)

    # def to_internal_value(self, data: Any) -> Any:
    #     try:
    #         data._name = self.storage_base_path + data.name
    #     except AttributeError:
    #         self.fail('invalid')
    #     result = super().to_internal_value(data)
    #     return result


class CustomFileField(serializers.FileField):
    storage_base_path: str

    def __init__(self, *args: Any, **kwargs: Any):
        self.storage_base_path = kwargs.pop('storage_base_path', '')
        super().__init__(*args, **kwargs)


# custom fixes for DRF weirdness
class PayloadNestedField(NestedBoundField):
    def __init__(self, field, value, errors, prefix=''):  # type: ignore
        if value is not None and not isinstance(value, Mapping):
            value = {}
        super().__init__(field, value, errors, prefix)

    def __getitem__(self, key: Any) -> Any:
        field = self.fields[key]
        value = self.value.get(key) if self.value else None
        error = self.errors.get(key) if isinstance(self.errors, dict) else None  # type: ignore
        if hasattr(field, 'fields'):
            return NestedBoundField(field, value, error, prefix=self.name + '.') # type: ignore
        if getattr(field, '_is_jsonfield', False):
            return JSONBoundField(field, value, error, prefix=self.name + '.') # type: ignore
        return BoundField(field, value, error, prefix=self.name + '.') # type: ignore

    def as_form_field(self) -> Any:
        values = {}
        for key, value in self.value.items():
            if isinstance(value, (list, dict)):
                values[key] = value
            else:
                if key in self.fields:
                    field = self.fields[key]
                    error = self.errors.get(key) if isinstance(self.errors, dict) else None  # type: ignore
                    if getattr(field, '_is_jsonfield', False) and error is not None or value is None:
                        if value is None:
                            values[key] = None
                        else:
                            class JSONString(str):
                                def __new__(cls, value):
                                    ret = str.__new__(cls, value)
                                    ret.is_json_string = True
                                    return ret
                            values[key] = JSONString(value)
                    else:
                        values[key] = '' if (value is None or value is False) else force_str(value)  # type: ignore
        
        return self.__class__(self._field, values, self.errors, self._prefix)  # type: ignore


class NestingCompatibleJSONField(serializers.JSONField):

    # Workaround for isinstance calls when importing the field isn't possible
    _is_jsonfield = True

    def get_value(self, dictionary: Any) -> Any:
        parser_context = self.parent.parent.context['view'].request.parser_context
        json_as_string = '__JSON_AS_STRING__' in parser_context and bool(parser_context['__JSON_AS_STRING__'])
        # FIXME: hack: manually duplicating the logic from the parent class but using a different approach
        # check if we can fix this in our multipart parser instead?
        # alternative: access the data get_serializer_class and pass it in here
        if json_as_string and self.field_name in dictionary:  # type: ignore
            # When HTML form input is used, mark up the input
            # as being a JSON string, rather than a JSON primitive.
            class JSONString(str):
                def __new__(cls, value):  # type: ignore
                    ret = str.__new__(cls, value)  # type: ignore
                    ret.is_json_string = True  # type: ignore
                    return ret
            return JSONString(dictionary[self.field_name])  # type: ignore
        return super().get_value(dictionary)


def get_data_point_serializer_for_data_series(
        actual_class: Type[BaseDataPointModificationSerializer],
        data_series_id: str,
        update: bool,
        point_in_time: Optional[datetime.datetime],
        should_include_versions: bool,
        patch: bool = False,
        data_series_query_info: Optional[DataSeriesQueryInfo] = None
) -> Type[BaseDataPointModificationSerializer]:
    """
    generates a serializer class that we can then instantiate for proper validation
    """
    # do as much as possible in here, then we can cache this definition
    # if we need better performance!

    data_series: DataSeries = get_object_or_404(DataSeries.objects.filter(id=data_series_id))

    payload_serializers: Dict[str, Any] = {}

    if data_series_query_info is None:
        _data_series_children_query_info = compute_data_series_query_info(data_series)
    else:
        _data_series_children_query_info = data_series_query_info

    def add_float_facts() -> None:
        for external_id, fact_info in _data_series_children_query_info.float_facts.items():
            payload_serializers[external_id] = serializers.FloatField(
                allow_null=fact_info.fact.optional,
                required=(not fact_info.fact.optional) and not patch
            )

    add_float_facts()

    def add_string_facts() -> None:
        for external_id, fact_info in _data_series_children_query_info.string_facts.items():
            payload_serializers[external_id] = serializers.CharField(
                allow_null=fact_info.fact.optional,
                allow_blank=True,
                max_length=256,
                required=(not fact_info.fact.optional) and not patch
            )

    add_string_facts()

    def add_text_facts() -> None:
        for external_id, fact_info in _data_series_children_query_info.text_facts.items():
            payload_serializers[external_id] = serializers.CharField(
                allow_null=fact_info.fact.optional,
                allow_blank=True,
                required=(not fact_info.fact.optional) and not patch
            )

    add_text_facts()

    def add_timestamp_facts() -> None:
        for external_id, fact_info in _data_series_children_query_info.timestamp_facts.items():
            payload_serializers[external_id] = serializers.DateTimeField(
                allow_null=fact_info.fact.optional,
                required=(not fact_info.fact.optional) and not patch
            )

    add_timestamp_facts()

    def add_json_facts() -> None:
        for external_id, fact_info in _data_series_children_query_info.json_facts.items():
            payload_serializers[external_id] = NestingCompatibleJSONField(
                binary=False,
                allow_null=fact_info.fact.optional,
                required=(not fact_info.fact.optional) and not patch
            )

    add_json_facts()

    base_dirs: Dict[str, str] = {}

    def add_image_facts() -> None:
        for external_id, fact_info in _data_series_children_query_info.image_facts.items():
            base_dirs[external_id] = file_based_fact_dir(
                tenant_name=data_series.tenant.name,
                data_series_id=data_series_id,
                fact_id=str(fact_info.dataseries_fact.fact.id),
                fact_type='image'
            )
            payload_serializers[external_id] = CustomImageField(
                allow_null=fact_info.fact.optional,
                required=(not fact_info.fact.optional) and not patch,
                storage_base_path=file_based_fact_dir(
                    tenant_name=data_series.tenant.name,
                    data_series_id=data_series_id,
                    fact_id=str(fact_info.dataseries_fact.fact.id),
                    fact_type='image'
                ),
                max_length=200
            )

    add_image_facts()

    def add_file_facts() -> None:
        for external_id, fact_info in _data_series_children_query_info.file_facts.items():
            base_dirs[external_id] = file_based_fact_dir(
                tenant_name=data_series.tenant.name,
                data_series_id=data_series_id,
                fact_id=str(fact_info.dataseries_fact.fact.id),
                fact_type='file'
            )
            payload_serializers[external_id] = CustomFileField(
                allow_null=fact_info.fact.optional,
                required=(not fact_info.fact.optional) and not patch,
                storage_base_path=file_based_fact_dir(
                    tenant_name=data_series.tenant.name,
                    data_series_id=data_series_id,
                    fact_id=str(fact_info.dataseries_fact.fact.id),
                    fact_type='file'
                ),
                max_length=200
            )

    add_file_facts()

    def add_boolean_facts() -> None:
        for external_id, fact_info in _data_series_children_query_info.boolean_facts.items():
            payload_serializers[external_id] = serializers.BooleanField(
                allow_null=fact_info.fact.optional,
                required=(not fact_info.fact.optional) and not patch
            )

    add_boolean_facts()

    def add_dimensions() -> None:
        for external_id, dim_info in _data_series_children_query_info.dimensions.items():
            _referenced_data_series: ReadOnlyDataSeries = dim_info.dimension.reference
            payload_serializers[external_id] = serializers.CharField(
                # self referencing dimensions are allowed to be empty
                # those are always allowed and not only when updating
                max_length=256,
                allow_null=(_referenced_data_series.id == data_series.id) or dim_info.dimension.optional,
                required=(_referenced_data_series.id != data_series.id and not dim_info.dimension.optional) and not patch,
                allow_blank=(_referenced_data_series.id == data_series.id) or dim_info.dimension.optional,
            )

    add_dimensions()

    _serialization_keys = data_point_serialization_keys(_data_series_children_query_info)

    if len(
            _serialization_keys['float_facts'] +
            _serialization_keys['string_facts'] +
            _serialization_keys['text_facts'] +
            _serialization_keys['timestamp_facts'] +
            _serialization_keys['json_facts'] +
            _serialization_keys['image_facts'] +
            _serialization_keys['file_facts'] +
            _serialization_keys['boolean_facts'] +
            _serialization_keys['dimensions']
    ) != \
            len(payload_serializers.keys()):
        raise APIException('unexpectedly found a duplicated external_id in the set of facts and dimensions')

    _patch_value = patch
    _point_in_time_value = point_in_time
    _should_include_versions = should_include_versions

    class PayloadSerializer(serializers.Serializer[Dict[str, Any]]):

        def create(self, validated_data: Any) -> Any:
            # we dont use this
            raise AssertionError()

        def update(self, instance: Any, validated_data: Any) -> Any:
            # we dont use this
            raise AssertionError()

        def to_internal_value(self, data: Dict[str, Any]) -> Dict[str, Any]:
            # from the base class, we need to check this before
            if not isinstance(data, Mapping):
                message = self.error_messages['invalid'].format(
                    datatype=type(data).__name__
                )
                raise ValidationError({
                    api_settings.NON_FIELD_ERRORS_KEY: [message]
                }, code='invalid')

            own_keys = payload_serializers.keys()
            extra_keys = set(data.keys()).difference(own_keys)

            if len(extra_keys) > 0:
                if data_series.allow_extra_fields:
                    for _extra_key in extra_keys:
                        if _extra_key in data:
                            # make sure downstream does not get the data
                            # if we ignore it
                            del data[_extra_key]
                else:
                    raise ValidationError(
                        f'{str(extra_keys)} were set, but were not recognized'
                    )

            return super().to_internal_value(data)  # type: ignore

        def get_fields(self) -> Dict[str, Any]:
            return payload_serializers

    class Specialized(actual_class):  # type: ignore
        patch = _patch_value

        point_in_time = _point_in_time_value
        should_include_versions = _should_include_versions

        external_id = serializers.CharField(
            max_length=256,
            write_only=True,
            required=not _patch_value,
            allow_null=False,
            allow_blank=False
        )

        data_series_children_query_info = _data_series_children_query_info

        serialization_keys = _serialization_keys

        payload = PayloadSerializer(
            default={},
            write_only=True
        )

        def __getitem__(self, key):  # type: ignore
            # hack, return a PayloadNestedField to make rendering the browsable API not crash on non dict values
            field = self.fields[key]
            value = self.data.get(key)
            error = self.errors.get(key) if hasattr(self, '_errors') else None
            if key == 'payload':
                return PayloadNestedField(field, value, error)  # type: ignore
            else:
                return super().__getitem__(key)

        def to_internal_value(self, data: Dict[str, Any]) -> Dict[str, Any]:
            for key in data.keys():
                if key != key.strip():
                    raise ValidationError(
                        f'top level key \'{str(key)}\' contained whitespace at the start/end. This is not allowed.'
                    )
            return cast(Dict[str, Any], super().to_internal_value(data))

        def validate(self, data: Any) -> Any:
            validated = super().validate(data)
            payload = validated['payload']
            # properly construct path based on the external id of the datapoint
            for external_id, base_dir in base_dirs.items():
                if external_id in payload:
                    _val = payload[external_id]
                    _external_id: str
                    if self.instance is not None:
                        _external_id = self.instance.external_id
                    else:
                        _external_id = validated['external_id']
                    if _val is not None:
                        # dont use external_id here or minio will die
                        # generate a random string, worst case older version is overwritten, but that's unlikely
                        _val._name = base_dir + gen_uuid(data_series_id=data_series_id, external_id=_external_id) + '/' + str(uuid.uuid1())
            return validated

    return Specialized
