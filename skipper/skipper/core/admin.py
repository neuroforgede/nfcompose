# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


from django import forms
from django.contrib import admin
from django.contrib.admin.filters import SimpleListFilter
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.db.models import Model, QuerySet
from django.http import HttpRequest
from django.utils import timezone
from django_multitenant.utils import get_tenant_column, get_current_tenant  # type: ignore
from guardian.admin import GuardedModelAdmin  # type: ignore
from rest_framework.authtoken.admin import TokenAdmin
from rest_framework.authtoken.models import TokenProxy  # type: ignore
from typing import Any, Optional, List, Iterable, Dict, Sequence, cast, Tuple

from django_celery_results.admin import TaskResultAdmin, GroupResultAdmin  # type: ignore
from django_celery_results.models import TaskResult, GroupResult  # type: ignore

from skipper.core.models.postgres_jobs import TenantPostgresQueueJob
from skipper.core.models.preshared_token import PreSharedToken
from skipper.core.models.softdelete import SoftDeletionQuerySet
from skipper.core.models.tenant import Tenant_User, Tenant, AllowedLoginRedirectHost


class TenantAwareAdminForm(forms.ModelForm):  # type: ignore
    request: HttpRequest

    def validate_impl(self, instance: Any) -> None:
        pass

    def clean(self) -> Any:
        super().clean()

        user = self.request.user

        if user.is_anonymous:
            raise AssertionError()

        if not user.is_superuser:
            tenant_users = list(Tenant_User.objects.filter(
                user=user
            ))
            if len(tenant_users) == 0:
                raise ValidationError('can not modify Objects without having a tenant set if the user is not super user')

            tenant_ids = [tenant_user.tenant.id for tenant_user in tenant_users]

            _instance: Any = self.instance
            if _instance.tenant_id not in tenant_ids:
                raise ValidationError('can only add objects to a Tenant if user is ' +
                                      'either superuser or has the Tenant set')

        self.validate_impl(self.instance)

        return self.cleaned_data


class TenantFilter(SimpleListFilter):
    title = 'Tenant'
    parameter_name = 'tenant'

    def lookups(self, request: HttpRequest, model_admin: Any) -> Any:
        tenant = get_current_tenant()
        tenants: Iterable[Tenant]
        # super users are still filtered here
        # because we only allow super users that are
        # part of tenants to see everything
        # that does not have a tenant_id, i.e. needs to be global
        if tenant is None:
            tenants = Tenant.objects.all()
        else:
            tenants = [tenant]
        return ((tenant.id, tenant) for tenant in tenants)

    def queryset(self, request: HttpRequest, queryset: 'QuerySet[Any]') -> 'QuerySet[Any]':
        selected = self.value()

        # WAS return queryset.filter(room=selected)
        # this does not handle All case correctly

        if selected:
            return queryset.filter(tenant=selected)
        else:
            return queryset


class _UserFilter(SimpleListFilter):
    title = 'User'
    parameter_name = 'user'

    def lookups(self, request: HttpRequest, model_admin: Any) -> Any:
        tenant = get_current_tenant()
        users: Iterable[User]
        is_superuser = request is not None and request.user.is_superuser
        if tenant is None or is_superuser:
            users = User.objects.all()
        else:
            users = User.objects.filter(
                tenant_user__tenant=tenant,
                tenant_user__deleted_at__isnull=True
            ).order_by('id')
        return ((user.id, user) for user in users)

    def queryset(self, request: HttpRequest, queryset: 'QuerySet[Any]') -> 'QuerySet[Any]':
        selected = self.value()

        # WAS return queryset.filter(room=selected)
        # this does not handle All case correctly

        if selected:
            return queryset.filter(user=selected)
        else:
            return queryset


class TenantAwareAdmin(GuardedModelAdmin):  # type: ignore
    form = TenantAwareAdminForm

    def get_form(self, request: HttpRequest, obj: Optional[Model] = None, **kwargs: Any) -> Any:
        form = super().get_form(request, obj=obj, **kwargs)
        form.request = request
        return form

    def get_list_filter(self, request: HttpRequest) -> Iterable[Any]:
        filters = super().get_list_filter(request)
        new_filters: List[Any] = []
        for _filter in filters:
            if _filter == "tenant":
                new_filters.append(TenantFilter)
            elif _filter == "user":
                new_filters.append(_UserFilter)
            else:
                new_filters.append(_filter)
        return new_filters

    def formfield_for_foreignkey(self, db_field: Any, request: HttpRequest, **kwargs: Any) -> Any:
        if db_field.name == "tenant":
            tenant = get_current_tenant()
            if tenant is not None:
                kwargs["queryset"] = Tenant.objects.filter(
                    id=tenant.id
                )

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request: HttpRequest) -> 'QuerySet[Any]':
        qs: QuerySet[Any] = super().get_queryset(request)

        tenant = get_current_tenant()
        if tenant is not None:
            tenant_mapping: Tenant_User
            filters = {'%s__in' % get_tenant_column(self.model): [tenant.id]}
            qs = qs.filter(**filters)
        return qs


