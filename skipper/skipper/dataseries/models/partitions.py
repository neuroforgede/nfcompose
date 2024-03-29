# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

import uuid
from django.db.models import Model, UUIDField, UniqueConstraint, CharField
from typing import Union

from skipper.core import models
from skipper.dataseries.raw_sql import escape


class PartitionByUUID(Model):
    """
    DEPRECATED
    """
    id = models.id_field()
    base_table = models.string_field(max_length=63)
    child_table = CharField(max_length=63)
    child_table_schema = CharField(max_length=63, null=True)
    partition_key = UUIDField()

    def __str__(self) -> str:
        return f'PartitionByUUID(id=\'{str(self.id)}\',base_table=\'{self.base_table}\',' \
               f'child_table=\'{self.child_table}\',partition_key=\'{str(self.partition_key)}\')'

    class Meta:
        db_table = '_3_partition_by_uuid'
        constraints = [
            UniqueConstraint(
                fields=['base_table', 'partition_key'],
                name=f"_3_partition_by_uuid_base_table_partition_key"
            ),
            UniqueConstraint(
                fields=['child_table', 'partition_key'],
                name=f"_3_partition_by_uuid_child_table_partition_key"
            )
        ]


def fully_qualified_partition_table(base_table: str, partition_key: Union[str, uuid.UUID]) -> str:
    partition = PartitionByUUID.objects.get(base_table=base_table, partition_key=partition_key)
    schema_prefix = f'{escape.escape(partition.child_table_schema)}.' if partition.child_table_schema is not None else ''
    return f'{schema_prefix}{escape.escape(partition.child_table)}'
