# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from skipper.core.models import fields, softdelete
from skipper.dataseries.models.metamodel.base_fact import BaseFact, BaseDataSeriesFactRelation


class JsonFact(BaseFact):
    dataseries_jsonfact: 'DataSeries_JsonFact'

    objects: 'softdelete.SoftDeletionManager[JsonFact]'  # type: ignore
    all_objects: 'softdelete.SoftDeletionManager[JsonFact]'  # type: ignore

    def get_dataseries_relation(self) -> 'DataSeries_JsonFact':
        return self.dataseries_jsonfact


class DataSeries_JsonFact(BaseDataSeriesFactRelation):
    fact: JsonFact = fields.unique_fkey(JsonFact)

    objects: 'softdelete.SoftDeletionManager[DataSeries_JsonFact]'  # type: ignore
    all_objects: 'softdelete.SoftDeletionManager[DataSeries_JsonFact]'  # type: ignore