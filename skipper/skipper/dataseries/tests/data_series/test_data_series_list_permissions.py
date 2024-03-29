# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


import io

from typing import Optional, Union, cast, Any, List, Dict
from django.http import HttpResponse
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from django.test.client import _MonkeyPatchedWSGIResponse as TestHttpResponse
else:
    TestHttpResponse = object

from PIL import Image as PIL_Image  # type: ignore
from django_multitenant.utils import set_current_tenant  # type: ignore
from guardian.shortcuts import assign_perm, remove_perm  # type: ignore
from rest_framework import status

from skipper import modules
from skipper.core.models.tenant import Tenant
from skipper.core.tests.base import BASE_URL, BaseRESTPermissionTest, BaseObjectLevelPermissionListEndpointTest
from skipper.dataseries.models import DATASERIES_PERMISSION_KEY_DATA_SERIES, ds_permission_for_rest_method, DataSeries

DATA_SERIES_BASE_URL = BASE_URL + modules.url_representation(modules.Module.DATA_SERIES) + '/'


def generate_photo_file() -> io.BytesIO:
    file = io.BytesIO()
    image = PIL_Image.new('RGBA', size=(100, 100), color=(155, 0, 0))
    image.save(file, 'png')
    file.name = 'test.png'
    file.seek(0)
    return file


def generate_some_other_photo_file() -> io.BytesIO:
    file = io.BytesIO()
    image = PIL_Image.new('RGBA', size=(100, 100), color=(200, 200, 0))
    image.save(file, 'png')
    file.name = 'test.png'
    file.seek(0)
    return file


class BaseDataSeriesRESTPermissionTest(BaseRESTPermissionTest):
    """
    rudimentarily tests whether the given methods are allowed to be run
    against the dataseries endpoint
    """
    # the list endpoint is disabled for datapoints if we do not select for a data series
    url_under_test = DATA_SERIES_BASE_URL + 'dataseries/'
    simulate_other_tenant = True


class NonGetDataSeriesRestPermissionTestMixin(object):
    """
    All non GET methods need GET permissions as well
    GET on the DataSeries is a baseline permission
    """
    test_user: Any

    def add_extra_permissions(self) -> None:
        data_series_read_permission = ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_DATA_SERIES,
            method='GET'
        )

        assign_perm(
            f'dataseries.{data_series_read_permission}',
            self.test_user,
        )

    def remove_extra_permissions(self) -> None:
        data_series_read_permission = ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_DATA_SERIES,
            method='GET'
        )

        remove_perm(
            f'dataseries.{data_series_read_permission}',
            self.test_user,
        )


class POSTDataSeriesRESTPermissionTest(NonGetDataSeriesRestPermissionTestMixin, BaseDataSeriesRESTPermissionTest):

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_DATA_SERIES,
            method='POST'
        )

    def method_under_test_malformed(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.post(
            path=self.url_under_test,
            format='json',
            data={}
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_400_BAD_REQUEST

    def proper_with_permission_status(self) -> int:
        return status.HTTP_201_CREATED

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.post(
            path=self.url_under_test,
            format='json',
            data={
                'external_id': 'some_dataseries_during_permission_test',
                'name': 'some_dataseries_during_permission_test'
            }
        )


class ListFilteringDataSeriesRESTPermissionTest(BaseObjectLevelPermissionListEndpointTest):
    url_under_test = DATA_SERIES_BASE_URL + 'dataseries/'

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_DATA_SERIES,
            method='GET'
        )

    def create_object(self) -> Any:
        tenant = Tenant.objects.filter(
            name='default_tenant'
        )[0]
        set_current_tenant(tenant)
        return DataSeries.objects.create(
            external_id='123123',
            name='1',
            tenant=tenant
        )

    def get_list(self) -> Union[HttpResponse, TestHttpResponse]:
        return cast(TestHttpResponse, self.user_client.get(
            path=self.url_under_test,
            format='json',
            data={}
        ))

    def extract_data_from_list(self, response: Any) -> List[Dict[str, Any]]:
        return cast(List[Dict[str, Any]], response.json()['results'])


class GETDataSeriesRESTPermissionTest(BaseDataSeriesRESTPermissionTest):

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_DATA_SERIES,
            method='GET'
        )

    def method_under_test_malformed(self) -> Union[HttpResponse, TestHttpResponse]:
        return cast(TestHttpResponse, self.user_client.get(
            path=self.url_under_test,
            format='json',
            data={}
        ))

    def malformed_with_permission_status(self) -> int:
        # for get we just use a proper one as well, how should we malform this here :D ?
        return status.HTTP_200_OK

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return cast(TestHttpResponse, self.user_client.get(
            path=self.url_under_test,
            format='json'
        ))


class PUTDataSeriesRESTPermissionTest(NonGetDataSeriesRestPermissionTestMixin, BaseDataSeriesRESTPermissionTest):

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_DATA_SERIES,
            method='PUT'
        )

    def method_under_test_malformed(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.put(
            path=self.url_under_test,
            format='json',
            data={}
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def proper_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.put(
            path=self.url_under_test,
            format='json',
            data={}
        )


class PATCHDataSeriesRESTPermissionTest(NonGetDataSeriesRestPermissionTestMixin, BaseDataSeriesRESTPermissionTest):

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_DATA_SERIES,
            method='PATCH'
        )

    def method_under_test_malformed(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.patch(
            path=self.url_under_test,
            format='json',
            data={}
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def proper_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.patch(
            path=self.url_under_test,
            format='json',
            data={}
        )


class HEADDataSeriesRESTPermissionTest(NonGetDataSeriesRestPermissionTestMixin, BaseDataSeriesRESTPermissionTest):

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_DATA_SERIES,
            method='HEAD'
        )

    def method_under_test_malformed(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.head(
            path=self.url_under_test,
            format='json'
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.head(
            path=self.url_under_test,
            format='json'
        )


class OPTIONSDataSeriesRESTPermissionTest(NonGetDataSeriesRestPermissionTestMixin, BaseDataSeriesRESTPermissionTest):

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_DATA_SERIES,
            method='OPTIONS'
        )

    def method_under_test_malformed(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.options(
            path=self.url_under_test,
            format='json'
        )

    def malformed_without_permission_status(self) -> int:
        return status.HTTP_403_FORBIDDEN

    def proper_without_permission_status(self) -> int:
        return status.HTTP_403_FORBIDDEN

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.options(
            path=self.url_under_test,
            format='json'
        )


class DELETEDataSeriesRESTPermissionTest(NonGetDataSeriesRestPermissionTestMixin, BaseDataSeriesRESTPermissionTest):

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_DATA_SERIES,
            method='DELETE'
        )

    def method_under_test_malformed(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.delete(
            path=self.url_under_test,
            format='json'
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def proper_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.delete(
            path=self.url_under_test,
            format='json'
        )


del BaseDataSeriesRESTPermissionTest
