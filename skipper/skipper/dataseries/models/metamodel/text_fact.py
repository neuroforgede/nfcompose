# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from skipper.core.models import fields, softdelete
from skipper.dataseries.models.metamodel.base_fact import BaseFact, BaseDataSeriesFactRelation


class TextFact(BaseFact):
    dataseries_textfact: 'DataSeries_TextFact'

    objects: 'softdelete.SoftDeletionManager[TextFact]'  # type: ignore
    all_objects: 'softdelete.SoftDeletionManager[TextFact]'  # type: ignore

    def get_dataseries_relation(self) -> 'DataSeries_TextFact':
        return self.dataseries_textfact


class DataSeries_TextFact(BaseDataSeriesFactRelation):
    fact: TextFact = fields.unique_fkey(TextFact)

    objects: 'softdelete.SoftDeletionManager[DataSeries_TextFact]'  # type: ignore
    all_objects: 'softdelete.SoftDeletionManager[DataSeries_TextFact]'  # type: ignore
