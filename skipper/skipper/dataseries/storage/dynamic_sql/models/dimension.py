# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from django.db.models import Model, DateTimeField, UUIDField, Manager

from skipper.core import models
from skipper.dataseries.storage.dynamic_sql.models.base_relation import BaseDataPointRelationMetaClass


class BaseDataPoint_Dimension(Model, metaclass=BaseDataPointRelationMetaClass):
    data_point_id = models.string_field(max_length=512, pk=True)
    point_in_time = DateTimeField(auto_now=False, db_index=False)
    dimension_id = UUIDField(null=False)
    value = models.string_field(max_length=512)
    user_id = models.string_field(max_length=512, null=True)
    record_source = models.string_field(max_length=512, null=True)
    sub_clock = models.BigIntegerField(null=True, blank=False)

    class Meta:
        abstract = True

    class MyMeta:
        base_entity_name = 'DataPoint_Dimension'


class DataPoint_Dimension(BaseDataPoint_Dimension):
    objects: 'Manager[DataPoint_Dimension]'

    class MyMeta(BaseDataPoint_Dimension.MyMeta):
        is_view = True


class WritableDataPoint_Dimension(BaseDataPoint_Dimension):
    class MyMeta(BaseDataPoint_Dimension.MyMeta):
        pass