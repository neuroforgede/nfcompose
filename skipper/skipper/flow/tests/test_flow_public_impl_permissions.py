# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from typing import Optional

from django.contrib.auth.models import User
from guardian.shortcuts import assign_perm, remove_perm  # type: ignore
from rest_framework import status
from rest_framework.test import APIClient
from urllib.parse import urlparse

from skipper import modules, settings
from skipper.core.models.tenant import Tenant_User, Tenant
from skipper.core.tests.base import BaseViewTest, BASE_URL
from skipper.flow.models import HttpEndpoint, Engine

DATA_SERIES_BASE_URL = BASE_URL + modules.url_representation(modules.Module.FLOW) + '/'


def test_normal_user_permissions(self: 'HttpEndpointPermissionTest', method: str, not_the_method: str) -> None:
    # first, test with proper permissions set, and with global permissions
    # that the user can use any flows at all
    user = User.objects.create(
        username='some_user',
        password='some_password',
        email='some@email.de',
        is_superuser=False,
        is_staff=False
    )
    tenant = Tenant.objects.create(
        name='other_tenant2'
    )
    wrong_tenant = Tenant.objects.create(
        name='wrong_tenant'
    )
    Tenant_User.objects.create(
        tenant=tenant,
        user=user
    )
    client = APIClient()
    unauthenticated_client = APIClient()

    client.login(username=user.username, password=user.password)

    # user should not be allowed to do anything, to start off
    response = client.get(
        path=self.actual_url_under_test,
        data=None,
        follow=False,
        **{
            "HTTP_X_Original_Uri": f'/api/flow/public/impl/{tenant.name}/some/stuff/here',
            "HTTP_X_Original_Method": method
        }  # type: ignore
    )
    self.assertEquals(status.HTTP_403_FORBIDDEN, response.status_code)

    response = unauthenticated_client.get(
        path=self.actual_url_under_test,
        data=None,
        follow=False,
        **{
            "HTTP_X_Original_Uri": f'/api/flow/public/impl/{tenant.name}/some/stuff/here',
            "HTTP_X_Original_Method": method
        }  # type: ignore
    )
    self.assertEquals(status.HTTP_403_FORBIDDEN, response.status_code)

    assign_perm('flow.impl', user)

    external_id = 0

    def test_with_engine_object(_tenant_to_use: Tenant, all_set_status: int, _method: str,
                                path_regex: str, tested_path: str, expected_path: Optional[str] = None) -> None:
        nonlocal external_id
        endpoint = HttpEndpoint.objects.create(
            external_id=str(external_id),
            tenant=_tenant_to_use,
            path=path_regex,
            method=_method,
            system=True,
            public=True
        )
        external_id += 1

        # the flow exists for the tenant, normal users of this tenant should see it via public routing
        client.force_login(user)
        _response = client.get(
            path=self.actual_url_under_test,
            data=None,
            follow=False,
            **{
                "HTTP_X_Original_Uri": tested_path,
                "HTTP_X_Original_Method": _method
            }  # type: ignore
        )
        self.assertEquals(all_set_status, _response.status_code)

        assign_perm('flow.use', user, endpoint)

        _response = unauthenticated_client.get(
            path=self.actual_url_under_test,
            data=None,
            follow=False,
            **{
                "HTTP_X_Original_Uri": tested_path,
                "HTTP_X_Original_Method": _method
            }  # type: ignore
        )
        self.assertEquals(all_set_status, _response.status_code)

        if all_set_status == status.HTTP_200_OK:
            self.assertEqual(_response['flowuser'], '')
            self.assertEqual(_response['flowcookies'], '')

            # meh, just use the default for testing hence None, None, None
            self.assertEqual(_response['flowupstream'], settings.flow_upstream_impl(None, None, None))  # type: ignore
            self.assertEqual(_response['flowpath'], expected_path)
            self.assertEqual(_response['flowhostname'], urlparse(_response['flowupstream']).hostname)
        else:
            self.assertNotIn('flowuser', _response)
            self.assertNotIn('flowcookies', _response)
            self.assertNotIn('flowupstream', _response)
            self.assertNotIn('flowpath', _response)
            self.assertNotIn('flowhostname', _response)

        # and for an authenticated client it should behave the same
        client.force_login(user)
        _response = client.get(
            path=self.actual_url_under_test,
            data=None,
            follow=False,
            **{
                "HTTP_X_Original_Uri": tested_path,
                "HTTP_X_Original_Method": _method
            }  # type: ignore
        )
        self.assertEquals(all_set_status, _response.status_code)

        if all_set_status == status.HTTP_200_OK:
            self.assertEqual(_response['flowuser'], '')
            self.assertEqual(_response['flowcookies'], '')

            # meh, just use the default for testing hence None, None, None
            self.assertEqual(_response['flowupstream'], settings.flow_upstream_impl(None, None, None))  # type: ignore
            self.assertEqual(_response['flowhostname'], urlparse(_response['flowupstream']).hostname)
            self.assertEqual(_response['flowpath'], expected_path)
        else:
            self.assertNotIn('flowuser', _response)
            self.assertNotIn('flowcookies', _response)
            self.assertNotIn('flowupstream', _response)
            self.assertNotIn('flowpath', _response)
            self.assertNotIn('flowhostname', _response)

    test_with_engine_object(wrong_tenant, status.HTTP_403_FORBIDDEN, not_the_method, '/api/flow/impl/some/stuff/here',
                            f'/api/flow/public/impl/{tenant.name}/some/stuff/here', None)
    test_with_engine_object(wrong_tenant, status.HTTP_403_FORBIDDEN, method, '/api/flow/impl/some/stuff/here',
                            f'/api/flow/public/impl/{tenant.name}/some/stuff/here', None)
    test_with_engine_object(tenant, status.HTTP_200_OK, not_the_method, '/api/flow/impl/some/stuff/here',
                            f'/api/flow/public/impl/{tenant.name}/some/stuff/here', '/api/flow/impl/some/stuff/here')
    test_with_engine_object(tenant, status.HTTP_200_OK, method, '/api/flow/impl/some/stuff/here',
                            f'/api/flow/public/impl/{tenant.name}/some/stuff/here', '/api/flow/impl/some/stuff/here')

    test_with_engine_object(wrong_tenant, status.HTTP_403_FORBIDDEN, not_the_method, '/api/flow/impl/some/stuff/here',
                            f'/api/flow/public/impl/{tenant.name}/some/stuff/here/but/with/more', None)
    test_with_engine_object(tenant, status.HTTP_403_FORBIDDEN, method, '/api/flow/impl/some/stuff/here',
                            f'/api/flow/public/impl/{tenant.name}/some/stuff/here/but/with/more', None)

    test_with_engine_object(tenant, status.HTTP_200_OK, method, '^/api/flow/impl/some/regex/with/markers/already$',
                            f'/api/flow/public/impl/{tenant.name}/some/regex/with/markers/already',
                            '/api/flow/impl/some/regex/with/markers/already')

    test_with_engine_object(tenant, status.HTTP_200_OK, method, '^/api/flow/impl/some/regex/with/optional/?$',
                            f'/api/flow/public/impl/{tenant.name}/some/regex/with/optional',
                            '/api/flow/impl/some/regex/with/optional')
    test_with_engine_object(tenant, status.HTTP_200_OK, method, '^/api/flow/impl/again/some/regex/with/optional/?$',
                            f'/api/flow/public/impl/{tenant.name}/again/some/regex/with/optional/',
                            '/api/flow/impl/again/some/regex/with/optional/')

    test_with_engine_object(tenant, status.HTTP_200_OK, method, '^/api/flow/impl/test/uri/parameters/stripped$',
                            f'/api/flow/public/impl/{tenant.name}/test/uri/parameters/stripped?toast=a',
                            '/api/flow/impl/test/uri/parameters/stripped?toast=a')

    # remove global perm
    remove_perm('flow.impl', user)

    client.force_login(user)
    response = client.get(
        path=self.actual_url_under_test,
        data=None,
        follow=False,
        **{
            "HTTP_X_Original_Uri": 'some/stuff/here',
            "HTTP_X_Original_Method": method
        }  # type: ignore
    )
    self.assertEquals(status.HTTP_403_FORBIDDEN, response.status_code)


