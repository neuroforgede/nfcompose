# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from django.db import transaction
from django.db.models import QuerySet
from guardian.shortcuts import assign_perm  # type: ignore
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, BooleanField, ChoiceField
from rest_framework.generics import get_object_or_404
from rest_framework.relations import HyperlinkedIdentityField, HyperlinkedRelatedField
from typing import List, Dict, Any, cast

from skipper.core.models.validation import validate_external_id_url_safe
from skipper.core.serializers.base import BaseSerializer
from skipper.flow import constants
from skipper.flow.models import HttpEndpoint, \
    DEFAULT_PERMISSION_STRINGS_ON_HTTP_ENDPOINT_CREATE, validate_path, method_choices
from skipper.flow.models.engine import Engine, ENGINE_PERMISSION_KEY_ENGINE


class EngineHyperlinkedRelatedField(
    HyperlinkedRelatedField  # type: ignore
):

    def get_queryset(self) -> 'QuerySet[Engine]':
        # if you are allowed to see an engine, you are allowed to use the engine
        # this should be enough, since if you have the permission to add endpoints
        return Engine._qs(
            self.context['request'],
            ENGINE_PERMISSION_KEY_ENGINE,
            'GET'
        )


class HttpEndpointSerializer(BaseSerializer):
    url = HyperlinkedIdentityField(view_name=constants.http_endpoint_view_base_name + '-detail')
    engine = EngineHyperlinkedRelatedField(required=True, view_name=constants.engine_view_base_name + '-detail')
    external_id = CharField(allow_null=False, allow_blank=False)
    path = CharField(allow_null=False, allow_blank=False, validators=[validate_path])
    method = ChoiceField(choices=method_choices)
    public = BooleanField()

    sub_views: List[Dict[str, str]] = [
        {
            'sub_path': 'permission_user',
            'view_name': constants.http_endpoint_permission_user_base_name + '-list'
        },
        {
            'sub_path': 'permission_group',
            'view_name': constants.http_endpoint_permission_group_base_name + '-list'
        }
    ]

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        validated = super().validate(attrs)  # type: ignore
        validated['system'] = False
        return cast(Dict[str, Any], validated)

    def validate_external_id(self, external_id: str) -> str:
        kwargs = self.context.get('view').kwargs  # type: ignore

        if 'pk' not in kwargs:
            if HttpEndpoint.objects.all().filter(external_id=external_id).exists():
                raise ValidationError(
                    f'external id \'{external_id}\' is already in use by another HttpEndpoint')
        else:
            _id = kwargs['pk']
            _endpoint: HttpEndpoint = get_object_or_404(
                HttpEndpoint.objects.filter(id=_id))
            if external_id != _endpoint.external_id:
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
                for perm in DEFAULT_PERMISSION_STRINGS_ON_HTTP_ENDPOINT_CREATE:
                    assign_perm(
                        perm,
                        user,
                        obj=created
                    )

            return created

    class Meta:
        model = HttpEndpoint
        fields = (
            'url',
            'id',
            'engine',
            'external_id',
            'path',
            'method',
            'public',
        )
