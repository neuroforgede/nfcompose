# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import re
import uuid
from typing import Any, Optional, Union, Callable, cast

from django.contrib.auth.models import User, AnonymousUser
from django.core.exceptions import ValidationError
from django.db.models import ForeignKey, DO_NOTHING, CharField, BooleanField, F, QuerySet, Q, \
    UniqueConstraint
from django.http import HttpRequest
from rest_framework.request import Request

from skipper.core.models import softdelete, fields, TenantForeignKey
from skipper.core.models.softdelete import SoftDeletionTenantManager
from skipper.core.models.tenant import get_tenant_model, Tenant, SoftDeleteTenantValidateExternalIdMixin
from skipper.flow.models.permissions import gen_permissions, get_permission_string_for_action_and_http_verb
from .engine import Engine
from ...core.models.guardian import get_objects_for_user_custom
from ...settings import flow_upstream_impl, flow_system_secret

_http_methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"]


HTTP_ENDPOINT_PERMISSION_KEY_HTTP_ENDPOINT = 'http_endpoint'
HTTP_ENDPOINT_PERMISSION_KEY_PERMISSION = 'permission'


ALL_ASSEMBLED_HTTP_ENDPOINT_PERMISSIONS = [
    *gen_permissions(entity='http_endpoint', action=HTTP_ENDPOINT_PERMISSION_KEY_HTTP_ENDPOINT),
    *gen_permissions(entity='http_endpoint', action=HTTP_ENDPOINT_PERMISSION_KEY_PERMISSION),
    ('use', 'Allowed to use endpoint')
]

ALL_AVAILABLE_HTTP_ENDPOINT_PERMISSION_STRINGS = [
    f'flow.{perm[0]}' for perm in ALL_ASSEMBLED_HTTP_ENDPOINT_PERMISSIONS
]

DEFAULT_PERMISSION_STRINGS_ON_HTTP_ENDPOINT_CREATE = ALL_AVAILABLE_HTTP_ENDPOINT_PERMISSION_STRINGS


def validate_path(path: str) -> None:
    try:
        re.compile(path)
    except re.error as e:
        raise ValidationError('path regex invalid: ' + str(e))


_default_ordering = ['system', F('external_id').asc(nulls_last=True)]

method_choices = [(elem, elem) for elem in _http_methods]


