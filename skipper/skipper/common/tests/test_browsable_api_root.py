# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
# If a copy of the MPL was not distributed with this file,
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from skipper.core.tests.base import BASE_URL


class BrowsableAPIRootTest(TestCase):

    def test_overview_renders_for_html_clients(self) -> None:
        User.objects.create_superuser(username='nf', password='nf', email='test@neuroforge.de')

        client = APIClient()
        self.assertTrue(client.login(username='nf', password='nf'))

        response = client.get(path=BASE_URL, HTTP_ACCEPT='text/html')

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertIn(b'NF Compose REST API', response.content)
