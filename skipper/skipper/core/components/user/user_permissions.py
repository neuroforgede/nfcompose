# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from typing import Any, Dict, List, Sequence, Set, Type, cast

from django.contrib.auth.models import Permission, User
from django.db import transaction
from django.db.models import Model, QuerySet
from guardian.shortcuts import assign_perm, remove_perm  # type: ignore
from rest_framework.exceptions import PermissionDenied
from rest_framework.fields import MultipleChoiceField
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import permissions

from skipper.core import constants
from skipper.common.components.auth.views.permissions import (
    generally_assignable_permissions
)
from skipper.core.serializers.base import BaseSerializer
from skipper.core.utils.permissions import (
    get_assignable_permissions,
    get_directly_assigned_user_permissions
)
from skipper.core.renderers import CustomizableBrowsableAPIRendererObjectMixin
from skipper.core.models.permissions import get_permissions_class, get_permission_string_for_action_and_http_verb


class CoreUserPermissionsViewMixin:
    permission_classes: Any = (get_permissions_class('user', 'user_permission'),)


"""
includes also all permissions that should not be settable on tenant users
"""
all_generally_assignable_permissions = set([
    get_permission_string_for_action_and_http_verb("user", action, method) 
    for method in ["GET", "OPTIONS", "HEAD", "POST", "PUT", "PATCH", "DELETE"]
    for action in ["user", "user_permission"]
]).union(generally_assignable_permissions)


class UserPermissionsView(
    CoreUserPermissionsViewMixin,
    CustomizableBrowsableAPIRendererObjectMixin,
    GenericAPIView,  # type: ignore
    RetrieveModelMixin,
    UpdateModelMixin
):
    skipper_base_name = constants.core_user_permission_view_set_name

    perm_prefix: str
    all_perms_without_prefix: Set[str]

    def get(self, request: Request, pk: str) -> Response:
        with transaction.atomic():
            instance: User = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)

    def put(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return self.update(request, args, kwargs)

    def get_serializer_class(self) -> Any:

        _assignable_permissions = get_assignable_permissions(self.request.user, all_generally_assignable_permissions)

        class GenericUserPermissionSerializer(BaseSerializer):
            user_permissions = MultipleChoiceField(
                choices=sorted(list(_assignable_permissions))
            )

            def to_representation(self, obj: User) -> Any:
                perm: Permission
                # only the directly assigned ones
                representation = {
                    'user_permissions': sorted(
                        list(get_directly_assigned_user_permissions(obj, all_generally_assignable_permissions))
                    )
                }
                return representation

            def update(self, instance: Model, validated_data: Dict[str, Any]) -> Model:
                with transaction.atomic():
                    if 'user_permissions' not in validated_data:
                        return instance

                    new_permissions = set(validated_data['user_permissions'])

                    _directly_assigned = get_directly_assigned_user_permissions(
                        cast(User, instance), all_generally_assignable_permissions
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
                model = User
                fields: List[str] = ['user_permissions']

        return GenericUserPermissionSerializer

    def get_queryset(self) -> QuerySet[User]:
        return User.objects.all()
