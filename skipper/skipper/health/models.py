# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Model, CharField, DateTimeField, FloatField
from django.db.models.fields.json import JSONField  # type: ignore
from django.http import HttpRequest
from enum import Enum
from guardian.admin import GuardedModelAdmin  # type: ignore
from typing import Tuple, Dict, Any, cast, Optional, List, TypedDict

from skipper import settings
from skipper.core.models import softdelete, fields
from skipper.core.raw_sql.role import user_exists
from skipper.dataseries.raw_sql import escape
from skipper.dataseries.raw_sql.permissions import grant_select_permissions, revoke_select_permissions

_subsystem_health_table = '_5_SubSystemHealth'.lower()


class HealthCheckDatabaseUser(softdelete.SoftDeletionModel):
    """
    HealthCheckDatabaseUsers are users which should have access to the PostgreSQL
    schema for healthchecks (_5_healthcheck). In there NF Compose exposes
    all healthcheck information it knows about itself via views.
    """
    # this is allowed to be non unique since only superusers are allowed to change things here
    role = CharField(max_length=63, blank=False, null=False, primary_key=True, unique=False)

    all_objects: softdelete.SoftDeletionManager = softdelete.SoftDeletionManager(alive_only=False)  # type: ignore
    objects: softdelete.SoftDeletionManager = softdelete.SoftDeletionManager()  # type: ignore

    def clean(self) -> None:
        if not user_exists(role=self.role, connection_name='default'):
            raise ValidationError(f'role "{self.role}" does not exist on database')
        super().clean()

    def save(self, force_insert: bool = False, force_update: bool = False, using: Any = None, update_fields: Any = None) -> None:
        if not user_exists(role=self.role, connection_name='default'):
            raise ValidationError(f'role "{self.role}" does not exist on database')
        if self.role in settings.SYSTEM_POSTGRES_DATABASE_ROLES:
            raise ValidationError(f'role "{self.role}" can not be managed as it is a system database role')
        with transaction.atomic():
            super().save(force_insert, force_update, using, update_fields)
            if self.deleted_at is None:
                grant_select_permissions(
                    role=self.role,
                    table=_subsystem_health_table,
                    connection_name='default',
                    schema_escaped=escape.escape('_5_healthcheck')
                )
            else:
                revoke_select_permissions(
                    role=self.role,
                    table=_subsystem_health_table,
                    connection_name='default',
                    schema_escaped=escape.escape('_5_healthcheck')
                )

    class Meta:
        db_table = '_5_HealthCheckDatabaseUser'.lower()

    def __str__(self) -> str:
        return f'_5_HealthCheckDatabaseUser "{self.role}"'


# only superusers are allowed to change things as this
# is a critical path!
class HealthCheckDatabaseUserAdmin(GuardedModelAdmin):  # type: ignore
    prepopulated_fields: Dict[str, Any] = {}
    list_display = ('role', 'deleted_at')
    search_fields = ('role',)
    list_filter = ('deleted_at',)
    ordering = ('role',)

    def has_view_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return request.user.is_superuser

    def has_change_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return request.user.is_superuser

    def has_delete_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return request.user.is_superuser

    def has_add_permission(self, request: HttpRequest) -> bool:
        return request.user.is_superuser


admin.site.register(HealthCheckDatabaseUser, HealthCheckDatabaseUserAdmin)


class SubSystemHealthStatus(Enum):
    # default should always be the first, so DRF displays it by default in the UI
    UNKNOWN = 'UNKNOWN'
    UNHEALTHY = 'UNHEALTHY'
    HEALTHY = 'HEALTHY'

    @classmethod
    def choices(cls) -> Tuple[Tuple[str, str], ...]:
        return tuple((i.name, i.value) for i in cls)


class SubSystemHealth(Model):
    key = CharField(max_length=100, primary_key=True)
    last_check = DateTimeField(null=True)
    health = CharField(
        max_length=100,
        null=False,
        default=SubSystemHealthStatus.UNKNOWN.value,
        choices=SubSystemHealthStatus.choices(),
        db_index=False
    )
    last_errors = JSONField(null=True)
    time_taken = FloatField(null=True)

    class Meta:
        db_table = _subsystem_health_table