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
from rest_framework import status

from skipper import modules
from skipper.core.tests.base import BASE_URL
from skipper.core.tests.base.regular_detail_permission import BaseModelDetailPermissionTest
from skipper.flow.models import Engine, ENGINE_PERMISSION_KEY_ENGINE, flow_permission_for_rest_method, \
    ENGINE_PERMISSION_KEY_SECRET, ENGINE_PERMISSION_KEY_ACCESS

ENGINE_BASE_URL = BASE_URL + modules.url_representation(modules.Module.FLOW) + '/engine/'

class BaseEngineDetailPermissionTest(BaseModelDetailPermissionTest):

    url_under_test = ENGINE_BASE_URL

    permission_code_prefix = 'flow'
    
    skip_setup_assertions: bool = True

    obj_json: Dict[str, Any]
    model_type: Type[Model] = Engine

    permission_key = ENGINE_PERMISSION_KEY_ENGINE

    base_class_name = 'BaseEngineDetailPermissionTest'

    def create_obj_via_rest(self) -> None:
        self.obj_json = self.create_payload(self.url_under_test, payload={
            'external_id': 'external_id1',
            'upstream': 'http://nodered.local/'
        }, simulate_tenant=False)

    def read_permission(self) -> str:
        return flow_permission_for_rest_method(
            entity='engine',
            action=self.permission_key,
            method='GET'
        )

