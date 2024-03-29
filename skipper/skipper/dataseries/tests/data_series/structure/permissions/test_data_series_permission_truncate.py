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

from skipper.dataseries.models import ds_permission_for_rest_method, \
    DATASERIES_PERMISSION_KEY_TRUNCATE_DATA_SERIES
from skipper.dataseries.tests.base.data_series_child_list_permission_test import BaseDataSeriesDetailPermissionTest


class BaseDataSeriesChildListTruncatePermissionTest(BaseDataSeriesDetailPermissionTest):
    pass


class GETDataSeriesChildListTruncatePermissionTest(BaseDataSeriesChildListTruncatePermissionTest):

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_TRUNCATE_DATA_SERIES,
            method='GET'
        )

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return None

    def malformed_with_permission_status(self) -> int:
        raise NotImplementedError()

    def proper_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return cast(TestHttpResponse, self.user_client.get(
            path=self.data_series_json['truncate'],
            format='json'
        ))


class POSTDataSeriesChildListTruncatePermissionTest(BaseDataSeriesChildListTruncatePermissionTest):

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_TRUNCATE_DATA_SERIES,
            method='POST'
        )

    def method_under_test_malformed(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.post(
            path=self.data_series_json['truncate'],
            format='json',
            data={}
        )

    def malformed_with_permission_status(self) -> int:
        # cant really malform something that has no parameters
        return status.HTTP_200_OK

    def proper_with_permission_status(self) -> int:
        # FIXME: Should maybe change to 201?
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.post(
            path=self.data_series_json['truncate'],
            format='json',
            data={}
        )


class POSTDataSeriesChildListTruncateAsMaterializedPermissionTest(BaseDataSeriesChildListTruncatePermissionTest):

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_TRUNCATE_DATA_SERIES,
            method='POST'
        )

    def method_under_test_malformed(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.post(
            path=self.data_series_json['truncate'],
            format='json',
            data={}
        )

    def malformed_with_permission_status(self) -> int:
        # cant really malform something that has no parameters
        return status.HTTP_200_OK

    def proper_with_permission_status(self) -> int:
        # FIXME: Should maybe change to 201?
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.post(
            path=self.data_series_json['truncate'],
            format='json',
            data={}
        )


class PUTDataSeriesChildListTruncatePermissionTest(BaseDataSeriesChildListTruncatePermissionTest):

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_TRUNCATE_DATA_SERIES,
            method='PUT'
        )

    def method_under_test_malformed(self) -> Union[HttpResponse, TestHttpResponse]:
        put_request = self.user_client.put(
            path=self.data_series_json['truncate'],
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
            path=self.data_series_json['truncate'],
            format='json',
            data={}
        )


class PATCHDataSeriesChildListTruncatePermissionTest(BaseDataSeriesChildListTruncatePermissionTest):

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_TRUNCATE_DATA_SERIES,
            method='PATCH'
        )

    def method_under_test_malformed(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.patch(
            path=self.data_series_json['truncate'],
            format='json',
            data={}
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def proper_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.patch(
            path=self.data_series_json['truncate'],
            format='json',
            data={}
        )


class HEADDataSeriesChildListTruncatePermissionTest(BaseDataSeriesChildListTruncatePermissionTest):

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_TRUNCATE_DATA_SERIES,
            method='HEAD'
        )

    def method_under_test_malformed(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.head(
            path=self.data_series_json['truncate'],
            format='json'
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def proper_with_permission_status(self) -> int:
        # FIXME: Should this really not be allowed?
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.head(
            path=self.data_series_json['truncate'],
            format='json'
        )


class OPTIONSDataSeriesChildListTruncatePermissionTest(BaseDataSeriesChildListTruncatePermissionTest):

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_TRUNCATE_DATA_SERIES,
            method='OPTIONS'
        )

    def method_under_test_malformed(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.options(
            path=self.data_series_json['truncate'],
            format='json'
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.options(
            path=self.data_series_json['truncate'],
            format='json'
        )


class DELETEDataSeriesChildListTruncatePermissionTest(BaseDataSeriesChildListTruncatePermissionTest):

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_TRUNCATE_DATA_SERIES,
            method='DELETE'
        )

    def method_under_test_malformed(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.delete(
            path=self.data_series_json['truncate'],
            format='json'
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def proper_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.delete(
            path=self.data_series_json['truncate'],
            format='json'
        )


del BaseDataSeriesChildListTruncatePermissionTest
