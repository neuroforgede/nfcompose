# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from django.db.models import BooleanField

from skipper.core.models import fields, softdelete

from skipper.dataseries.models.metamodel.django_base import DataSeriesMetaModel, DataSeriesChildRelationModel
from skipper.dataseries.models.metamodel.data_series import DataSeries


class Dimension(DataSeriesMetaModel):
    """
    Dimensions are modelled as the relation between two DataSeries (read: DataSeries_DataSeries)
    These are an extra entity, so that we can later provide additional functionality
    like e.g. defining extra filters for the cube definition (this is then again an extra relation to stay normalized!)
    """
    id = fields.id_field()
    name = fields.string_field(max_length=256)

    # Dimensions are basically only a relation between two DataSeries,
    # We could really have even modelled Dimensions
    # as DataSeries_DataSeries, but we opted against it
    # as we maybe want to add extra data
    reference = fields.fkey(DataSeries)
    optional = BooleanField()

    dataseries_dimension: 'DataSeries_Dimension'

    objects: 'softdelete.SoftDeletionManager[Dimension]'  # type: ignore
    all_objects: 'softdelete.SoftDeletionManager[Dimension]'  # type: ignore


class DataSeries_Dimension(DataSeriesChildRelationModel):
    """
    Mapping table that maps a DataSeries definition to its Dimensions
    """
    id = fields.id_field()
    data_series = fields.fkey(DataSeries)
    dimension = fields.unique_fkey(Dimension)

    objects: 'softdelete.SoftDeletionManager[DataSeries_Dimension]'  # type: ignore
    all_objects: 'softdelete.SoftDeletionManager[DataSeries_Dimension]'  # type: ignore
