# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import re
from typing import Type, Sequence, Any

from django.http import Http404
from rest_framework import permissions, status
from rest_framework.generics import GenericAPIView
from rest_framework.renderers import JSONRenderer
from rest_framework.request import Request
from rest_framework.response import Response
from urllib.parse import urlparse

from skipper.core.views.mixin import HasTenantSetPermission
from skipper.core.renderers import CustomizableBrowsableAPIRenderer, \
    CustomizableBrowsableAPIRendererObjectMixin
from skipper.flow import constants
from skipper.flow.models import Engine, get_permissions_class, \
    ENGINE_PERMISSION_KEY_ACCESS
from skipper.flow.serializers.engine import EngineSerializer
from skipper.flow.views.common import sanitize_cookies
from skipper.flow.views.engine_crud import EngineViewMixin


class BaseEngineAccessView(
    CustomizableBrowsableAPIRendererObjectMixin,
    EngineViewMixin,
    GenericAPIView,  # type: ignore
):
    """
    allows to control the Engine secret value
    """
    skipper_base_name = constants.engine_access_view_base_name + '-root'

    renderer_classes = [JSONRenderer, CustomizableBrowsableAPIRenderer]

    permission_classes = [
        HasTenantSetPermission,
        get_permissions_class('engine', ENGINE_PERMISSION_KEY_ACCESS)
    ]

    engine_permission_key = ENGINE_PERMISSION_KEY_ACCESS

    def get_name_string(self) -> str:
        if 'pk' in self.kwargs:
            _engine = self.get_object()
            return f'Engine {_engine.external_id}'
        else:
            return self.get_view_name()

    def _access(self, request: Request, pk: str) -> Response:
        self._base_perm_check(request)
        try:
            _engine: Engine = self.get_object()
        except Http404:
            # if an engine matching the current user was not found, return a 403 so that
            # nginx knows to forbid the access
            return Response(status=status.HTTP_403_FORBIDDEN)
        else:
            upstream = _engine.upstream
            engine_hostname = urlparse(upstream).hostname

            response = Response({'upstream': upstream}, status=status.HTTP_200_OK)
            response['enginetenant'] = _engine.tenant.name
            response['engineupstream'] = upstream
            response['enginesecret'] = _engine.secret
            response['enginehostname'] = engine_hostname
            response['enginecookies'] = sanitize_cookies(request.COOKIES)
            response['enginebasepath'] = f'/api/flow/engine/{str(_engine.id)}/access/'
            return response

    def get_serializer_class(self) -> Any:
        return EngineSerializer


class EngineAccessView(BaseEngineAccessView):
    def get(self, request: Request, pk: str) -> Response:
        return self._access(request, pk)


class NginXEngineAccessView(BaseEngineAccessView):
    def get(self, request: Request) -> Response:
        if 'X-Original-Uri' not in request.headers:
            return Response(status=status.HTTP_403_FORBIDDEN)
        original_uri_match = re.match(r'^/api/flow/engine/(?P<engine>[^/.]+)/access.*$', request.headers['X-Original-Uri'])
        if original_uri_match is None:
            return Response(status=status.HTTP_403_FORBIDDEN)
        engine_id = original_uri_match.group(1)
        # hack, but meh
        self.kwargs['pk'] = engine_id
        return self._access(request, engine_id)
