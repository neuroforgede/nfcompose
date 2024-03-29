# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

import datetime
from django.utils import timezone
from rest_framework import serializers
from typing import List

from skipper.core.serializers.base import BaseSerializer
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.raw_sql import dbtime


class PruneDataSeriesSerializer(BaseSerializer):
    older_than = serializers.DateTimeField(allow_null=True, required=False, default=None)
    accept = serializers.BooleanField(allow_null=True, required=False, default=False)

    def validate_older_than(self, older_than: datetime.datetime) -> datetime.datetime:
        if older_than is None:
            older_than = dbtime.now() - timezone.timedelta(days=30)
        return older_than

    class Meta:
        # not really this class, but this is the closest one anyways
        model = DataSeries
        fields: List[str] = ['older_than', 'accept']
