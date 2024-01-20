# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from django.db import transaction
from django.db.models import Model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.request import Request
from typing import Dict, Any, cast

from skipper.core.validators import json_dict_str_str
from skipper.dataseries import constants
from skipper.dataseries.models.metamodel.consumer import Consumer, ConsumerMode, DataSeries_Consumer
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.models.metamodel.django_base import DataSeriesMetaModel
from skipper.core.models.validation import validate_external_id_url_safe
from skipper.core.serializers.common import MultipleParameterHyperlinkedIdentityField
from skipper.dataseries.serializers.metamodel.base import _named_serializer_fields
from skipper.dataseries.serializers.metamodel.base_data_series_child import BaseDefaultDataSeriesChildSerializer


class ConsumerHyperlinkedIdentityField(MultipleParameterHyperlinkedIdentityField):

    def get_extra_lookup_url_kwargs(self, obj: Model, view_name: str, request: Request, format: str) -> Dict[str, Any]:
        consumer = cast(Consumer, obj)
        return {'data_series': consumer.dataseries_consumer.data_series.id}


class ConsumerSerializer(BaseDefaultDataSeriesChildSerializer):
    url = ConsumerHyperlinkedIdentityField(view_name=constants.data_series_consumer_base_name + '-detail')
    headers = serializers.JSONField(allow_null=False, validators=[json_dict_str_str])
    health = serializers.CharField(read_only=True)
    mode = serializers.ChoiceField(choices=ConsumerMode.choices(), default=ConsumerMode.IN_ORDER.value)

    child_column_name = 'consumer'
    consumer_model = Consumer
    child_model = Consumer
    relation_model = DataSeries_Consumer

    def to_representation(self, obj: Consumer) -> Any:
        representation = super().to_representation(obj)
        representation['events'] = self.get_sub_url(
            view_name=constants.data_series_consumer_event_base_name + '-list',
            args=[obj.dataseries_consumer.data_series.id, obj.id]
        )
        return representation

    def _access_existing_data_series(self: Any, pk: str) -> DataSeries:
        _dim: Consumer = get_object_or_404(
            Consumer.objects.filter(id=pk))
        return _dim.dataseries_consumer.data_series

    def validate_headers(self, headers: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(headers, dict):
            raise ValidationError('headers must be a JSON object')
        return headers

    def _get_external_id(self: Any, child: Consumer) -> str:
        return child.dataseries_consumer.external_id

    def create(self, validated_data: Dict[str, Any]) -> DataSeriesMetaModel:
        with transaction.atomic():
            created = cast(Consumer, super().create(validated_data))
            return created

    def validate_external_id(self, external_id: str) -> str:
        kwargs = self.context.get('view').kwargs  # type: ignore
        data_series = self._get_data_series()

        if 'pk' not in kwargs:
            if data_series.dataseries_consumer_set.all().filter(external_id=external_id).exists():
                raise ValidationError(
                    f'external id \'{external_id}\' is already in use by another Consumer in this data series definition')
        else:
            _id = kwargs['pk']
            _child: Consumer = get_object_or_404(
                Consumer.objects.filter(id=_id))
            if external_id != self._get_external_id(_child):
                raise ValidationError('changing of external_id is not supported!')

        # since consumers are not directly translated into SQL
        # names, it is perfectly fine to allow for longer strings
        if not validate_external_id_url_safe(external_id):
            raise ValidationError("Only letters, numbers, '-' and '_' are allowed in external_ids of structure elements, 1-256 chars")

        return external_id

    class Meta:
        model = Consumer
        fields = _named_serializer_fields((
            'target',
            'mode',
            'headers',
            'timeout',
            'retry_backoff_every',
            'retry_backoff_delay',
            'retry_max',
            'health'
        ))
