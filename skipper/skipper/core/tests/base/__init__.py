# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from django.db import transaction
from django.db.models import Model
from django.http import HttpResponse
from guardian.shortcuts import assign_perm, remove_perm  # type: ignore

from typing import Type, Any, Dict, Optional, List, Union

from django.contrib.auth.models import User, Permission
from django.test import TestCase
from django_multitenant.utils import set_current_tenant  # type: ignore
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from skipper import settings
from skipper.core.models.tenant import Tenant, Tenant_User
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from django.test.client import _MonkeyPatchedWSGIResponse as TestHttpResponse
else:
    TestHttpResponse = object

BASE_URL = "http://testserver/" + settings.ROOT_API_PATH
LOGIN_URL = BASE_URL + "common/auth/login/"

PAGE_SIZE = settings.DEFAULT_PAGE_SIZE


class BaseDefaultTenantDBTest(TestCase):

    @classmethod
    def setUpTestData(cls: Type['BaseDefaultTenantDBTest']) -> None:
        tenant = Tenant.objects.create(
            name='default_tenant'
        )
        user = User.objects.create_superuser(username='nf', password='nf', email='test@neuroforge.de')
        Tenant_User.objects.create(
            tenant=tenant,
            user=user
        )
        set_current_tenant(tenant)


class BaseViewTest(TestCase):
    url_under_test = BASE_URL + 'common/'
    simulate_other_tenant = False

    client: APIClient
    client2: APIClient
    user: User
    user2: User
    unauthorizedClient: APIClient

    skip_setup_assertions: bool = False

    @classmethod
    def setUpTestData(cls: Type['BaseViewTest']) -> None:
        tenant = Tenant.objects.create(
            name='default_tenant'
        )
        user = User.objects.create_superuser(username='nf', password='nf', email='test@neuroforge.de')
        Tenant_User.objects.create(
            tenant=tenant,
            user=user
        )

        other_tenant = Tenant.objects.create(
            name='other_tenant'
        )
        other_user = User.objects.create_superuser(username='nf2', password='nf2', email='test@neuroforge.de')
        Tenant_User.objects.create(
            tenant=other_tenant,
            user=other_user
        )

        client = APIClient()

        if not cls.skip_setup_assertions:
            response = client.get(path=cls.url_under_test, format='json')
            assert status.HTTP_403_FORBIDDEN == response.status_code

            response = client.post(path=cls.url_under_test, format='json')
            assert status.HTTP_403_FORBIDDEN == response.status_code

            response = client.put(path=cls.url_under_test, format='json')
            assert status.HTTP_403_FORBIDDEN == response.status_code

            response = client.delete(path=cls.url_under_test, format='json')
            assert status.HTTP_403_FORBIDDEN == response.status_code

            if cls.url_under_test != (BASE_URL + 'common/'):
                response = client.get(path=cls.url_under_test + '123l1kjl12öj3kjasf/', format='json')
                assert status.HTTP_403_FORBIDDEN == response.status_code

                response = client.post(path=cls.url_under_test + '123l1kjl12öj3kjasf/', format='json')
                assert status.HTTP_403_FORBIDDEN == response.status_code

                response = client.put(path=cls.url_under_test + '123l1kjl12öj3kjasf/', format='json')
                assert status.HTTP_403_FORBIDDEN == response.status_code

                response = client.delete(path=cls.url_under_test + '123l1kjl12öj3kjasf/', format='json')
                assert status.HTTP_403_FORBIDDEN == response.status_code

    def get_payload(
        self, 
        url: str, 
        payload: Any = None, 
        format: str = 'json', 
        debug: bool = False, 
        client: Optional[APIClient] = None
    ) -> Any:

        _unauthorized = self.unauthorizedClient.get(path=url, format=format, data={})
        self.assertEqual(status.HTTP_403_FORBIDDEN, _unauthorized.status_code)

        _unauthorized_api = self.unauthorizedClient.get(path=url, format='api', data={})
        self.assertEqual(status.HTTP_403_FORBIDDEN, _unauthorized_api.status_code)

        if self.simulate_other_tenant and client is None:
            _other_tenant = self.client2.get(path=url, format=format, data={})
            self.assertEqual(status.HTTP_404_NOT_FOUND, _other_tenant.status_code)

            _other_tenant_api = self.client2.get(path=url, format='api', data={})
            self.assertEqual(status.HTTP_404_NOT_FOUND, _other_tenant_api.status_code)

        response = self._client(client).get(path=url, format=format, data=payload)
        if debug:
            print(response.content)
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        response_api = self._client(client).get(path=url, format='api', data=payload)
        if debug:
            print(response_api.content)
        self.assertEqual(status.HTTP_200_OK, response_api.status_code)

        return response.json()

    def _client(self, client: Optional[APIClient] = None) -> APIClient:
        if client is None:
            return self.client
        return client

    def create_payload_unchecked(
        self, 
        url: str, 
        payload: Any, 
        format: str = 'json', 
        client: Optional[APIClient] = None
    ) -> Response:

        def _payload() -> Any:
            if callable(payload):
                return payload()
            return payload

        created_response = self._client(client).post(path=url, format=format, data=_payload())
        return created_response

    def create_payload(
        self, 
        url: str, 
        payload: Any, 
        format: str = 'json',
        debug: bool = False,
        equality_check: bool = True, 
        client: Optional[APIClient] = None, 
        simulate_tenant: bool = True
    ) -> Any:
        """
        implicitly also tests the detail page (and whether it returns the same content as the creation endpoint)
        """
        _unauthorized = self.unauthorizedClient.post(path=url, format=format, data={})
        self.assertEqual(status.HTTP_403_FORBIDDEN, _unauthorized.status_code)

        def _payload() -> Any:
            if callable(payload):
                return payload()
            return payload

        if simulate_tenant and self.simulate_other_tenant and client is None:
            _other_tenant = self.client2.post(path=url, format=format, data=_payload())
            self.assertEqual(status.HTTP_404_NOT_FOUND, _other_tenant.status_code)

        created_response = self._client(client).post(path=url, format=format, data=_payload())
        if debug:
            print(created_response.content)
        try:
            debug_json = created_response.json()
        except:  # noqa
            debug_json = None
        self.assertEqual(status.HTTP_201_CREATED, created_response.status_code, debug_json)
        created_json = created_response.json()
        if debug:
            print(f'created json: {created_json}')
        detail_json = self.get_payload(created_json['url'], format=format)
        if debug:
            print(f'detail json: {detail_json}')
        if equality_check:
            self.assertEqual(created_json, detail_json)
        return created_json

    def delete_payload(
        self, 
        url: str, 
        payload: Any = None, 
        client: Optional[APIClient] = None
    ) -> Any:
        """
        implicitly also tests the detail page (and whether it returns a 404)
        """
        _unauthorized = self.unauthorizedClient.delete(path=url, format='json', data={})
        self.assertEqual(status.HTTP_403_FORBIDDEN, _unauthorized.status_code)

        if self.simulate_other_tenant and client is None:
            _other_tenant = self.client2.delete(path=url, format='json', data={})
            self.assertEqual(status.HTTP_404_NOT_FOUND, _other_tenant.status_code)

        response = self._client(client).delete(path=url, format='json', data=payload)
        self.assertEqual(status.HTTP_204_NO_CONTENT, response.status_code)
        response_retrieve = self._client(client).get(path=url, format='json')
        self.assertEqual(status.HTTP_404_NOT_FOUND, response_retrieve.status_code)
        return {}

    def update_payload(
        self, 
        url: str, 
        payload: Any, 
        format: str = 'json', 
        debug: bool = False, 
        equality_check: bool = False, 
        client: Optional[APIClient] = None
    ) -> Any:
        """
        implicitly also tests the detail page (and whether it returns the same content as the update endpoint)
        """
        _unauthorized = self.unauthorizedClient.put(path=url, format='json', data={})
        self.assertEqual(status.HTTP_403_FORBIDDEN, _unauthorized.status_code)

        def _payload() -> Any:
            if callable(payload):
                return payload()
            return payload

        if self.simulate_other_tenant and client is None:
            _other_tenant = self.client2.put(path=url, format=format, data=_payload())
            self.assertEqual(status.HTTP_404_NOT_FOUND, _other_tenant.status_code)

        updated_response = self._client(client).put(path=url, format=format, data=_payload())
        if debug:
            print(updated_response.content)
        self.assertEqual(status.HTTP_200_OK, updated_response.status_code)
        updated_json = updated_response.json()
        detail_json = self.get_payload(updated_json['url'], format=format)
        if equality_check:
            self.assertEqual(updated_json, detail_json)
        return updated_json

    def patch_payload(
        self, 
        url: str, 
        payload: Any, 
        format: str = 'json', 
        debug: bool = False, 
        equality_check: bool = False, 
        client: Optional[APIClient] = None
    ) -> Any:
        """
        implicitly also tests the detail page (and whether it returns the same content as the update endpoint)
        """
        _unauthorized = self.unauthorizedClient.patch(path=url, format='json', data={})
        self.assertEqual(status.HTTP_403_FORBIDDEN, _unauthorized.status_code)

        def _payload() -> Any:
            if callable(payload):
                return payload()
            return payload

        if self.simulate_other_tenant and client is None:
            _other_tenant = self.client2.patch(path=url, format=format, data=_payload())
            self.assertEqual(status.HTTP_404_NOT_FOUND, _other_tenant.status_code)

        updated_response = self._client(client).patch(path=url, format=format, data=_payload())
        if debug:
            print(updated_response.content)
        self.assertEqual(status.HTTP_200_OK, updated_response.status_code)
        updated_json = updated_response.json()
        detail_json = self.get_payload(updated_json['url'], format=format)
        if equality_check:
            self.assertEqual(updated_json, detail_json)
        return updated_json

    def setUp(self) -> None:
        self.client = APIClient()
        self.client.login(username='nf', password='nf')
        self.user = User.objects.get(username='nf')
        self.client2 = APIClient()
        self.client2.login(username='nf2', password='nf2')
        self.user2 = User.objects.get(username='nf2')
        self.unauthorizedClient = APIClient()


