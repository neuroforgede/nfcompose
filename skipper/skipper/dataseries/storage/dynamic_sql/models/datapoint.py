# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from typing import List

from django.db.models import Model, UUIDField, DateTimeField, QuerySet, Manager

from skipper.core import models
from skipper.dataseries.storage.contract.models import DisplayDataPoint
from skipper.dataseries.models import calc_db_table


class BaseDataPoint(Model):
    """
    DataPoint is the only direct child of a DataSeries. This is
    due to the following reasons:

    - We want to be able to query quickly for all datapoints
    - We have to generate a hashed id for the datapoint
        - If we used regular relation tables, we would have to duplicate the id generation
          that we use for DataPoints into the relation table just for the sake of
    - If we had the relation DataSeries_DataPoint, DataVault design would be more confusing as
      it already is
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
    The actual DataPoint interface we use everywhere.
    All inserts, updates, etc are properly managed
    by instead of triggers.

    NEVER CALL save on instances of this, or this will duplicate
    entries in the db and pollute it
    """
    objects: 'Manager[DataPoint]'

    class Meta:
        managed = False
        default_permissions: List[str] = []
        db_table = calc_db_table('ViewDataPoint')


class WritableDataPoint(BaseDataPoint):
    """
    should not really be used in any code, but this is
    intended so that django properly generates the class
    """
    objects: 'Manager[WritableDataPoint]'

    class Meta:
        managed = False
        default_permissions: List[str] = []
        db_table = calc_db_table('DataPoint')

# explicit reexport
DisplayDataPoint = DisplayDataPoint