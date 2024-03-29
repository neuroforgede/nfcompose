# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from typing import Any

from django.contrib.auth.models import Group
from django.db.models import QuerySet
from django_filters.rest_framework import FilterSet, CharFilter  # type: ignore
from django_multitenant.utils import get_current_tenant  # type: ignore
from rest_framework import viewsets
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer

from skipper.common import constants
from skipper.common.components.auth import serializers
from skipper.core.views import mixin

from skipper.common.components.auth.views.permissions import AuthTenantViewMixin


class GroupFilterSet(FilterSet):  # type: ignore
    name = CharFilter(field_name="name",
                      method='name_equal', label='name')
    fully_qualified = CharFilter(field_name="fully_qualified", method="fully_qualified_equal", label="Fully Qualified")

    def name_equal(self, qs: 'QuerySet[Any]', name: str, value: str) -> 'QuerySet[Any]':
        tenant = get_current_tenant()
        return qs.filter(name=tenant.name + '@@' + value)

    def fully_qualified_equal(self, qs: 'QuerySet[Any]', name: str, value: str) -> 'QuerySet[Any]':
        return qs.filter(name=value)


class GroupViewSet(
    AuthTenantViewMixin,
    mixin.HttpErrorAwareCreateModelMixin,
    viewsets.ModelViewSet  # type: ignore
):
    """
    API endpoint that allows to view or edit Groups.
    The Admin page has more options for this, though.
    """
    skipper_base_name = constants.common_auth_group_view_set_name

    serializer_class = serializers.GroupSerializer

    filterset_class = GroupFilterSet

    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]

    def get_queryset(self) -> 'QuerySet[Any]':
        tenant = get_current_tenant()
        return Group.objects.filter(
            tenant_group__tenant=tenant,
            tenant_group__system=False
        ).order_by('id')
