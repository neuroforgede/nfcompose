# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from typing import Any, Set, Dict, List, cast

from django.contrib.auth.models import Group, Permission
from django.db import transaction
from django.db.models import QuerySet, Model
from django_multitenant.utils import get_current_tenant  # type: ignore
from guardian.shortcuts import remove_perm, assign_perm  # type: ignore
from rest_framework.exceptions import PermissionDenied
from rest_framework.fields import MultipleChoiceField
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin
from rest_framework.request import Request
from rest_framework.response import Response

from skipper.common import constants
from skipper.core.serializers.base import BaseSerializer
from skipper.core.utils.permissions import get_assignable_permissions, get_directly_assigned_group_permissions
from skipper.core.renderers import CustomizableBrowsableAPIRendererObjectMixin

from skipper.common.components.auth.views.permissions import generally_assignable_permissions, \
    AuthTenantViewMixin


class GroupPermissionsView(
    AuthTenantViewMixin,
    CustomizableBrowsableAPIRendererObjectMixin,
    GenericAPIView,  # type: ignore
    RetrieveModelMixin,
    UpdateModelMixin
):
    """
    PUT removes the permissions if the user running this operation has the permissions itself
        all other permissions are
    """
    skipper_base_name = constants.common_auth_group_permission_view_set_name

    perm_prefix: str
    all_perms_without_prefix: Set[str]

    def get(self, request: Request, pk: str) -> Response:
        with transaction.atomic():
            instance: Group = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)

    def put(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return self.update(request, args, kwargs)

    def get_serializer_class(self) -> Any:

        _assignable_permissions = get_assignable_permissions(self.request.user, generally_assignable_permissions)

        class GenericGroupPermissionSerializer(BaseSerializer):
            group_permissions = MultipleChoiceField(
                choices=sorted(list(generally_assignable_permissions))
            )

            def to_representation(self, obj: Group) -> Any:
                perm: Permission
                # only the directly assigned ones
                representation = {
                    'group_permissions': sorted(
                        list(get_directly_assigned_group_permissions(obj, generally_assignable_permissions))
                    )
                }
                return representation

            def update(self, instance: Model, validated_data: Dict[str, Any]) -> Model:
                with transaction.atomic():
                    if 'group_permissions' not in validated_data:
                        return instance

                    new_permissions = set(validated_data['group_permissions'])

                    _directly_assigned = get_directly_assigned_group_permissions(
                        cast(Group, instance), generally_assignable_permissions
                    )

                    to_remove = (_directly_assigned - new_permissions)
                    to_add = (new_permissions - _directly_assigned)

                    permissions_we_dont_have = (to_remove - _assignable_permissions).union(
                        to_add - _assignable_permissions
                    )

                    if len(permissions_we_dont_have) > 0:
                        raise PermissionDenied(
                            f'can\'t change permissions you do not have: {str(permissions_we_dont_have)}'
                        )

                    for perm in to_remove:
                        remove_perm(
                            perm,
                            instance
                        )

                    for permission in to_add:
                        assign_perm(
                            permission,
                            instance
                        )

                    return instance

            class Meta:
                model = Group
                fields: List[str] = ['group_permissions']

        return GenericGroupPermissionSerializer

    def get_queryset(self) -> QuerySet[Group]:
        tenant = get_current_tenant()
        return Group.objects.filter(
            tenant_group__tenant=tenant
        ).order_by('id').all()
