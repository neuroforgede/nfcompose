# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from functools import lru_cache
from django.db import connections
from typing import Any, Generator
from django.conf import settings

import sqlparse  # type: ignore
from sqlparse import tokens as T  # type: ignore
from sqlparse.sql import Token, Identifier, TokenList  # type: ignore

class LintingException(Exception):
    pass

class BadTokenLintingException(LintingException):
    pass

class UnexpectedNameLintingException(BadTokenLintingException):
    pass


def find_all_groups(token: Token) -> Generator[TokenList, None, None]:
    if isinstance(token, TokenList):
        for child in token.get_sublists():
            for elem in find_all_groups(child):
                yield elem
        yield token

NAME_WHITELIST = {
    # functions
    'jsonb_build_object',
    'jsonb_agg',
    'jsonb_strip_nulls',
    'to_char',
    'clock_timestamp',
    'count',

    # identifiers in queries and inserts
    'dp',
    'ds_dp',
    'ds_dp2',
    'id',
    'payload',
    'point_in_time',
    'external_id',
    'deleted_at',
    'inserted_at',
    'tenant_id',
    'data_series_id',
    'pagination_data',
    'value',
    'sub_clock',
    'deleted',
    'data_point_id',
    'data_point_versions',
    'fact_id',
    'dimension_id',
    'user_id',
    'record_source',
    'versions',

    # required at least in inserts
    'target_tbl',
    'rows',

    # in deletes/pruning
    'to_delete',
    'tbl',
    'tbl2',
    'historical_data',
    'data',

    # PostgreSQL stuff
    'varying',
    'pg_catalog',
    'pg_default',
    'btree',
    'nextval',
    'EXCLUDED',
    'INFORMATION_SCHEMA',
    'views',
    'table_catalog',
    'current_database',
    'table_schema',
    'ANY',

    # SQL types
    'varchar',
    'timestamptz',

    # technical stuff
    'citus',
    'multi_shard_modify_mode'
}

def lint_identifier(identifier: Identifier) -> None:
    for token in identifier.tokens:
        if token.ttype in [T.Name]:
            if str(token) not in NAME_WHITELIST:
                print(f'SQLLinterError: unexpected Name \'{str(token)}\'')
                raise UnexpectedNameLintingException(f'unexpected Name \'{str(token)}\'')
        elif token.ttype not in [None, T.Name.Builtin, T.Name.Placeholder, T.Keyword.Order, T.Keyword.TZCast, T.Punctuation, T.Keyword, T.Literal.String.Symbol, T.Literal.String.Single, T.Text.Whitespace]:
            print(f'SQLLinterError: unexpected token \'{str(token)}\' in identifier of type {str(token.ttype)}')
            raise BadTokenLintingException(f'unexpected token \'{str(token)}\' in identifier of type {str(token.ttype)}')

def lint_identifiers(tokens: Token) -> None:
    for token in find_all_groups(tokens):
        if isinstance(token, Identifier):
            lint_identifier(token)

def lint_split(sql: str) -> None:
    statements = sqlparse.split(sql)
    if len(statements) > 1:
        raise LintingException('more than one statement found in sql')

@lru_cache
def lint(sql: str) -> None:
    if getattr(settings, 'SQL_LINT', None) == 'strict':
        parsed = sqlparse.parse(sql)
        for statement in parsed:
            lint_identifiers(statement)

def monkey_patch_cursor(cursor: Any) -> None:
    _execute = cursor.execute
    def patched_execute(query: str, vars: Any = None) -> None:
        lint(query)
        _execute(query, vars)
    cursor.execute = patched_execute


def sql_cursor(connection_name: str) -> Any:
    cursor = connections[connection_name].cursor()
    if getattr(settings, 'SQL_LINT', None) == 'strict':
        monkey_patch_cursor(cursor)
    return cursor