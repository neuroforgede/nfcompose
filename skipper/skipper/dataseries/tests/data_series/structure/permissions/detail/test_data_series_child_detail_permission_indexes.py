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

from skipper import modules
from skipper.core.tests.base import BASE_URL
from skipper.dataseries.models import DATASERIES_PERMISSION_KEY_STRUCTURE_ELEMENT, ds_permission_for_rest_method
from skipper.dataseries.tests.base.data_series_child_detail_permission_test import \
    BaseDataSeriesChildDetailPermissionTest

DATA_SERIES_BASE_URL = BASE_URL + modules.url_representation(modules.Module.DATA_SERIES) + '/'


class DataSeriesChildDetailStructurePermissionTest(BaseDataSeriesChildDetailPermissionTest):
    sub_url: str
    target_json: Any

    def create_detail_sub_element(self) -> None:
        self.target_json = self.create_payload(
            self.data_series_json['float_facts'],
            payload={
                'name': 'fact',
                'external_id': 'fact_id',
                'optional': True
            }
        )
        self.data_series_detail_sub_element_json = self.create_payload(
            f'{self.data_series_json[self.sub_url]}', payload={
                'name': 'index_name',
                'external_id': 'index_name_external_id',
                'targets': [{
                    'target_id': self.target_json['id'],
                    'target_type': 'FLOAT_FACT'
                }]
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
                'name': 'index_new_name',
                'external_id': 'index_name_external_id',
                'targets': [{
                    'target_id': self.target_json['id'],
                    'target_type': 'FLOAT_FACT'
                }]
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
                'name': 'index_even_newer_name',
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


class GETIndexes(GETDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'indexes'


del GETDataSeriesChildDetailStructurePermissionTest


class POSTIndexes(POSTDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'indexes'


del POSTDataSeriesChildDetailStructurePermissionTest


class PUTIndexes(PUTDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'indexes'


del PUTDataSeriesChildDetailStructurePermissionTest


class PATCHIndexes(PATCHDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'indexes'


del PATCHDataSeriesChildDetailStructurePermissionTest


class HEADIndexes(HEADDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'indexes'


del HEADDataSeriesChildDetailStructurePermissionTest


class OPTIONSIndexes(OPTIONSDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'indexes'


del OPTIONSDataSeriesChildDetailStructurePermissionTest


class DELETEIndexes(DELETEDataSeriesChildDetailStructurePermissionTest):
    sub_url = 'indexes'


del DELETEDataSeriesChildDetailStructurePermissionTest


del DataSeriesChildDetailStructurePermissionTest
