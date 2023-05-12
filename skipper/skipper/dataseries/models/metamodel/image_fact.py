# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from skipper.core.models import fields, softdelete
from skipper.dataseries.models.metamodel.base_fact import BaseFact, BaseDataSeriesFactRelation


class ImageFact(BaseFact):
    dataseries_imagefact: 'DataSeries_ImageFact'

    objects: 'softdelete.SoftDeletionManager[ImageFact]'  # type: ignore
    all_objects: 'softdelete.SoftDeletionManager[ImageFact]'  # type: ignore

    def get_dataseries_relation(self) -> 'DataSeries_ImageFact':
        return self.dataseries_imagefact


class DataSeries_ImageFact(BaseDataSeriesFactRelation):
    fact: ImageFact = fields.unique_fkey(ImageFact)

    objects: 'softdelete.SoftDeletionManager[DataSeries_ImageFact]'  # type: ignore
    all_objects: 'softdelete.SoftDeletionManager[DataSeries_ImageFact]'  # type: ignore
