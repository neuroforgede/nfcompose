# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import unittest

from faker import Faker  # type: ignore

from compose_client.library.models.definition.group import Group, GroupPermissions
from compose_client.library.models.raw.group import RawGroup, RawGroupPermissions

fake = Faker()


class GroupConversionTest(unittest.TestCase):

    def test_conversion(self) -> None:
        group_name = fake.user_name()
        raw = RawGroup(
            url=fake.url(),
            permissions=fake.url(),
            name=group_name,
            fully_qualified=f"{fake.user_name()}@@{group_name}",
            id=1
        )
        converted = Group.from_raw(raw)
        self.assertEqual(converted.name, raw.name)


class GroupPermissionsConversionTest(unittest.TestCase):

    def test_conversion(self) -> None:
        raw = RawGroupPermissions(
            group_permissions=['perm_1', 'perm_2']
        )
        converted = GroupPermissions.from_raw(raw)
        self.assertEqual(converted.group_permissions, raw.group_permissions)
