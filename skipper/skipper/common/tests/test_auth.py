# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient, RequestsClient
from typing import Dict, Any, cast

from skipper.core.tests.base import BaseViewTest, BASE_URL


class UserTest(BaseViewTest):
    url_under_test = BASE_URL + "common/auth/user/"


class GroupTest(BaseViewTest):
    url_under_test = BASE_URL + "common/auth/group/"


class AuthTokenTest(TestCase):

    def test_get_auth_token_wrong_user(self) -> None:
        User.objects.create_superuser(username='nf', password='nf', email='test@neuroforge.de')
        client = APIClient()

        response = client.post(path=BASE_URL + "common/auth/authtoken/", data={
            'user': 'wrong_user',
            'password': 'nf'
        })
        self.assertEquals(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_get_auth_token_wrong_password(self) -> None:
        User.objects.create_superuser(username='nf', password='nf', email='test@neuroforge.de')
        client = APIClient()

        response = client.post(path=BASE_URL + "common/auth/authtoken/", data={
            'user': 'nf',
            'password': 'wrong_password'
        })
        self.assertEquals(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_get_auth_token_no_password(self) -> None:
        User.objects.create_superuser(username='nf', password='nf', email='test@neuroforge.de')
        client = APIClient()

        response = client.post(path=BASE_URL + "common/auth/authtoken/", data={
            'password': 'nf'
        })
        self.assertEquals(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_get_auth_token_no_user(self) -> None:
        User.objects.create_superuser(username='nf', password='nf', email='test@neuroforge.de')
        client = APIClient()

        response = client.post(path=BASE_URL + "common/auth/authtoken/", data={
            'user': 'nf'
        })
        self.assertEquals(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_get_auth_token(self) -> None:
        User.objects.create_superuser(username='nf', password='nf', email='test@neuroforge.de')
        client = APIClient()

        def get_token() -> Dict[str, Any]:
            response = client.post(path=BASE_URL + "common/auth/authtoken/", data={
                'username': 'nf',
                'password': 'nf'
            }, format='json')
            self.assertEquals(status.HTTP_200_OK, response.status_code)

            token_json = response.json()
            self.assertTrue('token' in token_json)
            return cast(Dict[str, Any], token_json)

        token_1 = get_token()
        token_2 = get_token()

        # 2022-07-06: we use JWT tokens now, so
        # the tokens MUST not be the same anymore
        self.assertNotEquals(token_1['token'], token_2['token'])


    def test_login_as_other_user(self) -> None:
        User.objects.create_superuser(username='nf', password='nf', email='test@neuroforge.de')
        User.objects.create_superuser(username='nf2', password='nf2', email='test@neuroforge.de')

        client = APIClient()
        client.login(username='nf', password='nf')

        def get_token() -> Dict[str, Any]:
            response = client.post(path=BASE_URL + "common/auth/authtoken/", data={
                'username': 'nf2',
                'password': 'nf2'
            }, format='json')
            self.assertEquals(status.HTTP_200_OK, response.status_code)

            token_json = response.json()
            self.assertTrue('token' in token_json)
            return cast(Dict[str, Any], token_json)

        get_token()

        # getting the token should not log us in even if we are logged in
        response = client.get(path=BASE_URL + "common/auth/check/", format='json')
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertEquals(response.json()['username'], 'nf')

    def test_should_not_log_in(self) -> None:
        User.objects.create_superuser(username='nf', password='nf', email='test@neuroforge.de')
        User.objects.create_superuser(username='nf2', password='nf2', email='test@neuroforge.de')

        client = APIClient()

        def get_token() -> Dict[str, Any]:
            response = client.post(path=BASE_URL + "common/auth/authtoken/", data={
                'username': 'nf2',
                'password': 'nf2'
            })
            self.assertEquals(status.HTTP_200_OK, response.status_code)

            token_json = response.json()
            self.assertTrue('token' in token_json)
            return cast(Dict[str, Any], token_json)

        get_token()

        # getting the token should not log us in even if we are logged in
        response = client.get(path=BASE_URL + "common/auth/check/", format='json')
        self.assertEquals(status.HTTP_403_FORBIDDEN, response.status_code)
