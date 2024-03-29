# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from typing import Optional, Union, Any

from django.contrib.auth.models import User, Permission
from django.http import HttpRequest, HttpResponse

from skipper.core.views.mixin import HasTenantSetPermission
from skipper.dataseries.storage.contract import StorageBackendType
from skipper.dataseries.storage.views import storage_backend_info


class StorageBackendDataPermission(BasePermission):

    def has_permission(self, request: HttpRequest, view: Any) -> bool:
        user = request.user
        if user is None:
            return False
        else:
            if user.is_superuser:
                return True
            if user.has_perm('dataseries.storage_backend_data'):
                return True
            return False


@api_view()
@permission_classes([permissions.IsAuthenticated, HasTenantSetPermission, StorageBackendDataPermission])
def storage_backend_data_view(request: HttpRequest, path: Optional[str] = None) -> Union[HttpResponse, Response]:
    """
    get information about all the storage engines and their underlying structures that are relevant to this tenant
    """
    response: Union[HttpResponse, Response]
    infos = {}
    for backend in StorageBackendType:
        infos[str(backend)] = storage_backend_info(backend)
    response = Response(infos, status=status.HTTP_200_OK)
    return response
