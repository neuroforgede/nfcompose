# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

import unittest
from faker import Faker  # type: ignore

from compose_client.library.models.definition.engine import EngineDefinition, Engine, EngineSecret
from compose_client.library.service.diff import diff_engine_definition, diff_all_engine_definitions
from compose_client.library.models.operation.general import OperationType

fake = Faker()

_secret = fake.password()

class EngineDefinitionDiffTest(unittest.TestCase):

    def gen_all_set(self) -> EngineDefinition:
        return EngineDefinition(
            engine=Engine(
                external_id='',
                upstream='http://nodered.local'
            ),
            secret=EngineSecret(
                secret=_secret
            )
        )

    def test_new_engine_definition(self) -> None:
        base = None
        target = self.gen_all_set()

        diff = diff_engine_definition(base, target)
        self.assertIsNotNone(diff.engine)
        self.assertIsNotNone(diff.secret)

        self.assertEqual(OperationType.CREATE, diff.engine.operation_type)
        self.assertEqual(OperationType.CREATE, diff.secret.operation_type)

        self.assertEqual(target.engine.to_dict(), diff.engine.payload)
        self.assertEqual(target.secret.to_dict(), diff.secret.payload)

    def test_delete_engine_definition_default(self) -> None:
        base = self.gen_all_set()
        target = None

        diff = diff_engine_definition(base, target)
        self.assertIsNone(diff.engine)
        self.assertIsNone(diff.secret)


    def test_delete_engine_definition(self) -> None:
        base = self.gen_all_set()
        target = None

        diff = diff_engine_definition(base, target, delete_in_base=True)
        self.assertIsNotNone(diff.engine)
        self.assertIsNotNone(diff.secret)

        self.assertEqual(OperationType.DELETE, diff.engine.operation_type)
        self.assertEqual(OperationType.DELETE, diff.secret.operation_type)

        self.assertEqual(base.engine.to_dict(), diff.engine.payload)
        self.assertEqual(base.secret.to_dict(), diff.secret.payload)

    def test_update_engine_definition(self) -> None:
        base = self.gen_all_set()
        target = self.gen_all_set()

        target.engine.upstream = 'http://some.other.upstream'
        # has to be the same
        target.secret.secret = base.secret.secret

        diff = diff_engine_definition(base, target)
        self.assertIsNotNone(diff.engine)
        self.assertIsNone(diff.secret)

        self.assertEqual(OperationType.UPDATE, diff.engine.operation_type)

        self.assertEqual(target.engine.to_dict(), diff.engine.payload)

    def test_update_secret_definition(self) -> None:
        base = self.gen_all_set()
        target = self.gen_all_set()

        target.secret.secret = base.secret.secret + '__'

        diff = diff_engine_definition(base, target)
        self.assertIsNone(diff.engine)
        self.assertIsNotNone(diff.secret)

        self.assertEqual(OperationType.UPDATE, diff.secret.operation_type)

        self.assertEqual(target.secret.to_dict(), diff.secret.payload)

    def test_update_whole_definition(self) -> None:
        base = self.gen_all_set()
        target = self.gen_all_set()

        target.engine.upstream = 'http://some.other.upstream'
        target.secret.secret = base.secret.secret + '__'

        diff = diff_engine_definition(base, target)
        self.assertIsNotNone(diff.engine)
        self.assertIsNotNone(diff.secret)

        self.assertEqual(OperationType.UPDATE, diff.engine.operation_type)
        self.assertEqual(OperationType.UPDATE, diff.secret.operation_type)

        self.assertEqual(target.engine.to_dict(), diff.engine.payload)
        self.assertEqual(target.secret.to_dict(), diff.secret.payload)

    def test_list_diff_same(self) -> None:
        base = self.gen_all_set()
        target = self.gen_all_set()

        diffs = list(diff_all_engine_definitions([base], [target]))

        non_empty_diffs = [elem for elem in diffs if not elem.empty()]

        self.assertEqual(1, len(diffs))
        self.assertEqual(0, len(non_empty_diffs))

    def test_list_diff_correct_for_update(self) -> None:
        base = self.gen_all_set()
        target = self.gen_all_set()

        target.engine.upstream = 'http://some.other.upstream'
        target.secret.secret = base.secret.secret + '__'

        diffs = list(diff_all_engine_definitions([base], [target]))

        non_empty_diffs = [elem for elem in diffs if not elem.empty()]

        self.assertEqual(1, len(diffs))
        self.assertEqual(1, len(non_empty_diffs))

        self.assertEqual(OperationType.UPDATE, diffs[0].engine.operation_type)
        self.assertEqual(OperationType.UPDATE, diffs[0].secret.operation_type)

    def test_list_diff_correct_for_create(self) -> None:
        target = self.gen_all_set()

        diffs = list(diff_all_engine_definitions([], [target]))

        non_empty_diffs = [elem for elem in diffs if not elem.empty()]

        self.assertEqual(1, len(diffs))
        self.assertEqual(1, len(non_empty_diffs))

        self.assertEqual(OperationType.CREATE, diffs[0].engine.operation_type)
        self.assertEqual(OperationType.CREATE, diffs[0].secret.operation_type)

    def test_list_diff_correct_for_delete_default(self) -> None:
        base = self.gen_all_set()

        diffs = list(diff_all_engine_definitions([base], []))

        non_empty_diffs = [elem for elem in diffs if not elem.empty()]

        self.assertEqual(1, len(diffs))
        self.assertEqual(0, len(non_empty_diffs))

        self.assertEqual(None, diffs[0].engine)
        self.assertEqual(None, diffs[0].secret)

    def test_list_diff_correct_for_delete(self) -> None:
        base = self.gen_all_set()

        diffs = list(diff_all_engine_definitions([base], [], delete_in_base=True))

        non_empty_diffs = [elem for elem in diffs if not elem.empty()]

        self.assertEqual(1, len(diffs))
        self.assertEqual(1, len(non_empty_diffs))

        self.assertEqual(OperationType.DELETE, diffs[0].engine.operation_type)
        self.assertEqual(OperationType.DELETE, diffs[0].secret.operation_type)



