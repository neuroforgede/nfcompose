# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from typing import Any, Sequence, Type

from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser
from django.db.models import QuerySet
from django_filters.rest_framework import FilterSet, CharFilter  # type: ignore
from django_multitenant.utils import get_current_tenant  # type: ignore
from rest_framework import viewsets, permissions
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer

from skipper.core import constants
from skipper.core.components.user.serializers import UserSerializer
from skipper.core.views import mixin
from skipper.core.models.permissions import get_permissions_class


class CoreUserViewMixin:
    permission_classes: Any  = (get_permissions_class('user', 'user'),)


class UserFilterSet(FilterSet):  # type: ignore
    username = CharFilter(
        field_name="username", method='username_equal', label='Username'
    )

    def username_equal(self, qs: 'QuerySet[Any]', name: str, value: str) -> 'QuerySet[Any]':
        return qs.filter(username=value)


class UserViewSet(
    CoreUserViewMixin,
    mixin.HttpErrorAwareCreateModelMixin,
    viewsets.ModelViewSet  # type: ignore
):
    """
    API endpoint that allows to view or edit Users.
    """
    skipper_base_name = constants.core_user_view_set_name

    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]

    filterset_class = UserFilterSet

    serializer_class = UserSerializer

    def get_queryset(self) -> 'QuerySet[Any]':
        return (
            get_user_model()
            .objects
            .all()
            .exclude(username=constants.ANONYMOUS_USER_NAME)
            .order_by('id')
        )
