# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from typing import Dict, Any, Set, List, Union, cast

from django.contrib.auth.models import AnonymousUser, User, Group
from django.db import transaction
from django.db.models import Model, QuerySet
from django_filters.rest_framework import FilterSet, CharFilter  # type: ignore
from django_multitenant.utils import get_current_tenant  # type: ignore
from guardian.shortcuts import remove_perm, assign_perm  # type: ignore
from rest_framework import serializers
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin, ListModelMixin
from rest_framework.request import Request
from rest_framework.viewsets import GenericViewSet

from skipper.core.models.tenant import is_tenant_manager
from skipper.core.serializers.base import BaseSerializer
from skipper.core.serializers.common import MultipleParameterHyperlinkedIdentityField
from skipper.core.utils.permissions import (
    get_assignable_permissions, 
    perms_for_user, 
    directly_assigned_perms_for_user, 
    directly_assigned_perms_for_group
)
from skipper.core.renderers import CustomizableBrowsableAPIRendererObjectMixin


class OneParentHyperlinkedIdentityField(MultipleParameterHyperlinkedIdentityField):

    def get_extra_lookup_url_kwargs(self, obj: Model, view_name: str, request: Request, format: str) -> Dict[str, Any]:
        if request.parser_context is None:
            raise NotFound()
        kwargs = request.parser_context['kwargs']
        return {'parent1': kwargs['parent1']}


class UserFilterSet(FilterSet):  # type: ignore
    username = CharFilter(field_name="username",
                          method='username_equal', label='Username')
    fully_qualified = CharFilter(field_name="username", method="fully_qualified_equal", label="Fully Qualified")

    def username_equal(self, qs: 'QuerySet[Any]', name: str, value: str) -> 'QuerySet[Any]':
        tenant = get_current_tenant()
        if tenant is None:
            return qs
        else:
            return qs.filter(username=tenant.name + '@@' + value)

    def fully_qualified_equal(self, qs: 'QuerySet[Any]', name: str, value: str) -> 'QuerySet[Any]':
        return qs.filter(username=value)


class BasePermissionUserViewSet(
    CustomizableBrowsableAPIRendererObjectMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    ListModelMixin,
    GenericViewSet,  # type: ignore
):
    skipper_base_name: str

    perm_prefix: str
    all_perms_without_prefix: Set[str]

    filterset_class = UserFilterSet

    def get_object_for_perms(self) -> Any:
        raise NotImplementedError()

    def get_name_string(self) -> str:
        _ds_object = self.get_object_for_perms()
        if 'pk' in self.kwargs:
            return f'{_ds_object.external_id} - User Permissions: {self.get_object().username}'
        else:
            return f'{_ds_object.external_id} - User Permissions'

    def get_serializer_class(self) -> Any:
        obj_for_perms = self.get_object_for_perms()

        _view_base_name = self.skipper_base_name

        _perm_prefix = self.perm_prefix

        _all_perms_without_prefix = self.all_perms_without_prefix

        _generally_available_perms_with_prefix = {
            f'{self.perm_prefix}.{perm}' for perm in _all_perms_without_prefix
        }

        _requesting_user: Union[User, AnonymousUser] = self.request.user
        _assignable_permissions = \
            get_assignable_permissions(self.request.user, _generally_available_perms_with_prefix).intersection(
                perms_for_user(self.perm_prefix, self.request.user, obj_for_perms, _all_perms_without_prefix)
            )

        class GenericUserPermissionSerializer(BaseSerializer):
            url = OneParentHyperlinkedIdentityField(
                view_name=_view_base_name + '-detail',
                lookup_field='pk'
            )
            user_permissions = serializers.MultipleChoiceField(
                choices=sorted(list(_generally_available_perms_with_prefix))
            )

            def to_representation(self, obj: Any) -> Any:
                username = obj.username
                split = username.split('@@')
                _name: str
                if len(split) == 1:
                    _name = split[0]
                else:
                    _name = username[len(split[0]) + len('@@'):]

                representation = {
                    'url': self.get_sub_url(
                        _view_base_name + '-detail',
                        [obj_for_perms.id, obj.id]
                    ),
                    'id': obj.id,
                    'username': _name,
                    'fully_qualified': obj.username,
                    'user_permissions': sorted(list(
                        directly_assigned_perms_for_user(_perm_prefix, obj, obj_for_perms, _all_perms_without_prefix)
                    ))
                }
                return representation

            def update(self, instance: Model, validated_data: Dict[str, Any]) -> Model:
                with transaction.atomic():
                    if 'user_permissions' not in validated_data:
                        return instance

                    new_permissions = set(validated_data['user_permissions'])

                    _directly_assigned = directly_assigned_perms_for_user(_perm_prefix, cast(User, instance),
                                                                          obj_for_perms, _all_perms_without_prefix)

                    to_remove = (_directly_assigned - new_permissions)
                    to_add = (new_permissions - _directly_assigned)

                    permissions_we_dont_have = (to_remove - _assignable_permissions).union(
                        to_add - _assignable_permissions)

                    if (
                        len(permissions_we_dont_have) > 0 and 
                        not is_tenant_manager(_requesting_user, get_current_tenant())
                    ):
                        raise PermissionDenied(
                            f'can\'t change permissions you do not have: {str(permissions_we_dont_have)}')

                    for perm in to_remove:
                        remove_perm(
                            perm,
                            instance,
                            obj_for_perms
                        )

                    for permission in to_add:
                        assign_perm(
                            permission,
                            instance,
                            obj_for_perms
                        )

                    return instance

            class Meta:
                model = User
                fields: List[str] = ['url', 'user_permissions']

        return GenericUserPermissionSerializer

    def get_queryset(self) -> QuerySet[User]:
        # check permission
        self.get_object_for_perms()
        tenant = get_current_tenant()
        return User.objects.filter(
            tenant_user__tenant=tenant,
            tenant_user__system=False
        ).order_by('id').all()


