# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


from django.contrib.auth.models import User
from rest_framework import status
from typing import Any, Dict, List, Union, cast

from skipper import modules
from skipper.core.models.tenant import Tenant, Tenant_User
from skipper.core.tests.base import BASE_URL
from skipper.core.tests.base.object_level_permission import BaseObjectLevelPermissionAssignmentTest
from skipper.flow.models import PERMISSION_HTTP_VERBS, \
    HTTP_ENDPOINT_PERMISSION_KEY_HTTP_ENDPOINT, \
    HTTP_ENDPOINT_PERMISSION_KEY_PERMISSION, read_only_permissions, \
    get_permission_string_for_action_and_http_verb

FLOW_BASE_URL = BASE_URL + modules.url_representation(modules.Module.FLOW) + '/'


class HttpEndpointObjectLevelPermissionAssignmentTest(BaseObjectLevelPermissionAssignmentTest):
    def create_assignment_object(self) -> Dict[str, Any]:
        engine = self.create_payload(FLOW_BASE_URL + 'engine/', payload={
            'external_id': 'some_id_i_guess',
            'upstream': 'http://localhost:1245/cute_cat.gif'
        }, simulate_tenant=False)   # type: ignore
        return cast(Dict[str, Any], self.create_payload(FLOW_BASE_URL + 'httpendpoint/', payload={
            'engine': engine['url'],
            'external_id': 'some_id_i_guess_2',
            'path': '/endpoint_yo',
            'method': 'GET',
            'public': False
        }, simulate_tenant=False))

    # ------------------------------------------------------------------------------------------------------------------

    def get_permissions_on_assigner_minimum(self) -> List[str]:
        return list({
            *read_only_permissions('http_endpoint', [HTTP_ENDPOINT_PERMISSION_KEY_HTTP_ENDPOINT]),
            get_permission_string_for_action_and_http_verb(
                http_verb='PUT', action=HTTP_ENDPOINT_PERMISSION_KEY_PERMISSION, entity='http_endpoint'
            )
        })

    def get_permissions_to_assign(self) -> List[str]:
        return [
            get_permission_string_for_action_and_http_verb(
                http_verb=method, action=HTTP_ENDPOINT_PERMISSION_KEY_PERMISSION, entity='http_endpoint'
            ) 
            for method in PERMISSION_HTTP_VERBS
        ]


class HttpEndpointTenantManagerObjectLevelPermissionAssignmentTest(BaseObjectLevelPermissionAssignmentTest):
    def create_assigner_user_tenant_relation(self, user: User, tenant: Tenant) -> Union[Tenant_User, None]:
        return Tenant_User.objects.create(
            tenant=tenant,
            user=user,
            tenant_manager=True
        )

    def create_assignment_object(self) -> Dict[str, Any]:
        engine = self.create_payload(FLOW_BASE_URL + 'engine/', payload={
            'external_id': 'some_id_i_guess',
            'upstream': 'http://localhost:1245/cute_cat.gif'
        }, simulate_tenant=False)   # type: ignore
        return cast(Dict[str, Any], self.create_payload(FLOW_BASE_URL + 'httpendpoint/', payload={
            'engine': engine['url'],
            'external_id': 'some_id_i_guess_2',
            'path': '/endpoint_yo',
            'method': 'GET',
            'public': False
        }, simulate_tenant=False))

    # ------------------------------------------------------------------------------------------------------------------

    def get_permissions_on_assigner_minimum(self) -> List[str]:
        return list({
            *read_only_permissions('http_endpoint', [HTTP_ENDPOINT_PERMISSION_KEY_HTTP_ENDPOINT]),
            get_permission_string_for_action_and_http_verb(
                http_verb='PUT', action=HTTP_ENDPOINT_PERMISSION_KEY_PERMISSION, entity='http_endpoint'
            )
        })

    def get_permissions_to_assign(self) -> List[str]:
        return [
            get_permission_string_for_action_and_http_verb(
                http_verb=method, action=HTTP_ENDPOINT_PERMISSION_KEY_PERMISSION, entity='http_endpoint'
            ) 
            for method in PERMISSION_HTTP_VERBS
        ]
        
    def get_outcome_before_assigner_perm_assignment(self) -> int:
        return status.HTTP_200_OK
