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
from skipper.dataseries.models import DATASERIES_PERMISSION_KEY_STRUCTURE_ELEMENT, ds_permission_for_rest_method
from skipper.dataseries.tests.base.data_series_child_detail_permission_test import \
    BaseDataSeriesChildDetailPermissionTest

DATA_SERIES_BASE_URL = BASE_URL + modules.url_representation(modules.Module.DATA_SERIES) + '/'


class DataSeriesChildDetailDimensionPermissionTest(BaseDataSeriesChildDetailPermissionTest):
    sub_url: str

    def create_detail_sub_element(self) -> None:
        self.data_series_detail_sub_element_json = self.create_payload(
            f'{self.data_series_json[self.sub_url]}', payload={
                "external_id": "external_id",
                "name": "dimension_name",
                "reference": self.data_series_json['url'],
                "optional": False
            }, simulate_tenant=False)


class GETDataSeriesChildDetailDimensionPermissionTest(DataSeriesChildDetailDimensionPermissionTest):

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_STRUCTURE_ELEMENT,
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
            path=self.data_series_detail_sub_element_json['url'],
            format='json'
        ))

    def add_extra_permissions(self) -> None:
        pass

    def remove_extra_permissions(self) -> None:
        pass


class POSTDataSeriesChildDetailDimensionPermissionTest(DataSeriesChildDetailDimensionPermissionTest):
    sub_url: str

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_STRUCTURE_ELEMENT,
            method='POST'
        )

    def method_under_test_malformed(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.post(
            path=self.data_series_detail_sub_element_json['url'],
            format='json',
            data={}
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def proper_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.post(
            path=self.data_series_detail_sub_element_json['url'],
            format='json',
            data={}
        )


class PUTDataSeriesChildDetailDimensionPermissionTest(DataSeriesChildDetailDimensionPermissionTest):
    sub_url: str

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_STRUCTURE_ELEMENT,
            method='PUT'
        )

    def method_under_test_malformed(self) -> Union[HttpResponse, TestHttpResponse]:
        put_request = self.user_client.put(
            path=self.data_series_detail_sub_element_json['url'],
            format='json',
            data={}
        )
        return put_request

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_400_BAD_REQUEST

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.put(
            path=self.data_series_detail_sub_element_json['url'],
            format='json',
            data={
                "external_id": "external_id",
                "name": "new_dimension_name",
                "reference": self.data_series_json['url'],
                "optional": False
            }
        )


class PATCHDataSeriesChildDetailDimensionPermissionTest(DataSeriesChildDetailDimensionPermissionTest):
    sub_url: str

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_STRUCTURE_ELEMENT,
            method='PATCH'
        )

    def method_under_test_malformed(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.patch(
            path=self.data_series_detail_sub_element_json['url'],
            format='json',
            data={
                "external_id": "definitely_wrong_id"
            }
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_400_BAD_REQUEST

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.patch(
            path=self.data_series_detail_sub_element_json['url'],
            format='json',
            data={
                "name": "even_newer_dimension_name",
            }
        )


class HEADDataSeriesChildDetailDimensionPermissionTest(DataSeriesChildDetailDimensionPermissionTest):
    sub_url: str

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_STRUCTURE_ELEMENT,
            method='HEAD'
        )

    def method_under_test_malformed(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.head(
            path=self.data_series_detail_sub_element_json['url'],
            format='json'
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.head(
            path=self.data_series_detail_sub_element_json['url'],
            format='json'
        )


class OPTIONSDataSeriesChildDetailDimensionPermissionTest(DataSeriesChildDetailDimensionPermissionTest):
    sub_url: str

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_STRUCTURE_ELEMENT,
            method='OPTIONS'
        )

    def method_under_test_malformed(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.options(
            path=self.data_series_detail_sub_element_json['url'],
            format='json'
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.options(
            path=self.data_series_detail_sub_element_json['url'],
            format='json'
        )


class DELETEDataSeriesChildDetailDimensionPermissionTest(DataSeriesChildDetailDimensionPermissionTest):
    sub_url: str

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_STRUCTURE_ELEMENT,
            method='DELETE'
        )

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return None

    def malformed_with_permission_status(self) -> int:
        raise NotImplementedError()

    def proper_with_permission_status(self) -> int:
        return status.HTTP_204_NO_CONTENT

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.delete(
            path=self.data_series_detail_sub_element_json['url'],
            format='json'
        )


class GETDimension(GETDataSeriesChildDetailDimensionPermissionTest):
    sub_url = 'dimensions'


del GETDataSeriesChildDetailDimensionPermissionTest


class POSTDimension(POSTDataSeriesChildDetailDimensionPermissionTest):
    sub_url = 'dimensions'


del POSTDataSeriesChildDetailDimensionPermissionTest


class PUTDimension(PUTDataSeriesChildDetailDimensionPermissionTest):
    sub_url = 'dimensions'


del PUTDataSeriesChildDetailDimensionPermissionTest


class PATCHDimension(PATCHDataSeriesChildDetailDimensionPermissionTest):
    sub_url = 'dimensions'


del PATCHDataSeriesChildDetailDimensionPermissionTest


class HEADDimension(HEADDataSeriesChildDetailDimensionPermissionTest):
    sub_url = 'dimensions'


del HEADDataSeriesChildDetailDimensionPermissionTest


class OPTIONSDimension(OPTIONSDataSeriesChildDetailDimensionPermissionTest):
    sub_url = 'dimensions'


del OPTIONSDataSeriesChildDetailDimensionPermissionTest


class DELETE(DELETEDataSeriesChildDetailDimensionPermissionTest):
    sub_url = 'dimensions'


del DELETEDataSeriesChildDetailDimensionPermissionTest


del DataSeriesChildDetailDimensionPermissionTest