class TenantAwareSoftDeleteAdmin(TenantAwareAdmin):  # type: ignore
    actions = ['hard_delete']

    def hard_delete(self, request: HttpRequest, queryset: SoftDeletionQuerySet[Any]) -> None:
        queryset.hard_delete()

    def has_hard_delete_permission(self, request: HttpRequest) -> bool:
        return request.user.is_superuser


class AllowedLoginRedirectHostAdmin(TenantAwareSoftDeleteAdmin):
    prepopulated_fields: Dict[str, Any] = {}
    list_display: Sequence[str] = ('id', 'tenant', 'host', 'deleted_at')
    list_filter: Sequence[str] = ('id', 'tenant', 'host', 'deleted_at')
    search_fields: Sequence[str] = ('tenant__name', 'host')
    ordering: List[str] = []
    date_hierarchy: Optional[List[str]] = None


admin.site.register(AllowedLoginRedirectHost, AllowedLoginRedirectHostAdmin)


# only superusers are allowed to change things here as it is a critical path
class PreSharedTokenAdmin(GuardedModelAdmin):  # type: ignore
    """
    Token login with Admin controllable interface.
    These tokens should only be used for integration purposes as
    they have to be global. These should also not be changeable
    by the user because as soon as a user enters a token that
    is already in use, any error response from the system will
    tell an attacker that the password is already in use
    so they can just take the password and impersonate that user.
    """
    prepopulated_fields: Dict[str, Any] = {}
    list_display: Sequence[str] = ('user', 'key', 'deleted_at')
    list_filter = (_UserFilter, 'key', 'deleted_at')
    search_fields: Sequence[str] = ('user__username', )
    ordering: List[str] = ['user__username']
    date_hierarchy: Optional[List[str]] = None
    actions = ['hard_delete']

    def hard_delete(self, request: HttpRequest, queryset: SoftDeletionQuerySet[Any]) -> None:
        queryset.hard_delete()

    def has_hard_delete_permission(self, request: HttpRequest) -> bool:
        return request.user.is_superuser

    def formfield_for_foreignkey(self, db_field: Any, request: HttpRequest, **kwargs: Any) -> Any:
        if db_field.name == "user":
            tenant = get_current_tenant()
            is_superuser = request is not None and request.user.is_superuser
            if tenant is None or is_superuser:
                kwargs["queryset"] = User.objects.all()
            else:
                kwargs["queryset"] = User.objects.filter(
                    tenant_user__tenant=tenant,
                    tenant_user__deleted_at__isnull=True
                ).order_by('id')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request: HttpRequest) -> 'QuerySet[Any]':
        qs = super().get_queryset(request)

        tenant = get_current_tenant()
        is_superuser = request is not None and request.user.is_superuser
        if tenant is None or is_superuser:
            pass
        else:
            qs = qs.filter(
                user__tenant_user__tenant=tenant,
                user__tenant_user__deleted_at__isnull=True
            )

        return cast('QuerySet[Any]', qs)

    def has_view_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return get_current_tenant() is not None or request.user.is_superuser

    def has_change_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return request.user.is_superuser

    def has_delete_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return request.user.is_superuser

    def has_add_permission(self, request: HttpRequest) -> bool:
        return request.user.is_superuser


admin.site.register(PreSharedToken, PreSharedTokenAdmin)


class TenantJobAdminForm(TenantAwareAdminForm):
    class Meta:
        exclude = ['id']
        model = TenantPostgresQueueJob

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        _now = timezone.now()
        self.initial['execute_at'] = _now  # type: ignore
        self.initial['created_at'] = _now  # type: ignore


class TenantJobAdmin(TenantAwareAdmin):
    form = TenantJobAdminForm
    prepopulated_fields: Dict[str, Any] = {}
    list_display: Sequence[str] = ('id', 'queue', 'globally_unique_identifier', 'task', 'priority', 'created_at', 'execute_at')
    list_filter: Sequence[str] = ('tenant', 'queue', )
    search_fields: Sequence[str] = ('globally_unique_identifier', 'task')
    ordering: List[str] = []
    date_hierarchy: Optional[List[str]] = None

    def has_change_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return request.user.is_superuser

    def has_delete_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return request.user.is_superuser

    def has_add_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return request.user.is_superuser


