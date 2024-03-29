# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

import uuid

from django.contrib.auth.models import User
from django.test import TestCase
from django_multitenant.utils import set_current_tenant  # type: ignore
from guardian.shortcuts import assign_perm, remove_perm  # type: ignore
from rest_framework.exceptions import PermissionDenied
from typing import Any, Optional

from skipper.core.models.tenant import Tenant, Tenant_User
from skipper.dataseries.models.permissions import DATASERIES_PERMISSION_KEY_DATA_SERIES, ds_permission_for_rest_method, \
    ALL_AVAILABLE_PERMISSIONS_DATA_SERIES
from skipper.dataseries.models.metamodel.data_series import DataSeries
from skipper.dataseries.views.contract import get_data_series_object


class FakeRequest:
    user: User
    method: Any

    def __init__(self, user: User, method: Optional[str]) -> None:
        super().__init__()
        self.user = user
        self.method = method


class GetDataSeriesObjectTest(TestCase):
    tenant: Tenant
    data_series: DataSeries
    user: User

    def setUp(self) -> None:
        self.tenant = Tenant.objects.create(
            name='tenant'
        )
        self.tenant.save()
        set_current_tenant(self.tenant)

        self.data_series = DataSeries.objects.create(
            name='my_ds',
            external_id='1',
            tenant=self.tenant
        )

        self.data_series.save()

        self.user = User.objects.create_user(
            username='my_user'
        )
        self.user.save()

        Tenant_User.objects.create(
            user=self.user,
            tenant=self.tenant
        )

    def assign_perm(self, perm: str, obj: Any = None) -> None:
        assign_perm(
            perm,
            self.user,
            obj=obj
        )
        self.user = User.objects.filter(
            id=self.user.id
        ).all()[0]
        self.assertTrue(self.user.has_perm(perm, obj=obj))

    def remove_perm(self, perm: str, obj: Any = None) -> None:
        remove_perm(
            perm,
            self.user,
            obj=obj
        )
        self.user = User.objects.filter(
            id=self.user.id
        ).all()[0]
        self.assertFalse(self.user.has_perm(perm, obj=obj))

    def assign_ds_read_perm(self, obj: Any = None) -> None:
        ds_read_perm = self.perm(DATASERIES_PERMISSION_KEY_DATA_SERIES, 'GET')
        self.assign_perm(
            perm=ds_read_perm,
            obj=obj
        )

    def assign_staff(self) -> None:
        self.user.is_staff = True
        self.user.save()
        self.user = User.objects.filter(
            id=self.user.id
        ).all()[0]

    def perm(self, action: str, method: str) -> str:
        return 'dataseries.' + ds_permission_for_rest_method(
            action=action,
            method=method
        )

    def tearDown(self) -> None:
        set_current_tenant(None)

    # failing normal tests

    def test_fail_without_any_permissions(self) -> None:
        kwargs = {
            'data_series': str(self.data_series.id)
        }
        for method in ['GET', 'POST', 'PUT', 'PATCH', 'OPTIONS', 'HEAD']:
            fake_request = FakeRequest(user=self.user, method=method)
            try:
                get_data_series_object(kwargs_object=kwargs, action='MY_ACTION', request=fake_request)
                self.fail('expected a PermissionDenied')
            except PermissionDenied:
                pass

    def test_fail_with_only_global_ds_permission(self) -> None:
        kwargs = {
            'data_series': str(self.data_series.id)
        }
        self.assign_ds_read_perm()
        actions = ALL_AVAILABLE_PERMISSIONS_DATA_SERIES
        for action in actions:
            for method in ['GET', 'POST', 'PUT', 'PATCH', 'OPTIONS', 'HEAD']:
                fake_request = FakeRequest(user=self.user, method=method)
                try:
                    get_data_series_object(kwargs_object=kwargs, action=action, request=fake_request)
                    self.fail('expected a PermissionDenied')
                except PermissionDenied:
                    pass

    def test_fail_with_correct_global_perms(self) -> None:
        kwargs = {
            'data_series': str(self.data_series.id)
        }
        self.assign_ds_read_perm()
        actions = ALL_AVAILABLE_PERMISSIONS_DATA_SERIES
        for action in actions:
            for method in ['GET', 'POST', 'PUT', 'PATCH', 'OPTIONS', 'HEAD']:
                self.assign_perm(self.perm(action, method))
                fake_request = FakeRequest(user=self.user, method=method)
                try:
                    get_data_series_object(kwargs_object=kwargs, action=action, request=fake_request)
                    self.fail('expected a PermissionDenied')
                except PermissionDenied:
                    pass
                self.remove_perm(self.perm(action, method))

    def test_fail_with_global_and_ds_read_perms(self) -> None:
        kwargs = {
            'data_series': str(self.data_series.id)
        }
        self.assign_ds_read_perm()
        self.assign_ds_read_perm(self.data_series)
        actions = ALL_AVAILABLE_PERMISSIONS_DATA_SERIES
        for action in actions:
            for method in ['GET', 'POST', 'PUT', 'PATCH', 'OPTIONS', 'HEAD']:
                if action == DATASERIES_PERMISSION_KEY_DATA_SERIES and method == 'GET':
                    continue
                self.assign_perm(self.perm(action, method))
                fake_request = FakeRequest(user=self.user, method=method)
                try:
                    get_data_series_object(kwargs_object=kwargs, action=action, request=fake_request)
                    self.fail('expected a PermissionDenied')
                except PermissionDenied:
                    pass
                self.remove_perm(self.perm(action, method))

    def test_fail_with_proper_read_perms_but_only_object_perm(self) -> None:
        kwargs = {
            'data_series': str(self.data_series.id)
        }
        self.assign_ds_read_perm()
        self.assign_ds_read_perm(self.data_series)
        actions = ALL_AVAILABLE_PERMISSIONS_DATA_SERIES
        for action in actions:
            for method in ['GET', 'POST', 'PUT', 'PATCH', 'OPTIONS', 'HEAD']:
                if action == DATASERIES_PERMISSION_KEY_DATA_SERIES and method == 'GET':
                    continue

                self.assign_perm(self.perm(action, method), self.data_series)
                fake_request = FakeRequest(user=self.user, method=method)
                try:
                    get_data_series_object(kwargs_object=kwargs, action=action, request=fake_request)
                    self.fail('expected a PermissionDenied')
                except PermissionDenied:
                    pass
                self.remove_perm(self.perm(action, method), self.data_series)

    def test_fail_with_all_only_object_perm(self) -> None:
        kwargs = {
            'data_series': str(self.data_series.id)
        }
        self.assign_ds_read_perm(self.data_series)
        actions = ALL_AVAILABLE_PERMISSIONS_DATA_SERIES
        for action in actions:
            for method in ['GET', 'POST', 'PUT', 'PATCH', 'OPTIONS', 'HEAD']:
                self.assign_perm(self.perm(action, method), self.data_series)
                fake_request = FakeRequest(user=self.user, method=method)
                try:
                    get_data_series_object(kwargs_object=kwargs, action=action, request=fake_request)
                    self.fail('expected a PermissionDenied')
                except PermissionDenied:
                    pass
                self.remove_perm(self.perm(action, method), self.data_series)

    def test_fail_everything_correct_but_no_method(self) -> None:
        kwargs = {
            'data_series': str(self.data_series.id)
        }
        self.assign_ds_read_perm()
        self.assign_ds_read_perm(self.data_series)
        actions = ALL_AVAILABLE_PERMISSIONS_DATA_SERIES
        for action in actions:
            for method in ['GET', 'POST', 'PUT', 'PATCH', 'OPTIONS', 'HEAD']:
                self.assign_perm(self.perm(action, method))
                self.assign_perm(self.perm(action, method), self.data_series)

        for action in actions:
            fake_request = FakeRequest(user=self.user, method=None)
            try:
                get_data_series_object(kwargs_object=kwargs, action=action, request=fake_request)
                self.fail('expected a PermissionDenied')
            except PermissionDenied:
                pass

    # passing normal tests

    def test_found_correct_with_all_perms(self) -> None:
        kwargs = {
            'data_series': str(self.data_series.id)
        }
        self.assign_ds_read_perm()
        self.assign_ds_read_perm(self.data_series)
        actions = ALL_AVAILABLE_PERMISSIONS_DATA_SERIES
        for action in actions:
            for method in ['GET', 'POST', 'PUT', 'PATCH', 'OPTIONS', 'HEAD']:
                self.assign_perm(self.perm(action, method))
                self.assign_perm(self.perm(action, method), self.data_series)
                fake_request = FakeRequest(user=self.user, method=method)
                found_ds = get_data_series_object(kwargs_object=kwargs, action=action, request=fake_request)
                self.assertIsNotNone(found_ds)
                assert found_ds is not None
                self.assertEquals(self.data_series.id, found_ds.id)

                if action == DATASERIES_PERMISSION_KEY_DATA_SERIES and method == 'GET':
                    # dont remove GET perm
                    continue
                self.remove_perm(self.perm(action, method))
                self.remove_perm(self.perm(action, method), self.data_series)

    def test_not_found_correct_with_all_perms(self) -> None:
        kwargs = {
            'data_series': str(uuid.uuid4())
        }
        self.assign_ds_read_perm()
        self.assign_ds_read_perm(self.data_series)
        actions = ALL_AVAILABLE_PERMISSIONS_DATA_SERIES
        for action in actions:
            for method in ['GET', 'POST', 'PUT', 'PATCH', 'OPTIONS', 'HEAD']:
                self.assign_perm(self.perm(action, method))
                self.assign_perm(self.perm(action, method), self.data_series)
                fake_request = FakeRequest(user=self.user, method=method)
                found_ds = get_data_series_object(kwargs_object=kwargs, action=action, request=fake_request)
                self.assertIsNone(found_ds)

                if action == DATASERIES_PERMISSION_KEY_DATA_SERIES and method == 'GET':
                    # dont remove GET perm
                    continue
                self.remove_perm(self.perm(action, method))
                self.remove_perm(self.perm(action, method), self.data_series)

    # staff tests below
    # staff only need the correct global perms

    def test_found_correct_with_global_and_staff(self) -> None:
        kwargs = {
            'data_series': str(self.data_series.id)
        }
        self.assign_staff()
        self.assign_ds_read_perm()
        actions = ALL_AVAILABLE_PERMISSIONS_DATA_SERIES
        for action in actions:
            for method in ['GET', 'POST', 'PUT', 'PATCH', 'OPTIONS', 'HEAD']:
                self.assign_perm(self.perm(action, method))
                fake_request = FakeRequest(user=self.user, method=method)
                found_ds = get_data_series_object(kwargs_object=kwargs, action=action, request=fake_request)
                self.assertIsNotNone(found_ds)
                assert found_ds is not None
                self.assertEquals(self.data_series.id, found_ds.id)

                if action == DATASERIES_PERMISSION_KEY_DATA_SERIES and method == 'GET':
                    # dont remove GET perm
                    continue
                self.remove_perm(self.perm(action, method))

    def test_fail_with_only_staff(self) -> None:
        kwargs = {
            'data_series': str(self.data_series.id)
        }
        self.assign_staff()
        actions = ALL_AVAILABLE_PERMISSIONS_DATA_SERIES
        for action in actions:
            for method in ['GET', 'POST', 'PUT', 'PATCH', 'OPTIONS', 'HEAD']:
                fake_request = FakeRequest(user=self.user, method=method)
                try:
                    get_data_series_object(kwargs_object=kwargs, action=action, request=fake_request)
                    self.fail('expected a PermissionDenied')
                except PermissionDenied:
                    pass

    def test_fail_with_only_global_ds_permission_and_staff(self) -> None:
        kwargs = {
            'data_series': str(self.data_series.id)
        }
        self.assign_staff()
        self.assign_ds_read_perm()
        actions = ALL_AVAILABLE_PERMISSIONS_DATA_SERIES
        for action in actions:
            for method in ['GET', 'POST', 'PUT', 'PATCH', 'OPTIONS', 'HEAD']:
                if action == DATASERIES_PERMISSION_KEY_DATA_SERIES and method == 'GET':
                    # staff global read == staff object read
                    continue
                fake_request = FakeRequest(user=self.user, method=method)
                try:
                    get_data_series_object(kwargs_object=kwargs, action=action, request=fake_request)
                    self.fail('expected a PermissionDenied')
                except PermissionDenied:
                    pass
