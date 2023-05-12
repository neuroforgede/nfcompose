# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from django.contrib.auth.models import User
from rest_framework import status
from typing import Any, Dict, List, Union, cast

from skipper import modules
from skipper.core.models.tenant import Tenant, Tenant_User
from skipper.core.tests.base import BASE_URL
from skipper.core.tests.base.object_level_permission import BaseObjectLevelPermissionAssignmentTest
from skipper.dataseries.models import PERMISSION_HTTP_VERBS, \
    DATASERIES_PERMISSION_KEY_PERMISSION, DATASERIES_PERMISSION_KEY_DATA_POINT, \
    DATASERIES_PERMISSION_KEY_DATA_SERIES, read_only_permissions, \
    get_permission_string_for_action_and_http_verb

DATA_SERIES_BASE_URL = BASE_URL + modules.url_representation(modules.Module.DATA_SERIES) + '/'


class DataSeriesObjectLevelPermissionAssignmentTest(BaseObjectLevelPermissionAssignmentTest):
    def create_assignment_object(self) -> Dict[str, Any]:  # type: ignore
        return cast(Dict[str, Any], self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': 'my_data_series_1',
            'external_id': 'external_id1'
        }, simulate_tenant=False))

    # ------------------------------------------------------------------------------------------------------------------

    def get_permissions_on_assigner_minimum(self) -> List[str]:
        return list({
            *read_only_permissions([DATASERIES_PERMISSION_KEY_DATA_SERIES]),
            get_permission_string_for_action_and_http_verb(http_verb='PUT', action=DATASERIES_PERMISSION_KEY_PERMISSION)
        })

    def get_permissions_to_assign(self) -> List[str]:
        return [
            get_permission_string_for_action_and_http_verb(
                http_verb=method, action=DATASERIES_PERMISSION_KEY_DATA_POINT
            ) 
            for method in PERMISSION_HTTP_VERBS
        ]


class DataSeriesTenantManagerObjectLevelPermissionAssignmentTest(BaseObjectLevelPermissionAssignmentTest):
    def create_assigner_user_tenant_relation(self, user: User, tenant: Tenant) -> Union[Tenant_User, None]:
        return Tenant_User.objects.create(
            tenant=tenant,
            user=user,
            tenant_manager=True
        )
 
    def create_assignment_object(self) -> Dict[str, Any]:  # type: ignore
        return cast(Dict[str, Any], self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': 'my_data_series_1',
            'external_id': 'external_id1'
        }, simulate_tenant=False))

    # ------------------------------------------------------------------------------------------------------------------

    def get_permissions_on_assigner_minimum(self) -> List[str]:
        return list({
            *read_only_permissions([DATASERIES_PERMISSION_KEY_DATA_SERIES]),
            get_permission_string_for_action_and_http_verb(http_verb='PUT', action=DATASERIES_PERMISSION_KEY_PERMISSION)
        })

    def get_permissions_to_assign(self) -> List[str]:
        return [
            get_permission_string_for_action_and_http_verb(
                http_verb=method, action=DATASERIES_PERMISSION_KEY_DATA_POINT
            ) 
            for method in PERMISSION_HTTP_VERBS
        ]
        
    def get_outcome_before_assigner_perm_assignment(self) -> int:
        return status.HTTP_200_OK

