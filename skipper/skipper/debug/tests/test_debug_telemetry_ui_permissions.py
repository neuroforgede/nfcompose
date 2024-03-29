# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from django.contrib.auth.models import User
from guardian.shortcuts import assign_perm  # type: ignore
from rest_framework import status
from rest_framework.test import APIClient

from skipper import modules
from skipper.core.models.tenant import Tenant
from skipper.core.tests.base import BaseViewTest, BASE_URL

DEBUG_BASE_URL = BASE_URL + modules.url_representation(modules.Module.DEBUG) + '/'


class DebugTelemetryPermissionTest(BaseViewTest):
    url_under_test = DEBUG_BASE_URL + 'telemetry/ui/'

    simulate_other_tenant = True
    skip_setup_assertions = True

    def test_telemetry_permissions(self) -> None:
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

        client = APIClient()

        client.login(username=user.username, password=user.password)

        response = client.get(
            path=self.url_under_test,
            data=None,
            follow=False,
            **{
                "HTTP_X_Original_Uri": 'some/stuff/here',
                "HTTP_X_Original_Method": 'GET'
            }  # type: ignore
        )
        self.assertEquals(status.HTTP_403_FORBIDDEN, response.status_code)

        assign_perm('debug.telemetry.ui', user)

        client.force_login(user)

        response = client.get(
            path=self.url_under_test,
            data=None,
            follow=False,
            **{
                "HTTP_X_Original_Uri": 'some/stuff/here',
                "HTTP_X_Original_Method": 'GET'
            }  # type: ignore
        )
        self.assertEquals(status.HTTP_200_OK, response.status_code)
