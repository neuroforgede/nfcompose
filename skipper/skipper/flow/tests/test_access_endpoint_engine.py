# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from http.cookies import SimpleCookie

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from guardian.shortcuts import assign_perm  # type: ignore
from rest_framework import status
from rest_framework.test import APIClient

from skipper import modules
from skipper.core.models.tenant import Tenant, Tenant_User
from skipper.core.tests.base import BASE_URL
from skipper.flow.models import Engine, ENGINE_PERMISSION_KEY_ACCESS, \
    ENGINE_PERMISSION_KEY_ENGINE, get_permission_string_for_action_and_http_verb, Any

ENGINE_BASE_URL = BASE_URL + modules.url_representation(modules.Module.FLOW) + '/engine/'


class TestEngineEditEndpoint(TestCase):

    proper_user: User
    wrong_permissions_user: User
    other_tenant_user: User

    proper_client: APIClient
    wrong_permissions_client: APIClient
    other_tenant_client: APIClient

    engine: Engine

    def assign_proper_perms(self, user: User, engine: Engine) -> None:
        # assign global perms
        assign_perm(
            get_permission_string_for_action_and_http_verb(
                entity='engine',
                http_verb='GET',
                action=ENGINE_PERMISSION_KEY_ENGINE
            ),
            user
        )
        assign_perm(
            get_permission_string_for_action_and_http_verb(
                entity='engine',
                http_verb='GET',
                action=ENGINE_PERMISSION_KEY_ACCESS
            ),
            user
        )

        # object level permissions
        assign_perm(
            get_permission_string_for_action_and_http_verb(
                entity='engine',
                http_verb='GET',
                action=ENGINE_PERMISSION_KEY_ENGINE
            ),
            user,
            engine
        )
        assign_perm(
            get_permission_string_for_action_and_http_verb(
                entity='engine',
                http_verb='GET',
                action=ENGINE_PERMISSION_KEY_ACCESS
            ),
            user,
            engine
        )

    # TODO: separate this into separate classes?
    def setUp(self) -> None:
        tenant = Tenant.objects.create(
            name='proper_tenant'
        )

        self.engine = Engine.objects.create(
            tenant=tenant,
            external_id='thomas_the_tank_engine',
            upstream='http://thomas.tank.local:1880'
        )

        self.proper_user = User.objects.create(
            username='proper_user',
            password='some_password',
            email='some@email.de',
            is_superuser=False,
            is_staff=False
        )
        Tenant_User.objects.create(
            tenant=tenant,
            user=self.proper_user
        )
        self.assign_proper_perms(
            self.proper_user,
            self.engine
        )

        self.proper_client = APIClient()
        self.proper_client.force_login(self.proper_user)

        self.wrong_permissions_user = User.objects.create(
            username='wrong_permissions_user',
            password='some_password',
            email='some@email.de',
            is_superuser=False,
            is_staff=False
        )
        Tenant_User.objects.create(
            tenant=tenant,
            user=self.wrong_permissions_user
        )
        self.wrong_permissions_client = APIClient()
        self.wrong_permissions_client.force_login(
            self.wrong_permissions_user
        )

        self.other_tenant_user = User.objects.create(
            username='other_tenant_user',
            password='some_password',
            email='some@email.de',
            is_superuser=False,
            is_staff=False
        )
        other_tenant = Tenant.objects.create(
            name='other_tenant'
        )
        Tenant_User.objects.create(
            tenant=other_tenant,
            user=self.other_tenant_user
        )

        # we give the other tenant user the actual permissions that would work
        # but since the other user is not of the correct tenant that should still
        # enforce the Engine to not be available to that user
        self.assign_proper_perms(
            self.other_tenant_user,
            self.engine
        )

        self.other_tenant_client = APIClient()
        self.other_tenant_client.force_login(
            self.other_tenant_user
        )

    def test_access_endpoint_should_work_for_proper_user(self) -> None:
        self.assertIsNotNone(self.proper_client.cookies.get(settings.SESSION_COOKIE_NAME))
        response = self.proper_client.get(path=ENGINE_BASE_URL + str(self.engine.id) + '/access/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['engineupstream'], self.engine.upstream)
        self.assertIn('enginecookies', response)
        self.assertIn('enginehostname', response)
        cookie: SimpleCookie[Any] = SimpleCookie()
        cookie.value_decode(response['enginecookies'])
        self.assertIsNone(cookie.get(settings.SESSION_COOKIE_NAME))
        self.assertEqual(response['enginesecret'], self.engine.secret)

    def test_access_endpoint_should_not_work_for_wrong_tenant(self) -> None:
        response = self.other_tenant_client.get(path=ENGINE_BASE_URL + str(self.engine.id) + '/access/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertNotIn('engineupstream', response)
        self.assertNotIn('enginecookies', response)
        self.assertNotIn('enginesecret', response)
        self.assertNotIn('enginehostname', response)

    def test_access_endpoint_should_not_work_for_user_with_no_permission(self) -> None:
        response = self.wrong_permissions_client.get(path=ENGINE_BASE_URL + str(self.engine.id) + '/access/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertNotIn('engineupstream', response)
        self.assertNotIn('enginecookies', response)
        self.assertNotIn('enginesecret', response)
        self.assertNotIn('enginehostname', response)

    def test_access_endpoint_should_not_work_with_only_global_permissions(self) -> None:
        # assign global perms
        assign_perm(
            get_permission_string_for_action_and_http_verb(
                entity='engine',
                http_verb='GET',
                action=ENGINE_PERMISSION_KEY_ENGINE
            ),
            self.wrong_permissions_user
        )
        assign_perm(
            get_permission_string_for_action_and_http_verb(
                entity='engine',
                http_verb='GET',
                action=ENGINE_PERMISSION_KEY_ACCESS
            ),
            self.wrong_permissions_user
        )
        self.wrong_permissions_client.force_login(self.wrong_permissions_user)

        response = self.wrong_permissions_client.get(path=ENGINE_BASE_URL + str(self.engine.id) + '/access/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertNotIn('engineupstream', response)
        self.assertNotIn('enginecookies', response)
        self.assertNotIn('enginesecret', response)
        self.assertNotIn('enginehostname', response)

    def test_access_endpoint_should_not_work_with_global_and_only_object_level_access_permission(self) -> None:
        # assign global perms
        assign_perm(
            get_permission_string_for_action_and_http_verb(
                entity='engine',
                http_verb='GET',
                action=ENGINE_PERMISSION_KEY_ENGINE
            ),
            self.wrong_permissions_user
        )
        assign_perm(
            get_permission_string_for_action_and_http_verb(
                entity='engine',
                http_verb='GET',
                action=ENGINE_PERMISSION_KEY_ACCESS
            ),
            self.wrong_permissions_user
        )

        assign_perm(
            get_permission_string_for_action_and_http_verb(
                entity='engine',
                http_verb='GET',
                action=ENGINE_PERMISSION_KEY_ACCESS
            ),
            self.wrong_permissions_user,
            self.engine
        )

        self.wrong_permissions_client.force_login(self.wrong_permissions_user)

        response = self.wrong_permissions_client.get(path=ENGINE_BASE_URL + str(self.engine.id) + '/access/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertNotIn('engineupstream', response)
        self.assertNotIn('enginecookies', response)
        self.assertNotIn('enginesecret', response)
        self.assertNotIn('enginehostname', response)

    def test_access_endpoint_should_not_work_with_global_and_only_object_level_get_permission(self) -> None:
        # assign global perms
        assign_perm(
            get_permission_string_for_action_and_http_verb(
                entity='engine',
                http_verb='GET',
                action=ENGINE_PERMISSION_KEY_ENGINE
            ),
            self.wrong_permissions_user
        )
        assign_perm(
            get_permission_string_for_action_and_http_verb(
                entity='engine',
                http_verb='GET',
                action=ENGINE_PERMISSION_KEY_ACCESS
            ),
            self.wrong_permissions_user
        )

        assign_perm(
            get_permission_string_for_action_and_http_verb(
                entity='engine',
                http_verb='GET',
                action=ENGINE_PERMISSION_KEY_ENGINE
            ),
            self.wrong_permissions_user,
            self.engine
        )

        self.wrong_permissions_client.force_login(self.wrong_permissions_user)

        response = self.wrong_permissions_client.get(path=ENGINE_BASE_URL + str(self.engine.id) + '/access/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertNotIn('engineupstream', response)
        self.assertNotIn('enginecookies', response)
        self.assertNotIn('enginesecret', response)
        self.assertNotIn('enginehostname', response)

    def test_access_endpoint_should_not_work_with_all_object_level_but_no_global_permission(self) -> None:
        # assign object level perms
        assign_perm(
            get_permission_string_for_action_and_http_verb(
                entity='engine',
                http_verb='GET',
                action=ENGINE_PERMISSION_KEY_ENGINE
            ),
            self.wrong_permissions_user,
            self.engine
        )
        assign_perm(
            get_permission_string_for_action_and_http_verb(
                entity='engine',
                http_verb='GET',
                action=ENGINE_PERMISSION_KEY_ACCESS
            ),
            self.wrong_permissions_user,
            self.engine
        )

        self.wrong_permissions_client.force_login(self.wrong_permissions_user)

        response = self.wrong_permissions_client.get(path=ENGINE_BASE_URL + str(self.engine.id) + '/access/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertNotIn('engineupstream', response)
        self.assertNotIn('enginecookies', response)
        self.assertNotIn('enginesecret', response)
        self.assertNotIn('enginehostname', response)

    def test_access_endpoint_should_not_work_with_all_object_level_but_only_global_get_permission(self) -> None:
        assign_perm(
            get_permission_string_for_action_and_http_verb(
                entity='engine',
                http_verb='GET',
                action=ENGINE_PERMISSION_KEY_ENGINE
            ),
            self.wrong_permissions_user
        )

        # assign object level perms
        assign_perm(
            get_permission_string_for_action_and_http_verb(
                entity='engine',
                http_verb='GET',
                action=ENGINE_PERMISSION_KEY_ENGINE
            ),
            self.wrong_permissions_user,
            self.engine
        )
        assign_perm(
            get_permission_string_for_action_and_http_verb(
                entity='engine',
                http_verb='GET',
                action=ENGINE_PERMISSION_KEY_ACCESS
            ),
            self.wrong_permissions_user,
            self.engine
        )

        self.wrong_permissions_client.force_login(self.wrong_permissions_user)

        response = self.wrong_permissions_client.get(path=ENGINE_BASE_URL + str(self.engine.id) + '/access/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertNotIn('engineupstream', response)
        self.assertNotIn('enginecookies', response)
        self.assertNotIn('enginesecret', response)
        self.assertNotIn('enginehostname', response)

    def test_access_endpoint_should_not_work_with_all_object_level_but_only_global_access_permission(self) -> None:
        assign_perm(
            get_permission_string_for_action_and_http_verb(
                entity='engine',
                http_verb='GET',
                action=ENGINE_PERMISSION_KEY_ACCESS
            ),
            self.wrong_permissions_user
        )

        # assign object level perms
        assign_perm(
            get_permission_string_for_action_and_http_verb(
                entity='engine',
                http_verb='GET',
                action=ENGINE_PERMISSION_KEY_ENGINE
            ),
            self.wrong_permissions_user,
            self.engine
        )
        assign_perm(
            get_permission_string_for_action_and_http_verb(
                entity='engine',
                http_verb='GET',
                action=ENGINE_PERMISSION_KEY_ACCESS
            ),
            self.wrong_permissions_user,
            self.engine
        )

        self.wrong_permissions_client.force_login(self.wrong_permissions_user)

        response = self.wrong_permissions_client.get(path=ENGINE_BASE_URL + str(self.engine.id) + '/access/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertNotIn('engineupstream', response)
        self.assertNotIn('enginecookies', response)
        self.assertNotIn('enginesecret', response)
        self.assertNotIn('enginehostname', response)
