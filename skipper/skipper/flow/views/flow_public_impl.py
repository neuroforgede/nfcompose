# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

import logging
import re
from typing import Optional, List

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from urllib.parse import urlparse

from skipper.core.models.tenant import Tenant
from skipper.flow.models import HttpEndpoint
from skipper.flow.views.flow_common import flow_base_path, outside_base_path, path_from_uri
from skipper.settings import flow_upstream_impl
from .content_negotiation import no_content_negotiation_api_view

logger = logging.getLogger(__name__)


replace_pattern_public = re.compile(r'^/api/flow/public/impl/([0-9A-Za-z_\-]+)/(.*)$')
base_path_public = '/api/flow/public/impl/'


def can_use_endpoint_public_impl(tenant: Tenant, uri: str, method: str) -> Optional[HttpEndpoint]:
    endpoints = HttpEndpoint.active_endpoints(
        tenant=tenant,
        method=method,
        public=True
    ).all()
    for endpoint in endpoints:
        if re.match(f'^{endpoint.path}$', path_from_uri(uri)):
            # if any of the urls matches, give the go ahead
            return endpoint
    return None


@csrf_exempt
@no_content_negotiation_api_view(['GET'])  # type: ignore
@permission_classes([AllowAny])
def flow_impl_public_view(request: HttpRequest, path: Optional[str] = None) -> HttpResponse:
    """
    method to check if a user is allowed to do the request, not user facing
    nginx does all the heavy lifting
    """
    response: HttpResponse

    if 'X-Original-Uri' in request.headers and 'X-Original-Method' in request.headers:
        original_uri = request.headers['X-Original-Uri']
        original_method = request.headers['X-Original-Method']

        if original_method == 'OPTIONS':
            response = HttpResponse(status=status.HTTP_200_OK)
            upstream = getattr(settings, 'SKIPPER_CONTAINER_UPSTREAM', 'http://skipper')
            response['flowupstream'] = upstream
            response['flowhostname'] = urlparse(upstream).hostname
            response['flowpath'] = '/api/flow/options/'
            return response

        match = replace_pattern_public.match(original_uri)

        tenants: List[Tenant]
        if match:
            tenant_str = match.group(1)

            tenants = list(Tenant.objects.filter(
                name=tenant_str
            ).all())
        else:
            tenants = []

        if len(tenants) == 1:
            tenant = tenants[0]
            uri_without_tenant = replace_pattern_public.sub(
                f'{outside_base_path}/\\2',
                original_uri
            )

            _engine = can_use_endpoint_public_impl(
                tenant=tenant,
                uri=uri_without_tenant,
                method=original_method
            )
            if _engine is not None:
                response = HttpResponse(status=status.HTTP_200_OK)
                upstream = _engine.get_upstream(None, request)

                response['noderedproxy'] = upstream
                response['flowsecret'] = _engine.get_secret(None, request)
                response['flowuser'] = ''
                response['flowtenant'] = tenant.name
                # drop cookies for public flows by design
                # to prevent clickjacking via public flows
                response['flowcookies'] = ''
                # for now make the admins hard code this in the settings.py
                # we do not want to pass out our session cookies, login headers etc
                # to random urls
                response['flowupstream'] = upstream
                response['flowhostname'] = urlparse(upstream).hostname
                response['flowpath'] = replace_pattern_public.sub(
                    f'{flow_base_path(tenant, None, request)}/\\2',
                    original_uri
                )
                response['flowbasepath'] = f'{base_path_public}{tenant.name}/'
            else:
                response = HttpResponse(status=status.HTTP_403_FORBIDDEN)
        else:
            response = HttpResponse(status=status.HTTP_403_FORBIDDEN)
    else:
        logger.error('X-Original-Uri and X-Original-Method have to be set for node_red_impl_view to work')
        response = HttpResponse(status=status.HTTP_403_FORBIDDEN)
    return response
