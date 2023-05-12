# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

"""
This module is intended as a central place where backends can keep track of
any files they have stored. Any files they store should be registered
"""

from django.db.models import DO_NOTHING, ForeignKey, BigAutoField, UniqueConstraint, Index
from django.db.models.fields import DateTimeField, UUIDField
from django_multitenant.fields import TenantForeignKey  # type: ignore
from django_multitenant.mixins import TenantModelMixin  # type: ignore
from django_multitenant.models import TenantManager  # type: ignore
from typing import List

from skipper.core import models
from skipper.core.models.softdelete import SoftDeletionTenantModel, SoftDeletionTenantManager, SoftDeletionManager
from skipper.core.models.tenant import get_tenant_model


class FileLookup(SoftDeletionTenantModel):  # type: ignore
    """
    database entity that can be used by backends to keep track of
    stored files. Required for the flat history as well as the
    no history backend as both dont store the data as fine granularly
    as fully historized variants like the materialized backend
    """
    id = BigAutoField(primary_key=True)
    tenant = ForeignKey(get_tenant_model(), on_delete=DO_NOTHING, db_index=False, db_constraint=False)
    data_series_id = UUIDField(null=False, editable=False)
    fact_id = UUIDField(null=False, editable=False)
    data_point_id = models.string_field(null=False, max_length=512)
    point_in_time = DateTimeField(null=False, auto_now=False, db_index=False)
    sub_clock = models.BigIntegerField(null=False, blank=False)
    file_name = models.TextField(null=False, db_index=False)

    all_objects: SoftDeletionManager = SoftDeletionTenantManager(alive_only=False)  # type: ignore

    class Meta:
        managed = True
        # we dont need any permissions for this type.
        default_permissions: List[str] = []
        db_table = '_3_file_lookup'

        constraints = [
            UniqueConstraint(
                fields=['tenant_id', 'data_series_id', 'fact_id', 'data_point_id', 'point_in_time', 'sub_clock'],
                name='file_lookup_unique_file_lookup'
            )
        ]
        indexes = [
            Index(fields=['file_name'], name='file_lookup_name_lookup')
        ]
