# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from typing import Any, Dict, List, Sequence, Set, Type, cast

from django.contrib.auth.models import User
from django.db.models import Model, QuerySet
from django_filters.rest_framework import FilterSet, CharFilter  # type: ignore
from rest_framework.request import Request
from rest_framework.viewsets import ModelViewSet
from rest_framework import permissions, serializers
from rest_framework.generics import get_object_or_404
from rest_framework.serializers import ValidationError

from skipper.core import constants
from skipper.core.serializers.base import BaseSerializer
from skipper.core.serializers.common import MultipleParameterHyperlinkedIdentityField
from skipper.core.renderers import CustomizableBrowsableAPIRendererObjectMixin

from skipper.core.models.permissions import get_permissions_class
from skipper.core.models.tenant import Tenant_User, Tenant


class CoreTenantUserViewMixin:
    permission_classes: Any = (get_permissions_class('tenant', 'tenant-user'),)


class GenericTenantUsertHyperlinkedIdentityField(MultipleParameterHyperlinkedIdentityField):

    def get_extra_lookup_url_kwargs(self, obj: Model, view_name: str, request: Request, format: str) -> Dict[str, Any]:
        tenant_user = cast(Tenant_User, obj)
        return {'tenant_id': tenant_user.tenant.id}
    

class UserFilterSet(FilterSet):  # type: ignore
    username = CharFilter(
        field_name="username", method='username_equal', label='Username'
    )

    def username_equal(self, qs: 'QuerySet[Any]', name: str, value: str) -> 'QuerySet[Any]':
        return qs.filter(user__username=value)


class TenantUserViewSet(
    CoreTenantUserViewMixin,
    CustomizableBrowsableAPIRendererObjectMixin,
    ModelViewSet  # type: ignore
):
    skipper_base_name = constants.core_tenant_user_view_set_name
    kwargs: Dict[str, Any]

    filterset_class = UserFilterSet

    def get_serializer_class(self) -> Any:

        class GenericTenantUserSerializer(BaseSerializer):
            url = GenericTenantUsertHyperlinkedIdentityField(view_name=constants.core_tenant_user_view_set_name + '-detail')
            user = serializers.HyperlinkedRelatedField(
                view_name=constants.core_user_view_set_name + '-detail', 
                queryset=User.objects.exclude(username=constants.ANONYMOUS_USER_NAME)
            )
            tenant_manager = serializers.BooleanField()
            system = serializers.BooleanField()

            def to_representation(self, obj: Any) -> Any:
                repr = super().to_representation(obj)
                repr['username'] = obj.user.username
                return repr

            def validate_user(self, value: User) -> User:
                if Tenant_User.objects.filter(user=value).exists():
                    raise ValidationError("User is already assigned to a tenant")

            def create(self, validated_data: Any) -> Any:
                kwargs = self.context.get('view').kwargs  # type: ignore
                validated_data['tenant'] = Tenant.objects.get(id=kwargs['tenant_id'])

                return super().create(validated_data)

            class Meta:
                model = Tenant_User
                fields: List[str] = ['url', 'user', 'tenant_manager', 'system']

        return GenericTenantUserSerializer

    def get_queryset(self) -> QuerySet[Tenant_User]:
        tenant = get_object_or_404(Tenant.objects.filter(id=self.kwargs["tenant_id"]))
        return Tenant_User.objects.filter(
            tenant=tenant
        ).all()


