# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from skipper.core.models import fields, softdelete
from skipper.dataseries.models.metamodel.base_fact import BaseFact, BaseDataSeriesFactRelation


class TimestampFact(BaseFact):
    dataseries_timestampfact: 'DataSeries_TimestampFact'

    objects: 'softdelete.SoftDeletionManager[TimestampFact]'  # type: ignore
    all_objects: 'softdelete.SoftDeletionManager[TimestampFact]'  # type: ignore

    def get_dataseries_relation(self) -> 'DataSeries_TimestampFact':
        return self.dataseries_timestampfact


class DataSeries_TimestampFact(BaseDataSeriesFactRelation):
    fact: TimestampFact = fields.unique_fkey(TimestampFact)

    objects: 'softdelete.SoftDeletionManager[DataSeries_TimestampFact]'  # type: ignore
    all_objects: 'softdelete.SoftDeletionManager[DataSeries_TimestampFact]'  # type: ignore
