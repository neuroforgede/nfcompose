# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from typing import Any, Optional, Union, List

from skipper import modules
from skipper.core.models.tenant import Tenant
from skipper.core.tests.base import BASE_URL
from skipper.core.tests.base.permission import BasePermissionAssignmentTest
from skipper.flow.models import ENGINE_PERMISSION_KEY_PERMISSION, Engine, \
    ENGINE_PERMISSION_KEY_ENGINE, ALL_AVAILABLE_ENGINE_PERMISSION_STRINGS, \
    get_permission_string_for_action_and_http_verb


ENGINE_BASE_URL = BASE_URL + modules.url_representation(modules.Module.FLOW) + '/engine/'

url_under_test = ENGINE_BASE_URL


class EnginePermissionAssignmentTest(BasePermissionAssignmentTest):
    def possible_permissions(self) -> List[str]:
        return ALL_AVAILABLE_ENGINE_PERMISSION_STRINGS

    def baseline_permissions_to_see_object(self) -> List[str]:
        return [
            get_permission_string_for_action_and_http_verb('engine', ENGINE_PERMISSION_KEY_ENGINE, 'GET')
        ]

    def baseline_permissions_to_assign_permissions(self) -> List[str]:
        return [
            get_permission_string_for_action_and_http_verb('engine', ENGINE_PERMISSION_KEY_ENGINE, 'GET'),
            get_permission_string_for_action_and_http_verb('engine', ENGINE_PERMISSION_KEY_PERMISSION, 'PUT')
        ]

    def permission_modification_string(self, method: str) -> str:
        return get_permission_string_for_action_and_http_verb('engine', ENGINE_PERMISSION_KEY_PERMISSION, method)

    def get_user_permission_url(self, object: Any, user_id: Optional[Union[int, str]] = None) -> str:
        if user_id is None:
            return ENGINE_BASE_URL + str(object.id) + '/permission/user/'
        else:
            return ENGINE_BASE_URL + str(object.id) + '/permission/user/' + str(user_id) + '/'

    def get_group_permission_url(self, object: Any, user_id: Optional[Union[int, str]] = None) -> str:
        if user_id is None:
            return ENGINE_BASE_URL + str(object.id) + '/permission/group/'
        else:
            return ENGINE_BASE_URL + str(object.id) + '/permission/group/' + str(user_id) + '/'

    def add_object(self, tenant: Tenant) -> Any:
        return Engine.objects.create(
            tenant=tenant,
            upstream='http://nodered.local/',
            external_id='1'
        )
