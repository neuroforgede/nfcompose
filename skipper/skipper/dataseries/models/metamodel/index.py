# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


import uuid
from enum import Enum
from typing import List, Tuple
from django.db import models
from django.db.models.base import Model
from django.db.models.fields import CharField
from skipper.core.models import fields
from skipper.core.models import softdelete
from skipper.core.models.softdelete import SoftDeletionQuerySet
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.models.metamodel.django_base import DataSeriesChildRelationModel, DataSeriesMetaModel
from skipper.dataseries.storage.contract import IndexableDataSeriesChildType


class IndexRegistrySourceType(Enum):
    USER_DEFINED_INDEX = "USER_DEFINED_INDEX"

    @classmethod
    def choices(cls) -> Tuple[Tuple[str, str], ...]:
        return tuple((i.name, i.value) for i in cls)


class TargetTableType(Enum):
    MATERIALIZED = "MATERIALIZED"
    FLAT_HISTORY = "FLAT_HISTORY"

    @classmethod
    def choices(cls) -> Tuple[Tuple[str, str], ...]:
        return tuple((i.name, i.value) for i in cls)


class UserDefinedIndex(DataSeriesMetaModel):
    """
    Index entries pointing to facts facilitate indexing in postgres on these facts
    """
    id = fields.id_field()
    name = fields.string_field(max_length=256)

    userdefinedindex_target_set: 'SoftDeletionQuerySet[UserDefinedIndex_Target]'
    dataseries_userdefinedindex: 'DataSeries_UserDefinedIndex'
    objects: 'softdelete.SoftDeletionManager[UserDefinedIndex]'     # type: ignore
    all_objects: 'softdelete.SoftDeletionManager[UserDefinedIndex]'     # type: ignore

    def __str__(self) -> str:
        if self.dataseries_userdefinedindex is not None:
            return f'Index "{self.name}" ({str(self.dataseries_userdefinedindex.external_id)},{str(self.id)})'
        else:
            return f'Index "{self.name}" ({None},{str(self.id)})'


class DataSeries_UserDefinedIndex(DataSeriesChildRelationModel):
    """
    Mapping table that maps a DataSeries definition to its Indexes
    """

    id = fields.id_field()
    data_series = fields.fkey(DataSeries)
    user_defined_index = fields.unique_fkey(UserDefinedIndex)

    objects: 'softdelete.SoftDeletionManager[DataSeries_UserDefinedIndex]'  # type: ignore
    all_objects: 'softdelete.SoftDeletionManager[DataSeries_UserDefinedIndex]'  # type: ignore


class UserDefinedIndex_Target(DataSeriesMetaModel):
    """
    Maps Indexes to their target UUIDs (many-to-many!)
    """
    id = fields.id_field()
    user_defined_index = fields.fkey(UserDefinedIndex)
    target_id = fields.foreign_id_field()
    target_type = CharField(choices=IndexableDataSeriesChildType.choices(), blank=False, null=False, max_length=256)
    target_position_in_index_order = fields.int_field()

    class Meta:
        unique_together = (
            ('user_defined_index', 'target_id'),
            ('user_defined_index', 'target_position_in_index_order')
        )


class IndexByUUID(Model):
    """
    This is only for bookkeeping - All indexes actually placed using the UserDefinedIndex models are written down here.
    """
    id = fields.id_field()
    source_id = fields.foreign_id_field()
    source_type = models.CharField(choices=IndexRegistrySourceType.choices(), blank=False, null=False, max_length=256)
    db_name = fields.string_field(max_length=63)
    target_table = fields.string_field(max_length=63)
    target_table_type = models.CharField(choices=TargetTableType.choices(), blank=False, null=False, max_length=256)

    objects: 'softdelete.SoftDeletionManager[IndexByUUID]'  # type: ignore
    all_objects: 'softdelete.SoftDeletionManager[IndexByUUID]'  # type: ignore

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['db_name'], name='unique_index_db_name')
        ]
        unique_together = (('source_id', 'target_table_type'))
        db_table = '_3_index_by_uuid'


def get_indexes_by_target_id(target_id: uuid.UUID) -> List[UserDefinedIndex]:
    ret = UserDefinedIndex.objects.filter(userdefinedindex_target__target_id=target_id)
    return list(ret)
