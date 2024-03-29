# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

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


class DataSeriesChildDetailStructurePermissionTest(BaseDataSeriesChildDetailPermissionTest):
    sub_url: str

    def create_detail_sub_element(self) -> None:
        self.data_series_detail_sub_element_json = self.create_payload(
            f'{self.data_series_json[self.sub_url]}', payload={
                'name': 'fact_name',
                'external_id': 'fact_name_external_id',
                'optional': False
            }, simulate_tenant=False)


class GETDataSeriesChildDetailStructurePermissionTest(DataSeriesChildDetailStructurePermissionTest):

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


class POSTDataSeriesChildDetailStructurePermissionTest(DataSeriesChildDetailStructurePermissionTest):
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


class PUTDataSeriesChildDetailStructurePermissionTest(DataSeriesChildDetailStructurePermissionTest):
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
                'name': 'fact_new_name',
                'external_id': 'fact_name_external_id',
                "optional": False
            }
        )


class PATCHDataSeriesChildDetailStructurePermissionTest(DataSeriesChildDetailStructurePermissionTest):
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
                'name': 'fact_even_newer_name',
            }
        )


class HEADDataSeriesChildDetailStructurePermissionTest(DataSeriesChildDetailStructurePermissionTest):
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


class OPTIONSDataSeriesChildDetailStructurePermissionTest(DataSeriesChildDetailStructurePermissionTest):
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


class DELETEDataSeriesChildDetailStructurePermissionTest(DataSeriesChildDetailStructurePermissionTest):
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


class GET_float_facts(GETDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'float_facts'


class GET_string_facts(GETDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'string_facts'


class GET_json_facts(GETDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'json_facts'


class GET_text_facts(GETDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'text_facts'


class GET_image_facts(GETDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'image_facts'


class GET_timestamp_facts(GETDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'timestamp_facts'


class GET_boolean_facts(GETDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'boolean_facts'


del GETDataSeriesChildDetailStructurePermissionTest


class POST_float_facts(POSTDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'float_facts'


class POST_string_facts(POSTDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'string_facts'


class POST_json_facts(POSTDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'json_facts'


class POST_text_facts(POSTDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'text_facts'


class POST_image_facts(POSTDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'image_facts'


class POST_timestamp_facts(POSTDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'timestamp_facts'


class POST_boolean_facts(POSTDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'boolean_facts'


del POSTDataSeriesChildDetailStructurePermissionTest


class PUT_float_facts(PUTDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'float_facts'


class PUT_string_facts(PUTDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'string_facts'


class PUT_json_facts(PUTDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'json_facts'


class PUT_text_facts(PUTDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'text_facts'


class PUT_image_facts(PUTDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'image_facts'


class PUT_timestamp_facts(PUTDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'timestamp_facts'


class PUT_boolean_facts(PUTDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'boolean_facts'


del PUTDataSeriesChildDetailStructurePermissionTest


class PATCH_float_facts(PATCHDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'float_facts'


class PATCH_string_facts(PATCHDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'string_facts'


class PATCH_json_facts(PATCHDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'json_facts'


class PATCH_text_facts(PATCHDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'text_facts'


class PATCH_image_facts(PATCHDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'image_facts'


class PATCH_timestamp_facts(PATCHDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'timestamp_facts'


class PATCH_boolean_facts(PATCHDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'boolean_facts'


del PATCHDataSeriesChildDetailStructurePermissionTest


class HEAD_float_facts(HEADDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'float_facts'


class HEAD_string_facts(HEADDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'string_facts'


class HEAD_json_facts(HEADDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'json_facts'


class HEAD_text_facts(HEADDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'text_facts'


class HEAD_image_facts(HEADDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'image_facts'


class HEAD_timestamp_facts(HEADDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'timestamp_facts'

#
class HEAD_boolean_facts(HEADDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'boolean_facts'


del HEADDataSeriesChildDetailStructurePermissionTest


class OPTIONS_float_facts(OPTIONSDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'float_facts'


class OPTIONS_string_facts(OPTIONSDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'string_facts'


class OPTIONS_json_facts(OPTIONSDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'json_facts'


class OPTIONS_text_facts(OPTIONSDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'text_facts'


class OPTIONS_image_facts(OPTIONSDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'image_facts'


class OPTIONS_timestamp_facts(OPTIONSDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'timestamp_facts'


class OPTIONS_boolean_facts(OPTIONSDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'boolean_facts'


del OPTIONSDataSeriesChildDetailStructurePermissionTest


class DELETE_float_facts(DELETEDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'float_facts'


class DELETE_string_facts(DELETEDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'string_facts'


class DELETE_json_facts(DELETEDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'json_facts'


class DELETE_text_facts(DELETEDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'text_facts'


class DELETE_image_facts(DELETEDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'image_facts'


class DELETE_timestamp_facts(DELETEDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'timestamp_facts'


class DELETE_boolean_facts(DELETEDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'boolean_facts'


del DELETEDataSeriesChildDetailStructurePermissionTest


del DataSeriesChildDetailStructurePermissionTest
