# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from django.contrib import admin
from django.contrib.auth.models import Group, User, AnonymousUser
from django.core.exceptions import ValidationError
from django.db.models import ForeignKey, CASCADE, DO_NOTHING, OneToOneField, BooleanField, Model, Q
from django.db.models.constraints import UniqueConstraint
from django.http import HttpRequest
from django_multitenant.fields import TenantForeignKey  # type: ignore
from guardian.admin import GuardedModelAdmin  # type: ignore
from typing import Any, Dict, List, Optional, Sequence, Type, Union, cast

from skipper.core.models import softdelete, fields
from skipper.core.models.softdelete import SoftDeletionTenantModel, SoftDeletionQuerySet
from skipper.core.raw_sql.validate import validate_string
from skipper.core.models.permissions import gen_permissions

TENANT_PERMISSION_KEY_TENANT = 'tenant'
TENANT_PERMISSION_KEY_TENANT_USER = 'tenant-user'

ALL_ASSEMBLED_TENANT_PERMISSIONS = [
    *gen_permissions(entity='tenant', action=TENANT_PERMISSION_KEY_TENANT)
]
ALL_ASSEMBLED_TENANT_USER_PERMISSIONS = [
    *gen_permissions(entity='tenant', action=TENANT_PERMISSION_KEY_TENANT_USER)
]


class Tenant(softdelete.SoftDeletionModel):  # type: ignore
    id = fields.id_field()
    name = fields.string_field(max_length=32)

    objects: 'softdelete.SoftDeletionManager[Tenant]'
    all_objects: 'softdelete.SoftDeletionManager[Tenant]'

    @property
    def tenant_field(self) -> str:
        return 'id'

    @property
    def tenant_value(self) -> Any:
        return self.id

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not validate_string(self.name):
            raise ValidationError("Tenant name may only contain letters, numbers and '_'")
        if self.deleted_at == '':
            self.deleted_at = None
        super().save(*args, **kwargs)

    class Meta:
        db_table = '_core_Tenant'.lower()
        constraints = [
            UniqueConstraint(fields=['name'], name='core_Tenant_0'.lower())
        ]
        permissions = [
            *ALL_ASSEMBLED_TENANT_PERMISSIONS
        ]

    def __str__(self) -> str:
        return f'Tenant "{self.name}" ({str(self.id)})'


class Tenant_User(softdelete.SoftDeletionModel):
    id = fields.id_field()
    tenant = ForeignKey(Tenant, on_delete=DO_NOTHING)
    user = OneToOneField(User, on_delete=CASCADE)
    system = BooleanField(default=False)
    tenant_manager = BooleanField(default=False, null=False)

    objects: 'softdelete.SoftDeletionManager[Tenant_User]'
    all_objects: 'softdelete.SoftDeletionManager[Tenant_User]'

    class Meta:
        db_table = '_core_Tenant_User'.lower()
        permissions = [
            *ALL_ASSEMBLED_TENANT_USER_PERMISSIONS
        ]


def is_tenant_manager(user: Union[User, AnonymousUser], tenant: Tenant) -> bool:
    '''Return True if the user is in a tenant_user relation with the tenant where it is marked as tenant manager.'''
    
    if tenant is None or user is None:    
        raise TypeError('Both user and tenant must be specified, no wildcard lookups allowed')
    if isinstance(user, AnonymousUser):
        return False

    tenant_user_query = Tenant_User.objects.filter(
        user=user,
        tenant=tenant
    ).all()
    if len(tenant_user_query) > 1:
        raise AssertionError('user is registered to tenant multiple times, which is not allowed')
        
    if len(tenant_user_query) == 1:
        if tenant_user_query[0].tenant_manager is True:
            return True
    
    return False


class Tenant_Group(softdelete.SoftDeletionModel):
    id = fields.id_field()
    tenant = ForeignKey(Tenant, on_delete=DO_NOTHING)
    group = OneToOneField(Group, on_delete=CASCADE)
    system = BooleanField(default=False)

    class Meta:
        db_table = '_core_Tenant_Group'.lower()


