# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from skipper.core.models import fields, softdelete
from skipper.dataseries.models.metamodel.base_fact import BaseFact, BaseDataSeriesFactRelation


class FloatFact(BaseFact):
    dataseries_floatfact: 'DataSeries_FloatFact'

    objects: 'softdelete.SoftDeletionManager[FloatFact]'  # type: ignore
    all_objects: 'softdelete.SoftDeletionManager[FloatFact]'  # type: ignore

    def get_dataseries_relation(self) -> 'DataSeries_FloatFact':
        return self.dataseries_floatfact


class DataSeries_FloatFact(BaseDataSeriesFactRelation):
    fact: FloatFact = fields.unique_fkey(FloatFact)

    objects: 'softdelete.SoftDeletionManager[DataSeries_FloatFact]'  # type: ignore
    all_objects: 'softdelete.SoftDeletionManager[DataSeries_FloatFact]'  # type: ignore
