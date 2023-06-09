# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from typing import Dict, Any

from django.contrib.auth import get_user_model
from django.contrib.auth import password_validation
from django.contrib.auth.models import User
from django.db import transaction
from django_multitenant.utils import get_current_tenant  # type: ignore
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404

from skipper.core import constants


class UserSerializer(serializers.HyperlinkedModelSerializer):
    """
    Tenant unspecific User serializer
    """
    id = serializers.IntegerField(read_only=True)
    url = serializers.HyperlinkedIdentityField(view_name=constants.core_user_view_set_name + '-detail')
    password = serializers.CharField(write_only=True, max_length=128)
    username = serializers.CharField(max_length=150)
    permissions = serializers.HyperlinkedIdentityField(view_name=constants.core_user_permission_view_set_name)

    def validate_username(self, username: str) -> str:
        kwargs = self.context.get('view').kwargs  # type: ignore

        if 'pk' not in kwargs:
            if User.objects.all().filter(username=username).exists():
                raise ValidationError(
                    f'username \'{username}\' is already in use by another User')
        else:
            _id = kwargs['pk']
            _user: User = get_object_or_404(
                User.objects.filter(id=_id))
            if username != _user.username:
                raise ValidationError('changing of usernames is not supported!')
        return username

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
            user = super().create(validated_data)
            user.set_password(validated_data['password'])
            user.save()
            return user

    class Meta:
        model = get_user_model()
        fields = ('url', 'id',  'permissions', 'username', 'password', 'email', 'is_active')
