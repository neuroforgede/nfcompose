# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from rest_framework import viewsets, permissions
from rest_framework.mixins import RetrieveModelMixin, ListModelMixin, DestroyModelMixin
from rest_framework.renderers import JSONRenderer
from typing import Type, Sequence, Any

from skipper.core.views import mixin
from skipper.core.renderers import CustomizableBrowsableAPIRenderer, \
    CustomizableBrowsableAPIRendererObjectMixin
from skipper.health import constants
from skipper.health.models import SubSystemHealth
from skipper.health.serializers import SubSystemHealthSerializer


class HealthRestrictiveDjangoModelPermissions(mixin.RestrictiveDjangoModelPermissions):
    perms_map = {
        'GET': ['auth.view_%(model_name)s'],
        'OPTIONS': ['auth.view_%(model_name)s'],
        'HEAD': ['auth.view_%(model_name)s'],
        'POST': ['auth.add_%(model_name)s'],
        'PUT': ['auth.change_%(model_name)s'],
        'PATCH': ['auth.change_%(model_name)s'],
        'DELETE': ['auth.delete_%(model_name)s'],
    }


class HealthViewMixin:
    permission_classes: Any = (HealthRestrictiveDjangoModelPermissions,)


class SubSystemHealthViewSet(
    CustomizableBrowsableAPIRendererObjectMixin,
    HealthViewMixin,
    RetrieveModelMixin,
    ListModelMixin,
    DestroyModelMixin,
    viewsets.GenericViewSet,  # type: ignore
):
    skipper_base_name = constants.health_view_base_name

    lookup_value_regex = '[^/]+'

    renderer_classes = [JSONRenderer, CustomizableBrowsableAPIRenderer]

    queryset = SubSystemHealth.objects.all().order_by('key')

    ordering = ('key',)

    action: str

    def get_name_string(self) -> str:
        if 'pk' in self.kwargs:
            _subsystem = self.get_object()
            return f'Health for subsystem {_subsystem.key}'
        else:
            return self.get_view_name()

    def get_serializer_class(self) -> Any:
        return SubSystemHealthSerializer
