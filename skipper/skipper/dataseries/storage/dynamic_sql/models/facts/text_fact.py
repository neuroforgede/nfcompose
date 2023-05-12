# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from django.db.models import UUIDField, Manager

from skipper.core import models
from skipper.dataseries.storage.dynamic_sql.models.base_relation import BaseDataPointFactRelation


class BaseDataPoint_TextFact(BaseDataPointFactRelation):
    fact_id = UUIDField(null=False)
    value = models.text(null=True)

    objects: 'Manager[DataPoint_TextFact]'

    class Meta:
        abstract = True

    class MyMeta:
        base_entity_name = 'DataPoint_TextFact'


class DataPoint_TextFact(BaseDataPoint_TextFact):
    class MyMeta(BaseDataPoint_TextFact.MyMeta):
        is_view = True


class WritableDataPoint_TextFact(BaseDataPoint_TextFact):
    class MyMeta(BaseDataPoint_TextFact.MyMeta):
        pass