class _BaseRESTPermissionTest(BaseViewTest):
    def base_add_bare_user(self) -> None:
        pass

    def create_bare_user(self) -> None:
        tenant = Tenant.objects.filter(
            name='default_tenant'
        )[0]
        user = User.objects.create(
            username='test_user',
            password='test_user',
            email='test_user@neuroforge.de'
        )
        self.test_user = user
        Tenant_User.objects.create(
            tenant=tenant,
            user=user
        )
        self.user_client = APIClient()
        self.user_client.login(username='test_user', password='test_user')


class BaseRESTPermissionTest(_BaseRESTPermissionTest):
    """
    rudimentarily tests whether the given methods are allowed to be run
    against the dataseries endpoint
    """
    url_under_test: str
    simulate_other_tenant = True

    permission_code_prefix = 'dataseries'

    user_client: APIClient

    test_user: User

    base_class_name = 'BaseRESTPermissionTest'

    # FIXME: also test staff user access behaviour here?

    def permission_code_name(self) -> str:
        raise NotImplementedError()

    def method_under_test_malformed(self) -> Optional[Union[HttpResponse, TestHttpResponse]]:
        raise NotImplementedError()

    def malformed_with_permission_status(self) -> int:
        raise NotImplementedError()

    def proper_with_permission_status(self) -> int:
        raise NotImplementedError()

    def malformed_without_permission_status(self) -> int:
        return status.HTTP_403_FORBIDDEN

    def proper_without_permission_status(self) -> int:
        return status.HTTP_403_FORBIDDEN

    def method_under_test_proper(self) -> Union[HttpResponse, TestHttpResponse]:
        raise NotImplementedError()

    def add_extra_permissions(self) -> None:
        pass

    def remove_extra_permissions(self) -> None:
        pass

    def base_add_extra_permissions(self) -> None:
        pass

    def base_remove_extra_permissions(self) -> None:
        pass

    def after_base_test(self) -> None:
        pass

    def without_extra_permissions_test(self) -> None:
        return None

    def test(self) -> None:
        if self.__class__.__name__ == self.base_class_name:
            return
        self.create_bare_user()
        self.base_add_bare_user()

        def add_permission() -> None:
            with transaction.atomic():
                permission = Permission.objects.get(
                    content_type__app_label=self.permission_code_prefix,
                    codename=self.permission_code_name()
                )
                self.test_user.user_permissions.add(permission)
                self.test_user.save()

            self.test_user = User.objects.get(username=self.test_user.username)
            self.assertTrue(self.test_user.has_perm(f'{self.permission_code_prefix}.{self.permission_code_name()}'))
            # force login with the new object so that the permissions are not cached in the requests
            self.user_client.force_login(self.test_user)

        def remove_permission() -> None:
            with transaction.atomic():
                permission = Permission.objects.get(
                    content_type__app_label=self.permission_code_prefix,
                    codename=self.permission_code_name()
                )
                self.test_user.user_permissions.remove(permission)
                self.test_user.save()

            self.test_user = User.objects.get(username=self.test_user.username)
            self.assertTrue(not self.test_user.has_perm(f'{self.permission_code_prefix}.{self.permission_code_name()}'))
            # force login with the new object so that the permissions are not cached in the requests
            self.user_client.force_login(self.test_user)

        def without_permissions() -> None:
            malformed_without_permissions = self.method_under_test_malformed()
            if malformed_without_permissions is not None:
                self.assertEquals(self.malformed_without_permission_status(), malformed_without_permissions.status_code)
            proper_without_permissions = self.method_under_test_proper()
            self.assertEquals(self.proper_without_permission_status(), proper_without_permissions.status_code)

        def with_permissions() -> None:
            malformed_with_permissions = self.method_under_test_malformed()
            if malformed_with_permissions is not None:
                self.assertEquals(self.malformed_with_permission_status(), malformed_with_permissions.status_code)
            proper_with_permissions = self.method_under_test_proper()
            self.assertEquals(self.proper_with_permission_status(), proper_with_permissions.status_code)

        # not logged in
        without_permissions()

        add_permission()

        # maybe we need some extra permissions than the ones under test
        # this can be validated in here in subtyping classes
        self.without_extra_permissions_test()

        # add extra permissions
        self.base_add_extra_permissions()
        self.add_extra_permissions()

        # run the test with the correct permissions
        with_permissions()

        # remove the extra permissions
        self.remove_extra_permissions()
        self.base_remove_extra_permissions()

        # maybe we need some extra permissions than the ones under test
        # now if we remove them again, the requests should behave
        # the same as before
        self.without_extra_permissions_test()

        # remove the permission under test
        remove_permission()

        self.after_base_test()

        without_permissions()


