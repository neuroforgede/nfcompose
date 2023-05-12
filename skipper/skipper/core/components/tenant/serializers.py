# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from typing import Any, Dict, List
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404

from skipper.core import constants
from skipper.core.feature_flags import get_feature_flag
from skipper.core.models.tenant import Tenant
from skipper.core.serializers.base import BaseSerializer


def get_sub_views() -> List[Dict[str, str]]:
    sub_views = []
    if get_feature_flag("compose.core.tenant.tenant_user"):
        sub_views.append({
            'sub_path': 'user',
            'view_name': constants.core_tenant_user_view_set_name + '-list'
        })
    return sub_views


class TenantSerializer(BaseSerializer):
    url = serializers.HyperlinkedIdentityField(view_name=constants.core_tenant_view_set_name + '-detail')
    # user = serializers.HyperlinkedIdentityField(view_name=constants.core_tenant_user_view_set_name + '-detail')
    name = serializers.CharField(max_length=32)

    sub_views: List[Dict[str, str]] = get_sub_views()    

    def to_representation(self, instance: Any) -> Any:
        return super().to_representation(instance)

    def validate_name(self, name: str) -> str:
        kwargs = self.context.get('view').kwargs  # type: ignore
        if 'pk' not in kwargs:
            if Tenant.all_objects.all().filter(name=name).exists():
                raise ValidationError(
                    f'Name \'{name}\' is already in use by another (possibly deleted) Tenant.')
        else:
            _id = kwargs['pk']
            _tenant: Tenant = get_object_or_404(
                Tenant.objects.filter(id=_id))
            if name != _tenant.name:
                raise ValidationError('changing of tenant names is not supported!')
        return name

    def create(self, validated_data: Dict[str, Any]) -> Any:
        return super().create(validated_data)

    class Meta:
        model = Tenant
        fields = ('url', 'name')
        read_only_fields = ('url',)
