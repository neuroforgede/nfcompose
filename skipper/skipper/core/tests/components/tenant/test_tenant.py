# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from rest_framework import status

from skipper.core.tests.base import BaseViewTest, BASE_URL


class TenantTest(BaseViewTest):
    url_under_test = BASE_URL + 'core/tenant/'

    def test_duplicate_tenant_name_fails(self) -> None:
        initial_resp = self._client().post(
            path=self.url_under_test,
            data={
                'name': 'some_tenant'
            },
            format='json'
        )
        self.assertEqual(initial_resp.status_code, status.HTTP_201_CREATED)
        resp = self._client().post(
            path=self.url_under_test,
            data={
                'name': 'some_tenant'
            },
            format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    
    def test_deleted_tenants_uniqueness_constraint_for_name(self) -> None:
        initial_resp = self._client().post(
            path=self.url_under_test,
            data={
                'name': 'some_tenant'
            },
            format='json'
        )
        self.assertEqual(initial_resp.status_code, status.HTTP_201_CREATED)

        delete_resp = self._client().delete(
            path=initial_resp.json()['url']
        )
        self.assertEqual(delete_resp.status_code, status.HTTP_204_NO_CONTENT)

        not_found_resp = self._client().get(
            path=initial_resp.json()['url']
        )
        self.assertEqual(not_found_resp.status_code, status.HTTP_404_NOT_FOUND)

        resp = self._client().post(
            path=self.url_under_test,
            data={
                'name': 'some_tenant'
            },
            format='json'
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