class BaseObjectLevelPermissionListEndpointTest(_BaseRESTPermissionTest):

    base_class_name = 'BaseObjectLevelPermissionListEndpointTest'
    permission_code_prefix = 'dataseries'

    def permission_code_name(self) -> str:
        raise NotImplementedError()

    def create_object(self) -> Any:
        raise NotImplementedError()

    def get_list(self) -> Any:
        raise NotImplementedError()

    def extract_data_from_list(self, response: Union[HttpResponse, TestHttpResponse]) -> List[Dict[str, Any]]:
        raise NotImplementedError()

    def test(self) -> None:
        if self.__class__.__name__ == self.base_class_name:
            return
        self.create_bare_user()
        self.base_add_bare_user()

        def add_global_permission() -> None:
            with transaction.atomic():
                permission = Permission.objects.get(
                    content_type__app_label=self.permission_code_prefix,
                    codename=self.permission_code_name()
                )
                self.test_user.user_permissions.add(permission)
                self.test_user.save()

            self.test_user = User.objects.get(username=self.test_user.username)
            self.assertTrue(self.test_user.has_perm(f'{self.permission_code_prefix}.{self.permission_code_name()}'))
            # force login with the new object so that the permissions are not cached in the requests
            self.user_client.force_login(self.test_user)

        def add_object_permission(obj: Model) -> None:
            with transaction.atomic():
                assign_perm(
                    f'{self.permission_code_prefix}.{self.permission_code_name()}',
                    self.test_user,
                    obj=obj
                )

            self.test_user = User.objects.get(username=self.test_user.username)
            self.assertTrue(
                self.test_user.has_perm(f'{self.permission_code_prefix}.{self.permission_code_name()}', obj=obj)
            )
            # force login with the new object so that the permissions are not cached in the requests
            self.user_client.force_login(self.test_user)

        def remove_global_permission() -> None:
            with transaction.atomic():
                permission = Permission.objects.get(
                    content_type__app_label=self.permission_code_prefix,
                    codename=self.permission_code_name()
                )
                self.test_user.user_permissions.remove(permission)
                self.test_user.save()

            self.test_user = User.objects.get(username=self.test_user.username)
            self.assertTrue(not self.test_user.has_perm(f'{self.permission_code_prefix}.{self.permission_code_name()}'))
            # force login with the new object so that the permissions are not cached in the requests
            self.user_client.force_login(self.test_user)

        def remove_object_permission(obj: Model) -> None:
            with transaction.atomic():
                remove_perm(
                    f'{self.permission_code_prefix}.{self.permission_code_name()}',
                    self.test_user,
                    obj=obj
                )

            self.test_user = User.objects.get(username=self.test_user.username)
            self.assertFalse(
                self.test_user.has_perm(f'{self.permission_code_prefix}.{self.permission_code_name()}', obj=obj)
            )
            # force login with the new object so that the permissions are not cached in the requests
            self.user_client.force_login(self.test_user)

        add_global_permission()

        obj = self.create_object()

        list_response = self.get_list()
        self.assertEqual(status.HTTP_200_OK, list_response.status_code)
        list_data = self.extract_data_from_list(list_response)
        self.assertEqual(0, len(list_data))

        add_object_permission(obj)

        list_response = self.get_list()
        self.assertEqual(status.HTTP_200_OK, list_response.status_code)
        list_data = self.extract_data_from_list(list_response)
        self.assertEqual(1, len(list_data))

        remove_object_permission(obj)

        list_response = self.get_list()
        self.assertEqual(status.HTTP_200_OK, list_response.status_code)
        list_data = self.extract_data_from_list(list_response)
        self.assertEqual(0, len(list_data))

        remove_global_permission()
        list_response = self.get_list()
        self.assertEqual(status.HTTP_403_FORBIDDEN, list_response.status_code)

        add_object_permission(obj)
        remove_global_permission()
        list_response = self.get_list()
        self.assertEqual(status.HTTP_403_FORBIDDEN, list_response.status_code)
