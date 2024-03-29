# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.base_user import AbstractBaseUser
from django.db.models import QuerySet
from django_filters.rest_framework import FilterSet, CharFilter  # type: ignore
from django_multitenant.utils import get_current_tenant  # type: ignore
from rest_framework import viewsets
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer

from skipper.common import constants
from skipper.common.components.auth import serializers
from skipper.core.views import mixin

from skipper.common.components.auth.views.permissions import AuthTenantViewMixin


class UserFilterSet(FilterSet):  # type: ignore
    username = CharFilter(
        field_name="username", method='username_equal', label='Username'
    )
    fully_qualified = CharFilter(field_name="fully_qualified", method="fully_qualified_equal", label="Fully Qualified")

    def username_equal(self, qs: 'QuerySet[Any]', name: str, value: str) -> 'QuerySet[Any]':
        tenant = get_current_tenant()
        return qs.filter(username=tenant.name + '@@' + value)

    def fully_qualified_equal(self, qs: 'QuerySet[Any]', name: str, value: str) -> 'QuerySet[Any]':
        return qs.filter(username=value)


class UserViewSet(
    AuthTenantViewMixin,
    mixin.HttpErrorAwareCreateModelMixin,
    viewsets.ModelViewSet  # type: ignore
):
    """
    API endpoint that allows to view or edit Users.
    """
    skipper_base_name = constants.common_auth_user_view_set_name

    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]

    filterset_class = UserFilterSet

    serializer_class = serializers.UserSerializer

    def get_queryset(self) -> 'QuerySet[Any]':
        tenant = get_current_tenant()
        return get_user_model().objects.filter(
            is_superuser=False,
            is_staff=False,
            tenant_user__tenant=tenant,
            tenant_user__system=False
        ).order_by('id')
