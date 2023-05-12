# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import logging
from django.contrib.auth.models import User, AnonymousUser
from django.http import HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django_multitenant.utils import get_current_tenant  # type: ignore
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from typing import Any, Optional, Union

from skipper.core.models.tenant import Tenant
from skipper.core.views.util import check_cors
from skipper import environment_common

logger = logging.getLogger(__name__)


def can_use_telemetry_ui(tenant: Tenant, user: Optional[Union[User, AnonymousUser]]) -> bool:
    if user is None:
        return False
    if user.is_anonymous:
        return False
    if user.is_superuser:
        return True
    if user.has_perm('debug.telemetry.ui'):
        return True
    return False


@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def telemetry_ui_auth(request: HttpRequest, path: Optional[str] = None) -> HttpResponse:
    """
    method to check if a user is allowed to do the request, not user facing
    nginx does all the heavy lifting
    """
    if not environment_common.SKIPPER_OTEL_JAEGER_UI_ENABLED:
        return HttpResponse(status=status.HTTP_403_FORBIDDEN)
    tenant = get_current_tenant()
    _user = request.user
    response: HttpResponse
    if 'X-Original-Uri' in request.headers and 'X-Original-Method' in request.headers:
        original_method = request.headers['X-Original-Method']
        if check_cors(request=request, original_method=original_method) \
                or can_use_telemetry_ui(
                    tenant=tenant,
                    user=_user
                ):
            response = HttpResponse(status=status.HTTP_200_OK)
            response['telemetryuiupstream'] = environment_common.SKIPPER_OTEL_JAEGER_UI_UPSTREAM
        else:
            response = HttpResponse(status=status.HTTP_403_FORBIDDEN)
    else:
        logger.error('X-Original-Uri and X-Original-Method have to be set for telemetry_ui_auth to work')
        response = HttpResponse(status=status.HTTP_403_FORBIDDEN)
    return response
