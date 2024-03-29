# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from skipper.core.models import PreSharedToken
from skipper.core.tests.base import BASE_URL


class PresharedTokenAuthTest(TestCase):

    def test_unique_constraints(self) -> None:
        user1 = User.objects.create_superuser(username='nf', password='nf', email='test@neuroforge.de')
        user2 = User.objects.create_superuser(username='nf2', password='nf2', email='test2@neuroforge.de')

        user1_pst1 = PreSharedToken.objects.create(
            key='MY_AWESOME_SECRET_PRESHARED_TOKEN1',
            user=user1
        )
        # multiple preshared tokens per user are fine
        user1_pst2 = PreSharedToken.objects.create(
            key='MY_AWESOME_SECRET_PRESHARED_TOKEN2',
            user=user1
        )

        try:
            user2_pst = PreSharedToken.objects.create(
                key='MY_AWESOME_SECRET_PRESHARED_TOKEN1',
                user=user2
            )
            self.fail('expected a failure when creating the same preshared token twice')
        except IntegrityError:
            pass

    def test_preshared_token_middleware(self) -> None:
        user1 = User.objects.create_superuser(username='nf', password='nf', email='test@neuroforge.de')

        client = APIClient()

        unauthenticated = client.get(path=BASE_URL + "common/auth/check/")
        self.assertEquals(status.HTTP_403_FORBIDDEN, unauthenticated.status_code)

        user1_pst1 = PreSharedToken.objects.create(
            key='MY_AWESOME_SECRET_PRESHARED_TOKEN1',
            user=user1
        )

        authenticated = client.get(
            path=BASE_URL + "common/auth/check/",
            data=None,
            follow=False,
            HTTP_AUTHORIZATION=f'PreSharedToken {user1_pst1.key}'
        )
        self.assertEquals(status.HTTP_200_OK, authenticated.status_code)
        self.assertEquals(authenticated.json()['username'], user1.username)

        user1_pst2 = PreSharedToken.objects.create(
            key='MY_AWESOME_SECRET_PRESHARED_TOKEN2',
            user=user1
        )

        authenticated = client.get(
            path=BASE_URL + "common/auth/check/",
            data=None,
            follow=False,
            HTTP_AUTHORIZATION=f'PreSharedToken {user1_pst2.key}'
        )
        self.assertEquals(status.HTTP_200_OK, authenticated.status_code)
        self.assertEquals(authenticated.json()['username'], user1.username)

