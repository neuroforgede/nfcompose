# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import uuid
from typing import Type, Sequence, Any, Dict, Union

from django.db.models import QuerySet
from django.http import HttpRequest
from django_filters.rest_framework import FilterSet, CharFilter  # type: ignore
from rest_framework import viewsets, permissions
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.mixins import RetrieveModelMixin, ListModelMixin, DestroyModelMixin, CreateModelMixin, \
    UpdateModelMixin
from rest_framework.renderers import JSONRenderer
from rest_framework.request import Request

from skipper.core.views.mixin import HasTenantSetPermission
from skipper.core.views.permission import BasePermissionUserViewSet, \
    BasePermissionGroupViewSet
from skipper.core.renderers import CustomizableBrowsableAPIRenderer, \
    CustomizableBrowsableAPIRendererObjectMixin
from skipper.flow import constants
from skipper.flow.models import HttpEndpoint, get_permission_string_for_action_and_http_verb, \
    HTTP_ENDPOINT_PERMISSION_KEY_HTTP_ENDPOINT, \
    get_permissions_class, HTTP_ENDPOINT_PERMISSION_KEY_PERMISSION, ALL_ASSEMBLED_HTTP_ENDPOINT_PERMISSIONS
from skipper.flow.serializers.http_endpoint import HttpEndpointSerializer


class HttpEndpointFilterSet(FilterSet):  # type: ignore
    external_id = CharFilter(field_name='external_id',
                             method='external_id_equal', label='External Id')

    engine_id = CharFilter(field_name='engine_id', method='engine_id_equal', label='Engine Id')

    def external_id_equal(self, qs, name, value):  # type: ignore
        return qs.filter(**{'external_id': value})

    def engine_id_equal(self, qs, name, value):  # type: ignore
        try:
            engine_uuid = uuid.UUID(value)
        except ValueError:
            raise ValidationError('engine_id in query parameter is not a valid uuid')
        return qs.filter(**{'engine_id': engine_uuid})


class HttpEndpointViewMixin:
    http_endpoint_permission_key: str
    kwargs: Dict[str, Any]

    def _base_perm_check(self, request: Request) -> None:
        if not request.user.has_perm(get_permission_string_for_action_and_http_verb(
                entity='http_endpoint',
                action=HTTP_ENDPOINT_PERMISSION_KEY_HTTP_ENDPOINT,
                http_verb='GET'
        )):
            raise PermissionDenied()
        if not request.user.has_perm(get_permission_string_for_action_and_http_verb(
                entity='http_endpoint',
                action=self.http_endpoint_permission_key,
                http_verb=request.method
        )):
            raise PermissionDenied()

    def get_queryset(self) -> 'QuerySet[HttpEndpoint]':
        request: Request = self.request # type: ignore
        ret = HttpEndpoint._qs(request, self.http_endpoint_permission_key).order_by('id')
        if 'pk' in self.kwargs:
            _id = self.kwargs['pk']
            _id_as_uuid: uuid.UUID
            try:
                _id_as_uuid = uuid.UUID(str(_id))
            except ValueError as e:
                raise NotFound(f'did not find object with {_id} as it is no valid UUID')
            # this has to be done when fetching the queryset because we need to check OPTIONS requests properly
            if len(ret) == 0 and len(HttpEndpoint.objects.filter(id=_id_as_uuid)) == 1:
                raise PermissionDenied()
        return ret


class HttpEndpointViewSet(
    CustomizableBrowsableAPIRendererObjectMixin,
    HttpEndpointViewMixin,
    RetrieveModelMixin,
    ListModelMixin,
    DestroyModelMixin,
    CreateModelMixin,
    UpdateModelMixin,
    viewsets.GenericViewSet,  # type: ignore
):
    """
    API to dynamically define HttpEndpoints that can be used for routing.
    """
    skipper_base_name = constants.http_endpoint_view_base_name

    renderer_classes = [JSONRenderer, CustomizableBrowsableAPIRenderer]

    permission_classes  = [
        HasTenantSetPermission,
        get_permissions_class('http_endpoint', HTTP_ENDPOINT_PERMISSION_KEY_HTTP_ENDPOINT)
    ]

    http_endpoint_permission_key = HTTP_ENDPOINT_PERMISSION_KEY_HTTP_ENDPOINT

    ordering = ('id',)

    filterset_class = HttpEndpointFilterSet

    action: str

    def get_name_string(self) -> str:
        if 'pk' in self.kwargs:
            _http_endpoint = self.get_object()
            return f'HttpEndpoint {_http_endpoint.external_id}'
        else:
            return self.get_view_name()

    def get_serializer_class(self) -> Any:
        return HttpEndpointSerializer


class HttpEndpointPermissionViewSetMixin(object):
    kwargs: Dict[str, Any]

    permission_classes: Any = [
        HasTenantSetPermission,
        get_permissions_class('http_endpoint', HTTP_ENDPOINT_PERMISSION_KEY_PERMISSION),
    ]

    perm_prefix = 'flow'
    all_perms_without_prefix = set([perm[0] for perm in ALL_ASSEMBLED_HTTP_ENDPOINT_PERMISSIONS])

    renderer_classes: Any = [JSONRenderer, CustomizableBrowsableAPIRenderer]

    def get_object_for_perms(self) -> HttpEndpoint:
        request: Request = self.request # type: ignore
        http_endpoint_id = self.kwargs['parent1']
        _http_endpoint_objs = list(HttpEndpoint._qs(
            request,
            action=HTTP_ENDPOINT_PERMISSION_KEY_PERMISSION
        ).filter(id=http_endpoint_id).all())
        if len(_http_endpoint_objs) != 1:
            if len(HttpEndpoint.objects.filter(id=http_endpoint_id)) == 1:
                raise PermissionDenied()
            raise NotFound()
        return _http_endpoint_objs[0]


class HttpEndpointPermissionUserViewSet(
    HttpEndpointPermissionViewSetMixin,
    BasePermissionUserViewSet
):
    """
    API to define the permissions for an HttpEndpoint per User.
    Permission names are structured around basic REST verbs and should be self explanatory.
    In order for a User to use this permissions they still need the global permission.
    These global permissions have to be granted via the admin interface.
    """
    skipper_base_name = constants.http_endpoint_permission_user_base_name


class HttpEndpointPermissionGroupViewSet(
    HttpEndpointPermissionViewSetMixin,
    BasePermissionGroupViewSet
):
    """
    API to define the permissions for an HttpEndpoint per Group.
    Permission names are structured around basic REST verbs and should be self explanatory.
    In order for a Group to use this permissions they still need the global permission.
    These global permissions have to be granted via the admin interface.
    """
    skipper_base_name = constants.http_endpoint_permission_group_base_name

