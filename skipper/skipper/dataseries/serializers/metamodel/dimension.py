# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from django.db import transaction
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from django_multitenant.utils import get_current_tenant  # type: ignore
from rest_framework import serializers
from typing import Dict, Any, cast

from django.db.models import Model
from rest_framework.request import Request

from skipper.dataseries import constants
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.models.metamodel.dimension import Dimension, DataSeries_Dimension
from skipper.dataseries.models.metamodel.django_base import DataSeriesMetaModel
from skipper.dataseries.serializers.metamodel.base import _named_serializer_fields
from skipper.dataseries.serializers.metamodel.base_data_series_child import BaseDefaultDataSeriesChildSerializer
from skipper.core.serializers.common import MultipleParameterHyperlinkedIdentityField
from skipper.dataseries.storage import actions as storage_actions


class DimensionHyperlinkedIdentityField(MultipleParameterHyperlinkedIdentityField):

    def get_extra_lookup_url_kwargs(self, obj: Model, view_name: str, request: Request, format: str) -> Dict[str, Any]:
        dimension = cast(Dimension, obj)
        return {'data_series': dimension.dataseries_dimension.data_series.id}


class DimensionSerializer(BaseDefaultDataSeriesChildSerializer):
    url = DimensionHyperlinkedIdentityField(view_name=constants.data_series_dimension_base_name + '-detail')
    # use the manager here so that the tenant specific behaviour works properly
    reference = serializers.HyperlinkedRelatedField(view_name=constants.data_series_base_name + '-detail',
                                                    queryset=DataSeries.objects)

    child_column_name = 'dimension'
    dimension_model = Dimension
    child_model = Dimension
    relation_model = DataSeries_Dimension

    def _access_existing_data_series(self: Any, pk: str) -> DataSeries:
        _dim: Dimension = get_object_or_404(
            Dimension.objects.filter(id=pk))
        return _dim.dataseries_dimension.data_series

    def _get_external_id(self: Any, child: Dimension) -> str:
        return child.dataseries_dimension.external_id

    def validate_reference(self, reference: DataSeries) -> DataSeries:
        kwargs = self.context.get('view').kwargs  # type: ignore
        _own_data_series = self._get_data_series()

        if 'pk' in kwargs:
            _dim: Dimension = get_object_or_404(
                Dimension.objects.filter(id=kwargs['pk']))
            if _dim.reference.id != reference.id:
                raise ValidationError('a dimension can\'t change its referenced dataseries')
        return reference

    def create(self, validated_data: Dict[str, Any]) -> DataSeriesMetaModel:
        with transaction.atomic():
            created = cast(Dimension, super().create(validated_data))
            storage_actions.handle_create_dimension(
                data_series_id=self._get_data_series().id,
                data_series_external_id=self._get_data_series().external_id,
                dimension_id=str(created.id),
                tenant_name=get_current_tenant().name,
                external_id=created.dataseries_dimension.external_id,
                backend=self._get_data_series().backend,
                tenant_id=str(get_current_tenant().id)
            )
            return created

    class Meta:
        model = Dimension
        fields = _named_serializer_fields(('reference', 'optional'))