class GETEngineDetailPermissionTest(BaseEngineDetailPermissionTest):

    def permission_code_name(self) -> str:
        return flow_permission_for_rest_method(
            entity='engine',
            action=ENGINE_PERMISSION_KEY_ENGINE,
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


class POSTEngineDetailPermissionTest(BaseEngineDetailPermissionTest):

    def permission_code_name(self) -> str:
        return flow_permission_for_rest_method(
            entity='engine',
            action=ENGINE_PERMISSION_KEY_ENGINE,
            method='POST'
        )

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return self.user_client.post(
            path=self.obj_json['url'],
            data={
                "external_id": "123123%!",
                "upstream": "%"
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
                "external_id": "1",
                "upstream": "http://nodered.local/"
            }
        )


class OPTIONSEngineDetailPermissionTest(BaseEngineDetailPermissionTest):

    def permission_code_name(self) -> str:
        return flow_permission_for_rest_method(
            entity='engine',
            action=ENGINE_PERMISSION_KEY_ENGINE,
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


class HEADEngineDetailPermissionTest(BaseEngineDetailPermissionTest):

    def permission_code_name(self) -> str:
        return flow_permission_for_rest_method(
            entity='engine',
            action=ENGINE_PERMISSION_KEY_ENGINE,
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


class DELETEEngineDetailPermissionTest(BaseEngineDetailPermissionTest):

    def permission_code_name(self) -> str:
        return flow_permission_for_rest_method(
            entity='engine',
            action=ENGINE_PERMISSION_KEY_ENGINE,
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


class PUTEngineDetailPermissionTest(BaseEngineDetailPermissionTest):

    def permission_code_name(self) -> str:
        return flow_permission_for_rest_method(
            entity='engine',
            action=ENGINE_PERMISSION_KEY_ENGINE,
            method='PUT'
        )

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return self.user_client.put(
            path=self.obj_json['url'],
            data={}
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
                "upstream": "http://local.nodered.local/"
            }
        )


class PATCHEngineDetailPermissionTest(BaseEngineDetailPermissionTest):

    def permission_code_name(self) -> str:
        return flow_permission_for_rest_method(
            entity='engine',
            action=ENGINE_PERMISSION_KEY_ENGINE,
            method='PATCH'
        )

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return self.user_client.patch(
            path=self.obj_json['url'],
            data={
                "ptsdf": "1231"
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
                "upstream": "http://local.nodered.local/"
            }
        )


class GETEngineSecretPermissionTest(BaseEngineDetailPermissionTest):

    def permission_code_name(self) -> str:
        return flow_permission_for_rest_method(
            entity='engine',
            action=ENGINE_PERMISSION_KEY_SECRET,
            method='GET'
        )

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return cast(TestHttpResponse, self.user_client.get(
            path=self.obj_json['secret']
        ))

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return cast(TestHttpResponse, self.user_client.get(
            path=self.obj_json['secret']
        ))


class POSTEngineSecretPermissionTest(BaseEngineDetailPermissionTest):

    def permission_code_name(self) -> str:
        return flow_permission_for_rest_method(
            entity='engine',
            action=ENGINE_PERMISSION_KEY_SECRET,
            method='POST'
        )

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return self.user_client.post(
            path=self.obj_json['secret'],
            data={}
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def proper_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.post(
            path=self.obj_json['secret'],
            data={}
        )


class OPTIONSEngineSecretPermissionTest(BaseEngineDetailPermissionTest):

    def permission_code_name(self) -> str:
        return flow_permission_for_rest_method(
            entity='engine',
            action=ENGINE_PERMISSION_KEY_SECRET,
            method='OPTIONS'
        )

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return self.user_client.options(
            path=self.obj_json['secret']
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.options(
            path=self.obj_json['secret']
        )


class HEADEngineSecretPermissionTest(BaseEngineDetailPermissionTest):

    def permission_code_name(self) -> str:
        return flow_permission_for_rest_method(
            entity='engine',
            action=ENGINE_PERMISSION_KEY_SECRET,
            method='HEAD'
        )

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return self.user_client.head(
            path=self.obj_json['secret']
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.head(
            path=self.obj_json['secret']
        )


class DELETEEngineSecretPermissionTest(BaseEngineDetailPermissionTest):

    def permission_code_name(self) -> str:
        return flow_permission_for_rest_method(
            entity='engine',
            action=ENGINE_PERMISSION_KEY_SECRET,
            method='DELETE'
        )

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return None

    def proper_with_permission_status(self) -> int:
        return status.HTTP_204_NO_CONTENT

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        response = self.user_client.delete(
            path=self.obj_json['secret'],
            format='json'
        )
        return response


class PUTEngineSecretPermissionTest(BaseEngineDetailPermissionTest):

    def permission_code_name(self) -> str:
        return flow_permission_for_rest_method(
            entity='engine',
            action=ENGINE_PERMISSION_KEY_SECRET,
            method='PUT'
        )

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return self.user_client.put(
            path=self.obj_json['secret'],
            data={
                'secret': 'my_too_short_secret'
            }
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_400_BAD_REQUEST

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.put(
            path=self.obj_json['secret'],
            data={
                'secret': 'j7bNyBH96FgFEFF444UVeXCE28QzXJqA'
            }
        )


class PATCHEngineSecretPermissionTest(BaseEngineDetailPermissionTest):

    def permission_code_name(self) -> str:
        return flow_permission_for_rest_method(
            entity='engine',
            action=ENGINE_PERMISSION_KEY_SECRET,
            method='PATCH'
        )

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return self.user_client.patch(
            path=self.obj_json['secret'],
            data={}
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def proper_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.patch(
            path=self.obj_json['secret'],
            data={}
        )


class GETEngineAccessPermissionTest(BaseEngineDetailPermissionTest):

    def permission_code_name(self) -> str:
        return flow_permission_for_rest_method(
            entity='engine',
            action=ENGINE_PERMISSION_KEY_ACCESS,
            method='GET'
        )

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return cast(TestHttpResponse, self.user_client.get(
            path=self.obj_json['access']
        ))

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return cast(TestHttpResponse, self.user_client.get(
            path=self.obj_json['access']
        ))


class POSTEngineAccessPermissionTest(BaseEngineDetailPermissionTest):

    def permission_code_name(self) -> str:
        return flow_permission_for_rest_method(
            entity='engine',
            action=ENGINE_PERMISSION_KEY_ACCESS,
            method='POST'
        )

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return self.user_client.post(
            path=self.obj_json['access'],
            data={}
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def proper_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.post(
            path=self.obj_json['access'],
            data={}
        )


class OPTIONSEngineAccessPermissionTest(BaseEngineDetailPermissionTest):

    def permission_code_name(self) -> str:
        return flow_permission_for_rest_method(
            entity='engine',
            action=ENGINE_PERMISSION_KEY_ACCESS,
            method='OPTIONS'
        )

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return self.user_client.options(
            path=self.obj_json['access']
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.options(
            path=self.obj_json['access']
        )


class HEADEngineAccessPermissionTest(BaseEngineDetailPermissionTest):

    def permission_code_name(self) -> str:
        return flow_permission_for_rest_method(
            entity='engine',
            action=ENGINE_PERMISSION_KEY_ACCESS,
            method='HEAD'
        )

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return self.user_client.head(
            path=self.obj_json['access']
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.head(
            path=self.obj_json['access']
        )


class DELETEEngineAccessPermissionTest(BaseEngineDetailPermissionTest):

    def permission_code_name(self) -> str:
        return flow_permission_for_rest_method(
            entity='engine',
            action=ENGINE_PERMISSION_KEY_ACCESS,
            method='DELETE'
        )

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return None

    def proper_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        response = self.user_client.delete(
            path=self.obj_json['access'],
            format='json'
        )
        return response


class PUTEngineAccessPermissionTest(BaseEngineDetailPermissionTest):

    def permission_code_name(self) -> str:
        return flow_permission_for_rest_method(
            entity='engine',
            action=ENGINE_PERMISSION_KEY_ACCESS,
            method='PUT'
        )

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return self.user_client.put(
            path=self.obj_json['access'],
            data={}
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def proper_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.put(
            path=self.obj_json['access'],
            data={}
        )


class PATCHEngineAccessPermissionTest(BaseEngineDetailPermissionTest):

    def permission_code_name(self) -> str:
        return flow_permission_for_rest_method(
            entity='engine',
            action=ENGINE_PERMISSION_KEY_ACCESS,
            method='PATCH'
        )

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return self.user_client.patch(
            path=self.obj_json['access'],
            data={}
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def proper_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.patch(
            path=self.obj_json['access'],
            data={}
        )
