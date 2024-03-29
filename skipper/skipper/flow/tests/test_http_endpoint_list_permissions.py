# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from typing import Dict, Any, Optional, Union, cast, Any, List

from django.http import HttpResponse
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from django.test.client import _MonkeyPatchedWSGIResponse as TestHttpResponse
else:
    TestHttpResponse = object

from django.contrib.auth.models import User
from django_multitenant.utils import set_current_tenant  # type: ignore
from guardian.shortcuts import assign_perm  # type: ignore
from rest_framework import status

from skipper import modules
from skipper.core.models.tenant import Tenant
from skipper.core.tests.base import BASE_URL, BaseRESTPermissionTest, \
    BaseObjectLevelPermissionListEndpointTest
from skipper.flow.models import flow_permission_for_rest_method, \
    HTTP_ENDPOINT_PERMISSION_KEY_HTTP_ENDPOINT, HttpEndpoint, Engine, ALL_AVAILABLE_ENGINE_PERMISSION_STRINGS
from skipper.flow.tests.test_http_endpoint_crud import ENGINE_ENDPOINT_BASE_URL

ENGINE_BASE_URL = BASE_URL + modules.url_representation(modules.Module.FLOW) + '/httpendpoint/'


class POSTHttpEndpointListPermissionTest(BaseRESTPermissionTest):
    url_under_test = ENGINE_BASE_URL

    permission_code_prefix = 'flow'

    engine_json: Dict[str, Any]

    def base_add_bare_user(self) -> None:
        super().base_add_bare_user()
        user = User.objects.get(username='test_user')
        for elem in ALL_AVAILABLE_ENGINE_PERMISSION_STRINGS:
            assign_perm(elem, user)

        self.user_client.force_login(user)
        self.engine_json = self.user_client.post(path=ENGINE_ENDPOINT_BASE_URL, data={
            "external_id": "1",
            "upstream": "http://hans.peter.local/"
        }).json()

    def permission_code_name(self) -> str:
        return flow_permission_for_rest_method(
            entity='http_endpoint',
            action=HTTP_ENDPOINT_PERMISSION_KEY_HTTP_ENDPOINT,
            method='POST'
        )

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return self.user_client.post(
            path=self.url_under_test,
            data={
                "engine": self.engine_json['url'],
                "external_id": "1%1",
                "path": "/",
                "method": 'GET',
                "public": False
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
                "engine": self.engine_json['url'],
                "external_id": "11",
                "path": "/",
                "method": 'GET',
                "public": False
            }
        )


class ListFilteringDataSeriesRESTPermissionTest(BaseObjectLevelPermissionListEndpointTest):
    permission_code_prefix = 'flow'
    url_under_test = ENGINE_BASE_URL

    def permission_code_name(self) -> str:
        return flow_permission_for_rest_method(
            entity='http_endpoint',
            action=HTTP_ENDPOINT_PERMISSION_KEY_HTTP_ENDPOINT,
            method='GET'
        )

    def create_object(self) -> Any:
        tenant = Tenant.objects.filter(
            name='default_tenant'
        )[0]
        set_current_tenant(tenant)
        engine = Engine.objects.create(
            external_id="1",
            upstream="http://hans.peter.local/",
            secret='my_secret'
        )
        return HttpEndpoint.objects.create(
            engine=engine,
            external_id="11",
            path="/",
            method='GET',
            public=False,
            system=False
        )

    def get_list(self) -> Union[HttpResponse, TestHttpResponse]:
        return cast(TestHttpResponse, self.user_client.get(
            path=self.url_under_test,
            format='json',
            data={}
        ))

    def extract_data_from_list(self, response: Any) -> List[Dict[str, Any]]:
        return cast(List[Dict[str, Any]], response.json()['results'])


class GETHttpEndpointListPermissionTest(BaseRESTPermissionTest):
    url_under_test = ENGINE_BASE_URL

    permission_code_prefix = 'flow'

    def permission_code_name(self) -> str:
        return flow_permission_for_rest_method(
            entity='http_endpoint',
            action=HTTP_ENDPOINT_PERMISSION_KEY_HTTP_ENDPOINT,
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

class OPTIONSHttpEndpointListPermissionTest(BaseRESTPermissionTest):
    url_under_test = ENGINE_BASE_URL

    permission_code_prefix = 'flow'

    def permission_code_name(self) -> str:
        return flow_permission_for_rest_method(
            entity='http_endpoint',
            action=HTTP_ENDPOINT_PERMISSION_KEY_HTTP_ENDPOINT,
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


class HEADHttpEndpointListPermissionTest(BaseRESTPermissionTest):
    url_under_test = ENGINE_BASE_URL

    permission_code_prefix = 'flow'

    def permission_code_name(self) -> str:
        return flow_permission_for_rest_method(
            entity='http_endpoint',
            action=HTTP_ENDPOINT_PERMISSION_KEY_HTTP_ENDPOINT,
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


class DELETEHttpEndpointListPermissionTest(BaseRESTPermissionTest):
    url_under_test = ENGINE_BASE_URL

    permission_code_prefix = 'flow'

    def permission_code_name(self) -> str:
        return flow_permission_for_rest_method(
            entity='http_endpoint',
            action=HTTP_ENDPOINT_PERMISSION_KEY_HTTP_ENDPOINT,
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


class PUTHttpEndpointListPermissionTest(BaseRESTPermissionTest):
    url_under_test = ENGINE_BASE_URL

    permission_code_prefix = 'flow'

    def permission_code_name(self) -> str:
        return flow_permission_for_rest_method(
            entity='http_endpoint',
            action=HTTP_ENDPOINT_PERMISSION_KEY_HTTP_ENDPOINT,
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


class PATCHHttpEndpointListPermissionTest(BaseRESTPermissionTest):
    url_under_test = ENGINE_BASE_URL

    permission_code_prefix = 'flow'

    def permission_code_name(self) -> str:
        return flow_permission_for_rest_method(
            entity='http_endpoint',
            action=HTTP_ENDPOINT_PERMISSION_KEY_HTTP_ENDPOINT,
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
