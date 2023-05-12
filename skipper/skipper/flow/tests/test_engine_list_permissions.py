# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from typing import Dict, Any, Optional, Type, Union, cast, Any, List

from django.http import HttpResponse
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from django.test.client import _MonkeyPatchedWSGIResponse as TestHttpResponse
else:
    TestHttpResponse = object

from django_multitenant.utils import set_current_tenant  # type: ignore
from rest_framework import status

from skipper import modules
from skipper.core.models.tenant import Tenant
from skipper.core.tests.base import BASE_URL, BaseRESTPermissionTest, \
    BaseObjectLevelPermissionListEndpointTest
from skipper.flow.models import Engine, ENGINE_PERMISSION_KEY_ENGINE, flow_permission_for_rest_method

ENGINE_BASE_URL = BASE_URL + modules.url_representation(modules.Module.FLOW) + '/engine/'

# TODO: move this test into some sort of "base" unit test that can be configured
#  so that we do not have to write this sort of unit test every time


class POSTEngineListPermissionTest(BaseRESTPermissionTest):
    url_under_test = ENGINE_BASE_URL

    permission_code_prefix = 'flow'

    def permission_code_name(self) -> str:
        return flow_permission_for_rest_method(
            entity='engine',
            action=ENGINE_PERMISSION_KEY_ENGINE,
            method='POST'
        )

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return self.user_client.post(
            path=self.url_under_test,
            data={
                "external_id": "123123%!",
                "upstream": "%"
            }
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_400_BAD_REQUEST

    def proper_with_permission_status(self) -> int:
        return status.HTTP_201_CREATED

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.post(
            path=self.url_under_test,
            data={
                "external_id": "1",
                "upstream": "http://nodered.local/"
            }
        )


class ListFilteringDataSeriesRESTPermissionTest(BaseObjectLevelPermissionListEndpointTest):
    permission_code_prefix = 'flow'
    url_under_test = ENGINE_BASE_URL

    def permission_code_name(self) -> str:
        return flow_permission_for_rest_method(
            entity='engine',
            action=ENGINE_PERMISSION_KEY_ENGINE,
            method='GET'
        )

    def create_object(self) -> Any:
        tenant = Tenant.objects.filter(
            name='default_tenant'
        )[0]
        set_current_tenant(tenant)
        return Engine.objects.create(
            external_id='123123',
            upstream='http://nodered.local'
        )

    def get_list(self) -> Union[HttpResponse, TestHttpResponse]:
        return cast(TestHttpResponse, self.user_client.get(
            path=self.url_under_test,
            format='json',
            data={}
        ))

    def extract_data_from_list(self, response: Any) -> List[Dict[str, Any]]:
        return cast(List[Dict[str, Any]], response.json()['results'])


class GETEngineListPermissionTest(BaseRESTPermissionTest):
    url_under_test = ENGINE_BASE_URL

    permission_code_prefix = 'flow'

    def permission_code_name(self) -> str:
        return flow_permission_for_rest_method(
            entity='engine',
            action=ENGINE_PERMISSION_KEY_ENGINE,
            method='GET'
        )

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return cast(TestHttpResponse, self.user_client.get(
            path=self.url_under_test
        ))

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return cast(TestHttpResponse, self.user_client.get(
            path=self.url_under_test
        ))


class OPTIONSEngineListPermissionTest(BaseRESTPermissionTest):
    url_under_test = ENGINE_BASE_URL

    permission_code_prefix = 'flow'

    def permission_code_name(self) -> str:
        return flow_permission_for_rest_method(
            entity='engine',
            action=ENGINE_PERMISSION_KEY_ENGINE,
            method='OPTIONS'
        )

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return self.user_client.options(
            path=self.url_under_test,
            data={}
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.options(
            path=self.url_under_test,
            data={}
        )


class HEADEngineListPermissionTest(BaseRESTPermissionTest):
    url_under_test = ENGINE_BASE_URL

    permission_code_prefix = 'flow'

    def permission_code_name(self) -> str:
        return flow_permission_for_rest_method(
            entity='engine',
            action=ENGINE_PERMISSION_KEY_ENGINE,
            method='HEAD'
        )

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return self.user_client.head(
            path=self.url_under_test,
            data={}
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.head(
            path=self.url_under_test,
            data={}
        )


class DELETEEngineListPermissionTest(BaseRESTPermissionTest):
    url_under_test = ENGINE_BASE_URL

    permission_code_prefix = 'flow'

    def permission_code_name(self) -> str:
        return flow_permission_for_rest_method(
            entity='engine',
            action=ENGINE_PERMISSION_KEY_ENGINE,
            method='DELETE'
        )

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return self.user_client.delete(
            path=self.url_under_test,
            data={}
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def proper_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.delete(
            path=self.url_under_test,
            data={}
        )


class PUTEngineListPermissionTest(BaseRESTPermissionTest):
    url_under_test = ENGINE_BASE_URL

    permission_code_prefix = 'flow'

    def permission_code_name(self) -> str:
        return flow_permission_for_rest_method(
            entity='engine',
            action=ENGINE_PERMISSION_KEY_ENGINE,
            method='PUT'
        )

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return self.user_client.put(
            path=self.url_under_test,
            data={}
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def proper_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.put(
            path=self.url_under_test,
            data={}
        )


class PATCHEngineListPermissionTest(BaseRESTPermissionTest):
    url_under_test = ENGINE_BASE_URL

    permission_code_prefix = 'flow'

    def permission_code_name(self) -> str:
        return flow_permission_for_rest_method(
            entity='engine',
            action=ENGINE_PERMISSION_KEY_ENGINE,
            method='PATCH'
        )

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return self.user_client.patch(
            path=self.url_under_test,
            data={}
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def proper_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.patch(
            path=self.url_under_test,
            data={}
        )
