# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from rest_framework import serializers
from rest_framework.fields import CharField, JSONField, FloatField
from rest_framework.relations import HyperlinkedIdentityField

from skipper.core.serializers.base import BaseSerializer
from skipper.health import constants
from skipper.health.models import SubSystemHealth


class SubSystemHealthSerializer(BaseSerializer):
    url = HyperlinkedIdentityField(view_name=constants.health_view_base_name + '-detail')
    key = CharField(read_only=True)
    last_check = CharField(read_only=True)
    health = CharField(read_only=True)
    last_errors = JSONField(read_only=True)
    time_taken = FloatField(read_only=True)

    class Meta:
        model = SubSystemHealth
        fields = (
            'url',
            'key',
            'last_check',
            'health',
            'last_errors',
            'time_taken'
        )

