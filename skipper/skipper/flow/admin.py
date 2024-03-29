# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


from typing import Dict, Any, cast, Optional

from django.db.models import Model
from django.http import HttpRequest

from skipper.core.admin import TenantAwareSoftDeleteAdmin


class HttpEndpointAdmin(TenantAwareSoftDeleteAdmin):  # type: ignore
    prepopulated_fields: Dict[str, Any] = {}
    list_display = ('id', 'tenant', 'external_id', 'system', 'engine', 'path', 'method', 'public', 'deleted_at')
    search_fields = ('external_id', 'path',)
    list_filter = ('tenant', 'engine', 'system', 'path', 'deleted_at', 'public')
    readonly_fields = ['id']
    ordering = ('tenant__name', 'id')

    def has_view_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return request.user.is_superuser

    def has_change_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return request.user.is_superuser

    def has_delete_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return request.user.is_superuser

    def has_add_permission(self, request: HttpRequest) -> bool:
        return request.user.is_superuser


class EngineAdmin(TenantAwareSoftDeleteAdmin):  # type: ignore
    prepopulated_fields: Dict[str, Any] = {}
    list_display = ('id', 'tenant', 'external_id', 'upstream', 'deleted_at')
    search_fields = ('external_id', 'upstream',)
    list_filter = ('tenant', 'upstream', 'deleted_at')
    readonly_fields = ['id']
    ordering = ('tenant__name', 'id')

    def has_view_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return request.user.is_superuser

    def has_change_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return request.user.is_superuser

    def has_delete_permission(self, request: HttpRequest, obj: Optional[Model] = None) -> bool:
        return request.user.is_superuser

    def has_add_permission(self, request: HttpRequest) -> bool:
        return request.user.is_superuser

