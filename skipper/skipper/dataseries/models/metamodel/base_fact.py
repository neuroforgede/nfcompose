# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from typing import Any

from django.db.models import BooleanField

from skipper.core.models import fields, FKey
from skipper.dataseries.models.metamodel.django_base import DataSeriesMetaModel, DataSeriesChildRelationModel
from skipper.dataseries.models.metamodel.data_series import DataSeries


class BaseFact(DataSeriesMetaModel):
    id = fields.id_field()
    name = fields.string_field(max_length=256)
    optional = BooleanField()

    def get_dataseries_relation(self) -> 'BaseDataSeriesFactRelation':
        raise NotImplementedError('get_data_series_relation was not implemented')

    class Meta:
        abstract = True


class BaseDataSeriesFactRelation(DataSeriesChildRelationModel):
    id = fields.id_field()
    data_series = FKey(DataSeries)
    fact: BaseFact

    class Meta:
        abstract = True
