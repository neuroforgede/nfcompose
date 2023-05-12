# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from django.contrib.auth.models import User
from django.test import TestCase

from skipper.core.models.tenant import Tenant, Tenant_User, is_tenant_manager


class TestTenantManagerCheck(TestCase):

    @classmethod
    def setUpTestData(cls) -> None:
        Tenant.objects.create(
            name='default_tenant'
        )
        Tenant.objects.create(
            name='wrong_tenant'
        )

    def test_superuser_is_not_manager_correct_tenant(self) -> None:
        tenant = Tenant.objects.filter(
            name='default_tenant'
        )[0]
        super_user = User.objects.create_superuser(
            username='nf', 
            password='nf', 
            email='test@neuroforge.de'
        )
        Tenant_User.objects.create(
            tenant=tenant,
            user=super_user
        )

        self.assertFalse(is_tenant_manager(super_user, tenant))

    def test_superuser_is_not_manager_wrong_tenant(self) -> None:
        tenant = Tenant.objects.filter(
            name='default_tenant'
        )[0]
        super_user = User.objects.create_superuser(
            username='nf', 
            password='nf', 
            email='test@neuroforge.de'
        )
        Tenant_User.objects.create(
            tenant=tenant,
            user=super_user
        )

        tenant = Tenant.objects.filter(
            name='wrong_tenant'
        )[0]
        self.assertFalse(is_tenant_manager(super_user, tenant))

    def test_manager_is_manager_correct_tenant(self) -> None:
        tenant = Tenant.objects.filter(
            name='default_tenant'
        )[0]
        manager = User.objects.create(
            username='manager',
            password='manager',
            email='manager@neuroforge.de'
        )
        Tenant_User.objects.create(
            tenant=tenant,
            user=manager,
            tenant_manager=True
        )
        self.assertTrue(is_tenant_manager(manager, tenant))

    def test_manager_is_not_manager_wrong_tenant(self) -> None:
        tenant = Tenant.objects.filter(
            name='default_tenant'
        )[0]
        manager = User.objects.create(
            username='manager',
            password='manager',
            email='manager@neuroforge.de'
        )
        Tenant_User.objects.create(
            tenant=tenant,
            user=manager,
            tenant_manager=True
        )

        tenant = Tenant.objects.filter(
            name='wrong_tenant'
        )[0]
        self.assertFalse(is_tenant_manager(manager, tenant))

    def test_user_is_not_manager_correct_tenant(self) -> None:
        tenant = Tenant.objects.filter(
            name='default_tenant'
        )[0]
        normal_user = User.objects.create(
            username='user',
            password='user',
            email='user@neuroforge.de'
        )
        Tenant_User.objects.create(
            tenant=tenant,
            user=normal_user
        )

        self.assertFalse(is_tenant_manager(normal_user, tenant))

    def test_user_is_not_manager_wrong_tenant(self) -> None:
        tenant = Tenant.objects.filter(
            name='default_tenant'
        )[0]
        normal_user = User.objects.create(
            username='user',
            password='user',
            email='user@neuroforge.de'
        )
        Tenant_User.objects.create(
            tenant=tenant,
            user=normal_user
        )

        tenant = Tenant.objects.filter(
            name='wrong_tenant'
        )[0]
        self.assertFalse(is_tenant_manager(normal_user, tenant))