# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from datetime import timedelta
from django.core.validators import MinValueValidator, URLValidator
from django.db.models import URLField, FloatField, IntegerField, DurationField, CharField
from enum import Enum
from typing import Tuple, cast, Dict

from skipper.core.models import fields, softdelete
from skipper.core.models.fields import EmptyDictNotBlankJSONField
from skipper.core.validators import json_dict_str_str
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.models.metamodel.django_base import DataSeriesMetaModel, DataSeriesChildRelationModel


class ConsumerHealthState(Enum):
    # default should always be the first, so DRF displays it by default in the UI
    UNKNOWN = 'UNKNOWN'
    UNHEALTHY = 'UNHEALTHY'
    HEALTHY = 'HEALTHY'

    @classmethod
    def choices(cls) -> Tuple[Tuple[str, str], ...]:
        return tuple((i.name, i.value) for i in cls)


class Consumer(DataSeriesMetaModel):  # type: ignore
    id = fields.id_field()
    name = fields.string_field(max_length=256)

    target = URLField(max_length=1024, validators=[URLValidator(schemes=['https', 'http'])])
    headers = EmptyDictNotBlankJSONField(null=True, blank=False, default=dict, validators=[json_dict_str_str])

    timeout = FloatField(null=False, default=60, validators=[MinValueValidator(0.1)])

    health = CharField(max_length=100, null=False, default=ConsumerHealthState.UNKNOWN.value, choices=ConsumerHealthState.choices(), db_index=False)

    # by default backoff every 1
    retry_backoff_every = IntegerField(null=False, default=1)
    # if we have to back off, add 30 seconds delay by default
    retry_backoff_delay = DurationField(null=False, default=timedelta(seconds=30))
    # by default retry until forever (0)
    retry_max = IntegerField(null=False, default=0)

    dataseries_consumer: 'DataSeries_Consumer'

    objects: 'softdelete.SoftDeletionManager[Consumer]'  # type: ignore
    all_objects: 'softdelete.SoftDeletionManager[Consumer]'  # type: ignore

    def __str__(self) -> str:
        if self.dataseries_consumer is not None:
            return f'Consumer "{self.name}" ({str(self.dataseries_consumer.external_id)},{str(self.id)})'
        else:
            return f'Consumer "{self.name}" ({None},{str(self.id)})'


class DataSeries_Consumer(DataSeriesChildRelationModel):
    """
    Mapping table that maps a DataSeries definition to its consumers
    """
    id = fields.id_field()
    data_series = fields.fkey(DataSeries)
    consumer = fields.unique_fkey(Consumer)
    # since consumers are not directly translated into SQL
    # names, it is perfectly fine to allow for longer strings
    external_id = fields.external_id_field_url_safe()

    objects: 'softdelete.SoftDeletionManager[DataSeries_Consumer]'  # type: ignore
    all_objects: 'softdelete.SoftDeletionManager[DataSeries_Consumer]'  # type: ignore
