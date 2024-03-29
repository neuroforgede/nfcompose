# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from typing import List

from django.db.models import Model, UUIDField, DateTimeField, QuerySet, Manager

from skipper.core import models
from skipper.dataseries.storage.contract.models import DisplayDataPoint
from skipper.dataseries.models import calc_db_table


class BaseDataPoint(Model):
    """
    DEPRECATED: Don't use this for anything new
    """
    id = models.string_field(max_length=512, pk=True)
    data_series_id = UUIDField(null=False)
    external_id = models.external_id_field_sql_safe(null=False)
    deleted = models.BooleanField(default=False)
    point_in_time = DateTimeField(auto_now=False, db_index=False)
    user_id = models.string_field(max_length=512, null=True)
    record_source = models.string_field(max_length=512, null=True)
    sub_clock = models.BigIntegerField(null=True, blank=False)

    objects: 'Manager[BaseDataPoint]'

    class Meta:
        abstract = True


class DataPoint(BaseDataPoint):
    """
    DEPRECATED: Don't use this for anything new
    """

    class Meta:
        managed = False
        default_permissions: List[str] = []
        db_table = calc_db_table('ViewDataPoint')

# explicit reexport
DisplayDataPoint = DisplayDataPoint