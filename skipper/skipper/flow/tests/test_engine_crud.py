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
    DEFAULT_PERMISSION_STRINGS_ON_ENGINE_CREATE

ENGINE_BASE_URL = BASE_URL + modules.url_representation(modules.Module.FLOW) + '/engine/'

# TODO: move this test into some sort of "base" unit test that can be configured
#  so that we do not have to write this sort of unit test every time


class EngineCrudTest(BaseViewTest):
    url_under_test = ENGINE_BASE_URL
    simulate_other_tenant = True
    skip_setup_assertions = True

    def test_can_find_by_url(self) -> None:
        response = self.client.post(path=ENGINE_BASE_URL, data={
            "external_id": "1",
            "upstream": "http://hans.peter.local/"
        })
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        response2 = self.client.get(path=response.json()['url'])
        self.assertEqual(status.HTTP_200_OK, response2.status_code)

    def test_no_secret_returned(self) -> None:
        response = self.client.post(path=ENGINE_BASE_URL, data={
            "external_id": "1",
            "upstream": "http://hans.peter.local/"
        })
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        self.assertTrue(response.json()['secret'].startswith('http://'))

        response2 = self.client.get(path=response.json()['url'])
        self.assertEqual(status.HTTP_200_OK, response2.status_code)
        self.assertTrue(response2.json()['secret'].startswith('http://'))

    def test_other_tenant_cant_access_by_direct_url(self) -> None:
        response = self.client.post(path=ENGINE_BASE_URL, data={
            "external_id": "1",
            "upstream": "http://hans.peter.local/"
        })
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        other_tenant_response = self.client2.get(path=response.json()['url'])
        self.assertEqual(status.HTTP_404_NOT_FOUND, other_tenant_response.status_code)

    def test_other_tenant_cant_find_it_via_list(self) -> None:
        response = self.client.post(path=ENGINE_BASE_URL, data={
            "external_id": "1",
            "upstream": "http://hans.peter.local/"
        })
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        other_tenant_response = self.client2.get(path=ENGINE_BASE_URL)
        self.assertEqual(status.HTTP_200_OK, other_tenant_response.status_code)
        self.assertEqual(0, len(other_tenant_response.json()['results']))

    def test_other_tenant_can_create_with_same_external_id(self) -> None:
        response = self.client.post(path=ENGINE_BASE_URL, data={
            "external_id": "1",
            "upstream": "http://hans.peter.local/"
        })
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        other_tenant_response = self.client2.post(path=ENGINE_BASE_URL, data={
            "external_id": "1",
            "upstream": "http://hans.peter.local/"
        })
        self.assertEqual(status.HTTP_201_CREATED, other_tenant_response.status_code)

        self.assertEqual(2, len(Engine.objects.filter(external_id="1")))

    def test_default_permissions_is_equal_to_all_on_create(self) -> None:
        # This is here so that we don't actually mess up, asserts that we always give all permissions here
        # for users that created a resource
        self.assertEqual(set(ALL_AVAILABLE_ENGINE_PERMISSION_STRINGS), set(DEFAULT_PERMISSION_STRINGS_ON_ENGINE_CREATE))

    def test_create_should_assign_proper_default_object_level_permissions(self) -> None:
        tenant = Tenant.objects.filter(
            name='default_tenant'
        )[0]
        user = User.objects.create_superuser(
            username='my_awesome_test_user',
            password='my_awesome_test_user',
            email='mytest@neuroforge.de'
        )
        Tenant_User.objects.create(
            tenant=tenant,
            user=user
        )
        for elem in ALL_AVAILABLE_ENGINE_PERMISSION_STRINGS:
            assign_perm(elem, user)

        client = APIClient()
        client.force_login(user)

        response = client.post(path=ENGINE_BASE_URL, data={
            "external_id": "1",
            "upstream": "http://hans.peter.local/"
        })
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        engine = Engine.objects.get(external_id='1')

        for elem in DEFAULT_PERMISSION_STRINGS_ON_ENGINE_CREATE:
            self.assertTrue(user.has_perm(elem, obj=engine))

    def _assert_in_db(self, response_engine: Dict[str, Any]) -> None:
        engine = Engine.objects.get(id=response_engine['id'])
        self.assertEqual(str(engine.id), response_engine['id'])
        self.assertEqual(engine.external_id, response_engine['external_id'])
        self.assertEqual(engine.upstream, response_engine['upstream'])

        # has tenant set, unit tests use this per default in self.client
        self.assertEqual(engine.tenant.name, 'default_tenant')

    def test_post_without_external_id_should_fail(self) -> None:
        response = self.client.post(path=ENGINE_BASE_URL, data={
            "upstream": "http://hans.peter.local/"
        })
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

        self.assertEqual(0, len(Engine.objects.all()))

    def test_post_with_wrong_external_id_should_fail(self) -> None:
        response = self.client.post(path=ENGINE_BASE_URL, data={
            "external_id": "12&%12",
            "upstream": "http://hans.peter.local/"
        })
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

        self.assertEqual(0, len(Engine.objects.all()))

    def test_post_works_with_all_set(self) -> None:
        response = self.client.post(path=ENGINE_BASE_URL, data={
            "external_id": "1",
            "upstream": "http://hans.peter.local/"
        })
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        response_engine = response.json()
        self._assert_in_db(response_engine)

    def test_post_duplicate_should_raise_400(self) -> None:
        response = self.client.post(path=ENGINE_BASE_URL, data={
            "external_id": "1",
            "upstream": "http://hans.peter.local/"
        })
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        self._assert_in_db(response.json())

        failed_response = self.client.post(path=ENGINE_BASE_URL, data={
            "external_id": "1",
            "upstream": "http://hans.peter.local/"
        })
        self.assertEqual(status.HTTP_400_BAD_REQUEST, failed_response.status_code)

        self._assert_in_db(response.json())

    def test_post_external_id_required(self) -> None:
        response = self.client.post(path=ENGINE_BASE_URL, data={
            "external_id": "",
            "upstream": "http://hans.peter.local/"
        })
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_put_external_id_not_allowed_to_be_changed(self) -> None:
        response = self.client.post(path=ENGINE_BASE_URL, data={
            "external_id": "1",
            "upstream": "http://hans.peter.local/"
        })
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        self._assert_in_db(response.json())

        engine = response.json()

        broken_put = self.client.put(path=engine['url'], data={
            "external_id": "2",
            "upstream": "http://hans.peter.local/"
        })
        self.assertEqual(status.HTTP_400_BAD_REQUEST, broken_put.status_code)

        self._assert_in_db(response.json())

    def test_patch_external_id_not_allowed_to_be_changed(self) -> None:
        response = self.client.post(path=ENGINE_BASE_URL, data={
            "external_id": "1",
            "upstream": "http://hans.peter.local/"
        })
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        self._assert_in_db(response.json())

        engine = response.json()

        broken_put = self.client.patch(path=engine['url'], data={
            "external_id": "2"
        })
        self.assertEqual(status.HTTP_400_BAD_REQUEST, broken_put.status_code)

        self.assertEqual(1, len(Engine.objects.all()))
        self.assertEqual(0, len(Engine.objects.filter(external_id='2')))

        self._assert_in_db(engine)

    def test_put_with_changes_but_same_external_id(self) -> None:
        response = self.client.post(path=ENGINE_BASE_URL, data={
            "external_id": "1",
            "upstream": "http://hans.peter.local/"
        })
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        self._assert_in_db(response.json())

        engine = response.json()

        proper_put = self.client.put(path=engine['url'], data={
            "external_id": "1",
            "upstream": "http://hans.dampf.local/"
        })
        self.assertEqual(status.HTTP_200_OK, proper_put.status_code)

        self._assert_in_db(proper_put.json())

    def test_patch_with_changes_but_same_external_id(self) -> None:
        response = self.client.post(path=ENGINE_BASE_URL, data={
            "external_id": "1",
            "upstream": "http://hans.peter.local/"
        })
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        self._assert_in_db(response.json())

        engine = response.json()

        proper_patch = self.client.patch(path=engine['url'], data={
            "upstream": "http://hans.dampf.local/"
        })
        self.assertEqual(status.HTTP_200_OK, proper_patch.status_code)

        self._assert_in_db(proper_patch.json())

    def test_post_data_same_as_passed_into(self) -> None:
        response = self.client.post(path=ENGINE_BASE_URL, data={
            "external_id": "1",
            "upstream": "http://hans.peter.local/"
        })
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        self._assert_in_db(response.json())

        engine = response.json()

        self.assertEqual('1', engine['external_id'])
        self.assertEqual('http://hans.peter.local/', engine['upstream'])

        fetched_again = self.get_payload(url=engine['url'])
        self.assertEqual('1', fetched_again['external_id'])
        self.assertEqual('http://hans.peter.local/', fetched_again['upstream'])

    def test_put_data_same_as_passed_into(self) -> None:
        response = self.client.post(path=ENGINE_BASE_URL, data={
            "external_id": "1",
            "upstream": "http://hans.peter.local/"
        })
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        self._assert_in_db(response.json())

        engine = response.json()

        self.assertEqual('1', engine['external_id'])
        self.assertEqual('http://hans.peter.local/', engine['upstream'])

        fetched_again = self.get_payload(url=engine['url'])
        self.assertEqual('1', fetched_again['external_id'])
        self.assertEqual('http://hans.peter.local/', fetched_again['upstream'])

        updated_response = self.client.put(path=engine['url'], data={
            "external_id": "1",
            "upstream": "http://hans.dampf.local/"
        })
        self.assertEqual(status.HTTP_200_OK, updated_response.status_code)

        self._assert_in_db(updated_response.json())

        fetched_updated_again = self.get_payload(url=engine['url'])
        self.assertEqual('1', fetched_updated_again['external_id'])
        self.assertEqual('http://hans.dampf.local/', fetched_updated_again['upstream'])

    def test_patch_data_same_as_passed_into(self) -> None:
        response = self.client.post(path=ENGINE_BASE_URL, data={
            "external_id": "1",
            "upstream": "http://hans.peter.local/"
        })
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        self._assert_in_db(response.json())

        engine = response.json()

        self.assertEqual('1', engine['external_id'])
        self.assertEqual('http://hans.peter.local/', engine['upstream'])

        fetched_again = self.get_payload(url=engine['url'])
        self.assertEqual('1', fetched_again['external_id'])
        self.assertEqual('http://hans.peter.local/', fetched_again['upstream'])

        updated_response = self.client.patch(path=engine['url'], data={
            "upstream": "http://hans.dampf.local/"
        })
        self.assertEqual(status.HTTP_200_OK, updated_response.status_code)

        self._assert_in_db(updated_response.json())

        fetched_updated_again = self.get_payload(url=engine['url'])
        self.assertEqual('1', fetched_updated_again['external_id'])
        self.assertEqual('http://hans.dampf.local/', fetched_updated_again['upstream'])

    def test_delete(self) -> None:
        response = self.client.post(path=ENGINE_BASE_URL, data={
            "external_id": "1",
            "upstream": "http://hans.peter.local/"
        })
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        self._assert_in_db(response.json())

        delete_response = self.client.delete(path=response.json()['url'])

        self.assertEqual(status.HTTP_204_NO_CONTENT, delete_response.status_code)

        not_found_response = self.client.get(path=response.json()['url'])
        self.assertEqual(status.HTTP_404_NOT_FOUND, not_found_response.status_code)

        self.assertEqual(0, len(Engine.objects.all()))

