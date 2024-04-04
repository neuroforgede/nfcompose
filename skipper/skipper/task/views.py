# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

import logging
from django.contrib.auth.models import User, AnonymousUser
from django.http import HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django_multitenant.utils import get_current_tenant  # type: ignore
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from rest_framework.permissions import BasePermission, AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.utils.urls import replace_query_param  # type: ignore
from typing import Any, Optional, Union
from django.urls import reverse


from skipper.task import constants
from skipper import environment_common
from skipper import settings
from skipper.core.models.tenant import Tenant
from skipper.core.renderers import CustomizableBrowsableAPIRenderer
from skipper.core.views.util import check_cors
from skipper.settings import task_upstream_dashboard
from skipper.task.models import get_task_data, get_task_data_count
from skipper.task.serializers import TaskDataSerializer

logger = logging.getLogger(__name__)


class IsSuperUser(BasePermission):
    """
    Allows access only to Superusers.
    """

    def has_permission(self, request: Request, view: Any) -> bool:
        return bool(request.user and request.user.is_superuser)


@api_view(['GET'])
@permission_classes([IsSuperUser])
@renderer_classes([JSONRenderer, CustomizableBrowsableAPIRenderer])
def task_queue_overview(request: Request) -> Response:
    def _url(queue_name: str) -> str:
        return request.build_absolute_uri(
            reverse(constants.task_queue_view_base_name + '-list', kwargs={
                'queue_name': queue_name
            })
        )

    return Response({
        'celery': _url('celery'),
        'event_cleanup': _url('event_cleanup'),
        'data_series_cleanup': _url('data_series_cleanup'),
        'event_queue': _url('event_queue'),
        'file_registry_cleanup': _url('file_registry_cleanup'),
        'health_check': _url('health_check'),
        'persist_data': _url('persist_data'),
    })


@api_view(['GET'])
@permission_classes([IsSuperUser])
@renderer_classes([JSONRenderer, CustomizableBrowsableAPIRenderer])
def task_queue_list(request: Request, queue_name: str) -> Response:
    """
    Shows all tasks currently in the queue.
    This is intended only for debugging purposes and no stable API!
    """
    try:
        page = int(request.query_params.get("page", 0))
    except:
        page = 0

    try:
        pagesize = int(request.query_params.get("pagesize", settings.DEFAULT_PAGE_SIZE))
        if pagesize <= 0:
            pagesize = settings.DEFAULT_PAGE_SIZE
    except:
        pagesize = settings.DEFAULT_PAGE_SIZE

    queryset = get_task_data(page=page, pagesize=pagesize, queue_name=queue_name)

    serializer_class = TaskDataSerializer
    serializer = serializer_class(queryset, many=True, context={'request': request})

    total_count = get_task_data_count(queue_name=queue_name)

    if (page + 1 * pagesize) < total_count:
        next_page = replace_query_param(request.build_absolute_uri(), 'page', page + 1)
    else:
        next_page = None
    if page > 0:
        prev_page = replace_query_param(request.build_absolute_uri(), 'page', page - 1)
    else:
        prev_page = None

    return Response({
        'next': next_page,
        'previous': prev_page,
        'count': total_count,
        'results': serializer.data  # type: ignore
    })


def can_use_task_dashboard(tenant: Tenant, user: Optional[Union[User, AnonymousUser]]) -> bool:
    if user is None:
        return False
    if user.is_anonymous:
        return False
    if user.is_superuser:
        return True
    if user.has_perm('task.dashboard'):
        return True
    return False


@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def task_dashboard_auth(request: HttpRequest, path: Optional[str] = None) -> HttpResponse:
    """
    method to check if a user is allowed to do the request, not user facing
    nginx does all the heavy lifting
    """
    if not environment_common.SKIPPER_TASK_DASHBOARD_ENABLED:
        return HttpResponse(status=status.HTTP_403_FORBIDDEN)
    tenant = get_current_tenant()
    _user = request.user
    response: HttpResponse
    if 'X-Original-Uri' in request.headers and 'X-Original-Method' in request.headers:
        original_method = request.headers['X-Original-Method']
        if check_cors(request=request, original_method=original_method) \
                or can_use_task_dashboard(
                    tenant=tenant,
                    user=_user
                ):
            response = HttpResponse(status=status.HTTP_200_OK)
            response['taskdashboardupstream'] = task_upstream_dashboard(tenant, _user, request)
        else:
            response = HttpResponse(status=status.HTTP_403_FORBIDDEN)
    else:
        logger.error('X-Original-Uri and X-Original-Method have to be set for task_dashboard_auth to work')
        response = HttpResponse(status=status.HTTP_403_FORBIDDEN)
    return response
