# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from skipper.core.tests.base import BASE_URL


class CSRFTokenTest(TestCase):

    def test_get_csrf_token_no_auth(self) -> None:
        User.objects.create_superuser(username='nf', password='nf', email='test@neuroforge.de')
        client = APIClient()

        response = client.get(path=BASE_URL + "common/auth/csrftoken/")
        self.assertEquals(status.HTTP_200_OK, response.status_code)
