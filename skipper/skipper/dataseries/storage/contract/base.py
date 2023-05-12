# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


import json
from json import JSONDecodeError

import datetime
from abc import abstractmethod, ABCMeta
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.request import Request
from rest_framework.serializers import SerializerMetaclass
from typing import Dict, Any, Optional, Union, Tuple
from uuid import UUID

from skipper.core.serializers.base import BaseSerializer
from skipper.core.utils.memoize import Memoize
from skipper.dataseries import constants
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.raw_sql import dbtime
from skipper.dataseries.storage import repositories
from skipper.dataseries.storage.contract.fields import DataPointHyperlinkedIdentityField
from skipper.dataseries.storage.contract.repository import ReadOnlyDataPoint
from skipper.dataseries.storage.static_ds_information import DataSeriesQueryInfo, compute_data_series_query_info, \
    DataPointSerializationKeys, compute_basic_data_series_query_info
from skipper.dataseries.storage.uuid import gen_uuid
from skipper.dataseries.storage.validate import validate, ValidationRequest
from skipper.dataseries.storage.validate.contract import DataPointAccessor
from skipper.dataseries.views.contract import get_data_series_id
from skipper.dataseries.views.datapoint.external_id import use_external_id_as_dimension_identifier


class BaseDataPointSerializer(BaseSerializer):
    url = DataPointHyperlinkedIdentityField(view_name=constants.data_series_data_point_base_name + '-detail')
    history_url = DataPointHyperlinkedIdentityField(view_name=constants.data_series_history_data_point_base_name + '-detail')
    id = serializers.CharField(read_only=True)

    # allow all characters except /
    # this enables spaces in url paths
    lookup_value_regex = '[^/]+'


class ABCSerializerMeta(ABCMeta, SerializerMetaclass):
    pass


