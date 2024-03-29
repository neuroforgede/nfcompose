# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from typing import Type, Dict, Any

from django.contrib.auth.models import User
from django.db.models import Model
from guardian.shortcuts import remove_perm, assign_perm  # type: ignore
from rest_framework import status

from skipper.core.tests.base import BaseRESTPermissionTest


class BaseModelDetailPermissionTest(BaseRESTPermissionTest):
    permission_code_prefix: str

    skip_setup_assertions: bool = True

    obj_json: Dict[str, Any]
    model_type: Type[Model]

    permission_key: str

    base_class_name = 'BaseModelDetailPermissionTest'

    def proper_without_base_obj_permission_status(self) -> int:
        return status.HTTP_403_FORBIDDEN

    def malformed_without_base_obj_permission_status(self) -> int:
        return status.HTTP_403_FORBIDDEN

    def proper_without_obj_permission_status(self) -> int:
        return status.HTTP_403_FORBIDDEN

    def malformed_without_obj_permission_status(self) -> int:
        return status.HTTP_403_FORBIDDEN

    def __without_obj_permissions(self) -> None:
        malformed_without_permissions = self.method_under_test_malformed()
        if malformed_without_permissions is not None:
            self.assertEquals(self.malformed_without_base_obj_permission_status(),
                              malformed_without_permissions.status_code)
        proper_without_permissions = self.method_under_test_proper()
        self.assertEquals(self.proper_without_base_obj_permission_status(), proper_without_permissions.status_code)

    def _extra_add_base_permission(self) -> None:
        obj = self.model_type.objects.get(
            id=self.obj_json['id']
        )

        _read_permission = self.read_permission()

        assign_perm(
            f'{self.permission_code_prefix}.{_read_permission}',
            self.test_user,
        )

        # still does not have the permissions on the object
        # so we should get a 403
        self.test_user = User.objects.get(username=self.test_user.username)
        self.user_client.force_login(self.test_user)
        self.__without_obj_permissions()

        assign_perm(
            f'{self.permission_code_prefix}.{_read_permission}',
            self.test_user,
            obj=obj
        )

    def _extra_remove_base_perms(self) -> None:
        obj = self.model_type.objects.get(
            id=self.obj_json['id']
        )

        _read_permission = self.read_permission()

        remove_perm(
            f'{self.permission_code_prefix}.{_read_permission}',
            self.test_user,
            obj=obj
        )

        self.test_user = User.objects.get(username=self.test_user.username)
        self.user_client.force_login(self.test_user)
        self.__without_obj_permissions()

        remove_perm(
            f'{self.permission_code_prefix}.{_read_permission}',
            self.test_user,
        )

    def base_add_extra_permissions(self) -> None:
        obj = self.model_type.objects.get(
            id=self.obj_json['id']
        )

        assign_perm(
            f'{self.permission_code_prefix}.{self.permission_code_name()}',
            self.test_user,
            obj=obj
        )

        self._extra_add_base_permission()

    def base_remove_extra_permissions(self) -> None:
        obj = self.model_type.objects.get(
            id=self.obj_json['id']
        )

        remove_perm(
            f'{self.permission_code_prefix}.{self.permission_code_name()}',
            self.test_user,
            obj=obj
        )

        self._extra_remove_base_perms()

    def base_add_bare_user(self) -> None:
        super().base_add_bare_user()
        self.create_obj_via_rest()

    def create_obj_via_rest(self) -> None:
        raise NotImplementedError()

    def read_permission(self) -> str:
        raise NotImplementedError()

    def without_extra_permissions_test(self) -> None:
        malformed_without_permissions = self.method_under_test_malformed()
        if malformed_without_permissions is not None:
            self.assertEquals(self.malformed_without_obj_permission_status(), malformed_without_permissions.status_code)
        proper_without_permissions = self.method_under_test_proper()
        self.assertEquals(self.proper_without_obj_permission_status(), proper_without_permissions.status_code)

    def after_base_test(self) -> None:
        self._after_base_test(
            status_code_only_global=status.HTTP_403_FORBIDDEN
        )

    def _after_base_test(self, status_code_only_global: int) -> None:
        if self.__class__.__name__ == self.base_class_name:
            return

        _read_permission = _read_permission = self.read_permission()

        obj = self.model_type.objects.get(
            id=self.obj_json['id']
        )

        def without_permissions(expected_status_code: int) -> None:
            malformed_without_permissions = self.method_under_test_malformed()
            if malformed_without_permissions is not None:
                self.assertEquals(expected_status_code, malformed_without_permissions.status_code)
            proper_without_permissions = self.method_under_test_proper()
            self.assertEquals(expected_status_code, proper_without_permissions.status_code)

        # still has global permissions on object, so should get 403 after this
        remove_perm(
            f'{self.permission_code_prefix}.{_read_permission}',
            self.test_user,
            obj=obj
        )
        self.test_user = User.objects.get(username=self.test_user.username)
        self.user_client.force_login(self.test_user)
        without_permissions(expected_status_code=status_code_only_global)

        # does not have global permissions on object, so should get 403 after this
        remove_perm(
            f'{self.permission_code_prefix}.{_read_permission}',
            self.test_user
        )
        self.test_user = User.objects.get(username=self.test_user.username)
        self.user_client.force_login(self.test_user)

        without_permissions(expected_status_code=status.HTTP_403_FORBIDDEN)