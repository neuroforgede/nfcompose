# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from skipper.core.models import fields, softdelete
from skipper.dataseries.models.metamodel.base_fact import BaseFact, BaseDataSeriesFactRelation


class FileFact(BaseFact):
    dataseries_filefact: 'DataSeries_FileFact'

    objects: 'softdelete.SoftDeletionManager[FileFact]'  # type: ignore
    all_objects: 'softdelete.SoftDeletionManager[FileFact]'  # type: ignore

    def get_dataseries_relation(self) -> 'DataSeries_FileFact':
        return self.dataseries_filefact


class DataSeries_FileFact(BaseDataSeriesFactRelation):
    fact: FileFact = fields.unique_fkey(FileFact)

    objects: 'softdelete.SoftDeletionManager[DataSeries_FileFact]'  # type: ignore
    all_objects: 'softdelete.SoftDeletionManager[DataSeries_FileFact]'  # type: ignore
