# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from django.db.models import Model
from rest_framework import serializers
from rest_framework.request import Request
from typing import Dict, Any, cast

from skipper.dataseries import constants
from skipper.dataseries.models import ConsumerEvent
from skipper.dataseries.models.metamodel.django_base import DataSeriesMetaModel
from skipper.core.serializers.common import MultipleParameterHyperlinkedIdentityField


class ConsumerEventHyperlinkedIdentityField(MultipleParameterHyperlinkedIdentityField):

    def get_extra_lookup_url_kwargs(self, obj: Model, view_name: str, request: Request, format: str) -> Dict[str, Any]:
        consumer_event = cast(ConsumerEvent, obj)
        return {
            'data_series': consumer_event.consumer.dataseries_consumer.data_series.id,
            'consumer': consumer_event.consumer.id
        }


class ConsumerEventSerializer(serializers.ModelSerializer[ConsumerEvent]):
    url = ConsumerEventHyperlinkedIdentityField(view_name=constants.data_series_consumer_event_base_name + '-detail')

    def create(self, validated_data: Dict[str, Any]) -> ConsumerEvent:
        raise NotImplementedError()

    class Meta:
        model = ConsumerEvent
        fields = (
            'url',
            'id',
            'point_in_time',
            'sub_clock',
            'last_updated_at',
            'backoff_cycles',
            'retries_in_cycle',
            'handle_at',
            'retries',
            'payload',
            'state',
            'event_type',
            # explicitly do not return the response
            # or otherwise we end up giving users a "curl"
            # coming from our system.
            # 'response',
            # 'response_headers',
            'status_code',
            # explicitly leave out the exception as this
            # would leak information about the system
            # 'exception'
        )
