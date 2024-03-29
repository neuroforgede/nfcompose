# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


from typing import Sequence, Type, Dict, Any

from django_multitenant.utils import get_current_tenant  # type: ignore
from rest_framework import mixins
from rest_framework import permissions
from rest_framework import response
from rest_framework.permissions import BasePermission
from rest_framework.request import Request

from skipper import settings
from skipper.core.exceptions import http as http_exceptions


class AllowedToBrowseAPI(BasePermission):
    def has_permission(self, request: Request, view: Any) -> bool:
        return bool(request.user and (request.user.is_superuser or request.user.is_staff or request.user.has_perm('core.browse_api')))


class AllowedToBrowseAPIViewMixin:  # type: ignore
    permission_classes: Any = (permissions.IsAuthenticated, AllowedToBrowseAPI,)


class AuthenticatedViewMixin:  # type: ignore
    permission_classes: Any = (permissions.IsAuthenticated,)


class RestrictiveDjangoModelPermissions(permissions.DjangoModelPermissions):
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': ['%(app_label)s.view_%(model_name)s'],
        'HEAD': ['%(app_label)s.view_%(model_name)s'],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }


class HasTenantSetPermission(BasePermission):
    """
    Checks if the current user has a tenant set, if not, blocks the request
    """

    def has_permission(self, request: Request, view: Any) -> bool:
        tenant = get_current_tenant()
        if tenant is None:
            return False
        return True

    def has_object_permission(self, request: Request, view: Any, obj: Any) -> bool:
        tenant = get_current_tenant()
        if tenant is None:
            return False
        return True


class TenantViewMixin:
    permission_classes  = (
        RestrictiveDjangoModelPermissions, HasTenantSetPermission)


class SuccessHeadersMixin:
    def get_success_headers(self, data: Dict[str, str]) -> Dict[str, str]:
        try:
            return {'Location': str(data[settings.URL_FIELD_NAME])}
        except (TypeError, KeyError):
            return {}


class HttpErrorAwareCreateModelMixin(mixins.CreateModelMixin):
    def create(self, request: Request, *args: Any, **kwargs: Any) -> response.Response:
        try:
            return super().create(request, kwargs)
        except http_exceptions.HttpError as error:
            return response.Response(status=error.status, data=error.message)


class HttpErrorAwareUpdateModelMixin(mixins.UpdateModelMixin):
    def update(self, request: Request, *args: Any, **kwargs: Any) -> response.Response:
        try:
            return super().update(request, *args, **kwargs)
        except http_exceptions.HttpError as error:
            return response.Response(status=error.status, data=error.message)
