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
from django_multitenant.utils import set_current_tenant  # type: ignore
from rest_framework import status

from skipper.core.models.tenant import Tenant
from skipper.dataseries.models import DATASERIES_PERMISSION_KEY_DATA_SERIES, \
    DATASERIES_PERMISSION_KEY_CHECK_EXTERNAL_IDS, ds_permission_for_rest_method
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.tests.base.data_series_child_list_permission_test import BaseDataSeriesDetailPermissionTest, \
    DATA_SERIES_BASE_URL


class GETDataSeriesDetailPermissionTest(BaseDataSeriesDetailPermissionTest):

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            # explicitly wrong one, the base test handles everything already
            # FIXME: do this a bit more elegantly
            action=DATASERIES_PERMISSION_KEY_CHECK_EXTERNAL_IDS,
            method='OPTIONS'
        )

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return None

    def malformed_with_permission_status(self) -> int:
        raise NotImplementedError()

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return cast(TestHttpResponse, self.user_client.get(
            path=self.data_series_json['url'],
            format='json'
        ))


class POSTDataSeriesDetailPermissionTest(BaseDataSeriesDetailPermissionTest):

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_DATA_SERIES,
            method='POST'
        )

    def method_under_test_malformed(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.post(
            path=self.data_series_json['url'],
            format='json',
            data={}
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def proper_with_permission_status(self) -> int:
        return status.HTTP_405_METHOD_NOT_ALLOWED

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.post(
            path=self.data_series_json['url'],
            format='json',
            data={}
        )


class PUTDataSeriesDetailPermissionTest(BaseDataSeriesDetailPermissionTest):

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_DATA_SERIES,
            method='PUT'
        )

    def method_under_test_malformed(self) -> Union[HttpResponse, TestHttpResponse]:
        put_request = self.user_client.put(
            path=self.data_series_json['url'],
            format='json',
            data={
                **self.data_series_json,
                'external_id': '123'
            }
        )
        return put_request

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_400_BAD_REQUEST

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.put(
            path=self.data_series_json['url'],
            format='json',
            data={
                **self.data_series_json,
                'name': "123"
            }
        )


class PATCHDataSeriesDetailPermissionTest(BaseDataSeriesDetailPermissionTest):

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_DATA_SERIES,
            method='PATCH'
        )

    def method_under_test_malformed(self) -> Union[HttpResponse, TestHttpResponse]:
        put_request = self.user_client.patch(
            path=self.data_series_json['url'],
            format='json',
            data={
                'external_id': '123'
            }
        )
        return put_request

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_400_BAD_REQUEST

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.patch(
            path=self.data_series_json['url'],
            format='json',
            data={
                'name': "123"
            }
        )

class HEADDataSeriesDetailPermissionTest(BaseDataSeriesDetailPermissionTest):

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_DATA_SERIES,
            method='HEAD'
        )

    def method_under_test_malformed(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.head(
            path=self.data_series_json['url'],
            format='json'
        )

    def malformed_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def proper_with_permission_status(self) -> int:
        return status.HTTP_200_OK

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.head(
            path=self.data_series_json['url'],
            format='json'
        )


class OPTIONSDataSeriesDetailPermissionTest(BaseDataSeriesDetailPermissionTest):

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_DATA_SERIES,
            method='OPTIONS'
        )

    def method_under_test_malformed(self) -> Union[HttpResponse, TestHttpResponse]:
        return self.user_client.options(
            path=self.data_series_json['url'],
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
            path=self.data_series_json['url'],
            format='json'
        )


class DELETEDataSeriesDetailPermissionTest(BaseDataSeriesDetailPermissionTest):

    def permission_code_name(self) -> str:
        return ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_DATA_SERIES,
            method='DELETE'
        )

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        return None

    def malformed_with_permission_status(self) -> int:
        raise NotImplementedError()

    def proper_with_permission_status(self) -> int:
        return status.HTTP_204_NO_CONTENT

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        response = self.user_client.delete(
            path=self.data_series_json['url'],
            format='json'
        )
        set_current_tenant(Tenant.objects.filter(
            name='default_tenant'
        )[0])
        in_db: DataSeries = DataSeries.all_objects.filter(
            id=self.data_series_json['id']
        ).all()[0]
        in_db.deleted_at = None
        in_db.save()
        set_current_tenant(None)
        return response
