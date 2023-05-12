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


class TenantListGETTest(BaseRESTPermissionTest):
    url_under_test = BASE_URL + 'core/user/'

    skip_setup_assertions: bool = True

    permission_code_prefix = 'core'

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
            path=self.url_under_test
        ))


class TenantListHEADTest(BaseRESTPermissionTest):
    url_under_test = BASE_URL + 'core/user/'

    skip_setup_assertions: bool = True

    permission_code_prefix = 'core'

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
            path=self.url_under_test
        )


class TenantListOPTIONSTest(BaseRESTPermissionTest):
    url_under_test = BASE_URL + 'core/user/'

    skip_setup_assertions: bool = True

    permission_code_prefix = 'core'

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
            path=self.url_under_test
        )


class TenantListPOSTTest(BaseRESTPermissionTest):
    url_under_test = BASE_URL + 'core/user/'

    skip_setup_assertions: bool = True

    permission_code_prefix = 'core'

    def permission_code_name(self) -> str:
        return core_permission_for_rest_method('user', 'POST', 'user')

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return self.user_client.post(
            path=self.url_under_test,
            data={
                "namae_wa": "testuser123"
            },
            format='json'
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_400_BAD_REQUEST

    def proper_with_permission_status(self) -> int:
        return status.HTTP_201_CREATED

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.post(
            path=self.url_under_test,
            data={
                'username': 'test_user',
                'password': 'lkshdfjkghjashgoi4ewrpbn',
                'email': 'test_user@neurofoege.de',
                'groups': [],
                'is_active': True
            },
            format='json'
        )


class TenantListPUTTest(BaseRESTPermissionTest):
    url_under_test = BASE_URL + 'core/user/'

    skip_setup_assertions: bool = True

    permission_code_prefix = 'core'

    def permission_code_name(self) -> str:
        return core_permission_for_rest_method('user', 'PUT', 'user')

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return None

    def malformed_with_permission_status(self) -> int:
        raise NotImplementedError()

    def proper_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.put(
            path=self.url_under_test,
            data={},
            format='json'
        )


class TenantListPATCHTest(BaseRESTPermissionTest):
    url_under_test = BASE_URL + 'core/user/'

    skip_setup_assertions: bool = True

    permission_code_prefix = 'core'

    def permission_code_name(self) -> str:
        return core_permission_for_rest_method('user', 'PATCH', 'user')

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return None

    def malformed_with_permission_status(self) -> int:
        raise NotImplementedError()

    def proper_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.patch(
            path=self.url_under_test,
            data={},
            format='json'
        )


class TenantListDELETETest(BaseRESTPermissionTest):
    url_under_test = BASE_URL + 'core/user/'

    skip_setup_assertions: bool = True

    permission_code_prefix = 'core'

    def permission_code_name(self) -> str:
        return core_permission_for_rest_method('user', 'DELETE', 'user')

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return None

    def malformed_with_permission_status(self) -> int:
        raise NotImplementedError()

    def proper_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.delete(
            path=self.url_under_test
        )
