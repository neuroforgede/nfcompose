# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from typing import Optional, Union, cast, Any

from django.http import HttpResponse
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from django.test.client import _MonkeyPatchedWSGIResponse as TestHttpResponse
else:
    TestHttpResponse = object
from rest_framework import status

from skipper.dataseries.models import DATASERIES_PERMISSION_KEY_CONSUMER, ds_permission_for_rest_method
from skipper.dataseries.tests.base.data_series_child_list_permission_test import BaseDataSeriesDetailPermissionTest


class GETDataSeriesChildListConsumersPermissionTest(BaseDataSeriesDetailPermissionTest):

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_CONSUMER,
            method='GET'
        )

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return None

    def malformed_with_permission_status(self) -> int:
        raise NotImplementedError()

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return cast(TestHttpResponse, self.user_client.get(
            path=self.data_series_json['consumers'],
            format='json'
        ))


class POSTDataSeriesChildListConsumersPermissionTest(BaseDataSeriesDetailPermissionTest):

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_CONSUMER,
            method='POST'
        )

    def method_under_test_malformed(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.post(
            path=self.data_series_json['consumers'],
            format='json',
            data={}
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_400_BAD_REQUEST

    def proper_with_permission_status(self) -> int:
        return status.HTTP_201_CREATED

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.post(
            path=self.data_series_json['consumers'],
            format='json',
            data={
                "name": "1111",
                "target": "http://some-url.com",
                "headers": {
                    "Authorization": "Token some token yay"
                },
                "external_id": "111"
            }
        )


class PUTDataSeriesChildListConsumersPermissionTest(BaseDataSeriesDetailPermissionTest):

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_CONSUMER,
            method='PUT'
        )

    def method_under_test_malformed(self) -> Union[HttpResponse, TestHttpResponse]:
        put_request = self.user_client.put(
            path=self.data_series_json['consumers'],
            format='json',
            data={}
        )
        return put_request

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def proper_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.put(
            path=self.data_series_json['consumers'],
            format='json',
            data={}
        )


class PATCHDataSeriesChildListConsumersPermissionTest(BaseDataSeriesDetailPermissionTest):

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_CONSUMER,
            method='PATCH'
        )

    def method_under_test_malformed(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.patch(
            path=self.data_series_json['consumers'],
            format='json',
            data={}
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def proper_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.patch(
            path=self.data_series_json['consumers'],
            format='json',
            data={}
        )


class HEADDataSeriesChildListConsumersPermissionTest(BaseDataSeriesDetailPermissionTest):

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_CONSUMER,
            method='HEAD'
        )

    def method_under_test_malformed(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.head(
            path=self.data_series_json['consumers'],
            format='json'
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.head(
            path=self.data_series_json['consumers'],
            format='json'
        )


class OPTIONSDataSeriesChildListConsumersPermissionTest(BaseDataSeriesDetailPermissionTest):

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_CONSUMER,
            method='OPTIONS'
        )

    def method_under_test_malformed(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.options(
            path=self.data_series_json['consumers'],
            format='json'
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.options(
            path=self.data_series_json['consumers'],
            format='json'
        )


class DELETEDDataSeriesChildListConsumersPermissionTest(BaseDataSeriesDetailPermissionTest):

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_CONSUMER,
            method='DELETE'
        )

    def method_under_test_malformed(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.delete(
            path=self.data_series_json['consumers'],
            format='json'
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def proper_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.delete(
            path=self.data_series_json['consumers'],
            format='json'
        )
