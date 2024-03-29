# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from django.contrib.auth.models import User
from rest_framework.permissions import DjangoObjectPermissions
from rest_framework.request import Request
from typing import Type, Optional, Callable, Any

from skipper.core.views.mixin import RestrictiveDjangoModelPermissions
from skipper.dataseries.models import DATASERIES_PERMISSION_KEY_DATA_SERIES, ds_permission_for_rest_method


class HasDataSeriesGlobalReadPermission(RestrictiveDjangoModelPermissions):
    perms_map = {
        'GET': [f'dataseries.{ds_permission_for_rest_method("GET", DATASERIES_PERMISSION_KEY_DATA_SERIES)}'],
        'OPTIONS': [f'dataseries.{ds_permission_for_rest_method("GET", DATASERIES_PERMISSION_KEY_DATA_SERIES)}'],
        'HEAD': [f'dataseries.{ds_permission_for_rest_method("GET", DATASERIES_PERMISSION_KEY_DATA_SERIES)}'],
        'POST': [f'dataseries.{ds_permission_for_rest_method("GET", DATASERIES_PERMISSION_KEY_DATA_SERIES)}'],
        'PUT': [f'dataseries.{ds_permission_for_rest_method("GET", DATASERIES_PERMISSION_KEY_DATA_SERIES)}'],
        'PATCH': [f'dataseries.{ds_permission_for_rest_method("GET", DATASERIES_PERMISSION_KEY_DATA_SERIES)}'],
        'DELETE': [f'dataseries.{ds_permission_for_rest_method("GET", DATASERIES_PERMISSION_KEY_DATA_SERIES)}'],
    }


def get_dataseries_permissions_class(action: str) -> Type[RestrictiveDjangoModelPermissions]:
    class Permission(RestrictiveDjangoModelPermissions):
        perms_map = {
            'GET': [f'dataseries.{ds_permission_for_rest_method("GET", action)}'],
            'OPTIONS': [f'dataseries.{ds_permission_for_rest_method("OPTIONS", action)}'],
            'HEAD': [f'dataseries.{ds_permission_for_rest_method("HEAD", action)}'],
            'POST': [f'dataseries.{ds_permission_for_rest_method("POST", action)}'],
            'PUT': [f'dataseries.{ds_permission_for_rest_method("PUT", action)}'],
            'PATCH': [f'dataseries.{ds_permission_for_rest_method("PATCH", action)}'],
            'DELETE': [f'dataseries.{ds_permission_for_rest_method("DELETE", action)}'],
        }
    return Permission
