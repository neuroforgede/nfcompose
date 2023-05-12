# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from typing import Dict, Any

from django.contrib.auth.models import User
from guardian.shortcuts import assign_perm  # type: ignore
from rest_framework import status
from rest_framework.test import APIClient

from skipper import modules
from skipper.core.models.tenant import Tenant, Tenant_User
from skipper.core.tests.base import BASE_URL, BaseViewTest
from skipper.flow.models import Engine, ALL_AVAILABLE_ENGINE_PERMISSION_STRINGS, \
    HttpEndpoint, ALL_AVAILABLE_HTTP_ENDPOINT_PERMISSION_STRINGS, \
    DEFAULT_PERMISSION_STRINGS_ON_HTTP_ENDPOINT_CREATE, flow_permission_for_rest_method, ENGINE_PERMISSION_KEY_ENGINE

HTTP_ENDPOINT_BASE_URL = BASE_URL + modules.url_representation(modules.Module.FLOW) + '/httpendpoint/'
ENGINE_ENDPOINT_BASE_URL = BASE_URL + modules.url_representation(modules.Module.FLOW) + '/engine/'


class HttpEndpointCrudTest(BaseViewTest):
    url_under_test = HTTP_ENDPOINT_BASE_URL
    simulate_other_tenant = True
    skip_setup_assertions = True
    
    engine_json: Dict[str, Any]
    
    def setUp(self) -> None:
        super().setUp()
        self.engine_json = self.client.post(path=ENGINE_ENDPOINT_BASE_URL, data={
            "external_id": "1",
            "upstream": "http://hans.peter.local/"
        }).json()

    def test_system_endpoints_are_filtered_out_by_url_GET(self) -> None:
        endpoint = HttpEndpoint.objects.create(
            engine=None,
            system=True,
            path='/',
            method='GET',
            public=False,
            tenant=Tenant.objects.get(name='default_tenant')
        )
        response = self.client.get(path=f'{HTTP_ENDPOINT_BASE_URL}{str(endpoint.id)}/')
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_system_endpoints_are_filtered_out_by_url_PUT(self) -> None:
        endpoint = HttpEndpoint.objects.create(
            engine=None,
            system=True,
            path='/',
            method='GET',
            public=False,
            tenant=Tenant.objects.get(name='default_tenant')
        )
        response = self.client.put(path=f'{HTTP_ENDPOINT_BASE_URL}{str(endpoint.id)}/', data={})
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_system_endpoints_are_filtered_out_by_url_PATCH(self) -> None:
        endpoint = HttpEndpoint.objects.create(
            engine=None,
            system=True,
            path='/',
            method='GET',
            public=False,
            tenant=Tenant.objects.get(name='default_tenant')
        )
        response = self.client.patch(path=f'{HTTP_ENDPOINT_BASE_URL}{str(endpoint.id)}/', data={})
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_system_endpoints_are_filtered_out_by_url_DELETE(self) -> None:
        endpoint = HttpEndpoint.objects.create(
            engine=None,
            system=True,
            path='/',
            method='GET',
            public=False,
            tenant=Tenant.objects.get(name='default_tenant')
        )
        response = self.client.delete(path=f'{HTTP_ENDPOINT_BASE_URL}{str(endpoint.id)}/')
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_system_endpoints_are_filtered_out_by_url_OPTIONS(self) -> None:
        endpoint = HttpEndpoint.objects.create(
            engine=None,
            system=True,
            path='/',
            method='GET',
            public=False,
            tenant=Tenant.objects.get(name='default_tenant')
        )
        response = self.client.options(path=f'{HTTP_ENDPOINT_BASE_URL}{str(endpoint.id)}/')
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_system_endpoints_are_filtered_out_by_url_HEAD(self) -> None:
        endpoint = HttpEndpoint.objects.create(
            engine=None,
            system=True,
            path='/',
            method='GET',
            public=False,
            tenant=Tenant.objects.get(name='default_tenant')
        )
        response = self.client.head(path=f'{HTTP_ENDPOINT_BASE_URL}{str(endpoint.id)}/')
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_system_endpoints_are_filtered_out_in_list(self) -> None:
        HttpEndpoint.objects.create(
            engine=None,
            system=True,
            path='/',
            method='GET',
            public=False,
            tenant=Tenant.objects.get(name='default_tenant')
        )
        response = self.client.get(path=f'{HTTP_ENDPOINT_BASE_URL}')
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(0, len(response.json()['results']))

    def test_create_enforces_unique_external_id(self) -> None:
        response = self.client.post(path=HTTP_ENDPOINT_BASE_URL, data={
            "engine": self.engine_json['url'],
            "external_id": '1',
            "path": "/",
            "method": 'GET',
            "public": True
        })
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        response = self.client.post(path=HTTP_ENDPOINT_BASE_URL, data={
            "engine": self.engine_json['url'],
            "external_id": '1',
            "path": "/",
            "method": 'GET',
            "public": True
        })
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual(1, len(HttpEndpoint.objects.filter()))

    def test_create_allows_same_external_id_but_other_tenant(self) -> None:
        response = self.client.post(path=HTTP_ENDPOINT_BASE_URL, data={
            "engine": self.engine_json['url'],
            "external_id": '1',
            "path": "/",
            "method": 'GET',
            "public": True
        })
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        engine2_json = self.client2.post(path=ENGINE_ENDPOINT_BASE_URL, data={
            "external_id": "1",
            "upstream": "http://hans.peter.local/"
        }).json()
        response = self.client2.post(path=HTTP_ENDPOINT_BASE_URL, data={
            "engine": engine2_json['url'],
            "external_id": '1',
            "path": "/",
            "method": 'GET',
            "public": True
        })
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        self.assertEqual(2, len(HttpEndpoint.objects.all()))

    def test_create_allows_only_engine_of_same_tenant(self) -> None:
        engine2_json = self.client2.post(path=ENGINE_ENDPOINT_BASE_URL, data={
            "external_id": "1",
            "upstream": "http://hans.peter.local/"
        }).json()

        response = self.client.post(path=HTTP_ENDPOINT_BASE_URL, data={
            "engine": engine2_json['url'],
            "external_id": '1',
            "path": "/",
            "method": 'GET',
            "public": True
        })
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_create_sets_public_true(self) -> None:
        response = self.client.post(path=HTTP_ENDPOINT_BASE_URL, data={
            "engine": self.engine_json['url'],
            "external_id": '1',
            "path": "/",
            "method": 'GET',
            "public": True
        })
        endpoint: HttpEndpoint = HttpEndpoint.objects.get(id=response.json()['id'])
        self.assertTrue(endpoint.public)

    def test_create_sets_public_false(self) -> None:
        response = self.client.post(path=HTTP_ENDPOINT_BASE_URL, data={
            "engine": self.engine_json['url'],
            "external_id": '1',
            "path": "/",
            "method": 'GET',
            "public": False
        })
        endpoint: HttpEndpoint = HttpEndpoint.objects.get(id=response.json()['id'])
        self.assertFalse(endpoint.public)

    def test_create_sets_path(self) -> None:
        response = self.client.post(path=HTTP_ENDPOINT_BASE_URL, data={
            "engine": self.engine_json['url'],
            "external_id": '1',
            "path": "/",
            "method": 'GET',
            "public": False
        })
        endpoint: HttpEndpoint = HttpEndpoint.objects.get(id=response.json()['id'])
        self.assertEqual('/', endpoint.path)

    def test_create_sets_engine(self) -> None:
        response = self.client.post(path=HTTP_ENDPOINT_BASE_URL, data={
            "engine": self.engine_json['url'],
            "external_id": '1',
            "path": "/",
            "method": 'GET',
            "public": False
        })
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        endpoint: HttpEndpoint = HttpEndpoint.objects.get(id=response.json()['id'])
        self.assertIsNotNone(endpoint.engine)

    def test_can_find_by_url(self) -> None:
        response = self.client.post(path=HTTP_ENDPOINT_BASE_URL, data={
            "engine": self.engine_json['url'],
            "external_id": '1',
            "path": "/",
            "method": 'GET',
            "public": False
        })
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        response2 = self.client.get(path=response.json()['url'])
        self.assertEqual(status.HTTP_200_OK, response2.status_code)

    def test_other_tenant_cant_access_by_direct_url(self) -> None:
        response = self.client.post(path=HTTP_ENDPOINT_BASE_URL, data={
            "engine": self.engine_json['url'],
            "external_id": '1',
            "path": "/",
            "method": 'GET',
            "public": False
        })
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        other_tenant_response = self.client2.get(path=response.json()['url'])
        self.assertEqual(status.HTTP_404_NOT_FOUND, other_tenant_response.status_code)

    def test_other_tenant_cant_find_it_via_list(self) -> None:
        response = self.client.post(path=HTTP_ENDPOINT_BASE_URL, data={
            "engine": self.engine_json['url'],
            "external_id": '1',
            "path": "/",
            "method": 'GET',
            "public": False
        })
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        other_tenant_response = self.client2.get(path=HTTP_ENDPOINT_BASE_URL)
        self.assertEqual(status.HTTP_200_OK, other_tenant_response.status_code)
        self.assertEqual(0, len(other_tenant_response.json()['results']))

    def test_default_permissions_is_equal_to_all_on_create(self) -> None:
        # This is here so that we don't actually mess up, asserts that we always give all permissions here
        # for users that created a resource
        self.assertEqual(set(ALL_AVAILABLE_HTTP_ENDPOINT_PERMISSION_STRINGS), set(DEFAULT_PERMISSION_STRINGS_ON_HTTP_ENDPOINT_CREATE))

    def test_create_should_assign_proper_default_object_level_permissions(self) -> None:
        tenant = Tenant.objects.filter(
            name='default_tenant'
        )[0]
        user = User.objects.create(
            username='my_awesome_test_user',
            password='my_awesome_test_user',
            email='mytest@neuroforge.de'
        )
        Tenant_User.objects.create(
            tenant=tenant,
            user=user
        )

        engine = Engine.objects.get(id=self.engine_json['id'])

        for elem in ALL_AVAILABLE_HTTP_ENDPOINT_PERMISSION_STRINGS:
            assign_perm(elem, user)

        for elem in ALL_AVAILABLE_ENGINE_PERMISSION_STRINGS:
            assign_perm(elem, user, obj=engine)
            assign_perm(elem, user)

        client = APIClient()
        client.force_login(user)

        response = client.post(path=HTTP_ENDPOINT_BASE_URL, data={
            "engine": self.engine_json['url'],
            "external_id": '1',
            "path": "/",
            "method": 'GET',
            "public": False
        })
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        http_endpoint = HttpEndpoint.objects.get(external_id='1')

        for elem in DEFAULT_PERMISSION_STRINGS_ON_HTTP_ENDPOINT_CREATE:
            self.assertTrue(user.has_perm(elem, obj=http_endpoint))


    def test_user_needs_proper_permissions_on_engine_to_use(self) -> None:
        tenant = Tenant.objects.filter(
            name='default_tenant'
        )[0]
        user = User.objects.create(
            username='my_awesome_test_user',
            password='my_awesome_test_user',
            email='mytest@neuroforge.de'
        )
        Tenant_User.objects.create(
            tenant=tenant,
            user=user
        )

        engine = Engine.objects.get(id=self.engine_json['id'])

        for elem in ALL_AVAILABLE_HTTP_ENDPOINT_PERMISSION_STRINGS:
            assign_perm(elem, user)

        for elem in ALL_AVAILABLE_ENGINE_PERMISSION_STRINGS:
            # dont assign permissions here just yet
            assign_perm(elem, user)

        client = APIClient()
        client.force_login(user)

        response = client.post(path=HTTP_ENDPOINT_BASE_URL, data={
            "engine": self.engine_json['url'],
            "external_id": '1',
            "path": "/",
            "method": 'GET',
            "public": False
        })
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

        assign_perm(f"flow.{flow_permission_for_rest_method('engine', 'GET', ENGINE_PERMISSION_KEY_ENGINE)}", user, obj=engine)

        response = client.post(path=HTTP_ENDPOINT_BASE_URL, data={
            "engine": self.engine_json['url'],
            "external_id": '1',
            "path": "/",
            "method": 'GET',
            "public": False
        })
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        http_endpoint = HttpEndpoint.objects.get(external_id='1')

        for elem in DEFAULT_PERMISSION_STRINGS_ON_HTTP_ENDPOINT_CREATE:
            self.assertTrue(user.has_perm(elem, obj=http_endpoint))

    def _assert_in_db(self, response_http_endpoint: Dict[str, Any], engine_json: Dict[str, Any]) -> None:
        endpoint = HttpEndpoint.objects.get(id=response_http_endpoint['id'])
        self.assertEqual(str(endpoint.id), response_http_endpoint['id'])
        self.assertEqual(endpoint.external_id, response_http_endpoint['external_id'])
        self.assertEqual(endpoint.public, response_http_endpoint['public'])
        self.assertEqual(endpoint.path, response_http_endpoint['path'])
        self.assertEqual(endpoint.method, response_http_endpoint['method'])

        self.assertEqual(str(endpoint.engine.id), engine_json['id'])

        # has tenant set, unit tests use this per default in self.client
        self.assertEqual(endpoint.tenant.name, 'default_tenant')

    def test_post_without_external_id_should_fail(self) -> None:
        response = self.client.post(path=HTTP_ENDPOINT_BASE_URL, data={
            "engine": self.engine_json['url'],
            "path": "/",
            "method": 'GET',
            "public": False
        })
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

        self.assertEqual(0, len(HttpEndpoint.objects.all()))

    def test_post_with_wrong_external_id_should_fail(self) -> None:
        response = self.client.post(path=HTTP_ENDPOINT_BASE_URL, data={
            "engine": self.engine_json['url'],
            "external_id": "12%21$",
            "path": "/",
            "method": 'GET',
            "public": False
        })
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

        self.assertEqual(0, len(HttpEndpoint.objects.all()))

    def test_post_works_with_all_set(self) -> None:
        response = self.client.post(path=HTTP_ENDPOINT_BASE_URL, data={
            "engine": self.engine_json['url'],
            "external_id": "1",
            "path": "/",
            "method": 'GET',
            "public": False
        })
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        response_engine = response.json()
        self._assert_in_db(response_engine, self.engine_json)

    def test_post_duplicate_should_raise_400(self) -> None:
        response = self.client.post(path=HTTP_ENDPOINT_BASE_URL, data={
            "engine": self.engine_json['url'],
            "external_id": "11",
            "path": "/",
            "method": 'GET',
            "public": False
        })
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        self._assert_in_db(response.json(), self.engine_json)

        failed_response = self.client.post(path=HTTP_ENDPOINT_BASE_URL, data={
            "engine": self.engine_json['url'],
            "external_id": "11",
            "path": "/ssdfsf",
            "method": 'POST',
            "public": True
        })
        self.assertEqual(status.HTTP_400_BAD_REQUEST, failed_response.status_code)

        self._assert_in_db(response.json(), self.engine_json)

    def test_post_external_id_required(self) -> None:
        response = self.client.post(path=HTTP_ENDPOINT_BASE_URL, data={
            "external_id": "",
            "engine": self.engine_json['url'],
            "path": "/",
            "method": 'GET',
            "public": False
        })
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

        self.assertEqual(0, len(HttpEndpoint.objects.all()))

    def test_delete_engine_is_disallowed_if_it_is_referenced(self) -> None:
        response = self.client.post(path=HTTP_ENDPOINT_BASE_URL, data={
            "engine": self.engine_json['url'],
            "external_id": "11",
            "path": "/",
            "method": 'GET',
            "public": False
        })
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        self._assert_in_db(response.json(), self.engine_json)

        endpoint = response.json()

        engine_delete = self.client.delete(path=self.engine_json['url'], data={
            "engine": self.engine_json['url'],
            "external_id": "22",
            "path": "/",
            "method": 'GET',
            "public": False
        })
        self.assertEqual(status.HTTP_400_BAD_REQUEST, engine_delete.status_code)

        self._assert_in_db(endpoint, self.engine_json)

    def test_delete_engine_is_allowed_if_it_is_referenced_with_cascade(self) -> None:
        response = self.client.post(path=HTTP_ENDPOINT_BASE_URL, data={
            "engine": self.engine_json['url'],
            "external_id": "11",
            "path": "/",
            "method": 'GET',
            "public": False
        })
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        self._assert_in_db(response.json(), self.engine_json)

        endpoint = response.json()

        engine_delete = self.client.delete(path=self.engine_json['url'] + '?cascade_delete', data={
            "engine": self.engine_json['url'],
            "external_id": "22",
            "path": "/",
            "method": 'GET',
            "public": False
        })
        self.assertEqual(status.HTTP_204_NO_CONTENT, engine_delete.status_code)

        self.assertEqual(0, len(Engine.objects.all()))
        self.assertEqual(0, len(HttpEndpoint.objects.all()))

    def test_delete_engine_is_allowed_if_it_is_referenced_but_endpoint_is_also_dead(self) -> None:
        response = self.client.post(path=HTTP_ENDPOINT_BASE_URL, data={
            "engine": self.engine_json['url'],
            "external_id": "11",
            "path": "/",
            "method": 'GET',
            "public": False
        })
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        self._assert_in_db(response.json(), self.engine_json)

        endpoint = response.json()

        response = self.client.delete(endpoint['url'])
        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)

        self.assertEqual(0, len(HttpEndpoint.objects.all()))

        engine_delete = self.client.delete(path=self.engine_json['url'], data={
            "engine": self.engine_json['url'],
            "external_id": "22",
            "path": "/",
            "method": 'GET',
            "public": False
        })
        self.assertEqual(status.HTTP_204_NO_CONTENT, engine_delete.status_code)

        self.assertEqual(0, len(Engine.objects.all()))

    def test_put_external_id_not_allowed_to_be_changed(self) -> None:
        response = self.client.post(path=HTTP_ENDPOINT_BASE_URL, data={
            "engine": self.engine_json['url'],
            "external_id": "11",
            "path": "/",
            "method": 'GET',
            "public": False
        })
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        self._assert_in_db(response.json(), self.engine_json)

        endpoint = response.json()

        broken_put = self.client.put(path=endpoint['url'], data={
            "engine": self.engine_json['url'],
            "external_id": "22",
            "path": "/",
            "method": 'GET',
            "public": False
        })
        self.assertEqual(status.HTTP_400_BAD_REQUEST, broken_put.status_code)

        self._assert_in_db(response.json(), self.engine_json)

    def test_patch_external_id_not_allowed_to_be_changed(self) -> None:
        response = self.client.post(path=HTTP_ENDPOINT_BASE_URL, data={
            "engine": self.engine_json['url'],
            "external_id": "11",
            "path": "/",
            "method": 'GET',
            "public": False
        })
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        self._assert_in_db(response.json(), self.engine_json)

        endpoint = response.json()

        broken_put = self.client.patch(path=endpoint['url'], data={
            "external_id": "2"
        })
        self.assertEqual(status.HTTP_400_BAD_REQUEST, broken_put.status_code)

        self.assertEqual(1, len(HttpEndpoint.objects.all()))
        self.assertEqual(0, len(HttpEndpoint.objects.filter(external_id='2')))

        self._assert_in_db(endpoint, self.engine_json)

    def test_put_with_changes_but_same_external_id(self) -> None:
        response = self.client.post(path=HTTP_ENDPOINT_BASE_URL, data={
            "engine": self.engine_json['url'],
            "external_id": "11",
            "path": "/",
            "method": 'GET',
            "public": False
        })
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        self._assert_in_db(response.json(), self.engine_json)

        endpoint = response.json()

        engine2_json = self.client.post(path=ENGINE_ENDPOINT_BASE_URL, data={
            "external_id": "2",
            "upstream": "http://hans.peter.local/"
        }).json()

        proper_put = self.client.put(path=endpoint['url'], data={
            "engine": engine2_json['url'],
            "external_id": "11",
            "path": "/sss",
            "method": 'POST',
            "public": True
        })
        self.assertEqual(status.HTTP_200_OK, proper_put.status_code)
        self._assert_in_db(proper_put.json(), engine2_json)

    def test_patch_with_changes_but_same_external_id(self) -> None:
        response = self.client.post(path=HTTP_ENDPOINT_BASE_URL, data={
            "engine": self.engine_json['url'],
            "external_id": "11",
            "path": "/",
            "method": 'GET',
            "public": False
        })
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        self._assert_in_db(response.json(), self.engine_json)

        endpoint = response.json()

        engine2_json = self.client.post(path=ENGINE_ENDPOINT_BASE_URL, data={
            "external_id": "2",
            "upstream": "http://hans.peter.local/"
        }).json()

        proper_put = self.client.patch(path=endpoint['url'], data={
            "engine": engine2_json['url'],
            "external_id": "11",
            "path": "/sss",
            "method": 'POST',
            "public": True
        })
        self.assertEqual(status.HTTP_200_OK, proper_put.status_code)
        self._assert_in_db(proper_put.json(), engine2_json)

    def test_post_data_same_as_passed_into(self) -> None:
        response = self.client.post(path=HTTP_ENDPOINT_BASE_URL, data={
            "engine": self.engine_json['url'],
            "external_id": "11",
            "path": "/",
            "method": 'GET',
            "public": False
        })
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        self._assert_in_db(response.json(), self.engine_json)

        endpoint = response.json()

        self.assertEqual('11', endpoint['external_id'])
        self.assertEqual('/', endpoint['path'])
        self.assertEqual('GET', endpoint['method'])
        self.assertEqual(False, endpoint['public'])

    def test_put_data_same_as_passed_into(self) -> None:
        response = self.client.post(path=HTTP_ENDPOINT_BASE_URL, data={
            "engine": self.engine_json['url'],
            "external_id": "11",
            "path": "/",
            "method": 'GET',
            "public": False
        })
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        self._assert_in_db(response.json(), self.engine_json)

        endpoint = response.json()

        fetched_again = self.get_payload(url=endpoint['url'])
        self.assertEqual(self.engine_json['url'], fetched_again['engine'])
        self.assertEqual('11', fetched_again['external_id'])
        self.assertEqual('/', fetched_again['path'])
        self.assertEqual('GET', fetched_again['method'])
        self.assertEqual(False, fetched_again['public'])

        engine2_json = self.client.post(path=ENGINE_ENDPOINT_BASE_URL, data={
            "external_id": "2",
            "upstream": "http://hans.peter.local/"
        }).json()

        updated_response = self.client.put(path=endpoint['url'], data={
            "engine": engine2_json['url'],
            "external_id": "11",
            "path": "/ss",
            "method": 'POST',
            "public": True
        })
        self.assertEqual(status.HTTP_200_OK, updated_response.status_code)

        self._assert_in_db(updated_response.json(), engine2_json)

        fetched_updated_again = self.get_payload(url=endpoint['url'])
        self.assertEqual(engine2_json['url'], fetched_updated_again['engine'])
        self.assertEqual('11', fetched_updated_again['external_id'])
        self.assertEqual('/ss', fetched_updated_again['path'])
        self.assertEqual('POST', fetched_updated_again['method'])
        self.assertEqual(True, fetched_updated_again['public'])


    def test_patch_data_same_as_passed_into(self) -> None:
        response = self.client.post(path=HTTP_ENDPOINT_BASE_URL, data={
            "engine": self.engine_json['url'],
            "external_id": "11",
            "path": "/",
            "method": 'GET',
            "public": False
        })
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        self._assert_in_db(response.json(), self.engine_json)

        endpoint = response.json()

        fetched_again = self.get_payload(url=endpoint['url'])
        self.assertEqual(self.engine_json['url'], fetched_again['engine'])
        self.assertEqual('11', fetched_again['external_id'])
        self.assertEqual('/', fetched_again['path'])
        self.assertEqual('GET', fetched_again['method'])
        self.assertEqual(False, fetched_again['public'])

        engine2_json = self.client.post(path=ENGINE_ENDPOINT_BASE_URL, data={
            "external_id": "2",
            "upstream": "http://hans.peter.local/"
        }).json()

        updated_response = self.client.patch(path=endpoint['url'], data={
            "engine": engine2_json['url'],
            "external_id": "11",
            "path": "/ss",
            "method": 'POST',
            "public": True
        })
        self.assertEqual(status.HTTP_200_OK, updated_response.status_code)

        self._assert_in_db(updated_response.json(), engine2_json)

        fetched_updated_again = self.get_payload(url=endpoint['url'])
        self.assertEqual(engine2_json['url'], fetched_updated_again['engine'])
        self.assertEqual('11', fetched_updated_again['external_id'])
        self.assertEqual('/ss', fetched_updated_again['path'])
        self.assertEqual('POST', fetched_updated_again['method'])
        self.assertEqual(True, fetched_updated_again['public'])

    def test_delete(self) -> None:
        response = self.client.post(path=HTTP_ENDPOINT_BASE_URL, data={
            "engine": self.engine_json['url'],
            "external_id": "11",
            "path": "/",
            "method": 'GET',
            "public": False
        })
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        self._assert_in_db(response.json(), self.engine_json)

        delete_response = self.client.delete(path=response.json()['url'])

        self.assertEqual(status.HTTP_204_NO_CONTENT, delete_response.status_code)

        not_found_response = self.client.get(path=response.json()['url'])
        self.assertEqual(status.HTTP_404_NOT_FOUND, not_found_response.status_code)

        self.assertEqual(0, len(HttpEndpoint.objects.all()))

