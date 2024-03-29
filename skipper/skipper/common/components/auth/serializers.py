# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


from typing import Dict, Any

from django.contrib.auth import get_user_model
from django.contrib.auth import password_validation
from django.contrib.auth.models import Group, User
from django.db import transaction
from django.db.models import QuerySet, Model
from django_multitenant.utils import get_current_tenant  # type: ignore
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404

from skipper.common import constants
from skipper.core.exceptions.http import Http404
from skipper.core.models.tenant import Tenant_Group, Tenant_User


class GroupHyperlinkedRelatedField(
    serializers.HyperlinkedRelatedField  # type: ignore
):

    def get_queryset(self) -> 'QuerySet[Group]':
        tenant = get_current_tenant()
        return Group.objects.filter(
            tenant_group__tenant=tenant,
            tenant_group__system=False
        )


class UserSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    url = serializers.HyperlinkedIdentityField(view_name=constants.common_auth_user_view_set_name + '-detail')
    password = serializers.CharField(write_only=True, max_length=128)
    groups = GroupHyperlinkedRelatedField(view_name=constants.common_auth_group_view_set_name + '-detail', many=True)
    # we would have 150 - 32 = 118, but leave a bit extra room
    username = serializers.CharField(max_length=100)
    permissions = serializers.HyperlinkedIdentityField(view_name=constants.common_auth_user_permission_view_set_name)

    def to_representation(self, instance: Any) -> Any:
        representation = super().to_representation(instance)
        representation['fully_qualified'] = representation['username']
        split = representation['username'].split('@@')
        _name: str
        if len(split) == 1:
            _name = split[0]
        else:
            _name = representation['username'][len(split[0]) + len('@@'):]
        representation['username'] = _name
        return representation

    def validate_username(self, username: str) -> str:
        if '@@' in username:
            raise ValidationError("may not contain '@@'")

        tenant = get_current_tenant()
        name_with_tenant = f'{tenant.name}@@{username}'

        kwargs = self.context.get('view').kwargs  # type: ignore

        if 'pk' not in kwargs:
            if User.objects.all().filter(username=name_with_tenant).exists():
                raise ValidationError(
                    f'username \'{username}\' is already in use by another User')
        else:
            _id = kwargs['pk']
            _user: User = get_object_or_404(
                User.objects.filter(id=_id))
            if name_with_tenant != _user.username:
                raise ValidationError('changing of usernames is not supported!')
        return name_with_tenant

    def validate_password(self, password: str) -> str:
        password_validation.validate_password(password)
        return password

    def update(self, instance: Any, validated_data: Dict[str, Any]) -> Any:
        with transaction.atomic():
            super().update(instance, validated_data)
            if 'password' in validated_data:
                instance.set_password(validated_data['password'])
                instance.save()
            return instance

    def create(self, validated_data: Dict[str, Any]) -> Any:
        with transaction.atomic():
            tenant = get_current_tenant()
            if tenant is None:
                raise Http404('did not find tenant!')
            user = super().create(validated_data)
            user.set_password(validated_data['password'])
            user.save()
            Tenant_User.objects.create(
                tenant=get_current_tenant(),
                user=user,
                system=False
            )
            return user

    class Meta:
        model = get_user_model()
        fields = ('url', 'id',  'permissions', 'username', 'password', 'email', 'groups', 'is_active')


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.IntegerField(read_only=True)
    url = serializers.HyperlinkedIdentityField(view_name=constants.common_auth_group_view_set_name + '-detail')
    permissions = serializers.HyperlinkedIdentityField(view_name=constants.common_auth_group_permission_view_set_name)
    # we would have 150 - 32 = 118, but leave a bit extra room
    name = serializers.CharField(max_length=100)

    def to_representation(self, instance: Any) -> Any:
        representation = super().to_representation(instance)
        representation['fully_qualified'] = representation['name']
        split = representation['name'].split('@@')
        _name: str
        if len(split) == 1:
            _name = split[0]
        else:
            _name = representation['name'][len(split[0]) + len('@@'):]
        representation['name'] = _name
        return representation

    def update(self, instance: Model, validated_data: Dict[str, Any]) -> Any:
        with transaction.atomic():
            super().update(instance, validated_data)
            return instance

    def validate_name(self, name: str) -> str:
        if '@@' in name:
            raise ValidationError("may not contain '@@'")

        tenant = get_current_tenant()
        name_with_tenant = f'{tenant.name}@@{name}'

        kwargs = self.context.get('view').kwargs  # type: ignore

        if 'pk' not in kwargs:
            if Group.objects.all().filter(name=name_with_tenant).exists():
                raise ValidationError(
                    f'name \'{name}\' is already in use by another Group')
        else:
            _id = kwargs['pk']
            _group: Group = get_object_or_404(
                Group.objects.filter(id=_id))
            if name_with_tenant != _group.name:
                raise ValidationError('changing of group names is not supported!')
        return name_with_tenant

    def create(self, validated_data: Dict[str, Any]) -> Any:
        with transaction.atomic():
            tenant = get_current_tenant()
            if tenant is None:
                raise Http404('did not find tenant!')
            group = super().create(validated_data)
            Tenant_Group.objects.create(
                tenant=get_current_tenant(),
                group=group,
                system=False
            )
            return group

    class Meta:
        model = Group
        fields = ('url', 'id', 'permissions', 'name')
