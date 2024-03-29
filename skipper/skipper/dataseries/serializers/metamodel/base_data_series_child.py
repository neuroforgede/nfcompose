# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from django.core.exceptions import ValidationError
from django.db import models, transaction
from rest_framework.generics import get_object_or_404
from typing import Type, Any, Dict, cast

from rest_framework import serializers

from skipper.core.exceptions import http as http_exceptions
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.models.metamodel.django_base import DataSeriesMetaModel, DataSeriesChildRelationModel
from skipper.core.models.validation import validate_external_id_sql_safe
from skipper.dataseries.serializers.metamodel.base import DataSeriesBaseSerializer
from skipper.dataseries.views.contract import get_data_series_id


class BaseDefaultDataSeriesChildSerializer(DataSeriesBaseSerializer):
    external_id = serializers.CharField(max_length=256, write_only=True, required=True, allow_null=False)

    child_model: Type[DataSeriesMetaModel]
    relation_model: Type[DataSeriesChildRelationModel]

    child_column_name: str

    def _access_existing_data_series(self: Any, pk: str) -> DataSeries:
        raise NotImplementedError()

    def _get_external_id(self: Any, child: Any) -> str:
        raise NotImplementedError()

    def to_representation(self, obj: Any) -> Any:
        ret = super().to_representation(obj)
        ret['external_id'] = self._get_external_id(obj)
        return ret

    def validate_structural_child_relation_for_external_id(self, query_set: models.QuerySet[DataSeriesChildRelationModel], external_id: str,
                                                           child_type: str) -> None:
        if query_set.filter(external_id=external_id).exists():
            raise ValidationError(
                f'external id \'{external_id}\' is already in use by a {child_type} in this data series definition')

    def validate_external_id(self, external_id: str) -> str:
        kwargs = self.context.get('view').kwargs  # type: ignore
        data_series = self._get_data_series()

        if 'pk' not in kwargs:
            # we are creating a new one
            # disable this validation for bulk insert to improve performance
            if external_id is not None:
                self.validate_structural_child_relation_for_external_id(data_series.dataseries_dimension_set.all(),
                                                                        external_id, 'dimension')
                self.validate_structural_child_relation_for_external_id(data_series.dataseries_jsonfact_set.all(),
                                                                        external_id, 'json fact')
                self.validate_structural_child_relation_for_external_id(data_series.dataseries_imagefact_set.all(),
                                                                        external_id, 'image fact')
                self.validate_structural_child_relation_for_external_id(data_series.dataseries_stringfact_set.all(),
                                                                        external_id, 'string fact')
                self.validate_structural_child_relation_for_external_id(data_series.dataseries_textfact_set.all(),
                                                                        external_id, 'text fact')
                self.validate_structural_child_relation_for_external_id(data_series.dataseries_floatfact_set.all(),
                                                                        external_id, 'float fact')
                self.validate_structural_child_relation_for_external_id(data_series.dataseries_booleanfact_set.all(),
                                                                        external_id, 'boolean fact')
                self.validate_structural_child_relation_for_external_id(data_series.dataseries_timestampfact_set.all(),
                                                                        external_id, 'timestamp fact')

        else:
            _id = kwargs['pk']
            _child: DataSeriesMetaModel = get_object_or_404(
                self.child_model.objects.filter(id=_id))  # type: ignore
            if external_id != self._get_external_id(_child):
                raise ValidationError('changing of external_id is not supported!')

        if not validate_external_id_sql_safe(external_id):
            raise ValidationError("Only letters, numbers and '_' are allowed in external_ids of structure elements, 1-50 chars")

        return external_id

    def _get_data_series(self: Any) -> DataSeries:
        kwargs = self.context.get('view').kwargs

        if 'pk' not in kwargs:
            if 'data_series' not in kwargs:
                raise http_exceptions.Http400('data_series not set in request')
            data_series_id = get_data_series_id(kwargs)
            data_series: DataSeries = get_object_or_404(
                DataSeries.objects.filter(id=data_series_id))
        else:
            data_series = self._access_existing_data_series(kwargs['pk'])

        return data_series

    def create(self, validated_data: Dict[str, Any]) -> DataSeriesMetaModel:
        kwargs = self.context.get('view').kwargs  # type: ignore
        if 'data_series' not in kwargs:
            raise http_exceptions.Http400('data_series not set in request')
        data_series_id = get_data_series_id(kwargs)

        with transaction.atomic():
            data_series = get_object_or_404(
                DataSeries.objects.filter(id=data_series_id))

            _external_id = validated_data['external_id']
            del validated_data['external_id']

            child = cast(DataSeriesMetaModel, super().create(validated_data))
            args = {'data_series': data_series, 'external_id': _external_id, self.child_column_name: child}
            self.relation_model.objects.create(
                **args
            ).save()

            return child