class HttpEndpoint(SoftDeleteTenantValidateExternalIdMixin, softdelete.SoftDeletionTenantModel):
    id = fields.id_field()
    external_id = fields.external_id_field_url_safe()
    tenant = ForeignKey(get_tenant_model(), on_delete=DO_NOTHING)
    path = CharField(max_length=256, validators=[validate_path])
    method = CharField(max_length=10, choices=method_choices)
    public = BooleanField(default=False)
    # set null but system = true means that it is not routed to the system engine
    engine_id: uuid.UUID
    # no db constraint, we want to keep the broken id in here to keep routing working
    # and so that we do not accidentally do stupid things just because we deleted an Engine
    # FIXME: NFCOMPOSE-T-43 ensure that only users that have read access to an Engine are allowed to set the engine
    #  here (what about the admin pages? => those should probably be superuser only once the REST API is defined)
    engine: Engine = TenantForeignKey(Engine, null=True, blank=True, on_delete=DO_NOTHING, db_constraint=False)
    # FIXME: NFCOMPOSE-T-43 by default False, must be set to False by REST API
    system = BooleanField()

    all_objects: softdelete.SoftDeletionManager = softdelete.SoftDeletionTenantManager(alive_only=False)  # type: ignore
    objects: softdelete.SoftDeletionManager = SoftDeletionTenantManager()  # type: ignore

    @staticmethod
    def _qs(request: Union[Request, HttpRequest],
            action: str) -> 'QuerySet[HttpEndpoint]':
        return get_objects_for_user_custom(
            request.user,
            [
                get_permission_string_for_action_and_http_verb(
                    entity='http_endpoint',
                    action=HTTP_ENDPOINT_PERMISSION_KEY_HTTP_ENDPOINT,
                    http_verb='GET'
                ),
                get_permission_string_for_action_and_http_verb(
                    entity='http_endpoint',
                    action=action,
                    http_verb=request.method
                )
            ],
            HttpEndpoint.objects.all().filter(system=False),
            True,
            app_label='flow'
        )

    @staticmethod
    def active_endpoints(
        tenant: Tenant,
        method: str,
        public: bool
     ) -> 'QuerySet[HttpEndpoint]':
        return HttpEndpoint.objects.all().filter(
            Q(
                engine_id__isnull=False,
                # FML, Django, really?
                # access the something in the joined data that is definitely there if the join works
                # ensure it is not null
                engine__external_id__isnull=False,
                engine__deleted_at__isnull=True,
                system=False
            ) | Q(
                engine_id__isnull=True,
                # FML, Django, really?
                # access the something in the joined data that is definitely there if the join works
                # ensure it is null
                engine__external_id__isnull=True,
                system=True
            ),
            tenant=tenant,
            method=method,
            public=public
        ).order_by(*_default_ordering)

    def _engine_prop(
            self,
            user: Optional[Union[User, AnonymousUser]],
            request: Optional[Union[HttpRequest, Request]],
            propertyName: str,
            system_property_accessor: Callable[[Union[Tenant], Optional[Union[User, AnonymousUser]], Optional[Union[HttpRequest, Request]]], str]
    ) -> str:
        if self.engine_id is None and not self.system:
            raise AssertionError('engine must be set or HttpEndpoint must be marked as system')
        if self.engine_id is not None:
            try:
                if self.engine.deleted_at is not None:
                    raise AssertionError('referenced engine seems to be deleted')
                if self.engine.tenant_id != self.tenant_id:
                    raise AssertionError('Engines tenant does not match HttpEndpoint tenant')
            except Engine.DoesNotExist as e:
                raise AssertionError('referenced engine seems to not exist or was hard deleted', e)
            return cast(str, getattr(self.engine, propertyName))
        if self.system:
            if self.public:
                if request is None:
                    raise AssertionError('request is required to get an upstream property from a public system flow if no engine is set')
                return system_property_accessor(self.tenant, user, request)
            else:
                if user is None or request is None:
                    raise AssertionError('user and request are required to get an upstream property from a system flow if no engine is set')
                return system_property_accessor(self.tenant, user, request)
        raise AssertionError('should not reach this!')

    def get_secret(self, user: Optional[Union[User, AnonymousUser]], request: Optional[Union[HttpRequest, Request]]) -> str:
        _secret = self._engine_prop(user, request, 'secret', flow_system_secret)
        if _secret is None or len(_secret) == 0:
            raise AssertionError('engine secret is not properly defined for Engine')
        return _secret

    def get_upstream(self, user: Optional[Union[User, AnonymousUser]], request: Optional[Union[HttpRequest, Request]]) -> str:
        return self._engine_prop(user, request, 'upstream', flow_upstream_impl)

    def __str__(self) -> str:
        return f'HttpEndpoint "{self.external_id}" ({str(self.path)})'

    def clean(self) -> None:
        if self.engine is None and not self.system:
            raise ValidationError('engine is required when system=False')
        super().clean()

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.engine is None and not self.system:
            raise ValidationError('engine is required when system=False')
        super().save(*args, **kwargs)

    class Meta:
        db_table = f'_4_http_endpoint'.lower()
        permissions = [
            *ALL_ASSEMBLED_HTTP_ENDPOINT_PERMISSIONS
        ]
        constraints = [
            UniqueConstraint(fields=['tenant_id', 'external_id'],
                             name=f'_4_http_endpoint_tenant_id_external_id__1',
                             condition=Q(deleted_at__isnull=True))
        ]
        # order by system first (system=False first), then external_id as breaker
        ordering = _default_ordering
