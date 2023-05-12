# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from typing import Optional, Union, cast, Any

from django.http import HttpResponse
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from django.test.client import _MonkeyPatchedWSGIResponse as TestHttpResponse
else:
    TestHttpResponse = object
from rest_framework import status

from skipper.dataseries.models import DATASERIES_PERMISSION_KEY_STRUCTURE_ELEMENT, ds_permission_for_rest_method
from skipper.dataseries.tests.base.data_series_child_list_permission_test import BaseDataSeriesDetailPermissionTest


class GETDataSeriesChildListStructurePermissionTest(BaseDataSeriesDetailPermissionTest):
    sub_url: str

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
            path=self.data_series_json[self.sub_url],
            format='json'
        ))

    def add_extra_permissions(self) -> None:
        pass

    def remove_extra_permissions(self) -> None:
        pass


class POSTDataSeriesChildListStructurePermissionTest(BaseDataSeriesDetailPermissionTest):
    sub_url: str

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_STRUCTURE_ELEMENT,
            method='POST'
        )

    def method_under_test_malformed(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.post(
            path=self.data_series_json[self.sub_url],
            format='json',
            data={}
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_400_BAD_REQUEST

    def proper_with_permission_status(self) -> int:
        return status.HTTP_201_CREATED

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.post(
            path=self.data_series_json[self.sub_url],
            format='json',
            data={
                'external_id': 'some_fact_during_permission_test',
                'name': 'some_fact_during_permission_test',
                'optional': False
            }
        )


class PUTDataSeriesChildListStructurePermissionTest(BaseDataSeriesDetailPermissionTest):
    sub_url: str

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_STRUCTURE_ELEMENT,
            method='PUT'
        )

    def method_under_test_malformed(self) -> Union[HttpResponse, TestHttpResponse]:
        put_request = self.user_client.put(
            path=self.data_series_json[self.sub_url],
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
            path=self.data_series_json[self.sub_url],
            format='json',
            data={}
        )


class PATCHDataSeriesChildListStructurePermissionTest(BaseDataSeriesDetailPermissionTest):
    sub_url: str

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_STRUCTURE_ELEMENT,
            method='PATCH'
        )

    def method_under_test_malformed(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.patch(
            path=self.data_series_json[self.sub_url],
            format='json',
            data={}
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def proper_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.patch(
            path=self.data_series_json[self.sub_url],
            format='json',
            data={}
        )


class HEADDataSeriesChildListStructurePermissionTest(BaseDataSeriesDetailPermissionTest):
    sub_url: str

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_STRUCTURE_ELEMENT,
            method='HEAD'
        )

    def method_under_test_malformed(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.head(
            path=self.data_series_json[self.sub_url],
            format='json'
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.head(
            path=self.data_series_json[self.sub_url],
            format='json'
        )


class OPTIONSDataSeriesChildListStructurePermissionTest(BaseDataSeriesDetailPermissionTest):
    sub_url: str

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_STRUCTURE_ELEMENT,
            method='OPTIONS'
        )

    def method_under_test_malformed(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.options(
            path=self.data_series_json[self.sub_url],
            format='json'
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.options(
            path=self.data_series_json[self.sub_url],
            format='json'
        )


class DELETEDataSeriesChildListStructurePermissionTest(BaseDataSeriesDetailPermissionTest):
    sub_url: str

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_STRUCTURE_ELEMENT,
            method='DELETE'
        )

    def method_under_test_malformed(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.delete(
            path=self.data_series_json[self.sub_url],
            format='json'
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def proper_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.delete(
            path=self.data_series_json[self.sub_url],
            format='json'
        )


class GET_float_facts(GETDataSeriesChildListStructurePermissionTest):
    sub_url = 'float_facts'


class GET_string_facts(GETDataSeriesChildListStructurePermissionTest):
    sub_url = 'string_facts'


class GET_json_facts(GETDataSeriesChildListStructurePermissionTest):
    sub_url = 'json_facts'


class GET_text_facts(GETDataSeriesChildListStructurePermissionTest):
    sub_url = 'text_facts'


class GET_image_facts(GETDataSeriesChildListStructurePermissionTest):
    sub_url = 'image_facts'


class GET_file_facts(GETDataSeriesChildListStructurePermissionTest):
    sub_url = 'file_facts'


class GET_timestamp_facts(GETDataSeriesChildListStructurePermissionTest):
    sub_url = 'timestamp_facts'


class GET_boolean_facts(GETDataSeriesChildListStructurePermissionTest):
    sub_url = 'boolean_facts'


del GETDataSeriesChildListStructurePermissionTest


class POST_float_facts(POSTDataSeriesChildListStructurePermissionTest):
    sub_url = 'float_facts'


class POST_string_facts(POSTDataSeriesChildListStructurePermissionTest):
    sub_url = 'string_facts'


class POST_json_facts(POSTDataSeriesChildListStructurePermissionTest):
    sub_url = 'json_facts'


class POST_text_facts(POSTDataSeriesChildListStructurePermissionTest):
    sub_url = 'text_facts'


class POST_image_facts(POSTDataSeriesChildListStructurePermissionTest):
    sub_url = 'image_facts'


class POST_file_facts(POSTDataSeriesChildListStructurePermissionTest):
    sub_url = 'file_facts'


class POST_timestamp_facts(POSTDataSeriesChildListStructurePermissionTest):
    sub_url = 'timestamp_facts'


class POST_boolean_facts(POSTDataSeriesChildListStructurePermissionTest):
    sub_url = 'boolean_facts'


del POSTDataSeriesChildListStructurePermissionTest


class PUT_float_facts(PUTDataSeriesChildListStructurePermissionTest):
    sub_url = 'float_facts'


class PUT_string_facts(PUTDataSeriesChildListStructurePermissionTest):
    sub_url = 'string_facts'


class PUT_json_facts(PUTDataSeriesChildListStructurePermissionTest):
    sub_url = 'json_facts'


class PUT_text_facts(PUTDataSeriesChildListStructurePermissionTest):
    sub_url = 'text_facts'


class PUT_image_facts(PUTDataSeriesChildListStructurePermissionTest):
    sub_url = 'image_facts'


class PUT_file_facts(PUTDataSeriesChildListStructurePermissionTest):
    sub_url = 'file_facts'


class PUT_timestamp_facts(PUTDataSeriesChildListStructurePermissionTest):
    sub_url = 'timestamp_facts'


class PUT_boolean_facts(PUTDataSeriesChildListStructurePermissionTest):
    sub_url = 'boolean_facts'


del PUTDataSeriesChildListStructurePermissionTest


class PATCH_float_facts(PATCHDataSeriesChildListStructurePermissionTest):
    sub_url = 'float_facts'


class PATCH_string_facts(PATCHDataSeriesChildListStructurePermissionTest):
    sub_url = 'string_facts'


class PATCH_json_facts(PATCHDataSeriesChildListStructurePermissionTest):
    sub_url = 'json_facts'


class PATCH_text_facts(PATCHDataSeriesChildListStructurePermissionTest):
    sub_url = 'text_facts'


class PATCH_image_facts(PATCHDataSeriesChildListStructurePermissionTest):
    sub_url = 'image_facts'


class PATCH_file_facts(PATCHDataSeriesChildListStructurePermissionTest):
    sub_url = 'file_facts'


class PATCH_timestamp_facts(PATCHDataSeriesChildListStructurePermissionTest):
    sub_url = 'timestamp_facts'


class PATCH_boolean_facts(PATCHDataSeriesChildListStructurePermissionTest):
    sub_url = 'boolean_facts'


del PATCHDataSeriesChildListStructurePermissionTest


class HEAD_float_facts(HEADDataSeriesChildListStructurePermissionTest):
    sub_url = 'float_facts'


class HEAD_string_facts(HEADDataSeriesChildListStructurePermissionTest):
    sub_url = 'string_facts'


class HEAD_json_facts(HEADDataSeriesChildListStructurePermissionTest):
    sub_url = 'json_facts'


class HEAD_text_facts(HEADDataSeriesChildListStructurePermissionTest):
    sub_url = 'text_facts'


class HEAD_image_facts(HEADDataSeriesChildListStructurePermissionTest):
    sub_url = 'image_facts'


class HEAD_file_facts(HEADDataSeriesChildListStructurePermissionTest):
    sub_url = 'file_facts'


class HEAD_timestamp_facts(HEADDataSeriesChildListStructurePermissionTest):
    sub_url = 'timestamp_facts'


class HEAD_boolean_facts(HEADDataSeriesChildListStructurePermissionTest):
    sub_url = 'boolean_facts'


del HEADDataSeriesChildListStructurePermissionTest


class OPTIONS_float_facts(OPTIONSDataSeriesChildListStructurePermissionTest):
    sub_url = 'float_facts'


class OPTIONS_string_facts(OPTIONSDataSeriesChildListStructurePermissionTest):
    sub_url = 'string_facts'


class OPTIONS_json_facts(OPTIONSDataSeriesChildListStructurePermissionTest):
    sub_url = 'json_facts'


class OPTIONS_text_facts(OPTIONSDataSeriesChildListStructurePermissionTest):
    sub_url = 'text_facts'


class OPTIONS_image_facts(OPTIONSDataSeriesChildListStructurePermissionTest):
    sub_url = 'image_facts'


class OPTIONS_file_facts(OPTIONSDataSeriesChildListStructurePermissionTest):
    sub_url = 'file_facts'


class OPTIONS_timestamp_facts(OPTIONSDataSeriesChildListStructurePermissionTest):
    sub_url = 'timestamp_facts'


class OPTIONS_boolean_facts(OPTIONSDataSeriesChildListStructurePermissionTest):
    sub_url = 'boolean_facts'


del OPTIONSDataSeriesChildListStructurePermissionTest


class DELETE_float_facts(DELETEDataSeriesChildListStructurePermissionTest):
    sub_url = 'float_facts'


class DELETE_string_facts(DELETEDataSeriesChildListStructurePermissionTest):
    sub_url = 'string_facts'


class DELETE_json_facts(DELETEDataSeriesChildListStructurePermissionTest):
    sub_url = 'json_facts'


class DELETE_text_facts(DELETEDataSeriesChildListStructurePermissionTest):
    sub_url = 'text_facts'


class DELETE_image_facts(DELETEDataSeriesChildListStructurePermissionTest):
    sub_url = 'image_facts'


class DELETE_file_facts(DELETEDataSeriesChildListStructurePermissionTest):
    sub_url = 'file_facts'


class DELETE_timestamp_facts(DELETEDataSeriesChildListStructurePermissionTest):
    sub_url = 'timestamp_facts'


class DELETE_boolean_facts(DELETEDataSeriesChildListStructurePermissionTest):
    sub_url = 'boolean_facts'


del DELETEDataSeriesChildListStructurePermissionTest
