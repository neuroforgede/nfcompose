# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG

import unittest
from faker import Faker  # type: ignore

from compose_client.library.models.definition.group import GroupDefinition, Group, GroupPermissions
from compose_client.library.models.operation.general import OperationType
from compose_client.library.service.diff import diff_group_definition, diff_all_group_definitions

fake = Faker()

_secret = fake.password()


class GroupDefinitionDiffTest(unittest.TestCase):

    def gen_all_set(self) -> GroupDefinition:
        return GroupDefinition(
            group=Group(
                name=fake.user_name()
            ),
            group_permissions=GroupPermissions(
                group_permissions=['perm_1', 'perm_2']
            )
        )

    def test_new_group_definition(self) -> None:
        base = None
        target = self.gen_all_set()

        diff = diff_group_definition(base, target)
        self.assertIsNotNone(diff.group)
        self.assertIsNotNone(diff.group_permissions)

        self.assertEqual(OperationType.CREATE, diff.group.operation_type)
        self.assertEqual(OperationType.CREATE, diff.group_permissions.operation_type)

        self.assertEqual(target.group.to_dict(), diff.group.payload)
        self.assertEqual(target.group_permissions.to_dict(), diff.group_permissions.payload)

    def test_delete_group_definition_default(self) -> None:
        base = self.gen_all_set()
        target = None

        diff = diff_group_definition(base, target)
        self.assertIsNone(diff.group)
        self.assertIsNone(diff.group_permissions)

    def test_delete_group_definition(self) -> None:
        base = self.gen_all_set()
        target = None

        diff = diff_group_definition(base, target, delete_in_base=True)
        self.assertIsNotNone(diff.group)
        self.assertIsNotNone(diff.group_permissions)

        self.assertEqual(OperationType.DELETE, diff.group.operation_type)
        self.assertEqual(OperationType.DELETE, diff.group_permissions.operation_type)

        self.assertEqual(base.group.to_dict(), diff.group.payload)
        self.assertEqual(base.group_permissions.to_dict(), diff.group_permissions.payload)

    def test_update_group_definition(self) -> None:
        base = self.gen_all_set()
        target = self.gen_all_set()

        # identifier must be same
        target.group.name = base.group.name
        # has to be the same
        target.group_permissions.group_permissions = base.group_permissions.group_permissions

        diff = diff_group_definition(base, target)
        # no real diff possible since group has no other values
        self.assertIsNone(diff.group)
        self.assertIsNone(diff.group_permissions)

    def test_update_secret_definition(self) -> None:
        base = self.gen_all_set()
        target = self.gen_all_set()

        # identifier must be same
        target.group.name = base.group.name
        target.group_permissions.group_permissions = []

        diff = diff_group_definition(base, target)
        self.assertIsNone(diff.group)
        self.assertIsNotNone(diff.group_permissions)

        self.assertEqual(OperationType.UPDATE, diff.group_permissions.operation_type)

        self.assertEqual(target.group_permissions.to_dict(), diff.group_permissions.payload)

    def test_update_whole_definition(self) -> None:
        base = self.gen_all_set()
        target = self.gen_all_set()

        # identifier must be same
        target.group.name = base.group.name
        target.group_permissions.group_permissions = []

        diff = diff_group_definition(base, target)
        # no real diff possible since group has no other values
        self.assertIsNone(diff.group)
        self.assertIsNotNone(diff.group_permissions)

        self.assertEqual(OperationType.UPDATE, diff.group_permissions.operation_type)

        self.assertEqual(target.group_permissions.to_dict(), diff.group_permissions.payload)

    def test_list_diff_same(self) -> None:
        base = self.gen_all_set()
        target = self.gen_all_set()

        # identifier, must be same
        target.group.name = base.group.name

        diffs = list(diff_all_group_definitions([base], [target]))

        non_empty_diffs = [elem for elem in diffs if not elem.empty()]

        self.assertEqual(1, len(diffs))
        self.assertEqual(0, len(non_empty_diffs))

    def test_list_diff_correct_for_update(self) -> None:
        base = self.gen_all_set()
        target = self.gen_all_set()

        # group name is identifier, so must be the same
        target.group.name = base.group.name
        target.group_permissions.group_permissions = []

        diffs = list(diff_all_group_definitions([base], [target]))

        non_empty_diffs = [elem for elem in diffs if not elem.empty()]

        self.assertEqual(1, len(diffs))
        self.assertEqual(1, len(non_empty_diffs))

        self.assertIsNone(diffs[0].group)
        self.assertEqual(OperationType.UPDATE, diffs[0].group_permissions.operation_type)

    def test_list_diff_correct_for_create(self) -> None:
        target = self.gen_all_set()

        diffs = list(diff_all_group_definitions([], [target]))

        non_empty_diffs = [elem for elem in diffs if not elem.empty()]

        self.assertEqual(1, len(diffs))
        self.assertEqual(1, len(non_empty_diffs))

        self.assertEqual(OperationType.CREATE, diffs[0].group.operation_type)
        self.assertEqual(OperationType.CREATE, diffs[0].group_permissions.operation_type)

    def test_list_diff_correct_for_delete_default(self) -> None:
        base = self.gen_all_set()

        diffs = list(diff_all_group_definitions([base], []))

        non_empty_diffs = [elem for elem in diffs if not elem.empty()]

        self.assertEqual(1, len(diffs))
        self.assertEqual(0, len(non_empty_diffs))

        self.assertEqual(None, diffs[0].group)
        self.assertEqual(None, diffs[0].group_permissions)

    def test_list_diff_correct_for_delete(self) -> None:
        base = self.gen_all_set()

        diffs = list(diff_all_group_definitions([base], [], delete_in_base=True))

        non_empty_diffs = [elem for elem in diffs if not elem.empty()]

        self.assertEqual(1, len(diffs))
        self.assertEqual(1, len(non_empty_diffs))

        self.assertEqual(OperationType.DELETE, diffs[0].group.operation_type)
        self.assertEqual(OperationType.DELETE, diffs[0].group_permissions.operation_type)



