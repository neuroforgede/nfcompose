# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from django.db import transaction
from django_multitenant.utils import get_current_tenant  # type: ignore
from rest_framework.generics import get_object_or_404
from typing import Dict, Any, cast, Type

from django.db.models import Model
from rest_framework.request import Request

from skipper.dataseries.models.metamodel.base_fact import BaseFact, BaseDataSeriesFactRelation
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.models.metamodel.django_base import DataSeriesMetaModel
from skipper.core.serializers.common import MultipleParameterHyperlinkedIdentityField
from skipper.dataseries.serializers.metamodel.base import _named_serializer_fields
from skipper.dataseries.serializers.metamodel.base_data_series_child import BaseDefaultDataSeriesChildSerializer
from skipper.dataseries.storage import actions as storage_actions
from skipper.dataseries.storage.contract import FactType


class BaseFactSerializer(BaseDefaultDataSeriesChildSerializer):
    child_column_name = 'fact'

    class Meta:
        fields = _named_serializer_fields(('optional',))


class BaseFactHyperlinkedIdentityField(MultipleParameterHyperlinkedIdentityField):

    def get_extra_lookup_url_kwargs(self, obj: Model, view_name: str, request: Request, format: str) -> Dict[str, Any]:
        fact = cast(BaseFact, obj)
        return {'data_series': fact.get_dataseries_relation().data_series.id}


def generate_fact_serializer(
        detail_base_name: str,
        model_type: Type[BaseFact],
        relation_type: Type[BaseDataSeriesFactRelation],
        fact_type: FactType
) -> Type[BaseFactSerializer]:
    class ActualSerializer(BaseFactSerializer):
        url = BaseFactHyperlinkedIdentityField(view_name=f'{detail_base_name}-detail')

        relation_model = relation_type
        child_model = model_type

        def _access_existing_data_series(self: Any, pk: str) -> DataSeries:
            _fact: BaseFact = \
                get_object_or_404(model_type.objects.filter(id=pk))  # type: ignore
            return _fact.get_dataseries_relation().data_series

        def _get_external_id(self: Any, child: BaseFact) -> str:
            return child.get_dataseries_relation().external_id

        def create(self, validated_data: Dict[str, Any]) -> DataSeriesMetaModel:
            with transaction.atomic():
                created = cast(BaseFact, super().create(validated_data))
                storage_actions.handle_create_fact(
                    data_series_id=self._get_data_series().id,
                    data_series_external_id=self._get_data_series().external_id,
                    fact_id=str(created.id),
                    fact_type=fact_type,
                    tenant_name=get_current_tenant().name,
                    external_id=created.get_dataseries_relation().external_id,
                    backend=self._get_data_series().backend,
                    tenant_id=str(get_current_tenant().id)
                )
                return created

        class Meta(BaseFactSerializer.Meta):
            model = model_type

    return ActualSerializer
