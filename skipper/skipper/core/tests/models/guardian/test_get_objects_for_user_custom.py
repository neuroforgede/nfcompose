# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


from typing import Any
from django.contrib.auth.models import User
from django.db.models import QuerySet
from django_multitenant.utils import set_current_tenant # type: ignore
from django.test import TestCase

from skipper.dataseries.models import get_permission_string_for_action_and_http_verb, \
    DATASERIES_PERMISSION_KEY_DATA_SERIES
from skipper.core.models.guardian import get_objects_for_user_custom
from skipper.core.models.tenant import Tenant, Tenant_User
from skipper.dataseries.models.metamodel.data_series import DataSeries


class TestGetObjectsForUserCustom(TestCase):
    _tenant: Tenant
    _ds_in_tenant: DataSeries
    
    _qs: QuerySet[Any]

    def setUp(self) -> None:
        super().setUp()
        self._tenant = Tenant.objects.create(name='default_tenant')
        set_current_tenant(self._tenant)
        self._ds_in_tenant = DataSeries.objects.create(
            tenant=self._tenant,
            name="some_name",
            external_id='1'
        )
        self._qs = DataSeries.objects.all()
        self.assertEqual(len(self._qs), 1)

    def test_no_special_status(self) -> None:
        user = User.objects.create_user(username='nf', password='nf', email='test@neuroforge.de')
        qs = get_objects_for_user_custom(
            user=user,
            perms=[
                get_permission_string_for_action_and_http_verb(
                    action=DATASERIES_PERMISSION_KEY_DATA_SERIES,
                    http_verb='GET'
                )
            ],
            queryset=self._qs,
            with_staff=True,
            app_label='dataseries'
        )

        self.assertEqual(len(qs), 0)

    def test_superuser_respected(self) -> None:
        user = User.objects.create_superuser(username='nf', password='nf', email='test@neuroforge.de')
        qs = get_objects_for_user_custom(
            user=user,
            perms=[
                get_permission_string_for_action_and_http_verb(
                    action=DATASERIES_PERMISSION_KEY_DATA_SERIES,
                    http_verb='GET'
                )
            ],
            queryset=self._qs,
            with_staff=True,
            app_label='dataseries'
        )

        self.assertEqual(len(qs), 1)

    def test_staff_respected(self) -> None:
        user = User.objects.create_user(username='nf', password='nf', email='test@neuroforge.de', is_staff=True)
        qs = get_objects_for_user_custom(
            user=user,
            perms=[
                get_permission_string_for_action_and_http_verb(
                    action=DATASERIES_PERMISSION_KEY_DATA_SERIES,
                    http_verb='GET'
                )
            ],
            queryset=self._qs,
            with_staff=True,
            app_label='dataseries'
        )

        self.assertEqual(len(qs), 1)

    def test_tenant_manager_respected(self) -> None:
        user = User.objects.create_user(username='nf', password='nf', email='test@neuroforge.de')
        Tenant_User.objects.create(
            tenant=self._tenant,
            user=user,
            tenant_manager=True
        )
        qs = get_objects_for_user_custom(
            user=user,
            perms=[
                get_permission_string_for_action_and_http_verb(
                    action=DATASERIES_PERMISSION_KEY_DATA_SERIES,
                    http_verb='GET'
                )
            ],
            queryset=self._qs,
            with_staff=True,
            app_label='dataseries'
        )

        self.assertEqual(len(qs), 1)
