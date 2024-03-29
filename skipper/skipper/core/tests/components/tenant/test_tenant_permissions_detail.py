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

TENANT_LIST_URL = BASE_URL + 'core/tenant/'


class TenantDetailPermissionBaseTest(BaseRESTPermissionTest):
    """
    rudimentarily tests whether the given methods are allowed to be run
    against the dataseries detail endpoints
    """

    skip_setup_assertions: bool = True

    tenant_json: Dict[str, Any]

    simulate_other_tenant = False

    def create_tenant(self) -> None:
        self.tenant_json = self.create_payload(
            url=TENANT_LIST_URL,
            payload={'name': 'test_tenant'},
            simulate_tenant=False
        )

    def base_add_bare_user(self) -> None:
        self.create_tenant()


class TenantDetailPermissionGETTest(TenantDetailPermissionBaseTest):
    
    permission_code_prefix = 'core'

    def permission_code_name(self) -> str:
        return core_permission_for_rest_method('tenant', 'GET', 'tenant')

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return None

    def malformed_with_permission_status(self) -> int:
        raise NotImplementedError()

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return cast(TestHttpResponse, self.user_client.get(
            path=self.tenant_json['url']
        ))


class TenantDetailPermissionHEADTest(TenantDetailPermissionBaseTest):
    
    permission_code_prefix = 'core'

    def permission_code_name(self) -> str:
        return core_permission_for_rest_method('tenant', 'HEAD', 'tenant')

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return None

    def malformed_with_permission_status(self) -> int:
        raise NotImplementedError()

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.head(
            path=self.tenant_json['url']
        )


class TenantDetailPermissionPOSTTest(TenantDetailPermissionBaseTest):
    
    permission_code_prefix = 'core'

    def permission_code_name(self) -> str:
        return core_permission_for_rest_method('tenant', 'POST', 'tenant')

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return self.user_client.post(
            path=self.tenant_json['url'],
            data={'naaaaaaame': 'test_tenant2'}
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def proper_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.post(
            path=self.tenant_json['url'],
            data={'name': 'test_tenant2'}
        )


class TenantDetailPermissionOPTIONSTest(TenantDetailPermissionBaseTest):
    
    permission_code_prefix = 'core'

    def permission_code_name(self) -> str:
        return core_permission_for_rest_method('tenant', 'OPTIONS', 'tenant')

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return None

    def malformed_with_permission_status(self) -> int:
        raise NotImplementedError()

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.options(
            path=self.tenant_json['url']
        )


class TenantDetailPermissionPUTTest(TenantDetailPermissionBaseTest):
    
    permission_code_prefix = 'core'

    def permission_code_name(self) -> str:
        return core_permission_for_rest_method('tenant', 'PUT', 'tenant')

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return self.user_client.put(
            path=self.tenant_json['url'],
            data={'naaaaaaame': 'test_tenant'}
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_400_BAD_REQUEST

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.put(
            path=self.tenant_json['url'],
            data={'name': 'test_tenant'}
        )


class TenantDetailPermissionPATCHTest(TenantDetailPermissionBaseTest):
    
    permission_code_prefix = 'core'

    def permission_code_name(self) -> str:
        return core_permission_for_rest_method('tenant', 'PATCH', 'tenant')

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return None

    def malformed_with_permission_status(self) -> int:
        raise NotImplementedError()

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.patch(
            path=self.tenant_json['url'],
            data={}
        )


class TenantDetailPermissionDELETETest(TenantDetailPermissionBaseTest):
    
    permission_code_prefix = 'core'

    def permission_code_name(self) -> str:
        return core_permission_for_rest_method('tenant', 'DELETE', 'tenant')

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return None

    def malformed_with_permission_status(self) -> int:
        raise NotImplementedError()

    def proper_with_permission_status(self) -> int:
        return status.HTTP_204_NO_CONTENT

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.delete(
            path=self.tenant_json['url']
        )


del TenantDetailPermissionBaseTest