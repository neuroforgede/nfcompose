# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from typing import Optional, Union, cast

from django.http import HttpResponse
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from django.test.client import _MonkeyPatchedWSGIResponse as TestHttpResponse
else:
    TestHttpResponse = object
from rest_framework import status

from skipper import modules
from skipper.core.tests.base import BASE_URL
from skipper.dataseries.models import DATASERIES_PERMISSION_KEY_HISTORY_DATA_POINT, ds_permission_for_rest_method
from skipper.dataseries.tests.base.data_series_child_detail_permission_test import \
    BaseDataSeriesChildDetailPermissionTest

DATA_SERIES_BASE_URL = BASE_URL + modules.url_representation(modules.Module.DATA_SERIES) + '/'


class DataSeriesChildDetailDataPointPermissionTest(BaseDataSeriesChildDetailPermissionTest):
    sub_url: str

    def create_detail_sub_element(self) -> None:
        self.data_series_detail_sub_element_json = self.create_payload(
            f'{self.data_series_json[self.sub_url]}', payload={
                'external_id': 'datapoint_external_id',
                'identify_dimensions_by_external_id': False
            }, simulate_tenant=False)


class GETDataSeriesChildDetailDataPointPermissionTest(DataSeriesChildDetailDataPointPermissionTest):

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_HISTORY_DATA_POINT,
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
            path=self.data_series_detail_sub_element_json['history_url'],
            format='json'
        ))

    def add_extra_permissions(self) -> None:
        pass

    def remove_extra_permissions(self) -> None:
        pass


class POSTDataSeriesChildDetailDataPointPermissionTest(DataSeriesChildDetailDataPointPermissionTest):
    sub_url: str

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_HISTORY_DATA_POINT,
            method='POST'
        )

    def method_under_test_malformed(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.post(
            path=self.data_series_detail_sub_element_json['history_url'],
            format='json',
            data={}
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def proper_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.post(
            path=self.data_series_detail_sub_element_json['history_url'],
            format='json',
            data={}
        )


class PUTDataSeriesChildDetailDataPointPermissionTest(DataSeriesChildDetailDataPointPermissionTest):
    sub_url: str

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_HISTORY_DATA_POINT,
            method='PUT'
        )

    def method_under_test_malformed(self) -> Union[HttpResponse, TestHttpResponse]:
        put_request = self.user_client.put(
            path=self.data_series_detail_sub_element_json['history_url'],
            format='json',
            data={}
        )
        return put_request

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def proper_with_permission_status(self) -> int:
        # cant update in history
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.put(
            path=self.data_series_detail_sub_element_json['history_url'],
            format='json',
            data={
                'external_id': 'datapoint_external_id',
                'identify_dimensions_by_external_id': False
            }
        )


class PATCHDataSeriesChildDetailDataPointPermissionTest(DataSeriesChildDetailDataPointPermissionTest):
    sub_url: str

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_HISTORY_DATA_POINT,
            method='PATCH'
        )

    def method_under_test_malformed(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.patch(
            path=self.data_series_detail_sub_element_json['history_url'],
            format='json',
            data={
                "external_id": "definitely_wrong_id"
            }
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def proper_with_permission_status(self) -> int:
        # cant update in history
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.patch(
            path=self.data_series_detail_sub_element_json['history_url'],
            format='json',
            data={
                'external_id': 'datapoint_external_id',
                'identify_dimensions_by_external_id': False
            }
        )


class HEADDataSeriesChildDetailDataPointPermissionTest(DataSeriesChildDetailDataPointPermissionTest):
    sub_url: str

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_HISTORY_DATA_POINT,
            method='HEAD'
        )

    def method_under_test_malformed(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.head(
            path=self.data_series_detail_sub_element_json['history_url'],
            format='json'
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.head(
            path=self.data_series_detail_sub_element_json['history_url'],
            format='json'
        )


class OPTIONSDataSeriesChildDetailDataPointPermissionTest(DataSeriesChildDetailDataPointPermissionTest):
    sub_url: str

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_HISTORY_DATA_POINT,
            method='OPTIONS'
        )

    def method_under_test_malformed(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.options(
            path=self.data_series_detail_sub_element_json['history_url'],
            format='json'
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.options(
            path=self.data_series_detail_sub_element_json['history_url'],
            format='json'
        )


class DELETEDataSeriesChildDetailDataPointPermissionTest(DataSeriesChildDetailDataPointPermissionTest):
    sub_url: str

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_HISTORY_DATA_POINT,
            method='DELETE'
        )

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return None

    def malformed_with_permission_status(self) -> int:
        raise NotImplementedError()

    def proper_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.delete(
            path=self.data_series_detail_sub_element_json['history_url'],
            format='json'
        )


class GETDataPoint(GETDataSeriesChildDetailDataPointPermissionTest):
    sub_url = 'data_points'


del GETDataSeriesChildDetailDataPointPermissionTest


class POSTDataPoint(POSTDataSeriesChildDetailDataPointPermissionTest):
    sub_url = 'data_points'


del POSTDataSeriesChildDetailDataPointPermissionTest


class PUTDataPoint(PUTDataSeriesChildDetailDataPointPermissionTest):
    sub_url = 'data_points'


del PUTDataSeriesChildDetailDataPointPermissionTest


class PATCHDataPoint(PATCHDataSeriesChildDetailDataPointPermissionTest):
    sub_url = 'data_points'


del PATCHDataSeriesChildDetailDataPointPermissionTest


class HEADDataPoint(HEADDataSeriesChildDetailDataPointPermissionTest):
    sub_url = 'data_points'


del HEADDataSeriesChildDetailDataPointPermissionTest


class OPTIONSDataPoint(OPTIONSDataSeriesChildDetailDataPointPermissionTest):
    sub_url = 'data_points'


del OPTIONSDataSeriesChildDetailDataPointPermissionTest


class DELETE(DELETEDataSeriesChildDetailDataPointPermissionTest):
    sub_url = 'data_points'


del DELETEDataSeriesChildDetailDataPointPermissionTest


del DataSeriesChildDetailDataPointPermissionTest
