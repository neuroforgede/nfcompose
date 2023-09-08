# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from django_multitenant.utils import get_current_tenant  # type: ignore
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from typing import Optional, cast

from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt

from skipper.flow.views.common import sanitize_cookies
from skipper.settings import flow_upstream_edit
from .content_negotiation import no_content_negotiation_api_view


def can_use_system_flow_edit(user: Optional[User]) -> bool:
    if user is None:
        return False
    if user.is_anonymous:
        return False
    if user.is_superuser:
        return True
    if user.is_staff and user.has_perm('flow.system.edit'):
        # only staff is allowed to use this as node red basically has access to
        # everything on the system
        return True
    return False


@csrf_exempt
@no_content_negotiation_api_view(['GET'])
@permission_classes([AllowAny])
def system_engine_access_view(request: HttpRequest, path: Optional[str] = None) -> HttpResponse:
    """
    method to check if a user is allowed to do the request, not user facing
    nginx does all the heavy lifting
    """
    tenant = get_current_tenant()
    user = request.user
    response: HttpResponse
    if user is None or user.is_anonymous:
        response = HttpResponse(status=status.HTTP_403_FORBIDDEN)
    elif can_use_system_flow_edit(cast(User, request.user)):
        response = HttpResponse(status=status.HTTP_200_OK)
        response['noderedproxy'] = flow_upstream_edit(tenant, user, request)
        response['noderedcookies'] = sanitize_cookies(request.COOKIES)
        # FIXME: configure this by engine
        response['noderedsecret'] = 'FIXME'
    else:
        response = HttpResponse(status=status.HTTP_403_FORBIDDEN)
    return response