class GroupFilterSet(FilterSet):  # type: ignore
    name = CharFilter(field_name="name",
                      method='name_equal', label='Name')
    fully_qualified = CharFilter(field_name="fully_qualified", method="fully_qualified_equal", label="Fully Qualified")

    def name_equal(self, qs: 'QuerySet[Any]', name: str, value: str) -> 'QuerySet[Any]':
        tenant = get_current_tenant()
        if tenant is None:
            return qs
        else:
            return qs.filter(name=tenant.name + '@@' + value)

    def fully_qualified_equal(self, qs: 'QuerySet[Any]', name: str, value: str) -> 'QuerySet[Any]':
        return qs.filter(name=value)


class BasePermissionGroupViewSet(
    CustomizableBrowsableAPIRendererObjectMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    ListModelMixin,
    GenericViewSet  # type: ignore
):
    skipper_base_name: str

    perm_prefix: str
    all_perms_without_prefix: Set[str]

    filterset_class = GroupFilterSet

    def get_object_for_perms(self) -> Any:
        raise NotImplementedError()

    def get_serializer_class(self) -> Any:
        obj_for_perms = self.get_object_for_perms()

        _perm_prefix = self.perm_prefix

        _all_perms_without_prefix = self.all_perms_without_prefix

        _generally_available_perms_with_prefix = {
            f'{self.perm_prefix}.{perm}' for perm in _all_perms_without_prefix
        }

        _requesting_user: Union[User, AnonymousUser] = self.request.user
        _assignable_permissions = \
            get_assignable_permissions(self.request.user, _generally_available_perms_with_prefix).intersection(
                perms_for_user(self.perm_prefix, self.request.user, obj_for_perms, _all_perms_without_prefix)
            )

        _view_base_name = self.skipper_base_name

        class GenericGroupPermissionSerializer(BaseSerializer):
            url = OneParentHyperlinkedIdentityField(
                view_name=_view_base_name + '-detail',
                lookup_field='pk'
            )
            group_permissions = serializers.MultipleChoiceField(
                choices=sorted(list(_generally_available_perms_with_prefix))
            )

            def to_representation(self, obj: Any) -> Any:
                name = obj.name
                split = name.split('@@')
                _name: str
                if len(split) == 1:
                    _name = split[0]
                else:
                    _name = name[len(split[0]) + len('@@'):]

                representation = {
                    'url': self.get_sub_url(
                        _view_base_name + '-detail',
                        [obj_for_perms.id, obj.id]
                    ),
                    'id': obj.id,
                    'name': _name,
                    'fully_qualified': obj.name,
                    'group_permissions': sorted(list(directly_assigned_perms_for_group(
                        _perm_prefix, obj, obj_for_perms, _all_perms_without_prefix
                    )))
                }
                return representation

            def update(self, instance: Model, validated_data: Dict[str, Any]) -> Model:
                with transaction.atomic():
                    if 'group_permissions' not in validated_data:
                        return instance

                    new_permissions = set(validated_data['group_permissions'])

                    _directly_assigned = directly_assigned_perms_for_group(_perm_prefix, cast(Group, instance), 
                                                                           obj_for_perms, _all_perms_without_prefix)

                    to_remove = (_directly_assigned - new_permissions)
                    to_add = (new_permissions - _directly_assigned)

                    permissions_we_dont_have = (to_remove - _assignable_permissions).union(
                        to_add - _assignable_permissions
                    )

                    if (
                        len(permissions_we_dont_have) > 0 and 
                        not is_tenant_manager(_requesting_user, get_current_tenant())
                    ):
                        raise PermissionDenied(
                            f'can\'t change permissions you do not have: {str(permissions_we_dont_have)}'
                        )

                    for perm in to_remove:
                        remove_perm(
                            perm,
                            instance,
                            obj_for_perms
                        )

                    for permission in to_add:
                        assign_perm(
                            permission,
                            instance,
                            obj_for_perms
                        )

                    return instance

            class Meta:
                model = Group
                fields: List[str] = ['url', 'group_permissions']

        return GenericGroupPermissionSerializer

    def get_queryset(self) -> QuerySet[Group]:
        # check permission
        self.get_object_for_perms()
        tenant = get_current_tenant()
        return Group.objects.filter(
            tenant_group__tenant=tenant,
            tenant_group__system=False
        ).order_by('id').all()
