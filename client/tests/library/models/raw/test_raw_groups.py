# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import unittest

from faker import Faker  # type: ignore

from compose_client.library.models.raw.group import RawGroup, RawGroupPermissions

fake = Faker()


class RawGroupConversionTest(unittest.TestCase):

    def test_raw_conversion(self) -> None:
        group_name = fake.user_name()
        dict = {
            "url": fake.url(),
            "permissions": fake.url(),
            "name": group_name,
            "fully_qualified": f"{fake.user_name()}@@{group_name}",
            "id": 1
        }
        parsed = RawGroup.from_dict(dict)
        self.assertEqual(parsed.url, dict['url'])
        self.assertEqual(parsed.permissions, dict['permissions'])
        self.assertEqual(parsed.name, dict['name'])
        self.assertEqual(parsed.fully_qualified, dict['fully_qualified'])

    def test_extra_data_raw_conversion(self) -> None:
        group_name = fake.user_name()
        dict = {
            "url": fake.url(),
            "permissions": fake.url(),
            "name": group_name,
            "fully_qualified": f"{fake.user_name()}@@{group_name}",
            "should": "not-be-here"
        }
        with self.assertRaises(Exception) as e:
            RawGroup.from_dict(dict)


class RawGroupPermissionsConversionTest(unittest.TestCase):

    def test_raw_conversion(self) -> None:
        dict = {
            "group_permissions": ['perm_1', 'perm_2']
        }
        parsed = RawGroupPermissions.from_dict(dict)
        self.assertEqual(parsed.group_permissions, dict['group_permissions'])

    def test_extra_data_raw_conversion(self) -> None:
        dict = {
            "group_permissions": ['perm_1', 'perm_2'],
            "should": "not-be-here"
        }
        with self.assertRaises(Exception) as e:
            RawGroupPermissions.from_dict(dict)
