# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from django.contrib.auth.models import Group, User
from guardian.shortcuts import assign_perm, remove_perm  # type: ignore
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient
from typing import Dict, List, Any, Union, cast

from skipper import modules
from skipper.core.models.tenant import Tenant, Tenant_Group, Tenant_User
from skipper.core.tests.base import BaseViewTest, BASE_URL

DATA_SERIES_BASE_URL = BASE_URL + modules.url_representation(modules.Module.DATA_SERIES) + '/'


class BaseObjectLevelPermissionAssignmentTest(BaseViewTest):
    simulate_other_tenant = False

    # Override me (if needed)
    def create_assigner_user(self) -> User:
        '''Creation response for the user making assignments'''
        return User.objects.create_user(username='test_user_1', password='test_user_1', email='test@neuroforge.de')

    # Override me (if needed)
    def create_assignee_user(self) -> Union[User, None]:
        '''Creation response for the assignee user'''
        return User.objects.create_user(username='test_user_2', password='test_user_2', email='test@neuroforge.de')

    # Override me (if needed)
    def create_assignee_group(self) -> Union[Group, None]:
        '''Creation response for the assignee group'''
        return Group.objects.create(name='test_group')

    # Override me (if needed)
    def create_assigner_user_tenant_relation(self, user: User, tenant: Tenant) -> Union[Tenant_User, None]:
        '''Creation response for the relation between the tenant and the user making assignments'''
        return Tenant_User.objects.create(
            tenant=tenant,
            user=user
        )

    # Override me (if needed)
    def create_assignee_user_tenant_relation(self, user: User, tenant: Tenant) -> Union[Tenant_User, None]:
        '''Creation response for the relation between the tenant and assignee user'''
        return Tenant_User.objects.create(
            tenant=tenant,
            user=user
        )

    # Override me (if needed)
    def create_assignee_group_tenant_relation(self, group: Group, tenant: Tenant) -> Union[Tenant_Group, None]:
        '''Creation response for the relation between the tenant and assignee group'''
        return Tenant_Group.objects.create(
            tenant=tenant,
            group=group
        )

    # Override me
    def create_assignment_object(self) -> Dict[str, Any]:
        '''The creation response for object that the permissions are made on'''
        raise NotImplementedError()

    # ------------------------------------------------------------------------------------------------------------------

    # Override me
    def get_permissions_on_assigner_minimum(self) -> List[str]:
        '''Permissions that the assigner must always have (object-level AND globally) 
        in order to be able to make assignments in general'''
        raise NotImplementedError()

    # Override me
    def get_permissions_to_assign(self) -> List[str]:
        '''Which permissions to test on'''
        raise NotImplementedError()

    # Override me (if needed)
    def get_outcome_before_assigner_perm_assignment(self) -> int:
        '''The expected status code when the assigner only has the minimum permissions'''
        return status.HTTP_403_FORBIDDEN

    # Override me (if needed)
    def get_outcome_after_assigner_perm_assignment(self) -> int:
        '''The expected status code when the assigner has the minimum permissions plus the to-assign one'''
        return status.HTTP_200_OK

    # ------------------------------------------------------------------------------------------------------------------

    # Override me (if needed)
    def get_user_perms_object(
        self, 
        object: Dict[str, Any], 
        user: User
    ) -> Any:
        '''Given an object (REST Representation) and user, returns the entry in the REST API that represents the 
        user's permissions on the object'''
        return self.get_payload(
            url=f"{object['permission_user']}?fully_qualified={user.username}"
        )['results'][0]

    # Override me (if needed)
    def get_group_perms_object(
        self, 
        object: Dict[str, Any], 
        group: Group
    ) -> Any:  # type: ignore
        '''Given an object (REST Representation) and group, returns the entry in the REST API that represents the 
        group's permissions on the object'''
        return self.get_payload(
            url=f"{object['permission_group']}?fully_qualified={group.name}"
        )['results'][0]

    # Override me (if needed)
    def get_object_level_user_perms(
        self, 
        object: Dict[str, Any], 
        user: User
    ) -> List[str]:  # type: ignore
        '''Given an object (REST Representation) and user, returns a list of all permission strings the user has 
        on the object (according to the API)'''
        _perms_obj = self.get_user_perms_object(object=object, user=user)
        return cast(List[str], _perms_obj['user_permissions'])

    # Override me (if needed)
    def get_object_level_group_perms(
        self, 
        object: Dict[str, Any], 
        group: Group
    ) -> List[str]:
        '''Given an object (REST Representation) and group, returns a list of all permission strings the group has 
        on the object (according to the API)'''
        _perms_obj = self.get_group_perms_object(object=object, group=group)
        return cast(List[str], _perms_obj['group_permissions'])

    # Override me (if needed)
    def set_object_level_user_perms_superuser(
        self, 
        assignment_object: Dict[str, Any], 
        assignee_user: User, 
        perms: List[str]
    ) -> None:
        '''Set the permissions that assignee_user has on assignment_object, but 
        bypassing any assigner permission checks.'''
        _perms_obj = self.get_user_perms_object(object=assignment_object, user=assignee_user)
        _perms_obj['user_permissions'] = perms
        self.update_payload(
            url=_perms_obj['url'],
            payload=_perms_obj
        )

    # Override me (if needed)
    def set_object_level_group_perms_superuser(
        self, 
        assignment_object: Dict[str, Any], 
        assignee_group: Group, 
        perms: List[str]
    ) -> None:
        '''Set the permissions that assignee_group has on assignment_object, but 
        bypassing any assigner permission checks.'''
        _perms_obj = self.get_group_perms_object(object=assignment_object, group=assignee_group)
        _perms_obj['group_permissions'] = perms
        self.update_payload(
            url=_perms_obj['url'],
            payload=_perms_obj
        )

    # Override me (if needed)
    def attempt_set_object_level_user_perms(
        self, 
        assignment_object: Dict[str, Any], 
        assigner_client: APIClient, 
        assignee_user: User, 
        perms: List[str]
    ) -> Response:
        '''Lets the assigner client attempt to set the permissions that assignee_user has on assignment_object. 
        Returns response without HTTP code check'''
        _perms_obj = self.get_user_perms_object(object=assignment_object, user=assignee_user)
        _perms_obj['user_permissions'] = perms
        return assigner_client.put(
            path=_perms_obj['url'],
            data=_perms_obj,
            format='json'
        )

    # Override me (if needed)
    def attempt_set_object_level_group_perms(
        self, 
        assignment_object: Dict[str, Any], 
        assigner_client: APIClient, 
        assignee_group: Group, perms: List[str]
    ) -> Response:
        '''Lets the assigner client attempt to set the permissions that assignee_group has on assignment_object. 
        Returns response without HTTP code check'''
        _perms_obj = self.get_group_perms_object(object=assignment_object, group=assignee_group)
        _perms_obj['group_permissions'] = perms
        return assigner_client.put(
            path=_perms_obj['url'],
            data=_perms_obj,
            format='json'
        )

    def check_permissions_equal(
        self,
        actual_permissions: List[str],
        expected_permissions: List[str]
    ) -> None:
        '''Asserts list equality, not sensitive to order but sensitive to count of identical entries.'''
        self.assertEqual(sorted(actual_permissions), sorted(expected_permissions))

    # ------------------------------------------------------------------------------------------------------------------

    def test(self) -> None:
        # Core test, should not be overridden. Behavior may be changed through overriding the other test functions.

        # if this is the base test, skip
        if self.__class__.__name__ == BaseObjectLevelPermissionAssignmentTest.__name__:
            return

        # initial setup
        tenant = Tenant.objects.get(
            name='default_tenant'
        )
        num_tenant_users = 2  # There are always a superuser (from base test) and the assigner
        assigner = self.create_assigner_user()
        if assigner is None:
            self.fail('no assigner created')
        self.create_assigner_user_tenant_relation(assigner, tenant)
        assignee_user = self.create_assignee_user()
        if assignee_user is not None:
            num_tenant_users += 1
            self.create_assignee_user_tenant_relation(assignee_user, tenant)
        assignee_group = self.create_assignee_group()
        if assignee_group is not None:
            num_tenant_users += 1
            self.create_assignee_group_tenant_relation(assignee_group, tenant)

        self.assertNotEqual(2, num_tenant_users, 'no assignees created')

        # assure all users and groups are properly registered
        self.assertEqual(
            num_tenant_users, 
            (
                len(Tenant_User.objects.filter(tenant=tenant).all()) + 
                len(Tenant_Group.objects.filter(tenant=tenant).all())
            )
        )

        assigner_client = APIClient()
        assigner_client.force_login(assigner)   # must always force login in tests if permissions change

        assignment_object = self.create_assignment_object()
        self.assertIsNotNone(assignment_object)

        # assure there are no perms anywhere yet
        self.check_permissions_equal(
            self.get_object_level_user_perms(assignment_object, assigner),
            []
        )
        if assignee_user is not None:
            self.check_permissions_equal(
                self.get_object_level_user_perms(assignment_object, assignee_user),
                []
            )
        if assignee_group is not None:
            self.check_permissions_equal(
                self.get_object_level_group_perms(assignment_object, assignee_group),
                []
            )

        # give assigner object-level base perms
        self.set_object_level_user_perms_superuser(
            assignment_object=assignment_object,
            assignee_user=assigner,
            perms=self.get_permissions_on_assigner_minimum()
        )

        # assigner must have baseline perms now
        self.check_permissions_equal(
            self.get_object_level_user_perms(assignment_object, assigner),
            self.get_permissions_on_assigner_minimum()
        )

        # the assigner must also have all minimum permissions globally, otherwise they are not able to assign anything
        for perm in self.get_permissions_on_assigner_minimum():
            assign_perm(perm, assigner)

        assigner_client.force_login(assigner)
        
        # repeats for every permission-to-assign individually and resets the permission to the previous state
        # after every loop
        for permission in self.get_permissions_to_assign():
            '''
            Pattern here:
                - attempt the assignment
                - check if response code is what was expected
                - if response code is 2xx:
                    - make sure permission was added
                    - remove it again
                - make sure permission is not there (it was either never added or cleaned up)

            This is done twice. The first time, the assigner does not have the object-level permission themselves,
            the second time they have it. The outcomes may differ and the functions 
                get_outcome_before_assigner_perm_assignment and
                get_outcome_after_assigner_perm_assignment
            reflect that.

            If the to-be-assigned permission is in the baseline permissions of the assigner, the first half of tests is 
            skipped as they don't make sense.
            '''
            resp: Response

            # --- assigner doesn't have permission that is being assigned ---

            # ... unless assigner has the permission already because it's baseline:
            if permission not in self.get_permissions_on_assigner_minimum():
                # assignee user:
                if assignee_user is not None:
                    resp = self.attempt_set_object_level_user_perms(
                        assignment_object=assignment_object,
                        assigner_client=assigner_client,
                        assignee_user=assignee_user,
                        perms=[permission]
                    )
                    self.assertEqual(self.get_outcome_before_assigner_perm_assignment(), resp.status_code)
                    if 200 <= resp.status_code < 300:  # should've been assigned
                        self.check_permissions_equal(
                            [permission],
                            self.get_object_level_user_perms(assignment_object, assignee_user)
                        )
                        self.set_object_level_user_perms_superuser(
                            assignment_object=assignment_object,
                            assignee_user=assignee_user,
                            perms=[]
                        )
                    self.check_permissions_equal(
                        [],
                        self.get_object_level_user_perms(assignment_object, assignee_user)
                    )

                # assignee group:
                if assignee_group is not None:
                    resp = self.attempt_set_object_level_group_perms(
                        assignment_object=assignment_object,
                        assigner_client=assigner_client,
                        assignee_group=assignee_group,
                        perms=[permission]
                    )
                    self.assertEqual(self.get_outcome_before_assigner_perm_assignment(), resp.status_code)
                    if 200 <= resp.status_code < 300:  # should've been assigned
                        self.check_permissions_equal(
                            [permission],
                            self.get_object_level_group_perms(assignment_object, assignee_group)
                        )
                        self.set_object_level_group_perms_superuser(
                            assignment_object=assignment_object,
                            assignee_group=assignee_group,
                            perms=[]
                        )
                    self.check_permissions_equal(
                        [],
                        self.get_object_level_group_perms(assignment_object, assignee_group)
                    )

            # --- assigner gets permission that is being assigned ---

            # ... unless assigner has the permission already because it's baseline:
            if permission not in self.get_permissions_on_assigner_minimum():
                self.set_object_level_user_perms_superuser(
                    assignment_object=assignment_object,
                    assignee_user=assigner,
                    perms=self.get_permissions_on_assigner_minimum() + [permission]
                )
                self.check_permissions_equal(
                    self.get_object_level_user_perms(
                        object=assignment_object,
                        user=assigner
                    ),
                    self.get_permissions_on_assigner_minimum() + [permission]
                )
            
                assign_perm(permission, assigner)
                assigner_client.force_login(assigner)
            
            # --- assigner gets permission that is being assigned ---

            # assignee user:
            if assignee_user is not None:
                resp = self.attempt_set_object_level_user_perms(
                    assignment_object=assignment_object,
                    assigner_client=assigner_client,
                    assignee_user=assignee_user,
                    perms=[permission]
                )
                self.assertEqual(self.get_outcome_after_assigner_perm_assignment(), resp.status_code)
                if 200 <= resp.status_code < 300:  # should've been assigned
                    self.check_permissions_equal(
                        [permission],
                        self.get_object_level_user_perms(assignment_object, assignee_user)
                    )
                    self.set_object_level_user_perms_superuser(
                        assignment_object=assignment_object,
                        assignee_user=assignee_user,
                        perms=[]
                    )
                self.check_permissions_equal(
                    [],
                    self.get_object_level_user_perms(assignment_object, assignee_user)
                )

            # assignee group:
            if assignee_group is not None:
                resp = self.attempt_set_object_level_group_perms(
                    assignment_object=assignment_object,
                    assigner_client=assigner_client,
                    assignee_group=assignee_group,
                    perms=[permission]
                )
                self.assertEqual(self.get_outcome_after_assigner_perm_assignment(), resp.status_code)
                if 200 <= resp.status_code < 300:  # should've been assigned
                    self.check_permissions_equal(
                        [permission],
                        self.get_object_level_group_perms(assignment_object, assignee_group)
                    )
                    self.set_object_level_group_perms_superuser(
                        assignment_object=assignment_object,
                        assignee_group=assignee_group,
                        perms=[]
                    )
                self.check_permissions_equal(
                    [],
                    self.get_object_level_group_perms(assignment_object, assignee_group)
                )

            # --- assigner loses permission that is being assigned ---

            # ... unless assigner had the permission already because it's baseline:
            if permission not in self.get_permissions_on_assigner_minimum():
                # reset assigner
                self.set_object_level_user_perms_superuser(
                    assignment_object=assignment_object,
                    assignee_user=assigner,
                    perms=self.get_permissions_on_assigner_minimum()
                )
                self.check_permissions_equal(
                    self.get_object_level_user_perms(
                        object=assignment_object,
                        user=assigner
                    ),
                    self.get_permissions_on_assigner_minimum()
                )
                remove_perm(permission, assigner)
                assigner_client.force_login(assigner)
