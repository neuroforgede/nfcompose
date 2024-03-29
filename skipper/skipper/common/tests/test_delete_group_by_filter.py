# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


from django.contrib.auth.models import User, Group
from django.db import IntegrityError
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from skipper.core.models import PreSharedToken
from skipper.core.models.tenant import Tenant_Group, Tenant
from skipper.core.tests.base import BASE_URL


class TestGroupDeleteByFilter(TestCase):

    def test_delete_group_by_filter(self) -> None:
        tenant = Tenant.objects.create(name='test_tenant')
        tenant.save()

        group = Group.objects.create(name='test')
        group.save()

        Tenant_Group.objects.create(
            group=group,
            tenant=tenant
        )

        Group.objects.filter(name='test').delete()
