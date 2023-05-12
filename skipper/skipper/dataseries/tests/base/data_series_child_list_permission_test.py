# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from django.contrib.auth.models import Permission, User
from guardian.shortcuts import assign_perm, remove_perm  # type: ignore
from rest_framework import status
from typing import Any, Dict, Optional

from skipper import modules
from skipper.core.tests.base import BASE_URL, BaseRESTPermissionTest
from skipper.dataseries.models import ds_permission_for_rest_method, DATASERIES_PERMISSION_KEY_DATA_SERIES
from skipper.dataseries.models.metamodel.data_series import DataSeries

DATA_SERIES_BASE_URL = BASE_URL + modules.url_representation(modules.Module.DATA_SERIES) + '/'


class BaseDataSeriesDetailPermissionTest(BaseRESTPermissionTest):
    """
    rudimentarily tests whether the given methods are allowed to be run
    against the dataseries detail endpoints
    """

    skip_setup_assertions: bool = True

    data_series_json: Dict[str, Any]

    base_class_name = 'BaseDataSeriesDetailPermissionTest'

    def proper_without_data_series_obj_permission_status(self) -> int:
        return status.HTTP_403_FORBIDDEN

    def malformed_without_data_series_obj_permission_status(self) -> int:
        return status.HTTP_403_FORBIDDEN

    def __without_data_series_obj_permissions(self) -> None:
        malformed_without_permissions = self.method_under_test_malformed()
        if malformed_without_permissions is not None:
            self.assertEquals(self.malformed_without_data_series_obj_permission_status(), malformed_without_permissions.status_code)
        proper_without_permissions = self.method_under_test_proper()
        self.assertEquals(self.proper_without_data_series_obj_permission_status(), proper_without_permissions.status_code)

    def _add_dataseries_perms(self) -> None:
        data_series = DataSeries.objects.get(
            id=self.data_series_json['id']
        )

        data_series_read_permission = ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_DATA_SERIES,
            method='GET'
        )

        assign_perm(
            f'dataseries.{data_series_read_permission}',
            self.test_user,
        )

        # still does not have the permissions on the object
        # so we should get a 403
        self.test_user = User.objects.get(username=self.test_user.username)
        self.user_client.force_login(self.test_user)
        self.__without_data_series_obj_permissions()

        assign_perm(
            f'dataseries.{data_series_read_permission}',
            self.test_user,
            obj=data_series
        )

    def _remove_dataseries_perms(self) -> None:
        data_series = DataSeries.objects.get(
            id=self.data_series_json['id']
        )

        data_series_read_permission = ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_DATA_SERIES,
            method='GET'
        )

        remove_perm(
            f'dataseries.{data_series_read_permission}',
            self.test_user,
            obj=data_series
        )

        self.test_user = User.objects.get(username=self.test_user.username)
        self.user_client.force_login(self.test_user)
        self.__without_data_series_obj_permissions()

        remove_perm(
            f'dataseries.{data_series_read_permission}',
            self.test_user,
        )

    def base_add_extra_permissions(self) -> None:
        data_series = DataSeries.objects.get(
            id=self.data_series_json['id']
        )

        assign_perm(
            f'{self.permission_code_prefix}.{self.permission_code_name()}',
            self.test_user,
            obj=data_series
        )

        self._add_dataseries_perms()

    def base_remove_extra_permissions(self) -> None:
        data_series = DataSeries.objects.get(
            id=self.data_series_json['id']
        )

        remove_perm(
            f'{self.permission_code_prefix}.{self.permission_code_name()}',
            self.test_user,
            obj=data_series
        )

        self._remove_dataseries_perms()

    def base_add_bare_user(self) -> None:
        self.create_data_series()

    def create_data_series(self) -> None:
        self.data_series_json = self.create_payload(DATA_SERIES_BASE_URL + 'dataseries/', payload={
            'name': 'my_data_series_1',
            'external_id': 'external_id1'
        }, simulate_tenant=False)

    def without_extra_permissions_test(self) -> None:
        malformed_without_permissions = self.method_under_test_malformed()
        if malformed_without_permissions is not None:
            self.assertEquals(status.HTTP_403_FORBIDDEN, malformed_without_permissions.status_code)
        proper_without_permissions = self.method_under_test_proper()
        self.assertEquals(status.HTTP_403_FORBIDDEN, proper_without_permissions.status_code)

    def after_base_test(self) -> None:
        self._after_base_test(
            status_code_only_global_dataseries=status.HTTP_403_FORBIDDEN
        )

    def _after_base_test(self, status_code_only_global_dataseries: int) -> None:
        if self.__class__.__name__ == self.base_class_name:
            return

        data_series_read_permission = ds_permission_for_rest_method(
            action=DATASERIES_PERMISSION_KEY_DATA_SERIES,
            method='GET'
        )

        data_series = DataSeries.objects.get(
            id=self.data_series_json['id']
        )

        def without_permissions(expected_status_code: int) -> None:
            malformed_without_permissions = self.method_under_test_malformed()
            if malformed_without_permissions is not None:
                self.assertEquals(expected_status_code, malformed_without_permissions.status_code)
            proper_without_permissions = self.method_under_test_proper()
            self.assertEquals(expected_status_code, proper_without_permissions.status_code)

        # still has global permissions on dataseries, so should get 403 after this
        remove_perm(
            f'dataseries.{data_series_read_permission}',
            self.test_user,
            obj=data_series
        )
        self.test_user = User.objects.get(username=self.test_user.username)
        self.user_client.force_login(self.test_user)
        without_permissions(expected_status_code=status_code_only_global_dataseries)

        # does not have global permissions on dataseries, so should get 403 after this
        remove_perm(
            f'dataseries.{data_series_read_permission}',
            self.test_user
        )
        self.test_user = User.objects.get(username=self.test_user.username)
        self.user_client.force_login(self.test_user)

        without_permissions(expected_status_code=status.HTTP_403_FORBIDDEN)
