# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import unittest
from dataclasses import dataclass
from typing import Any

from dataclasses_json import dataclass_json

from compose_client.library.models.identifiable import Identifiable
from compose_client.library.service.diff import list_diff_dataseries_child
from compose_client.library.models.operation.general import OperationType


@dataclass_json
@dataclass
class DiffObj(Identifiable):
    external_id: str
    payload: str

    def to_dict(self) -> Any: ...


class DiffTest(unittest.TestCase):
    """
    tests the various diff methods that are used by other higher level diff methods
    """

    def test_add_new(self) -> None:
        base = [DiffObj(external_id='1', payload='1')]
        target = [DiffObj(external_id='1', payload='1'), DiffObj(external_id='2', payload='2')]

        diff = list_diff_dataseries_child(base, target)

        self.assertEqual(1, len(diff))
        self.assertEqual('2', diff[0].external_id)
        self.assertEqual(OperationType.CREATE, diff[0].operation_type)
        self.assertEqual(target[1].to_dict(), diff[0].payload)

    def test_delete(self) -> None:
        base = [DiffObj(external_id='1', payload='1'), DiffObj(external_id='2', payload='2')]
        target = [DiffObj(external_id='1', payload='1')]

        diff = list_diff_dataseries_child(base, target)

        self.assertEqual(1, len(diff))
        self.assertEqual('2', diff[0].external_id)
        self.assertEqual(OperationType.DELETE, diff[0].operation_type)
        self.assertEqual(base[1].to_dict(), diff[0].payload)

    def test_update(self) -> None:
        base = [DiffObj(external_id='1', payload='1'), DiffObj(external_id='2', payload='2')]
        target = [DiffObj(external_id='1', payload='1'), DiffObj(external_id='2', payload='not2')]

        diff = list_diff_dataseries_child(base, target)

        self.assertEqual(1, len(diff))
        self.assertEqual('2', diff[0].external_id)
        self.assertEqual(OperationType.UPDATE, diff[0].operation_type)
        self.assertEqual(target[1].to_dict(), diff[0].payload)