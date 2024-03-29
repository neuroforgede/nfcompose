# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

import logging
import re
from typing import Optional, Union, cast

from django.conf import settings
from django.contrib.auth.models import User, AnonymousUser
from django.http import HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django_multitenant.utils import get_current_tenant  # type: ignore
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from urllib.parse import urlparse

from skipper.core.models.guardian import get_objects_for_user_custom
from skipper.core.models.tenant import Tenant
from skipper.flow.models import HttpEndpoint
from skipper.flow.views.common import sanitize_cookies
from skipper.flow.views.flow_common import flow_base_path, path_from_uri
from skipper.settings import flow_upstream_impl
from .content_negotiation import no_content_negotiation_api_view

logger = logging.getLogger(__name__)


base_path = '/api/flow/impl/'
replace_pattern = re.compile(r'^/api/flow/impl(.*)$')


def can_use_endpoint_impl(tenant: Tenant, user: Optional[Union[User, AnonymousUser]], uri: str, method: str) -> Optional[HttpEndpoint]:
    if user is None:
        return None
    if user.is_anonymous:
        return None
    if user.has_perm('flow.use') or user.has_perm('flow.impl'):  # globally, flow.impl is equivalent to flow.use (legacy reasons)
        endpoints = get_objects_for_user_custom(
            user=user,
            perms=['flow.use'],  # locally flow.use is required
            queryset=HttpEndpoint.active_endpoints(
                tenant=tenant,
                method=method,
                public=False
            ),
            with_staff=False,
            use_groups=True,
            app_label='flow'
        )
        for endpoint in endpoints:
            if re.match(f'^{endpoint.path}$', path_from_uri(uri)):
                # if any of the urls matches, give the go ahead
                return cast(HttpEndpoint, endpoint)
    return None


@csrf_exempt
@no_content_negotiation_api_view(['GET'])  # type: ignore
@permission_classes([AllowAny])
def flow_impl_view(request: HttpRequest, path: Optional[str] = None) -> HttpResponse:
    """
    method to check if a user is allowed to do the request, not user facing
    nginx does all the heavy lifting
    """
    tenant = get_current_tenant()
    _user = request.user
    response: HttpResponse
    if 'X-Original-Uri' in request.headers and 'X-Original-Method' in request.headers:
        original_uri = request.headers['X-Original-Uri']
        original_method = request.headers['X-Original-Method']

        if original_method == 'OPTIONS':
            response = HttpResponse(status=status.HTTP_200_OK)
            # this is the most common default we usually use, so keep it
            response['flowupstream'] = getattr(settings, 'SKIPPER_CONTAINER_UPSTREAM', 'http://skipper.local:8000')
            response['flowhostname'] = urlparse(response['flowupstream']).hostname
            response['flowpath'] = '/api/flow/options/'
            return response

        _endpoint = can_use_endpoint_impl(
            tenant=tenant,
            user=_user,
            uri=original_uri,
            method=original_method
        )
        if _endpoint is not None:
            response = HttpResponse(status=status.HTTP_200_OK)
            upstream = _endpoint.get_upstream(_user, tenant)
            flow_hostname = urlparse(upstream).hostname

            response['noderedproxy'] = upstream
            response['flowsecret'] = _endpoint.get_secret(_user, request)
            response['flowuser'] = str(_user.username)
            response['flowtenant'] = tenant.name
            response['flowcookies'] = sanitize_cookies(request.COOKIES)
            # for now make the admins hard code this in the settings.py
            # we do not want to pass out our session cookies, login headers etc
            # to random urls
            response['flowupstream'] = upstream
            response['flowhostname'] = flow_hostname
            response['flowpath'] = replace_pattern.sub(f'{flow_base_path(tenant, _user, request)}\\1', original_uri)
            response['flowbasepath'] = base_path
        else:
            response = HttpResponse(status=status.HTTP_403_FORBIDDEN)
    else:
        logger.error('X-Original-Uri and X-Original-Method have to be set for node_red_impl_view to work')
        response = HttpResponse(status=status.HTTP_403_FORBIDDEN)
    return response
