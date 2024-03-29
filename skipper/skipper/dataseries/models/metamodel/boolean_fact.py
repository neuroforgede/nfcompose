# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from skipper.core.models import fields, softdelete
from skipper.dataseries.models.metamodel.base_fact import BaseFact, BaseDataSeriesFactRelation


class BooleanFact(BaseFact):
    dataseries_booleanfact: 'DataSeries_BooleanFact'

    objects: 'softdelete.SoftDeletionManager[BooleanFact]'  # type: ignore
    all_objects: 'softdelete.SoftDeletionManager[BooleanFact]'  # type: ignore

    def get_dataseries_relation(self) -> 'DataSeries_BooleanFact':
        return self.dataseries_booleanfact


class DataSeries_BooleanFact(BaseDataSeriesFactRelation):
    fact: BooleanFact = fields.unique_fkey(BooleanFact)

    objects: 'softdelete.SoftDeletionManager[DataSeries_BooleanFact]'  # type: ignore
    all_objects: 'softdelete.SoftDeletionManager[DataSeries_BooleanFact]'  # type: ignore
