# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from skipper.core.models import fields, softdelete
from skipper.dataseries.models.metamodel.base_fact import BaseFact, BaseDataSeriesFactRelation


class StringFact(BaseFact):
    dataseries_stringfact: 'DataSeries_StringFact'

    objects: 'softdelete.SoftDeletionManager[StringFact]'  # type: ignore
    all_objects: 'softdelete.SoftDeletionManager[StringFact]'  # type: ignore

    def get_dataseries_relation(self) -> 'DataSeries_StringFact':
        return self.dataseries_stringfact


class DataSeries_StringFact(BaseDataSeriesFactRelation):
    fact: StringFact = fields.unique_fkey(StringFact)

    objects: 'softdelete.SoftDeletionManager[DataSeries_StringFact]'  # type: ignore
    all_objects: 'softdelete.SoftDeletionManager[DataSeries_StringFact]'  # type: ignore