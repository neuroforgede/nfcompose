# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

import uuid
from typing import Protocol, Sequence, Any, Dict, Union, cast, List

from django.db.models import QuerySet, Model
from django.contrib.auth.base_user import AbstractBaseUser
from django.http import HttpRequest
from django_filters.rest_framework import FilterSet, CharFilter  # type: ignore
from rest_framework import viewsets, permissions
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.mixins import RetrieveModelMixin, ListModelMixin, DestroyModelMixin, CreateModelMixin, \
    UpdateModelMixin
from rest_framework.renderers import JSONRenderer
from rest_framework.request import Request

from skipper.core.models.guardian import get_objects_for_user_custom
from skipper.core.views.mixin import HasTenantSetPermission
from skipper.core.views.permission import BasePermissionUserViewSet, \
    BasePermissionGroupViewSet
from skipper.core.renderers import CustomizableBrowsableAPIRenderer, \
    CustomizableBrowsableAPIRendererObjectMixin
from skipper.flow import constants
from skipper.flow.models import Engine, get_permission_string_for_action_and_http_verb, ENGINE_PERMISSION_KEY_ENGINE, \
    get_permissions_class, ENGINE_PERMISSION_KEY_PERMISSION, \
    ALL_ASSEMBLED_ENGINE_PERMISSIONS, ENGINE_PERMISSION_KEY_SECRET, HttpEndpoint
from skipper.flow.serializers.engine import EngineSerializer


class EngineFilterSet(FilterSet):  # type: ignore
    external_id = CharFilter(field_name='external_id',
                             method='external_id_equal', label='External Id')

    def external_id_equal(self, qs, name, value):  # type: ignore
        return qs.filter(**{'external_id': value})

class EngineViewMixin:
    engine_permission_key: str
    kwargs: Dict[str, Any]

    def _base_perm_check(self, request: Request) -> None:
        if not request.user.has_perm(get_permission_string_for_action_and_http_verb(
                entity='engine',
                action=ENGINE_PERMISSION_KEY_ENGINE,
                http_verb='GET'
        )):
            raise PermissionDenied()
        if not request.user.has_perm(get_permission_string_for_action_and_http_verb(
                entity='engine',
                action=self.engine_permission_key,
                http_verb=request.method
        )):
            raise PermissionDenied()

    def get_queryset(self) -> 'QuerySet[Engine]':
        request: Request = self.request # type: ignore
        ret = Engine._qs(request, self.engine_permission_key).order_by('id')
        if 'pk' in self.kwargs:
            _id = self.kwargs['pk']
            _id_as_uuid: uuid.UUID
            try:
                _id_as_uuid = uuid.UUID(str(_id))
            except ValueError as e:
                raise NotFound(f'did not find object with {_id} as it is no valid UUID')
            # this has to be done when fetching the queryset because we need to check OPTIONS requests properly
            if len(ret) == 0 and len(Engine.objects.filter(id=_id_as_uuid)) == 1:
                raise PermissionDenied()
        return ret

