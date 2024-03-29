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

from django.db import transaction
from django.db.models import Model
from guardian.shortcuts import assign_perm  # type: ignore
from rest_framework import status

from skipper import modules
from skipper.core.tests.base import BASE_URL
from skipper.core.tests.base.regular_detail_permission import BaseModelDetailPermissionTest
from skipper.flow.models import Engine, HttpEndpoint, flow_permission_for_rest_method, \
    HTTP_ENDPOINT_PERMISSION_KEY_HTTP_ENDPOINT, ALL_AVAILABLE_ENGINE_PERMISSION_STRINGS

ENGINE_ENDPOINT_BASE_URL = BASE_URL + modules.url_representation(modules.Module.FLOW) + '/engine/'
HTTP_ENDPOINT_BASE_URL = BASE_URL + modules.url_representation(modules.Module.FLOW) + '/httpendpoint/'


class BaseHttpEndpointDetailPermissionTest(BaseModelDetailPermissionTest):
    url_under_test = HTTP_ENDPOINT_BASE_URL

    permission_code_prefix = 'flow'

    skip_setup_assertions: bool = True

    obj_json: Dict[str, Any]
    engine_json: Dict[str, Any]
    model_type: Type[Model] = HttpEndpoint

    permission_key = HTTP_ENDPOINT_PERMISSION_KEY_HTTP_ENDPOINT

    base_class_name = 'BaseHttpEndpointDetailPermissionTest'

    def create_obj_via_rest(self) -> None:
        self.engine_json = self.create_payload(ENGINE_ENDPOINT_BASE_URL, payload={
            'external_id': 'external_id1',
            'upstream': 'http://nodered.local/'
        }, simulate_tenant=False)
        for elem in ALL_AVAILABLE_ENGINE_PERMISSION_STRINGS:
            assign_perm(elem, self.test_user, obj=Engine.objects.get(external_id='external_id1'))
            assign_perm(elem, self.test_user)

        self.obj_json = self.create_payload(self.url_under_test, payload={
            "engine": self.engine_json['url'],
            "external_id": '1',
            "path": "/",
            "method": 'GET',
            "public": True
        }, simulate_tenant=False)

    def read_permission(self) -> str:
        return flow_permission_for_rest_method(
            entity='http_endpoint',
            action=self.permission_key,
            method='GET'
        )


class GETEngineDetailPermissionTest(BaseHttpEndpointDetailPermissionTest):

    def permission_code_name(self) -> str:
        return flow_permission_for_rest_method(
            entity='http_endpoint',
            action=HTTP_ENDPOINT_PERMISSION_KEY_HTTP_ENDPOINT,
            method='GET'
        )

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return cast(TestHttpResponse, self.user_client.get(
            path=self.obj_json['url']
        ))

    def _extra_add_base_permission(self) -> None:
        # noop
        pass

    def _extra_remove_base_perms(self) -> None:
        # noop
        pass

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return cast(TestHttpResponse, self.user_client.get(
            path=self.obj_json['url']
        ))


class POSTEngineDetailPermissionTest(BaseHttpEndpointDetailPermissionTest):

    def permission_code_name(self) -> str:
        return flow_permission_for_rest_method(
            entity='http_endpoint',
            action=HTTP_ENDPOINT_PERMISSION_KEY_HTTP_ENDPOINT,
            method='POST'
        )

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return self.user_client.post(
            path=self.obj_json['url'],
            data={
                "engine": self.engine_json['url'],
                "external_id": '1',
                "path": "/",
                "method": 'GET',
                "public": True
            }
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def proper_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.post(
            path=self.obj_json['url'],
            data={
                "engine": self.engine_json['url'],
                "external_id": '1',
                "path": "/",
                "method": 'GET',
                "public": True
            }
        )


class OPTIONSEngineDetailPermissionTest(BaseHttpEndpointDetailPermissionTest):

    def permission_code_name(self) -> str:
        return flow_permission_for_rest_method(
            entity='http_endpoint',
            action=HTTP_ENDPOINT_PERMISSION_KEY_HTTP_ENDPOINT,
            method='OPTIONS'
        )

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return self.user_client.options(
            path=self.obj_json['url']
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.options(
            path=self.obj_json['url']
        )


class HEADEngineDetailPermissionTest(BaseHttpEndpointDetailPermissionTest):

    def permission_code_name(self) -> str:
        return flow_permission_for_rest_method(
            entity='http_endpoint',
            action=HTTP_ENDPOINT_PERMISSION_KEY_HTTP_ENDPOINT,
            method='HEAD'
        )

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return self.user_client.head(
            path=self.obj_json['url']
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.head(
            path=self.obj_json['url']
        )


class DELETEEngineDetailPermissionTest(BaseHttpEndpointDetailPermissionTest):

    def permission_code_name(self) -> str:
        return flow_permission_for_rest_method(
            entity='http_endpoint',
            action=HTTP_ENDPOINT_PERMISSION_KEY_HTTP_ENDPOINT,
            method='DELETE'
        )

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return None

    def proper_with_permission_status(self) -> int:
        return status.HTTP_204_NO_CONTENT

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        sid = transaction.savepoint()
        response = self.user_client.delete(
            path=self.obj_json['url'],
            format='json'
        )
        transaction.savepoint_rollback(sid)
        return response


class PUTEngineDetailPermissionTest(BaseHttpEndpointDetailPermissionTest):

    def permission_code_name(self) -> str:
        return flow_permission_for_rest_method(
            entity='http_endpoint',
            action=HTTP_ENDPOINT_PERMISSION_KEY_HTTP_ENDPOINT,
            method='PUT'
        )

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return self.user_client.put(
            path=self.obj_json['url'],
            data={
                "external_id": 'SASDFAF',
                "engine": self.engine_json['url'],
                "path": "/s",
                "method": 'MEH',
                "public": False
            }
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_400_BAD_REQUEST

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.put(
            path=self.obj_json['url'],
            data={
                "external_id": self.obj_json['external_id'],
                "engine": self.engine_json['url'],
                "path": "/s",
                "method": 'POST',
                "public": False
            }
        )


class PATCHEngineDetailPermissionTest(BaseHttpEndpointDetailPermissionTest):

    def permission_code_name(self) -> str:
        return flow_permission_for_rest_method(
            entity='http_endpoint',
            action=HTTP_ENDPOINT_PERMISSION_KEY_HTTP_ENDPOINT,
            method='PATCH'
        )

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return self.user_client.patch(
            path=self.obj_json['url'],
            data={
                "engine": self.engine_json['url'],
                "path": "/s",
                "method": 'POST',
                "public": False
            }
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.patch(
            path=self.obj_json['url'],
            data={
                "engine": self.engine_json['url'],
                "path": "/s",
                "method": 'POST',
                "public": False
            }
        )
