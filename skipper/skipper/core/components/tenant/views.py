# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from typing import Any, Sequence, Type

from django.db.models import QuerySet
from django_filters.rest_framework import FilterSet, CharFilter  # type: ignore
from rest_framework import viewsets, permissions
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer

from skipper.core import constants
from skipper.core.components.tenant import serializers
from skipper.core.models.tenant import Tenant
from skipper.core.views import mixin
from skipper.core.models.permissions import get_permissions_class


class CoreTenantPermMixin:
    permission_classes: Any  = (get_permissions_class('tenant', 'tenant'),)


class TenantFilterSet(FilterSet):  # type: ignore
    name = CharFilter(
        field_name="name", method='name_equal', label='Name'
    )

    def name_equal(self, qs: 'QuerySet[Any]', name: str, value: str) -> 'QuerySet[Any]':
        return qs.filter(name=value)


class TenantViewSet(
    CoreTenantPermMixin,
    mixin.HttpErrorAwareCreateModelMixin,
    viewsets.ModelViewSet  # type: ignore
):
    """
    API endpoint that allows to view or edit Tenants.
    """
    skipper_base_name = constants.core_tenant_view_set_name

    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]

    filterset_class = TenantFilterSet

    serializer_class = serializers.TenantSerializer

    def get_queryset(self) -> 'QuerySet[Any]':
        return Tenant.objects.all().order_by('id')