class EngineViewSet(
    CustomizableBrowsableAPIRendererObjectMixin,
    EngineViewMixin,
    RetrieveModelMixin,
    ListModelMixin,
    DestroyModelMixin,
    CreateModelMixin,
    UpdateModelMixin,
    viewsets.GenericViewSet,  # type: ignore
):
    """
    API to dynamically define Engines that can be used for routing HttpEndpoints.

    This API is by its nature really powerful and therefore should
    be guarded against any Create, Update, Deletions in a multi-tenant setup
    when using the default skipper_proxy.
    If endusers were to create their own Engines via the REST API, a malicious user
    can input problematic upstreams that he/she should not have access to and therefore
    proxy things in an unsafe manner.

    A possible solution for this would be a proxy setup like:

    1. skipper_proxy asks skipper for the routing details
       skipper answers with routing details for the flow
       as well as a tenant identifier. "enginetenant" for edit access,
       "flowtenant" for routed flows
    2. enhanced skipper_proxy => skipper_flow_relay
       The enhanced skipper_proxy does not handle the final routing itself,
       but simply sends the relevant routing details request to another
       nginx server via headers. This should be 100% isolated from all other docker
       containers. This then does the final routing.
    """
    skipper_base_name = constants.engine_view_base_name

    renderer_classes = [JSONRenderer, CustomizableBrowsableAPIRenderer]

    permission_classes  = [
        HasTenantSetPermission,
        get_permissions_class('engine', ENGINE_PERMISSION_KEY_ENGINE)
    ]

    engine_permission_key = ENGINE_PERMISSION_KEY_ENGINE

    ordering = ('id',)

    filterset_class = EngineFilterSet

    action: str

    def perform_destroy(self, instance: Engine) -> None:

        _cascade_delete_query: Union[str, List[str]] = self.request.query_params.get('cascade_delete', None)

        _cascade_delete = False
        if _cascade_delete_query == '' or _cascade_delete_query == 'true':
            _cascade_delete = True

        if _cascade_delete:
            # FIXME: this kinda breaks permissions a bit, but does make sense? we need to document this
            HttpEndpoint.objects.filter(engine=instance).delete()
        else:
            if HttpEndpoint.objects.filter(engine=instance).count() > 0:
                raise ValidationError('can\'t delete Engines that are referenced in endpoints')

        super().perform_destroy(instance)

    def get_name_string(self) -> str:
        if 'pk' in self.kwargs:
            _engine = self.get_object()
            return f'Engine {_engine.external_id}'
        else:
            return self.get_view_name()

    def get_serializer_class(self) -> Any:
        return EngineSerializer


class EnginePermissionViewSetMixin(object):
    kwargs: Dict[str, Any]

    permission_classes: Any = [
        HasTenantSetPermission,
        get_permissions_class('engine', ENGINE_PERMISSION_KEY_PERMISSION),
    ]

    perm_prefix = 'flow'
    all_perms_without_prefix = set([perm[0] for perm in ALL_ASSEMBLED_ENGINE_PERMISSIONS])

    renderer_classes: Any = [JSONRenderer, CustomizableBrowsableAPIRenderer]

    def get_object_for_perms(self) -> Engine:
        request: Request = self.request # type: ignore
        engine_id = self.kwargs['parent1']
        _engine_objs = list(Engine._qs(
            request,
            action=ENGINE_PERMISSION_KEY_PERMISSION
        ).filter(id=engine_id).all())
        if len(_engine_objs) != 1:
            if len(Engine.objects.filter(id=engine_id)) == 1:
                raise PermissionDenied()
            raise NotFound()
        return _engine_objs[0]


class EnginePermissionUserViewSet(
    EnginePermissionViewSetMixin,
    BasePermissionUserViewSet
):
    """
    API to define the permissions for an Engine per User.
    Permission names are structured around basic REST verbs and should be self explanatory.
    In order for a User to use this permissions they still need the global permission.
    These global permissions have to be granted via the admin interface.

    Note that the only permission required for the access endpoint is flow.engine_get_access for now
    since this is an integration endpoint that always checks if a user has access to an engine with a
    GET request internally.
    """
    skipper_base_name = constants.engine_permission_user_base_name


class EnginePermissionGroupViewSet(
    EnginePermissionViewSetMixin,
    BasePermissionGroupViewSet
):
    """
    API to define the permissions for an Engine per Group.
    Permission names are structured around basic REST verbs and should be self explanatory.
    In order for a Group to use this permissions they still need the global permission.
    These global permissions have to be granted via the admin interface.

    Note that the only permission required for the access endpoint is flow.engine_get_access for now
    since this is an integration endpoint that always checks if a user has access to an engine with a
    GET request internally.
    """
    skipper_base_name = constants.engine_permission_group_base_name

