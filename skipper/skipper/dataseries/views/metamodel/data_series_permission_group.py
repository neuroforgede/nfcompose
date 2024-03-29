# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from django.contrib.auth.models import Group, User, AnonymousUser
from django.db import transaction
from django.db.models import QuerySet, Model
from django_filters.rest_framework import FilterSet, CharFilter  # type: ignore
from django_multitenant.utils import get_current_tenant  # type: ignore
from guardian.shortcuts import assign_perm, remove_perm  # type: ignore
from rest_framework import serializers
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin, ListModelMixin
from rest_framework.renderers import JSONRenderer
from rest_framework.request import Request
from rest_framework.viewsets import GenericViewSet
from typing import Any, List, Dict, Union, cast
from skipper.core.models.tenant import is_tenant_manager

from skipper.core.serializers.base import BaseSerializer
from skipper.core.utils.permissions import perms_for_user, directly_assigned_perms_for_group, get_assignable_permissions
from skipper.dataseries import constants
from skipper.dataseries.models import DATASERIES_PERMISSION_KEY_PERMISSION, ALL_AVAILABLE_PERMISSIONS_DATA_SERIES, \
    PERMISSION_HTTP_VERBS, ds_permission_for_rest_method
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.core.serializers.common import MultipleParameterHyperlinkedIdentityField
from skipper.dataseries.views.common import get_dataseries_permissions_class
from skipper.dataseries.views.contract import get_data_series_object
from skipper.core.renderers import CustomizableBrowsableAPIRenderer, \
    CustomizableBrowsableAPIRendererObjectMixin
from skipper.dataseries.views.metamodel.permissions import metamodel_base_line_permissions


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


class DataSeriesPermissionGroupIdentityField(MultipleParameterHyperlinkedIdentityField):

    def get_extra_lookup_url_kwargs(self, obj: Model, view_name: str, request: Request, format: str) -> Dict[str, Any]:
        if request.parser_context is None:
            raise NotFound()
        kwargs = request.parser_context['kwargs']
        return {'data_series': kwargs['data_series']}


class DataSeriesPermissionGroupViewSet(
    CustomizableBrowsableAPIRendererObjectMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
    ListModelMixin,
    GenericViewSet,  # type: ignore
):
    """
    API to define the permissions on this dataseries per group.
    Permission names are structured around basic REST verbs and should be self explanatory.
    In order for a Group to use this permissions they still need the global permission.
    These global permissions have to be granted via the admin interface.
    """

    skipper_base_name = constants.data_series_permission_group_base_name

    filterset_class = GroupFilterSet
    permission_classes = [
        *metamodel_base_line_permissions,
        get_dataseries_permissions_class(DATASERIES_PERMISSION_KEY_PERMISSION)
    ]

    renderer_classes = [JSONRenderer, CustomizableBrowsableAPIRenderer]

    def get_data_series_object(self) -> DataSeries:
        _data_series_obj = get_data_series_object(
            kwargs_object=self.kwargs,
            action=DATASERIES_PERMISSION_KEY_PERMISSION,
            request=self.request
        )
        if _data_series_obj is None:
            raise NotFound()
        return _data_series_obj

    def get_name_string(self) -> str:
        _ds_object = self.get_data_series_object()
        if 'pk' in self.kwargs:
            return f'{_ds_object.name} - Group Permissions: {self.get_object().name}'
        else:
            return f'{_ds_object.name} - Group Permissions'

    def get_serializer_class(self) -> Any:
        data_series_obj = self.get_data_series_object()

        all_perms_without_prefix = set([
            ds_permission_for_rest_method(action=action, method=http_verb)
            for action in ALL_AVAILABLE_PERMISSIONS_DATA_SERIES
            for http_verb in PERMISSION_HTTP_VERBS
        ])

        generally_available_data_series_permissions = {
            f'dataseries.{elem}' for elem in all_perms_without_prefix
        }

        requesting_user: Union[User, AnonymousUser] = self.request.user
        assignable_permissions = \
            get_assignable_permissions(self.request.user, generally_available_data_series_permissions).intersection(
                perms_for_user('dataseries', self.request.user, data_series_obj, all_perms_without_prefix)
            )

        class DataSeriesPermissionSerializer(BaseSerializer):
            url = DataSeriesPermissionGroupIdentityField(
                view_name=constants.data_series_permission_group_base_name + '-detail',
                lookup_field='pk'
            )
            group_permissions = serializers.MultipleChoiceField(
                choices=sorted(list(generally_available_data_series_permissions))
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
                        constants.data_series_permission_group_base_name + '-detail',
                        [data_series_obj.id, obj.id]
                    ),
                    'id': obj.id,
                    'name': _name,
                    'fully_qualified': obj.name,
                    'group_permissions': sorted(list(directly_assigned_perms_for_group(
                        'dataseries', obj, data_series_obj, all_perms_without_prefix
                    )))
                }
                return representation

            def update(self, instance: Model, validated_data: Dict[str, Any]) -> Model:
                with transaction.atomic():
                    if 'group_permissions' not in validated_data:
                        return instance

                    new_permissions = set(validated_data['group_permissions'])

                    _directly_assigned = directly_assigned_perms_for_group('dataseries', cast(Group, instance), 
                                                                           data_series_obj, all_perms_without_prefix)

                    to_remove = (_directly_assigned - new_permissions)
                    to_add = (new_permissions - _directly_assigned)

                    permissions_we_dont_have = (
                        to_remove - assignable_permissions
                    ).union(
                        to_add - assignable_permissions
                    )

                    if (
                        len(permissions_we_dont_have) > 0 and 
                        not is_tenant_manager(requesting_user, get_current_tenant())
                    ):
                        raise PermissionDenied(
                            f'can\'t change permissions you do not have: {str(permissions_we_dont_have)}'
                        )

                    for perm in to_remove:
                        remove_perm(
                            perm,
                            instance,
                            data_series_obj
                        )

                    for permission in to_add:
                        assign_perm(
                            permission,
                            instance,
                            data_series_obj
                        )

                    return instance

            class Meta:
                model = Group
                fields: List[str] = ['url', 'group_permissions']

        return DataSeriesPermissionSerializer

    def get_queryset(self) -> QuerySet[Group]:
        # check permission
        get_data_series_object(
            kwargs_object=self.kwargs,
            action=DATASERIES_PERMISSION_KEY_PERMISSION,
            request=self.request
        )
        tenant = get_current_tenant()
        return Group.objects.filter(
            tenant_group__tenant=tenant,
            tenant_group__system=False
        ).order_by('id').all()
