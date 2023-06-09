# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from typing import Dict, Any, Optional, Type, Union, cast, Any

from django.http import HttpResponse
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from django.test.client import _MonkeyPatchedWSGIResponse as TestHttpResponse
else:
    TestHttpResponse = object

from rest_framework import status

from skipper.core.models.permissions import core_permission_for_rest_method
from skipper.core.tests.base import BASE_URL, BaseRESTPermissionTest

USER_LIST_URL = BASE_URL + 'core/user/'


class CoreUserPermissionPermissionBaseTest(BaseRESTPermissionTest):
    """
    rudimentarily tests whether the given methods are allowed to be run
    against the core user detail endpoints
    """

    skip_setup_assertions: bool = True

    permission_code_prefix = 'core'

    simulate_other_tenant = False

    user_dict: Dict[str, Any]

    def base_add_bare_user(self) -> None:
        self.user_dict = self.create_payload(
            url=USER_LIST_URL,
            payload={
                'username': 'some_test_user',
                'password': 'lkshdfjkghjashgoi4ewrpbn',
                'email': 'some_test_user@neurofoege.de',
                'is_active': True
            },
            simulate_tenant=False
        )


class CoreUserPermissionPermissionGETTest(CoreUserPermissionPermissionBaseTest):

    def permission_code_name(self) -> str:
        return core_permission_for_rest_method('user', 'GET', 'user_permission')

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return None

    def malformed_with_permission_status(self) -> int:
        raise NotImplementedError()

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return cast(TestHttpResponse, self.user_client.get(
            path=self.user_dict['permissions']
        ))


class CoreUserPermissionPermissionHEADTest(CoreUserPermissionPermissionBaseTest):

    def permission_code_name(self) -> str:
        return core_permission_for_rest_method('user', 'HEAD', 'user_permission')

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return None

    def malformed_with_permission_status(self) -> int:
        raise NotImplementedError()

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.head(
            path=self.user_dict['permissions'],
            format='json',
        )


class CoreUserPermissionPermissionPOSTTest(CoreUserPermissionPermissionBaseTest):

    def permission_code_name(self) -> str:
        return core_permission_for_rest_method('user', 'POST', 'user_permission')

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return None

    def malformed_with_permission_status(self) -> int:
        raise NotImplementedError()

    def proper_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.post(
            path=self.user_dict['permissions'],
            format='json',
            data={
                "user_permissions": []
            }
        )


class CoreUserPermissionPermissionOPTIONSTest(CoreUserPermissionPermissionBaseTest):

    def permission_code_name(self) -> str:
        return core_permission_for_rest_method('user', 'OPTIONS', 'user_permission')

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return None

    def malformed_with_permission_status(self) -> int:
        raise NotImplementedError()

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.options(
            path=self.user_dict['permissions']
        )


class CoreUserPermissionPermissionPUTTest(CoreUserPermissionPermissionBaseTest):

    def permission_code_name(self) -> str:
        return core_permission_for_rest_method('user', 'PUT', 'user_permission')

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return self.user_client.put(
            path=self.user_dict['permissions'],
            format='json',
            data={
                "usero_permissiones": []
            }
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_400_BAD_REQUEST

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.put(
            path=self.user_dict['permissions'],
            format='json',
            data={
                "user_permissions": []
            }
        )


class CoreUserPermissionPermissionPATCHTest(CoreUserPermissionPermissionBaseTest):

    def permission_code_name(self) -> str:
        return core_permission_for_rest_method('user', 'PATCH', 'user_permission')

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return None

    def malformed_with_permission_status(self) -> int:
        raise NotImplementedError()

    def proper_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.patch(
            path=self.user_dict['permissions'],
            format='json',
            data={
                "user_permissions": []
            }
        )


class CoreUserPermissionPermissionDELETETest(CoreUserPermissionPermissionBaseTest):

    def permission_code_name(self) -> str:
        return core_permission_for_rest_method('user', 'DELETE', 'user_permission')

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return None

    def malformed_with_permission_status(self) -> int:
        raise NotImplementedError()

    def proper_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.delete(
            path=self.user_dict['permissions']
        )


del CoreUserPermissionPermissionBaseTest