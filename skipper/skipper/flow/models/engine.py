# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

import uuid
from typing import Any, Union, Optional

from django.contrib.auth.password_validation import validate_password
from django.db.models import ForeignKey, DO_NOTHING, UniqueConstraint, Q, URLField, TextField, QuerySet
from django.http import HttpRequest
from rest_framework.request import Request
from django.core.validators import URLValidator

from skipper.core.models import softdelete, fields
from skipper.core.models.guardian import get_objects_for_user_custom
from skipper.core.models.softdelete import SoftDeletionTenantManager
from skipper.core.models.tenant import get_tenant_model, SoftDeleteTenantValidateExternalIdMixin
from skipper.flow.models.permissions import gen_permissions, get_permission_string_for_action_and_http_verb
from django.utils.crypto import get_random_string

ENGINE_PERMISSION_KEY_ENGINE = 'engine'
ENGINE_PERMISSION_KEY_ACCESS = 'access'
ENGINE_PERMISSION_KEY_PERMISSION = 'permission'
ENGINE_PERMISSION_KEY_SECRET = 'secret'


ALL_ASSEMBLED_ENGINE_PERMISSIONS = [
    *gen_permissions(entity='engine', action=ENGINE_PERMISSION_KEY_ENGINE),
    *gen_permissions(entity='engine', action=ENGINE_PERMISSION_KEY_PERMISSION),
    *gen_permissions(entity='engine', action=ENGINE_PERMISSION_KEY_SECRET),
    *gen_permissions(entity='engine', action=ENGINE_PERMISSION_KEY_ACCESS)
]

ALL_AVAILABLE_ENGINE_PERMISSION_STRINGS = [
    f'flow.{perm[0]}' for perm in ALL_ASSEMBLED_ENGINE_PERMISSIONS
]

DEFAULT_PERMISSION_STRINGS_ON_ENGINE_CREATE = ALL_AVAILABLE_ENGINE_PERMISSION_STRINGS


def gen_engine_secret() -> str:
    return get_random_string(length=64)


class Engine(SoftDeleteTenantValidateExternalIdMixin, softdelete.SoftDeletionTenantModel):
    id = fields.id_field()
    tenant = ForeignKey(get_tenant_model(), on_delete=DO_NOTHING)
    external_id = fields.external_id_field_url_safe()
    upstream = URLField(max_length=256, null=False, validators=[URLValidator(schemes=['https', 'http'])])
    secret = TextField(null=False, blank=False, default=gen_engine_secret, validators=[validate_password])

    all_objects: softdelete.SoftDeletionManager = softdelete.SoftDeletionTenantManager(alive_only=False)  # type: ignore
    objects: softdelete.SoftDeletionManager = SoftDeletionTenantManager()  # type: ignore

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.secret is None or len(self.secret) == 0:
            self.secret = gen_engine_secret()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f'Engine "{self.external_id}" ({str(self.upstream)})'

    @staticmethod
    def _qs(request: Union[Request, HttpRequest], action: str, method: Optional[str] = None) -> 'QuerySet[Engine]':
        _method = method
        if _method is None:
            _method = request.method
        return get_objects_for_user_custom(
            request.user,
            [
                get_permission_string_for_action_and_http_verb(
                    entity='engine',
                    action=ENGINE_PERMISSION_KEY_ENGINE,
                    http_verb='GET'
                ),
                get_permission_string_for_action_and_http_verb(
                    entity='engine',
                    action=action,
                    http_verb=_method
                )
            ],
            Engine.objects.all(),
            True,
            app_label='flow'
        )

    class Meta:
        db_table = f'_4_engine'.lower()
        constraints = [
            UniqueConstraint(fields=['tenant_id', 'external_id'],
                             name=f'_4_engine_tenant_id_external_id__1',
                             condition=Q(deleted_at__isnull=True))
        ]
        permissions = ALL_ASSEMBLED_ENGINE_PERMISSIONS
