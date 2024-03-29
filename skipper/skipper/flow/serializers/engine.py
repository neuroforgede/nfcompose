# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from typing import List, Dict, Any

from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from guardian.shortcuts import assign_perm  # type: ignore
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField
from rest_framework.generics import get_object_or_404
from rest_framework.relations import HyperlinkedIdentityField

from skipper.core.models.validation import validate_external_id_url_safe
from skipper.core.serializers.base import BaseSerializer
from skipper.flow import constants
from skipper.flow.models import Engine, DEFAULT_PERMISSION_STRINGS_ON_ENGINE_CREATE


class EngineSecretSerializer(BaseSerializer):
    secret = CharField(
        allow_null=False,
        allow_blank=False,
        required=True,
        min_length=32,
        validators=[validate_password]
    )

    def update(self, instance: Any, validated_data: Any) -> Any:
        raise AssertionError()

    def create(self, validated_data: Any) -> Any:
        raise AssertionError()

    class Meta:
        model = Engine
        fields = (
            'secret',
        )


class EngineSerializer(BaseSerializer):
    url = HyperlinkedIdentityField(view_name=constants.engine_view_base_name + '-detail')
    sub_views: List[Dict[str, str]] = [
        {
            'sub_path': 'access',
            'view_name': constants.engine_access_view_base_name + '-root'
        },
        {
            'sub_path': 'permission_user',
            'view_name': constants.engine_permission_user_base_name + '-list'
        },
        {
            'sub_path': 'permission_group',
            'view_name': constants.engine_permission_group_base_name + '-list'
        },
        {
            'sub_path': 'secret',
            'view_name': constants.engine_secret_view_base_name + '-root'
        },
    ]

    def validate_external_id(self, external_id: str) -> str:
        kwargs = self.context.get('view').kwargs  # type: ignore

        if 'pk' not in kwargs:
            if Engine.objects.all().filter(external_id=external_id).exists():
                raise ValidationError(
                    f'external id \'{external_id}\' is already in use by another Engine')
        else:
            _id = kwargs['pk']
            _engine: Engine = get_object_or_404(
                Engine.objects.filter(id=_id))
            if external_id != _engine.external_id:
                raise ValidationError('changing of external_id is not supported!')

        if not validate_external_id_url_safe(external_id):
            raise ValidationError("Only letters, numbers, '-', and '_' are allowed in external_ids, 1-50 chars")

        return external_id

    def create(self, validated_data: Dict[str, Any]) -> Any:
        with transaction.atomic():
            created = super().create(validated_data)

            user = None
            request = self.context.get("request")
            if request and hasattr(request, "user"):
                user = request.user

            assert user is not None

            if not user.is_anonymous:
                for perm in DEFAULT_PERMISSION_STRINGS_ON_ENGINE_CREATE:
                    assign_perm(
                        perm,
                        user,
                        obj=created
                    )

            return created

    class Meta:
        model = Engine
        fields = (
            'url',
            'id',
            'external_id',
            'upstream'
        )

