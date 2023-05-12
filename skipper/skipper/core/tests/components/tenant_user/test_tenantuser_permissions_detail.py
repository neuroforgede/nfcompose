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

TENANT_LIST_URL = BASE_URL + 'core/tenant/'
USER_LIST_URL = BASE_URL + 'core/user/'


class CoreTenantUserDetailPermissionBaseTest(BaseRESTPermissionTest):
    """
    rudimentarily tests whether the given methods are allowed to be run
    against the core/tenant/*/user detail endpoints
    """

    skip_setup_assertions: bool = True

    permission_code_prefix = 'core'

    simulate_other_tenant = False

    tenant_dict: Dict[str, Any]
    extra_user_dict: Dict[str, Any]
    tenant_user_dict: Dict[str, Any]

    def base_add_bare_user(self) -> None:
        self.tenant_dict = self.create_payload(
            url=TENANT_LIST_URL,
            payload={
                'name': 'test_tenant'
            },
            simulate_tenant=False
        )
        self.extra_user_dict = self.create_payload(
            url=USER_LIST_URL,
            payload={
                'username': 'extra_user',
                'password': 'lkshddsadsffjkghjashgoi4ewrpbn',
                'email': 'extra_user@neuroforge.de',
                'groups': [],
                'is_active': True
            },
            simulate_tenant=False
        )
        self.tenant_user_dict = self.create_payload(
            url=self.tenant_dict['user'],
            format='json',
            payload={
                'user': self.extra_user_dict['url'],
                'tenant_manager': False,
                'system': False
            }
        )


class CoreTenantUserListPermissionGETTest(CoreTenantUserDetailPermissionBaseTest):

    def permission_code_name(self) -> str:
        return core_permission_for_rest_method('tenant', 'GET', 'tenant-user')

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return None

    def malformed_with_permission_status(self) -> int:
        raise NotImplementedError()

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return cast(TestHttpResponse, self.user_client.get(
            path=self.tenant_user_dict['url']
        ))


class CoreTenantUserListPermissionHEADTest(CoreTenantUserDetailPermissionBaseTest):

    def permission_code_name(self) -> str:
        return core_permission_for_rest_method('tenant', 'HEAD', 'tenant-user')

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return None

    def malformed_with_permission_status(self) -> int:
        raise NotImplementedError()

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.head(
            path=self.tenant_user_dict['url'],
            format='json',
        )


class CoreTenantUserListPermissionPOSTTest(CoreTenantUserDetailPermissionBaseTest):

    def permission_code_name(self) -> str:
        return core_permission_for_rest_method('tenant', 'POST', 'tenant-user')

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return None

    def malformed_with_permission_status(self) -> int:
        raise NotImplementedError()

    def proper_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.post(
            path=self.tenant_user_dict['url'],
            format='json',
            data={
                'user': self.extra_user_dict['url'],
                'tenant_manager': False,
                'system': False
            }
        )


class CoreTenantUserListPermissionOPTIONSTest(CoreTenantUserDetailPermissionBaseTest):

    def permission_code_name(self) -> str:
        return core_permission_for_rest_method('tenant', 'OPTIONS', 'tenant-user')

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return None

    def malformed_with_permission_status(self) -> int:
        raise NotImplementedError()

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.options(
            path=self.tenant_user_dict['url']
        )


class CoreTenantUserListPermissionPUTTest(CoreTenantUserDetailPermissionBaseTest):

    def permission_code_name(self) -> str:
        return core_permission_for_rest_method('tenant', 'PUT', 'tenant-user')

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return self.user_client.put(
            path=self.tenant_user_dict['url'],
            format='json',
            data={'user':'https://www.google.com/'}
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_400_BAD_REQUEST

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.put(
            path=self.tenant_user_dict['url'],
            format='json',
            data=self.tenant_user_dict
        )


class CoreTenantUserListPermissionPATCHTest(CoreTenantUserDetailPermissionBaseTest):

    def permission_code_name(self) -> str:
        return core_permission_for_rest_method('tenant', 'PATCH', 'tenant-user')

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return self.user_client.patch(
            path=self.tenant_user_dict['url'],
            format='json',
            data={'user':'https://www.google.com/'}
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_400_BAD_REQUEST

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.patch(
            path=self.tenant_user_dict['url'],
            format='json',
            data=self.tenant_user_dict
        )


class CoreTenantUserListPermissionDELETETest(CoreTenantUserDetailPermissionBaseTest):

    def permission_code_name(self) -> str:
        return core_permission_for_rest_method('tenant', 'DELETE', 'tenant-user')

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return None

    def malformed_with_permission_status(self) -> int:
        raise NotImplementedError()

    def proper_with_permission_status(self) -> int:
        return status.HTTP_204_NO_CONTENT

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.delete(
            path=self.tenant_user_dict['url']
        )


del CoreTenantUserDetailPermissionBaseTest