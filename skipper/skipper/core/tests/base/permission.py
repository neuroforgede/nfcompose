# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

from django.contrib.auth.models import Group, User
from django.db import transaction
from guardian.shortcuts import assign_perm  # type: ignore
from rest_framework import status
from rest_framework.test import APIClient
from typing import List, Any, Optional, Union

from skipper.core.models.tenant import Tenant, Tenant_Group, Tenant_User
from skipper.core.tests.base import BaseViewTest

http_verbs = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']
client_methods = ['get', 'post', 'put', 'patch', 'delete']


class BasePermissionAssignmentTest(BaseViewTest):
    simulate_other_tenant = True
    skip_setup_assertions = True

    tenant: Tenant
    other_tenant: Tenant

    def setUp(self) -> None:
        super().setUp()
        self.tenant = Tenant.objects.filter(
            name='default_tenant'
        )[0]
        self.other_tenant = Tenant.objects.filter(
            name='other_tenant'
        )[0]

    def possible_permissions(self) -> List[str]:
        raise NotImplementedError()

    def baseline_permissions_to_see_object(self) -> List[str]:
        raise NotImplementedError()

    def baseline_permissions_to_assign_permissions(self) -> List[str]:
        raise NotImplementedError()

    def permission_modification_string(self, method: str) -> str:
        raise NotImplementedError()

    def get_user_permission_url(self, object: Any, user_id: Optional[Union[int, str]] = None) -> str:
        raise NotImplementedError()

    def get_group_permission_url(self, object: Any, user_id: Optional[Union[int, str]] = None) -> str:
        raise NotImplementedError()

    def add_object(self, tenant: Tenant) -> Any:
        raise NotImplementedError()

    def test_baseline_permissions_to_see_is_included_in_baseline_permissions_to_assign(self) -> None:
        if self.__class__ == BasePermissionAssignmentTest:
            return
        self.assertNotEqual(0, len(set(self.baseline_permissions_to_assign_permissions())
                                   .intersection(set(self.baseline_permissions_to_see_object()))))

    # test these for groups
    def test_delete_not_allowed_group_url(self) -> None:
        if self.__class__ == BasePermissionAssignmentTest:
            return

        group_to_assign_to = Group.objects.create(
            name='mygroup'
        )
        Tenant_Group.objects.create(
            tenant=self.tenant,
            group=group_to_assign_to
        )

        engine = self.add_object(self.tenant)
        response = self.client.delete(self.get_group_permission_url(engine))
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, response.status_code)

        response = self.client.delete(self.get_group_permission_url(engine, group_to_assign_to.id))
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, response.status_code)

    def test_delete_not_allowed_user_url(self) -> None:
        if self.__class__ == BasePermissionAssignmentTest:
            return
        engine = self.add_object(self.tenant)
        response = self.client.delete(self.get_user_permission_url(engine))
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, response.status_code)

        response = self.client.delete(self.get_user_permission_url(engine, self.user.id))
        self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, response.status_code)

    def test_cant_find_other_tenant_groups_by_id(self) -> None:
        if self.__class__ == BasePermissionAssignmentTest:
            return

        group_to_assign_to = Group.objects.create(
            name='my_other_group'
        )
        Tenant_Group.objects.create(
            tenant=self.other_tenant,
            group=group_to_assign_to
        )

        engine = self.add_object(self.tenant)
        response = self.client.get(self.get_group_permission_url(engine, group_to_assign_to.id))
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_cant_find_other_tenant_users_by_id(self) -> None:
        if self.__class__ == BasePermissionAssignmentTest:
            return
        engine = self.add_object(self.tenant)
        response = self.client.get(self.get_user_permission_url(engine, self.user2.id))
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_cant_find_system_groups_by_id(self) -> None:
        if self.__class__ == BasePermissionAssignmentTest:
            return
        # this is by spec for now, so include it in the test
        group = Group.objects.create(
            name='mygroup'
        )
        Tenant_Group.objects.create(
            tenant=self.tenant,
            group=group,
            system=True
        )

        engine = self.add_object(self.tenant)
        response = self.client.get(self.get_group_permission_url(engine, group.id))
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_cant_find_system_users_by_id(self) -> None:
        if self.__class__ == BasePermissionAssignmentTest:
            return
        # this is by spec for now, so include it in the test
        user = User.objects.create_superuser(username='other', password='other', email='other@neuroforge.de')
        Tenant_User.objects.create(
            tenant=self.tenant,
            user=user,
            system=True
        )

        engine = self.add_object(self.tenant)
        response = self.client.get(self.get_user_permission_url(engine, user.id))
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_can_only_find_own_tenant_groups_in_list(self) -> None:
        if self.__class__ == BasePermissionAssignmentTest:
            return

        group = Group.objects.create(
            name='mygroup'
        )
        Tenant_Group.objects.create(
            tenant=self.tenant,
            group=group,
            system=False
        )

        other_group = Group.objects.create(
            name='my_other_group'
        )
        Tenant_Group.objects.create(
            tenant=self.other_tenant,
            group=other_group,
            system=False
        )

        engine = self.add_object(self.tenant)
        response = self.client.get(self.get_group_permission_url(engine))
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        as_json = response.json()

        self.assertEqual(1, len(as_json['results']))
        self.assertEqual(group.name, as_json['results'][0]['name'])

    def test_can_only_find_own_tenant_users_in_list(self) -> None:
        if self.__class__ == BasePermissionAssignmentTest:
            return
        engine = self.add_object(self.tenant)
        response = self.client.get(self.get_user_permission_url(engine))
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        as_json = response.json()

        self.assertEqual(1, len(as_json['results']))
        self.assertEqual(self.user.username, as_json['results'][0]['username'])

    def test_cant_find_system_groups_in_list(self) -> None:
        if self.__class__ == BasePermissionAssignmentTest:
            return
        # this is by spec for now, so include it in the test
        group = Group.objects.create(
            name='mygroup'
        )
        Tenant_Group.objects.create(
            tenant=self.tenant,
            group=group,
            system=True
        )

        engine = self.add_object(self.tenant)
        response = self.client.get(self.get_group_permission_url(engine))
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        as_json = response.json()

        self.assertEqual(0, len(as_json['results']))

    def test_cant_find_system_users_in_list(self) -> None:
        if self.__class__ == BasePermissionAssignmentTest:
            return
        # current spec
        user = User.objects.create_superuser(username='other', password='other', email='other@neuroforge.de')
        Tenant_User.objects.create(
            tenant=self.tenant,
            user=user,
            system=True
        )

        engine = self.add_object(self.tenant)
        response = self.client.get(self.get_user_permission_url(engine))
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        as_json = response.json()

        self.assertEqual(1, len(as_json['results']))

    def test_requires_proper_permissions_per_http_verb_on_rest_api(self) -> None:
        if self.__class__ == BasePermissionAssignmentTest:
            return
        user = User.objects.create_user(username='other', password='other', email='other@neuroforge.de')
        Tenant_User.objects.create(
            tenant=self.tenant,
            user=user
        )

        user_to_assign_to = User.objects.create_user(
            username='user_to_assign_to',
            password='user_to_assign_to',
            email='usertoassignto@neuroforge.de'
        )
        Tenant_User.objects.create(
            tenant=self.tenant,
            user=user_to_assign_to
        )

        obj = self.add_object(self.tenant)

        for baseline_perm, client_method in zip(self.baseline_permissions_to_see_object(), client_methods):
            assign_perm(baseline_perm, user)
            assign_perm(baseline_perm, user, obj)

        for http_verb, client_method in zip(http_verbs, client_methods):
            user = User.objects.filter(username=user.username)[0]

            sid = transaction.savepoint()

            client = APIClient()
            client.force_login(user)

            resp = getattr(client, client_method)(path=self.get_user_permission_url(obj))
            self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

            resp = getattr(client, client_method)(path=self.get_user_permission_url(obj, user_to_assign_to.id))
            self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

            perm = self.permission_modification_string(method=http_verb)

            assign_perm(perm, user)

            client = APIClient()
            client.force_login(user)

            resp = getattr(client, client_method)(path=self.get_user_permission_url(obj))
            self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

            resp = getattr(client, client_method)(path=self.get_user_permission_url(obj, user_to_assign_to.id))
            self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

            assign_perm(perm, user, obj)

            client = APIClient()
            client.force_login(user)

            resp = getattr(client, client_method)(path=self.get_user_permission_url(obj))
            self.assertNotEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

            if http_verb == 'POST':
                self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)

            resp = getattr(client, client_method)(path=self.get_user_permission_url(obj, user_to_assign_to.id))
            self.assertNotEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

            if http_verb == 'POST':
                self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)

            transaction.savepoint_rollback(sid)

    def test_requires_baseline_permissions(self) -> None:
        if self.__class__ == BasePermissionAssignmentTest:
            return
        user = User.objects.create_user(username='other', password='other', email='other@neuroforge.de')
        Tenant_User.objects.create(
            tenant=self.tenant,
            user=user
        )

        user_to_assign_to = User.objects.create_user(
            username='user_to_assign_to',
            password='user_to_assign_to',
            email='usertoassignto@neuroforge.de'
        )
        Tenant_User.objects.create(
            tenant=self.tenant,
            user=user_to_assign_to
        )

        obj = self.add_object(self.tenant)

        for http_verb, client_method in zip(http_verbs, client_methods):
            user = User.objects.filter(username=user.username)[0]

            sid = transaction.savepoint()

            perm = self.permission_modification_string(method=http_verb)

            assign_perm(perm, user)
            assign_perm(perm, user, obj)

            client = APIClient()
            client.force_login(user)

            resp = getattr(client, client_method)(path=self.get_user_permission_url(obj))
            self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

            resp = getattr(client, client_method)(path=self.get_user_permission_url(obj, user_to_assign_to.id))
            self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

            transaction.savepoint_rollback(sid)

        for baseline_perm, client_method in zip(self.baseline_permissions_to_see_object(), client_methods):
            assign_perm(baseline_perm, user)
            assign_perm(baseline_perm, user, obj)

        for http_verb, client_method in zip(http_verbs, client_methods):
            user = User.objects.filter(username=user.username)[0]

            sid = transaction.savepoint()

            perm = self.permission_modification_string(method=http_verb)

            assign_perm(perm, user)
            assign_perm(perm, user, obj)

            client = APIClient()
            client.force_login(user)

            resp = getattr(client, client_method)(path=self.get_user_permission_url(obj))
            self.assertNotEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

            if http_verb == 'POST':
                self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)

            resp = getattr(client, client_method)(path=self.get_user_permission_url(obj, user_to_assign_to.id))
            self.assertNotEqual(status.HTTP_403_FORBIDDEN, resp.status_code)

            if http_verb == 'POST':
                self.assertEqual(status.HTTP_405_METHOD_NOT_ALLOWED, resp.status_code)

            transaction.savepoint_rollback(sid)

    def test_user_permission_assignment_and_requires_permission_on_itself_to_assign_it(self) -> None:
        if self.__class__ == BasePermissionAssignmentTest:
            return
        user = User.objects.create_user(username='other', password='other', email='other@neuroforge.de')
        Tenant_User.objects.create(
            tenant=self.tenant,
            user=user
        )

        user_to_assign_to = User.objects.create_user(
            username='user_to_assign_to',
            password='user_to_assign_to',
            email='usertoassignto@neuroforge.de'
        )
        Tenant_User.objects.create(
            tenant=self.tenant,
            user=user_to_assign_to
        )

        obj = self.add_object(self.tenant)

        baseline_perms_set = set(self.baseline_permissions_to_assign_permissions())

        for baseline_perm in baseline_perms_set:
            assign_perm(baseline_perm, user)
            assign_perm(baseline_perm, user, obj)

        for perm in self.possible_permissions():
            if perm in baseline_perms_set:
                continue

            _path = self.get_user_permission_url(obj, user_to_assign_to.id)

            def _assert_not_allowed() -> None:
                resp = client.put(path=_path, data={
                    "user_permissions": [
                        perm
                    ]
                })

                self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)
                self.assertFalse(user_to_assign_to.has_perm(perm=perm, obj=obj))
                self.assertFalse(user_to_assign_to.has_perm(perm=perm))

            def _assert_allowed() -> None:
                resp = client.put(path=_path, data={
                    "user_permissions": [
                        perm
                    ]
                })

                self.assertEqual(status.HTTP_200_OK, resp.status_code)
                self.assertTrue(user_to_assign_to.has_perm(perm=perm, obj=obj))
                self.assertFalse(user_to_assign_to.has_perm(perm=perm))

            user = User.objects.filter(username=user.username)[0]

            # does not have it => bad request
            client = APIClient()
            client.force_login(user)

            _assert_not_allowed()

            sid = transaction.savepoint()

            # only has global => not allowed
            assign_perm(perm, user)

            client = APIClient()
            client.force_login(user)

            _assert_not_allowed()

            # has perms => allowed
            assign_perm(perm, user, obj)

            client = APIClient()
            client.force_login(user)
            _assert_allowed()

            transaction.savepoint_rollback(sid)

            sid = transaction.savepoint()

            # only has obj => not allowed
            assign_perm(perm, user, obj)

            client = APIClient()
            client.force_login(user)

            _assert_not_allowed()

            transaction.savepoint_rollback(sid)

    def test_group_permission_assignment_and_requires_permission_on_itself_to_assign_it(self) -> None:
        if self.__class__ == BasePermissionAssignmentTest:
            return
        user = User.objects.create_user(username='other', password='other', email='other@neuroforge.de')
        Tenant_User.objects.create(
            tenant=self.tenant,
            user=user
        )

        group_to_assign_to = Group.objects.create(
            name='mygroup'
        )
        Tenant_Group.objects.create(
            tenant=self.tenant,
            group=group_to_assign_to
        )
        user_to_assign_to = User.objects.create_user(
            username='user_to_assign_to',
            password='user_to_assign_to',
            email='usertoassignto@neuroforge.de'
        )
        user_to_assign_to.groups.add(group_to_assign_to)
        user_to_assign_to.save()
        Tenant_User.objects.create(
            tenant=self.tenant,
            user=user_to_assign_to
        )

        obj = self.add_object(self.tenant)

        baseline_perms_set = set(self.baseline_permissions_to_assign_permissions())

        for baseline_perm in baseline_perms_set:
            assign_perm(baseline_perm, user)
            assign_perm(baseline_perm, user, obj)

        for perm in self.possible_permissions():
            if perm in baseline_perms_set:
                continue

            _path = self.get_group_permission_url(obj, group_to_assign_to.id)

            def _assert_not_allowed() -> None:
                resp = client.put(path=_path, data={
                    "group_permissions": [
                        perm
                    ]
                })

                self.assertEqual(status.HTTP_403_FORBIDDEN, resp.status_code)
                self.assertFalse(user_to_assign_to.has_perm(perm=perm, obj=obj))

            def _assert_allowed() -> None:
                resp = client.put(path=_path, data={
                    "group_permissions": [
                        perm
                    ]
                })

                self.assertEqual(status.HTTP_200_OK, resp.status_code)
                self.assertTrue(user_to_assign_to.has_perm(perm=perm, obj=obj))
                self.assertFalse(user_to_assign_to.has_perm(perm=perm))

            user = User.objects.filter(username=user.username)[0]

            # does not have it => bad request
            client = APIClient()
            client.force_login(user)

            _assert_not_allowed()

            sid = transaction.savepoint()

            # only has global => not allowed
            assign_perm(perm, user)

            client = APIClient()
            client.force_login(user)

            _assert_not_allowed()

            # has perms => allowed
            assign_perm(perm, user, obj)

            client = APIClient()
            client.force_login(user)
            _assert_allowed()

            transaction.savepoint_rollback(sid)

            sid = transaction.savepoint()

            # only has obj => not allowed
            assign_perm(perm, user, obj)

            client = APIClient()
            client.force_login(user)

            _assert_not_allowed()

            transaction.savepoint_rollback(sid)

    # TODO: remove baseline permissions one by one and check they are all required?

    # TODO: try to remove a perm from a user which we ourselves do not have
    #  (we know this does not work, but this is not tested)

    # TODO: can't assign permissions for users/groups not in the current tenant
    #  (this is already somewhat tested via the list endpoint,
    #  but not enforced and therefore relies on the queryset construction)