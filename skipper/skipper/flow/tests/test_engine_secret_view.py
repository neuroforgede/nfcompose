# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from typing import Dict, Any, cast

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


class EngineCrudTest(BaseViewTest):
    url_under_test = ENGINE_BASE_URL
    simulate_other_tenant = True
    skip_setup_assertions = True

    def _engine(self, external_id: str = '1') -> Dict[str, Any]:
        response = self.client.post(path=ENGINE_BASE_URL, data={
            "external_id": external_id,
            "upstream": "http://hans.peter.local/"
        })
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        return cast(Dict[str, Any], response.json())

    def test_secret_set_by_default(self) -> None:
        engine = self._engine()

        secret_response = self.client.get(path=engine['secret'])
        secret_json = secret_response.json()

        engine_obj: Engine = Engine.objects.get(id=engine['id'])

        self.assertIn('secret', secret_json)
        self.assertGreater(len(secret_json['secret']), 15)
        self.assertEqual(secret_json['secret'], engine_obj.secret)

    def test_secret_put(self) -> None:
        engine = self._engine()

        response = self.client.put(path=engine['secret'], data={
            "secret": "my_new_super_secret_password_pls_dont_steal"
        })
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        secret_json = response.json()

        self.assertIn('secret', secret_json)
        self.assertEqual("my_new_super_secret_password_pls_dont_steal", secret_json['secret'])

        engine_obj: Engine = Engine.objects.get(id=engine['id'])
        self.assertEqual("my_new_super_secret_password_pls_dont_steal", engine_obj.secret)

    def test_secret_delete_with_custom_password(self) -> None:
        engine = self._engine()

        engine_obj: Engine = Engine.objects.get(id=engine['id'])
        engine_obj.secret = "my_new_super_secret_password_pls_dont_steal"

        del_response = self.client.delete(path=engine['secret'])
        self.assertEqual(status.HTTP_204_NO_CONTENT, del_response.status_code)

        secret_json = self.client.get(path=engine['secret']).json()

        # should have a new secret generated even if we set it manually
        self.assertIn('secret', secret_json)
        self.assertNotEqual("my_new_super_secret_password_pls_dont_steal", secret_json['secret'])

        # ne secret should have been persisted as well
        engine_obj.refresh_from_db()
        self.assertEqual(engine_obj.secret, secret_json['secret'])

    def test_secret_delete(self) -> None:
        engine = self._engine()

        engine_obj: Engine = Engine.objects.get(id=engine['id'])
        _old_secret = engine_obj.secret

        del_response = self.client.delete(path=engine['secret'])
        self.assertEqual(status.HTTP_204_NO_CONTENT, del_response.status_code)

        secret_json = self.client.get(path=engine['secret']).json()

        # should have a new secret generated
        self.assertIn('secret', secret_json)
        self.assertNotEqual(_old_secret, secret_json['secret'])

        # ne secret should have been persisted as well
        engine_obj.refresh_from_db()
        self.assertEqual(engine_obj.secret, secret_json['secret'])
