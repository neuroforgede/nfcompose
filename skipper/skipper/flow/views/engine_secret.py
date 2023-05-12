# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from typing import Type, Sequence, Any

from django.db import transaction
from rest_framework import permissions, status
from rest_framework.generics import GenericAPIView
from rest_framework.renderers import JSONRenderer
from rest_framework.request import Request
from rest_framework.response import Response

from skipper.core.views.mixin import HasTenantSetPermission
from skipper.core.renderers import CustomizableBrowsableAPIRenderer, \
    CustomizableBrowsableAPIRendererObjectMixin
from skipper.flow import constants
from skipper.flow.models import Engine, get_permissions_class, \
    ENGINE_PERMISSION_KEY_SECRET, gen_engine_secret
from skipper.flow.serializers.engine import EngineSecretSerializer
from skipper.flow.views.engine_crud import EngineViewMixin


class EngineSecretView(
    CustomizableBrowsableAPIRendererObjectMixin,
    EngineViewMixin,
    GenericAPIView,  # type: ignore
):
    """
    allows to control the Engine secret value
    """
    skipper_base_name = constants.engine_secret_view_base_name + '-root'

    renderer_classes = [JSONRenderer, CustomizableBrowsableAPIRenderer]

    permission_classes = [
        HasTenantSetPermission,
        get_permissions_class('engine', ENGINE_PERMISSION_KEY_SECRET)
    ]

    engine_permission_key = ENGINE_PERMISSION_KEY_SECRET

    def get_name_string(self) -> str:
        if 'pk' in self.kwargs:
            _engine = self.get_object()
            return f'Engine {_engine.external_id}'
        else:
            return self.get_view_name()

    def get(self, request: Request, pk: str) -> Response:
        self._base_perm_check(request)
        with transaction.atomic():
            _engine: Engine = self.get_object()
            return Response({
                'secret': _engine.secret
            }, status=status.HTTP_200_OK)

    def delete(self, request: Request, pk: str) -> Response:
        self._base_perm_check(request)
        with transaction.atomic():
            _engine: Engine = self.get_object()
            _engine.secret = gen_engine_secret()
            _engine.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    def put(self, request: Request, pk: str) -> Response:
        self._base_perm_check(request)
        with transaction.atomic():
            _engine: Engine = self.get_object()
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            _engine.secret = serializer.validated_data['secret']
            _engine.save()
            return Response({
                'secret': _engine.secret
            }, status=status.HTTP_200_OK)

    def get_serializer_class(self) -> Any:
        return EngineSecretSerializer
