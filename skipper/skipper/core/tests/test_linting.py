# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from unittest.case import TestCase
from django.test.testcases import TransactionTestCase
from skipper.settings import DATA_SERIES_DYNAMIC_SQL_DB

from skipper.core.lint import lint, LintingException, UnexpectedNameLintingException, sql_cursor

class TestLintingCursor(TransactionTestCase):
    def test_sql_cursor(self) -> None:
        with self.assertRaises(LintingException):
            with sql_cursor(DATA_SERIES_DYNAMIC_SQL_DB) as cursor:
                cursor.execute('SELECT a FROM b')

class TestLinting(TestCase):
    def test_non_escaped(self) -> None:
        with self.assertRaises(LintingException):
            lint('SELECT a FROM b')

    def test_only_column_escaped(self) -> None:
        with self.assertRaises(LintingException):
            lint('SELECT "a" FROM b')

    def test_only_table_escaped(self) -> None:
        with self.assertRaises(LintingException):
            lint('SELECT a FROM "b"')

    def test_only_table_escaped_with_dot(self) -> None:
        with self.assertRaises(UnexpectedNameLintingException):
            lint('SELECT "b".a FROM "b"')

    def test_fully_escaped(self) -> None:
        lint('SELECT "a" FROM "b"')

    def test_fully_table_escaped_with_dot(self) -> None:
        lint('SELECT "b"."a" FROM "b"')