class BaseDataPointModificationSerializer(BaseDataPointSerializer, metaclass=ABCSerializerMeta):
    """
    Base serializer class for C_U_ (as in CRUD) operations
    on datapoints. Wraps all the logic for getting the appropriate
    data from the view/request etc so that storage backends
    can focus on actual serialization logic
    instead of DRF stuff
    """

    external_id = serializers.CharField(
        max_length=256,
        write_only=True,
        required=True,
        allow_null=False,
        allow_blank=False
    )
    identify_dimensions_by_external_id = serializers.BooleanField(default=False, write_only=True)

    point_in_time: Optional[datetime.datetime]
    should_include_versions: bool

    serialization_keys: DataPointSerializationKeys

    data_series_children_query_info: DataSeriesQueryInfo

    bulk_insert: bool

    patch: bool = False

    def __init__(self, *args, **kwargs) -> None:  # type: ignore

        def _get_data_series(self: BaseDataPointModificationSerializer) -> DataSeries:
            kwargs = self.context.get('view').kwargs  # type: ignore

            if 'data_series' not in kwargs:
                raise ValidationError('data_series not set in request')
            data_series_id = get_data_series_id(kwargs)
            data_series: DataSeries = get_object_or_404(
                DataSeries.objects.filter(id=data_series_id))

            return data_series

        self.__get_data_series = Memoize(_get_data_series)

        if self.data_series_children_query_info is None:
            self.data_series_children_query_info = compute_data_series_query_info(self.__get_data_series(self))

        if 'bulk_insert' in kwargs:
            self.bulk_insert = kwargs['bulk_insert']
            del kwargs['bulk_insert']
        else:
            self.bulk_insert = False

        super().__init__(*args, **kwargs)

    def get_data_series(self) -> DataSeries:
        return self.__get_data_series(self)

    def get_data_series_children_query_info(self) -> DataSeriesQueryInfo:
        return self.data_series_children_query_info

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        view: Any = self.context.get('view')
        get_dict = view.request.GET
        kwargs = view.kwargs
        bulk_insert: bool = self.bulk_insert

        # transform the http request into something the validate function can handle

        if 'payload' not in attrs:
            attrs['payload'] = {}

        if '__FILES_SUPPORTED__' in view.request.parser_context and not bool(view.request.parser_context['__FILES_SUPPORTED__']):
            for external_id, image_fact in self.data_series_children_query_info.image_facts.items():
                if external_id in attrs['payload']:
                    raise ValidationError('selected content type does not support files')
            for external_id, file_fact in self.data_series_children_query_info.file_facts.items():
                if external_id in attrs['payload']:
                    raise ValidationError('selected content type does not support files')

        data_point_id = None
        if 'pk' in kwargs:
            data_point_id = kwargs['pk']

        if 'by_external_id' in kwargs:
            if data_point_id is not None:
                data_point_id = gen_uuid(
                    data_series_id=self.data_series_children_query_info.data_series_id,
                    external_id=data_point_id
                )

        # TODO: cache this for the lifetime of the serializer
        def ___data_point_accessor(
            x: Tuple[str, Union[str, UUID]],
        ) -> Optional[ReadOnlyDataPoint]:
            identifier, data_series_id = x
            _ds = DataSeries.objects.get(id=data_series_id)

            _basic_query_info = compute_basic_data_series_query_info(
                _ds
            )

            return repositories.repository(_ds.get_backend_type()).get_data_point(identifier, _basic_query_info)

        __data_point_accessor = Memoize(___data_point_accessor)

        def _data_point_accessor(identifier: str, data_series_id: Union[str, UUID]) -> Optional[ReadOnlyDataPoint]:
            return __data_point_accessor((identifier, data_series_id))

        return validate(
            data=attrs,
            request=ValidationRequest(
                partial=self.patch,
                data_point_relation_info=self.data_series_children_query_info,
                data_point_id=data_point_id,
                bulk_insert=bulk_insert,
                external_id_as_dimension_identifier=use_external_id_as_dimension_identifier(get_dict, attrs),
                data_point_accessor=_data_point_accessor
            )
        )

    def to_representation(self, data_point: Any) -> Any:
        # just delegate to the same serializer we use for lists here
        data_series = get_object_or_404(
            DataSeries.objects.filter(id=data_point.data_series_id))

        _view = self.context.get('view')

        assert _view is not None
        _validated_data = None

        if hasattr(self, '_validated_data'):
            _validated_data = self.validated_data

        return self.impl_internal_to_representation(
            data_point=data_point,
            data_series=data_series,
            external_id_as_dimension_identifier=use_external_id_as_dimension_identifier(
                _view.request.GET,
                _validated_data
            )
        )

    def create(self, validated_data: Dict[str, Any]) -> Any:
        kwargs = self.context.get('view').kwargs  # type: ignore
        if 'data_series' not in kwargs:
            raise ValidationError('data_series not set in request')

        request: Request = self.context.get('view').request  # type: ignore

        return self.impl_create(
            validated_data=validated_data,
            user_id=str(request.user.id),
            record_source='REST API',
            data_series_id=get_data_series_id(kwargs),
            data_series_external_id=self.get_data_series().external_id,
            data_series_backend=self.get_data_series().backend,
            timestamp=dbtime.now(),
            sub_clock=dbtime.dp_sub_clock(self.get_data_series().tenant)
        )

    # TODO: improve typing for data_point here!
    def update(self, data_point: Any, validated_data: Dict[str, Any]) -> Any:
        kwargs = self.context.get('view').kwargs  # type: ignore
        if 'data_series' not in kwargs:
            raise ValidationError('data_series not set in request')

        request: Request = self.context.get('view').request  # type: ignore
        record_source = 'REST API PUT'
        if self.patch:
            record_source = 'REST API PATCH'

        if 'external_id' not in validated_data:
            validated_data['external_id'] = data_point.external_id

        return self.impl_update(
            data_point=data_point,
            validated_data=validated_data,
            user_id=str(request.user.id),
            record_source=record_source,
            data_series_id=get_data_series_id(kwargs),
            data_series_external_id=self.get_data_series().external_id,
            data_series_backend=self.get_data_series().backend,
            timestamp=dbtime.now(),
            sub_clock=dbtime.dp_sub_clock(self.get_data_series().tenant)
        )

    # implementation contract

    @abstractmethod
    def impl_internal_to_representation(
            self,
            data_point: Any,
            data_series: DataSeries,
            external_id_as_dimension_identifier: bool
    ) -> Dict[str, Any]:
        raise NotImplementedError()

    @abstractmethod
    def impl_create(
            self,
            validated_data: Dict[str, Any],
            user_id: str,
            record_source: str,
            data_series_id: str,
            data_series_external_id: str,
            data_series_backend: str,
            timestamp: datetime.datetime,
            sub_clock: int
    ) -> Any:
        raise NotImplementedError()

    @abstractmethod
    def impl_update(
            self,
            data_point: Any,
            validated_data: Dict[str, Any],
            user_id: str,
            record_source: str,
            data_series_id: str,
            data_series_external_id: str,
            data_series_backend: str,
            timestamp: datetime.datetime,
            sub_clock: int
    ) -> Any:
        raise NotImplementedError()