class AllowedLoginRedirectHost(SoftDeletionTenantModel):
    id = fields.id_field()
    tenant = TenantForeignKey(Tenant, on_delete=DO_NOTHING)
    host = fields.string_field(max_length=256)

    objects: 'softdelete.SoftDeletionManager[AllowedLoginRedirectHost]'  # type: ignore

    class Meta:
        db_table = '_core_AllowedLoginRedirectHost'.lower()


class TenantAdmin(GuardedModelAdmin):  # type: ignore
    prepopulated_fields: Dict[str, Any] = {}
    list_display: Sequence[str] = ('id', 'name', 'deleted_at')
    list_filter: Sequence[str] = ('name', 'deleted_at')
    search_fields: Sequence[str] = ('id', 'name')
    ordering: List[str] = []
    date_hierarchy: Optional[List[str]] = None
    actions = ['hard_delete']

    def hard_delete(self, request: HttpRequest, queryset: SoftDeletionQuerySet[Any]) -> None:
        queryset.hard_delete()

    def has_hard_delete_permission(self, request: HttpRequest) -> bool:
        return request.user.is_superuser

    def has_view_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return request.user.is_superuser

    def has_change_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return request.user.is_superuser

    def has_delete_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return request.user.is_superuser

    def has_add_permission(self, request: HttpRequest) -> bool:
        return request.user.is_superuser


admin.site.register(Tenant, TenantAdmin)


class Tenant_UserAdmin(GuardedModelAdmin):  # type: ignore
    prepopulated_fields: Dict[str, Any] = {}
    list_display: Sequence[str] = ('id', 'tenant', 'user', 'system', 'tenant_manager', 'deleted_at')
    list_filter: Sequence[str] = ('tenant', 'system', 'deleted_at', 'tenant_manager')
    search_fields: Sequence[str] = ('user__username', 'tenant__name')
    ordering: List[str] = []
    date_hierarchy: Optional[List[str]] = None
    actions = ['hard_delete']

    def hard_delete(self, request: HttpRequest, queryset: SoftDeletionQuerySet[Any]) -> None:
        queryset.hard_delete()

    def has_hard_delete_permission(self, request: HttpRequest) -> bool:
        return request.user.is_superuser

    def has_view_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return request.user.is_superuser

    def has_change_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return request.user.is_superuser

    def has_delete_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return request.user.is_superuser

    def has_add_permission(self, request: HttpRequest) -> bool:
        return request.user.is_superuser

    # since only super users are allowed to change this, it is fine to not filter here


admin.site.register(Tenant_User, Tenant_UserAdmin)


class Tenant_GroupAdmin(GuardedModelAdmin):  # type: ignore
    prepopulated_fields: Dict[str, Any] = {}
    list_display: Sequence[str] = ('id', 'tenant', 'group', 'system', 'deleted_at')
    list_filter = ('id', 'tenant', 'group', 'system', 'deleted_at')
    search_fields: Sequence[str] = ('group__name', 'tenant__name')
    ordering: List[str] = []
    date_hierarchy: Optional[List[str]] = None

    def hard_delete(self, request: HttpRequest, queryset: SoftDeletionQuerySet[Any]) -> None:
        queryset.hard_delete()

    def has_hard_delete_permission(self, request: HttpRequest) -> bool:
        return request.user.is_superuser

    def has_view_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return request.user.is_superuser

    def has_change_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return request.user.is_superuser

    def has_delete_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return request.user.is_superuser

    def has_add_permission(self, request: HttpRequest) -> bool:
        return request.user.is_superuser

    # since only super users are allowed to change this, it is fine to not filter here


admin.site.register(Tenant_Group, Tenant_GroupAdmin)


def get_tenant_model() -> Type[Tenant]:
    return Tenant


class SoftDeleteTenantValidateExternalIdMixin(object):
    id: Any
    tenant: Any
    external_id: Any
    objects: Any
    deleted_at: Any

    def validate_unique(
            self,
            exclude: Any = None
    ) -> None:
        """
        custom method to validate uniqueness so that django admin works properly
        """
        super().validate_unique(exclude=exclude)  # type: ignore
        if self.deleted_at is None:
            others_with_same_external_id = self.__class__.objects.filter(~Q(id=self.id)) \
                .filter(tenant=self.tenant.id, external_id=self.external_id).count()
            if others_with_same_external_id > 0:
                raise ValidationError('external_id must be unique for each tenant')
