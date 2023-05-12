# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from django.db.models import QuerySet
from django_filters.rest_framework import FilterSet, MultipleChoiceFilter, IsoDateTimeFromToRangeFilter  # type: ignore
from rest_framework import mixins, permissions
from typing import Type, Sequence, Any, Dict, cast

from skipper.dataseries import constants
from skipper.dataseries.models import DATASERIES_PERMISSION_KEY_CONSUMER, \
    ConsumerEvent, ConsumerEventType, ConsumerEventState
from skipper.dataseries.serializers.event import ConsumerEventSerializer
from skipper.dataseries.views.common import HasDataSeriesGlobalReadPermission, get_dataseries_permissions_class
from skipper.dataseries.views.contract import get_data_series_object
from skipper.dataseries.views.metamodel.permissions import metamodel_base_line_permissions
from skipper.dataseries.views.metamodel.structure import BaseDataSeriesViewSet


class DataSeries_ConsumerEventFilterSet(FilterSet):  # type: ignore
    point_in_time = IsoDateTimeFromToRangeFilter()
    last_updated_at = IsoDateTimeFromToRangeFilter()
    state = MultipleChoiceFilter(choices=ConsumerEventState.choices())
    event_type = MultipleChoiceFilter(choices=ConsumerEventType.choices())


class DataSeries_ConsumerEventViewSet(
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    BaseDataSeriesViewSet
):
    skipper_base_name = constants.data_series_consumer_event_base_name

    permission_classes  = (
        *metamodel_base_line_permissions,
        HasDataSeriesGlobalReadPermission,
        get_dataseries_permissions_class(DATASERIES_PERMISSION_KEY_CONSUMER),
        # no need to use get_dataseries_object_permissions_class here, this is checked by get_queryset already
        # get_dataseries_object_permissions_class(DATASERIES_PERMISSION_KEY_STRUCTURE_ELEMENT, get_data_series_for_child),
    )

    def get_view_name(self) -> str:
        return 'Events for Consumer'

    serializer_class = ConsumerEventSerializer

    filterset_class = DataSeries_ConsumerEventFilterSet

    def get_queryset(self) -> 'QuerySet[Any]':
        data_series = get_data_series_object(self.kwargs, DATASERIES_PERMISSION_KEY_CONSUMER, self.request)
        if data_series is None:
            return cast('QuerySet[Any]', ConsumerEvent.objects.none())
        else:
            filter: Dict[str, Any] = {
                f'consumer__dataseries_consumer__data_series': data_series.id
            }
            if 'by_external_id' in self.kwargs:
                filter['consumer__dataseries_consumer__external_id'] = self.kwargs['consumer']
            else:
                filter['consumer_id'] = self.kwargs['consumer']
            return cast(
                'QuerySet[Any]',
                ConsumerEvent.objects
                    .select_related('consumer')
                    .filter(**filter)
                    .order_by('id')
                    .all()
            )