class HttpEndpointPermissionTest(BaseViewTest):
    url_under_test = DATA_SERIES_BASE_URL

    actual_url_under_test = DATA_SERIES_BASE_URL + 'public/impl/'
    simulate_other_tenant = True
    skip_setup_assertions = True

    def test_OPTIONS_forbidden_without_headers(self) -> None:
        response = self.client.get(
            path=self.actual_url_under_test,
            data=None,
            follow=False,
            **{
            }  # type: ignore
        )
        self.assertEquals(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_OPTIONS_forbidden_without_headers_logged_out(self) -> None:
        self.client.logout()
        response = self.client.get(
            path=self.actual_url_under_test,
            data=None,
            follow=False,
            **{
            }  # type: ignore
        )
        self.assertEquals(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_OPTIONS_sets_upstream_properly(self) -> None:
        self.client.logout()
        response = self.client.get(
            path=self.actual_url_under_test,
            data=None,
            follow=False,
            **{
                "HTTP_X_Original_Uri": 'some/stuff/here',
                "HTTP_X_Original_Method": 'OPTIONS'
            }  # type: ignore
        )
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertEqual(response['flowupstream'], getattr(settings, 'SKIPPER_CONTAINER_UPSTREAM', 'http://skipper'))
        self.assertEqual(response['flowpath'], '/api/flow/options/')

    def test_OPTIONS_allowed_without_credentials_and_no_cors_headers(self) -> None:
        self.client.logout()
        response = self.client.get(
            path=self.actual_url_under_test,
            data=None,
            follow=False,
            **{
                "HTTP_X_Original_Uri": 'some/stuff/here',
                "HTTP_X_Original_Method": 'OPTIONS'
            }  # type: ignore
        )
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertEqual(response['flowupstream'], getattr(settings, 'SKIPPER_CONTAINER_UPSTREAM', 'http://skipper'))
        self.assertEqual(response['flowhostname'], urlparse(response['flowupstream']).hostname)
        self.assertEqual(response['flowpath'], '/api/flow/options/')

    def test_OPTIONS_allowed_without_credentials(self) -> None:
        for method in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']:
            self.client.logout()
            response = self.client.get(
                path=self.actual_url_under_test,
                data=None,
                follow=False,
                **{
                    "HTTP_X_Original_Uri": '/api/flow/public/impl/default_tenant/some/stuff/here',
                    "HTTP_X_Original_Method": 'OPTIONS',
                    "HTTP_ACCESS_CONTROL_REQUEST_METHOD": method
                }  # type: ignore
            )
            self.assertEquals(status.HTTP_200_OK, response.status_code)
            self.assertEqual(response['flowupstream'],
                             getattr(settings, 'SKIPPER_CONTAINER_UPSTREAM', 'http://skipper'))
            self.assertEqual(response['flowhostname'], urlparse(response['flowupstream']).hostname)
            self.assertEqual(response['flowpath'], '/api/flow/options/')

    def test_OPTIONS_without_credentials_on_wrong_prefixed_original_uri(self) -> None:
        for method in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']:
            self.client.logout()
            response = self.client.get(
                path=self.actual_url_under_test,
                data=None,
                follow=False,
                **{
                    "HTTP_X_Original_Uri": '/api/wrong/prefix/flow/public/impl/default_tenant/some/stuff/here',
                    "HTTP_X_Original_Method": 'OPTIONS',
                    "HTTP_ACCESS_CONTROL_REQUEST_METHOD": method
                }  # type: ignore
            )
            self.assertEquals(status.HTTP_200_OK, response.status_code)
            self.assertEqual(response['flowupstream'],
                             getattr(settings, 'SKIPPER_CONTAINER_UPSTREAM', 'http://skipper'))
            self.assertEqual(response['flowhostname'], urlparse(response['flowupstream']).hostname)
            self.assertEqual(response['flowpath'], '/api/flow/options/')

    def test_headers_missing(self) -> None:
        response = self.client.get(
            path=self.actual_url_under_test,
            data=None,
            follow=False
        )
        self.assertEquals(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_method_header_missing(self) -> None:
        response = self.client.get(
            path=self.actual_url_under_test,
            data=None,
            follow=False,
            **{
                "HTTP_X_Original_Uri": 'some/stuff/here',
            }  # type: ignore
        )
        self.assertEquals(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_uri_header_missing(self) -> None:
        response = self.client.get(
            path=self.actual_url_under_test,
            data=None,
            follow=False,
            **{
                "HTTP_X_Original_Method": 'GET'
            }  # type: ignore
        )
        self.assertEquals(status.HTTP_403_FORBIDDEN, response.status_code)

    def test_public_endpoint_with_engine_returns_proper_headers_system(self) -> None:
        self.client.logout()
        tenant = Tenant.objects.filter(
            name='default_tenant'
        )[0]
        HttpEndpoint.objects.create(
            external_id='external_id',
            tenant=tenant,
            path='/api/flow/impl/some/stuff/here',
            method='GET',
            public=True,
            system=True
        )
        # test user is super user by default, so this works
        response = self.client.get(
            path=self.actual_url_under_test,
            data=None,
            follow=False,
            **{
                "HTTP_X_Original_Uri": '/api/flow/public/impl/default_tenant/some/stuff/here',
                "HTTP_X_Original_Method": 'GET'
            }  # type: ignore
        )
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(settings.SKIPPER_DEFAULT_NODE_RED_UPSTREAM, response['flowupstream'])
        self.assertEqual(response['flowhostname'], urlparse(response['flowupstream']).hostname)
        self.assertEqual('/api/flow/impl/some/stuff/here', response['flowpath'])
        self.assertEqual(settings.SKIPPER_DEFAULT_SYSTEM_SECRET, response['flowsecret'])

    def test_public_endpoint_with_engine_returns_proper_headers(self) -> None:
        self.client.logout()
        tenant = Tenant.objects.filter(
            name='default_tenant'
        )[0]
        engine = Engine.objects.create(
            tenant=tenant,
            external_id='my_little_engine',
            upstream='http://thomas.the.tank.engine.local'
        )
        HttpEndpoint.objects.create(
            external_id='external_id',
            tenant=tenant,
            path='/api/flow/impl/some/stuff/here',
            method='GET',
            engine=engine,
            public=True,
            system=False
        )
        # test user is super user by default, so this works
        response = self.client.get(
            path=self.actual_url_under_test,
            data=None,
            follow=False,
            **{
                "HTTP_X_Original_Uri": '/api/flow/public/impl/default_tenant/some/stuff/here',
                "HTTP_X_Original_Method": 'GET'
            }  # type: ignore
        )
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(engine.upstream, response['flowupstream'])
        self.assertEqual(response['flowhostname'], urlparse(response['flowupstream']).hostname)
        self.assertEqual('/api/flow/impl/some/stuff/here', response['flowpath'])
        self.assertEqual(engine.secret, response['flowsecret'])

    def test_GET(self) -> None:
        test_normal_user_permissions(self, 'GET', 'POST')

    def test_POST(self) -> None:
        test_normal_user_permissions(self, 'POST', 'GET')

    def test_PATCH(self) -> None:
        test_normal_user_permissions(self, 'PATCH', 'POST')

    def test_PUT(self) -> None:
        test_normal_user_permissions(self, 'PUT', 'POST')

    def test_DELETE(self) -> None:
        test_normal_user_permissions(self, 'DELETE', 'POST')