admin.site.register(TenantPostgresQueueJob, TenantJobAdmin)


# customizations of Auth admin things

class TenantAwareUserAdmin(UserAdmin):
    actions = ['hard_delete']

    def get_queryset(self, request: HttpRequest) -> 'QuerySet[Any]':
        qs = super().get_queryset(request)

        tenant = get_current_tenant()
        is_superuser = request is not None and request.user.is_superuser
        if tenant is None or is_superuser:
            pass
        else:
            qs = qs.filter(
                tenant_user__tenant=tenant,
                tenant_user__deleted_at__isnull=True
            )

        return qs

    def hard_delete(self, request: HttpRequest, queryset: SoftDeletionQuerySet[Any]) -> None:
        queryset.delete()

    def has_hard_delete_permission(self, request: HttpRequest) -> bool:
        return request.user.is_superuser

    def has_view_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return get_current_tenant() is not None or request.user.is_superuser

    def has_change_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return request.user.is_superuser

    def has_delete_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return request.user.is_superuser

    def has_add_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return request.user.is_superuser


admin.site.unregister(User)
admin.site.register(User, TenantAwareUserAdmin)


class TenantAwareGroupAdmin(GroupAdmin):
    actions = ['hard_delete']

    def get_queryset(self, request: HttpRequest) -> 'QuerySet[Any]':
        qs = super().get_queryset(request)

        tenant = get_current_tenant()
        is_superuser = request is not None and request.user.is_superuser
        if tenant is None or is_superuser:
            pass
        else:
            qs = qs.filter(
                tenant_group__tenant=tenant,
                tenant_group__deleted_at__isnull=True
            )

        return qs

    def hard_delete(self, request: HttpRequest, queryset: SoftDeletionQuerySet[Any]) -> None:
        queryset.delete()

    def has_hard_delete_permission(self, request: HttpRequest) -> bool:
        return request.user.is_superuser

    def has_view_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return get_current_tenant() is not None or request.user.is_superuser

    def has_change_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return request.user.is_superuser

    def has_delete_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return request.user.is_superuser

    def has_add_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return request.user.is_superuser


admin.site.unregister(Group)
admin.site.register(Group, TenantAwareGroupAdmin)


class TenantAwareTokenAdmin(TokenAdmin):

    def get_list_filter(self, request: HttpRequest) -> Any:
        filters = super().get_list_filter(request)
        new_filters: List[Any] = []
        for _filter in filters:
            if _filter == "user":
                new_filters.append(_UserFilter)
            else:
                new_filters.append(_filter)
        return new_filters

    def formfield_for_foreignkey(self, db_field: Any, request: Optional[HttpRequest], **kwargs: Any) -> Any:
        if db_field.name == "user":
            tenant = get_current_tenant()
            is_superuser = request is not None and request.user.is_superuser
            if tenant is None or is_superuser:
                kwargs["queryset"] = User.objects.all()
            else:
                kwargs["queryset"] = User.objects.filter(
                    tenant_user__tenant=tenant,
                    tenant_user__deleted_at__isnull=True
                ).order_by('id')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request: HttpRequest) -> 'QuerySet[Any]':
        qs = super().get_queryset(request)

        tenant = get_current_tenant()
        is_superuser = request is not None and request.user.is_superuser
        if tenant is None or is_superuser:
            pass
        else:
            qs = qs.filter(
                user__tenant_user__tenant=tenant,
                user__tenant_user__deleted_at__isnull=True
            )

        return qs


admin.site.unregister(TokenProxy)
admin.site.register(TokenProxy, TenantAwareTokenAdmin)


class HardenedTaskResultAdmin(TaskResultAdmin):  # type: ignore

    def has_view_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return request.user.is_superuser

    def has_change_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return request.user.is_superuser

    def has_add_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return False


admin.site.unregister(TaskResult)
admin.site.register(TaskResult, HardenedTaskResultAdmin)


class HardenedGroupResultAdmin(GroupResultAdmin):  # type: ignore

    def has_view_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return request.user.is_superuser

    def has_change_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return request.user.is_superuser

    def has_add_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return False


admin.site.unregister(GroupResult)
admin.site.register(GroupResult, HardenedGroupResultAdmin)