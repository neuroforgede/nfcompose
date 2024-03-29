# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

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


class CoreUserDetailPermissionBaseTest(BaseRESTPermissionTest):
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
                'groups': [],
                'is_active': True
            },
            simulate_tenant=False
        )


class CoreUserDetailPermissionGETTest(CoreUserDetailPermissionBaseTest):

    def permission_code_name(self) -> str:
        return core_permission_for_rest_method('user', 'GET', 'user')

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return None

    def malformed_with_permission_status(self) -> int:
        raise NotImplementedError()

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return cast(TestHttpResponse, self.user_client.get(
            path=self.user_dict['url']
        ))


class CoreUserDetailPermissionHEADTest(CoreUserDetailPermissionBaseTest):

    def permission_code_name(self) -> str:
        return core_permission_for_rest_method('user', 'HEAD', 'user')

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return None

    def malformed_with_permission_status(self) -> int:
        raise NotImplementedError()

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.head(
            path=self.user_dict['url'],
            format='json',
        )


class CoreUserDetailPermissionPOSTTest(CoreUserDetailPermissionBaseTest):

    def permission_code_name(self) -> str:
        return core_permission_for_rest_method('user', 'POST', 'user')

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return self.user_client.post(
            path=self.user_dict['url'],
            data={'naaaaaaame': 'test_tenant2'},
            format='json',
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def proper_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.post(
            path=self.user_dict['url'],
            format='json',
            data=self.user_dict
        )


class CoreUserDetailPermissionOPTIONSTest(CoreUserDetailPermissionBaseTest):

    def permission_code_name(self) -> str:
        return core_permission_for_rest_method('user', 'OPTIONS', 'user')

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return None

    def malformed_with_permission_status(self) -> int:
        raise NotImplementedError()

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.options(
            path=self.user_dict['url']
        )


class CoreUserDetailPermissionPUTTest(CoreUserDetailPermissionBaseTest):

    def permission_code_name(self) -> str:
        return core_permission_for_rest_method('user', 'PUT', 'user')

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return self.user_client.put(
            path=self.user_dict['url'],
            format='json',
            data=self.user_dict
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_400_BAD_REQUEST

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.put(
            path=self.user_dict['url'],
            format='json',
            data={
                **self.user_dict,
                'password': 'skdfjlkashjdgiophqaiupohgr'
            }
        )


class CoreUserDetailPermissionPATCHTest(CoreUserDetailPermissionBaseTest):

    def permission_code_name(self) -> str:
        return core_permission_for_rest_method('user', 'PATCH', 'user')

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return self.user_client.patch(
            path=self.user_dict['url'],
            format='json',
            data={'password': []}
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_400_BAD_REQUEST

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.patch(
            path=self.user_dict['url'],
            format='json',
            data=self.user_dict
        )


class CoreUserDetailPermissionDELETETest(CoreUserDetailPermissionBaseTest):

    def permission_code_name(self) -> str:
        return core_permission_for_rest_method('user', 'DELETE', 'user')

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return None

    def malformed_with_permission_status(self) -> int:
        raise NotImplementedError()

    def proper_with_permission_status(self) -> int:
        return status.HTTP_204_NO_CONTENT

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.delete(
            path=self.user_dict['url']
        )


del CoreUserDetailPermissionBaseTest