# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2024] © NeuroForge GmbH & Co. KG


import uuid
from typing import List, Optional, Union

from django.db import migrations, connections

from skipper.dataseries.raw_sql import escape
from skipper.dataseries.raw_sql.tenant import escaped_tenant_schema, ensure_schema
from skipper.dataseries.storage.dynamic_sql.materialized import materialized_table_name
from skipper.modules import Module
from skipper.settings import DATA_SERIES_DYNAMIC_SQL_DB

data_point_id_column_def = 'character varying(512) COLLATE pg_catalog."default"'
external_id_column_def = 'character varying(256) COLLATE pg_catalog."default"'


def drop_all_manual_trigger_functions(relation_table: str,
                                      entity_table: str) -> migrations.RunSQL:
    sql = f"""
            -- drop all cascade simulation stuff
            DROP TRIGGER IF EXISTS upd{entity_table}{relation_table} ON {entity_table};
            DROP FUNCTION IF EXISTS upd{entity_table}{relation_table}();

            -- drop all soft-delete stuff if exists
            DROP TRIGGER IF EXISTS sdel{entity_table}{relation_table} ON {entity_table};
            DROP FUNCTION IF EXISTS sdel{entity_table}{relation_table}();

            -- drop all auto delete stuff if exists
            DROP TRIGGER IF EXISTS del{entity_table}{relation_table} ON {entity_table};
            DROP FUNCTION IF EXISTS del{entity_table}{relation_table}();
            """
    return migrations.RunSQL(sql)


def fix_unique_constraint_for_soft_delete(table: str, columns: List[str],
                                          constraint_name_override: Optional[str] = None) -> migrations.RunSQL:
    # needs to be '{table}_{column}_key' as django generates this
    # for UniqueFKeys, which we want the behaviour of, but we want to overwrite
    # the unique constraint to work with deleted
    _column_snake = '_'.join(columns)
    constraint_name = f'{table}_{_column_snake}_key'
    if constraint_name_override is not None:
        constraint_name = constraint_name_override
    soft_del_index_name = f'{table}_{_column_snake}_sdidx'
    assert len(constraint_name) <= 61
    sql = f"""
        -- drop django generated constraint
        ALTER TABLE {table}
        DROP CONSTRAINT IF EXISTS {constraint_name};

        -- drop generated soft deletion index name
        DROP INDEX IF EXISTS {soft_del_index_name};

        -- drop indexes if they already exist
        DROP INDEX IF EXISTS {constraint_name}_0;
        DROP INDEX IF EXISTS {constraint_name}_1;

        -- create unique constraint if deleted_at is null
        CREATE UNIQUE INDEX {constraint_name}_0 ON {table} ({','.join(columns)})
        WHERE (deleted_at IS NULL);
        -- create unique constraint, also generates a UNIQUE index
        CREATE UNIQUE INDEX {constraint_name}_1 ON {table} ({','.join(columns)}, deleted_at)
        WHERE (deleted_at IS NOT NULL);
    """
    return migrations.RunSQL(sql)


def remove_unique_constraint_for_soft_delete(table: str, columns: List[str],
                                             constraint_name_override: Optional[str] = None) -> migrations.RunSQL:
    # needs to be '{table}_{column}_key' as django generates this
    # for UniqueFKeys, which we want the behaviour of, but we want to overwrite
    # the unique constraint to work with deleted_at
    _column_snake = '_'.join(columns)
    constraint_name = f'{table}_{_column_snake}_key'
    if constraint_name_override is not None:
        constraint_name = constraint_name_override
    soft_del_index_name = f'{table}_{_column_snake}_sdidx'
    assert len(constraint_name) <= 61
    sql = f"""
        -- drop indexes if they already exist
        DROP INDEX IF EXISTS {constraint_name}_0;
        DROP INDEX IF EXISTS {constraint_name}_1;
    """
    return migrations.RunSQL(sql)


def add_simple_foreign_key_constraint_with_soft_delete(source_table: str,
                                                       source_column: str,
                                                       target_table: str,
                                                       target_column: str,
                                                       idx_name: Optional[str] = None,
                                                       sdidx_name: Optional[str] = None,
                                                       sdel_name: Optional[str] = None,
                                                       fkey_name: Optional[str] = None) -> migrations.RunSQL:
    if fkey_name is None:
        fkey_name = f'{source_table}_fkey'
    assert len(fkey_name) <= 63
    # we do an underscore between the tables here so that we have a similar naming scheme to
    # what django generates
    if idx_name is None:
        idx_name = f'{target_table}_{target_column}_idx'
    if sdidx_name is None:
        sdidx_name = f'{target_table}_{target_column}_sdidx'
    if sdel_name is None:
        sdel_name = f'sdel{source_table}{target_table}'
    assert len(idx_name) <= 63
    assert len(sdidx_name) <= 63
    assert len(sdel_name) <= 63
    assert len(f'{sdel_name}()') <= 63
    sql = f"""
            ALTER TABLE {target_table}
            DROP CONSTRAINT IF EXISTS {fkey_name};

            ALTER TABLE {target_table}
            ADD CONSTRAINT {fkey_name}
            FOREIGN KEY ({target_column}) REFERENCES {source_table} ({source_column}) ON DELETE CASCADE ON UPDATE CASCADE;

            -- manually generate index as we instructed django not to do so
            DROP INDEX IF EXISTS {idx_name};
            CREATE INDEX {idx_name}
            ON {target_table} ({target_column});

            -- manually generate index for the same id but with deleted_at
            DROP INDEX IF EXISTS {sdidx_name};
            CREATE INDEX {sdidx_name}
            ON {target_table} ({target_column}, deleted_at);

            -- delete all soft-delete stuff
            DROP TRIGGER IF EXISTS {sdel_name} ON {source_table};
            DROP FUNCTION IF EXISTS {sdel_name}();

            -- auto soft-delete on relation table function
            CREATE FUNCTION {sdel_name}()
            RETURNS trigger AS
            $BODY$
            BEGIN
                IF new.deleted_at IS NOT NULL THEN
                    UPDATE {target_table}
                    SET deleted_at = new.deleted_at
                    WHERE {target_table}.{target_column} = old.{source_column}
                    AND deleted_at IS NULL;
                END IF;
                RETURN NULL;
            END;
            $BODY$
            LANGUAGE plpgsql VOLATILE;

            -- auto soft-delete on relation table trigger
            CREATE TRIGGER {sdel_name}
            AFTER UPDATE
            ON {source_table}
            FOR EACH ROW
            EXECUTE PROCEDURE {sdel_name}();
            """
    return migrations.RunSQL(sql)


def add_simple_foreign_key_constraint(source_table: str,
                                      source_column: str,
                                      target_table: str,
                                      target_column: str,
                                      idx_name: Optional[str] = None,
                                      sdidx_name: Optional[str] = None,
                                      fkey_name: Optional[str] = None) -> migrations.RunSQL:
    if fkey_name is None:
        fkey_name = f'{source_table}_fkey'
    assert len(fkey_name) <= 63
    # we do an underscore between the tables here so that we have a similar naming scheme to
    # what django generates
    if idx_name is None:
        idx_name = f'{target_table}_{target_column}_idx'
    if sdidx_name is None:
        sdidx_name = f'{target_table}_{target_column}_sdidx'
    assert len(idx_name) <= 63
    assert len(sdidx_name) <= 63
    sql = f"""
            ALTER TABLE {target_table}
            DROP CONSTRAINT IF EXISTS {fkey_name};

            ALTER TABLE {target_table}
            ADD CONSTRAINT {fkey_name}
            FOREIGN KEY ({target_column}) REFERENCES {source_table} ({source_column}) ON DELETE CASCADE ON UPDATE CASCADE;

            -- manually generate index as we instructed django not to do so
            DROP INDEX IF EXISTS {idx_name};
            CREATE INDEX {idx_name}
            ON {target_table} ({target_column});

            -- manually generate index for the same id but with deleted_at
            DROP INDEX IF EXISTS {sdidx_name};
            CREATE INDEX {sdidx_name}
            ON {target_table} ({target_column}, deleted_at);
            """
    return migrations.RunSQL(sql)


def declare_ownership_cascade_delete(
        relation_table: str,
        child_foreign_key: str,
        child_table: str,
        child_primary_key: str
) -> migrations.RunSQL:
    return migrations.RunSQL(f"""
    -- drop all auto delete stuff if exists
        DROP TRIGGER IF EXISTS del{relation_table} ON {relation_table};
        DROP FUNCTION IF EXISTS del{relation_table}();

        -- auto delete children function
        CREATE FUNCTION del{relation_table}()
        RETURNS trigger AS
        $BODY$
        BEGIN
            DELETE FROM {child_table}
            WHERE {child_table}.{child_primary_key} = old.{child_foreign_key};
            RETURN NULL;
        END;
        $BODY$
        LANGUAGE plpgsql VOLATILE;

        -- auto delete children trigger
        CREATE TRIGGER del{relation_table}
        AFTER DELETE
        ON {relation_table}
        FOR EACH ROW
        EXECUTE PROCEDURE del{relation_table}();
    """)


def declare_ownership_with_all_cascade(
        relation_table: str,
        parent_foreign_key: str,
        child_foreign_key: str,
        parent_table: str,
        parent_primary_key: str,
        child_table: str,
        child_primary_key: str) -> migrations.RunSQL:
    assert len(f'{relation_table}') <= 63
    assert len(f'{parent_table}_fkey') <= 63
    assert len(f'upd{parent_table}{relation_table}()') <= 63
    assert len(f'sdel{parent_table}{relation_table}()') <= 63
    assert len(f'del{parent_table}{relation_table}()') <= 63
    # we do an underscore between the tables here so that we have a similar naming scheme to
    # what django generates
    assert len(f'{relation_table}_{parent_foreign_key}_idx') <= 63
    assert len(f'{relation_table}_{parent_foreign_key}_sdidx') <= 63
    # Note: django already creates an index on the foreign key,
    # so we are fine if we do not declare a foreign key here
    #
    # We delete a possibly existing foreign key constraint, we have to
    # enforce the cascading behaviour in triggers by hand since we want
    # to have the parent-child relationship to also propagate deletes.
    # This is because we require the relation table in the trigger to delete.
    sql = f"""
        ALTER TABLE {relation_table} DROP CONSTRAINT IF EXISTS {parent_table}_fkey;

        -- manually generate index as we instructed django not to do so
        DROP INDEX IF EXISTS {relation_table}_{parent_foreign_key}_idx;
        CREATE INDEX {relation_table}_{parent_foreign_key}_idx
        ON {relation_table} ({parent_foreign_key});

        -- manually generate index for the same id but with deleted_at
        DROP INDEX IF EXISTS {relation_table}_{parent_foreign_key}_sdidx;
        CREATE INDEX {relation_table}_{parent_foreign_key}_sdidx
        ON {relation_table} ({parent_foreign_key}, deleted_at);

        -- drop all cascade simulation stuff
        DROP TRIGGER IF EXISTS upd{parent_table}{relation_table} ON {parent_table};
        DROP FUNCTION IF EXISTS upd{parent_table}{relation_table}();

        -- simulate cascade update function
        CREATE FUNCTION upd{parent_table}{relation_table}()
        RETURNS trigger AS
        $BODY$
        BEGIN
            UPDATE {relation_table}
            SET {parent_foreign_key} = new.{parent_primary_key}
            WHERE {parent_foreign_key} = old.{parent_primary_key};
            RETURN NULL;
        END;
        $BODY$
        LANGUAGE plpgsql VOLATILE;

        -- simulate cascade update trigger
        CREATE TRIGGER upd{parent_table}{relation_table}
        AFTER UPDATE
        ON {parent_table}
        FOR EACH ROW
        EXECUTE PROCEDURE upd{parent_table}{relation_table}();

        -- drop all soft-delete stuff if exists
        DROP TRIGGER IF EXISTS sdel{parent_table}{relation_table} ON {parent_table};
        DROP FUNCTION IF EXISTS sdel{parent_table}{relation_table}();

        -- auto soft-delete children function
        CREATE FUNCTION sdel{parent_table}{relation_table}()
        RETURNS trigger AS
        $BODY$
        BEGIN
            IF new.deleted_at IS NOT NULL THEN
                UPDATE {child_table}
                SET deleted_at = new.deleted_at
                WHERE {child_table}.{child_primary_key}
                    IN (SELECT {relation_table}.{child_foreign_key}
                        FROM {relation_table}
                        WHERE {relation_table}.{parent_foreign_key} = old.{parent_primary_key}
                    );
                UPDATE {relation_table}
                SET deleted_at = new.deleted_at
                AND deleted_at IS NULL
                WHERE {relation_table}.{parent_foreign_key} = old.{parent_primary_key};
            END IF;
            RETURN NULL;
        END;
        $BODY$
        LANGUAGE plpgsql VOLATILE;

        -- auto soft-delete children trigger
        CREATE TRIGGER sdel{parent_table}{relation_table}
        AFTER UPDATE
        ON {parent_table}
        FOR EACH ROW
        EXECUTE PROCEDURE sdel{parent_table}{relation_table}();

        -- drop all auto delete stuff if exists
        DROP TRIGGER IF EXISTS del{parent_table}{relation_table} ON {parent_table};
        DROP FUNCTION IF EXISTS del{parent_table}{relation_table}();

        -- auto delete children function
        CREATE FUNCTION del{parent_table}{relation_table}()
        RETURNS trigger AS
        $BODY$
        BEGIN
            DELETE FROM {child_table}
            WHERE {child_table}.{child_primary_key}
                IN (SELECT {relation_table}.{child_foreign_key}
                    FROM {relation_table}
                    WHERE {relation_table}.{parent_foreign_key} = old.{parent_primary_key}
                );
            DELETE FROM {relation_table}
            WHERE {relation_table}.{parent_foreign_key} = old.{parent_primary_key};
            RETURN NULL;
        END;
        $BODY$
        LANGUAGE plpgsql VOLATILE;

        -- auto delete children trigger
        CREATE TRIGGER del{parent_table}{relation_table}
        AFTER DELETE
        ON {parent_table}
        FOR EACH ROW
        EXECUTE PROCEDURE del{parent_table}{relation_table}();
        """
    return migrations.RunSQL(sql)


def migrations_for_dataseries_child(child_name: str, child_foreign_key: str) -> List[migrations.operations.base.Operation]:
    return [
        add_simple_foreign_key_constraint_with_soft_delete(
            source_table=f'_{str(Module.DATA_SERIES.value)}_data_series',
            source_column='id',
            target_table=f'_{str(Module.DATA_SERIES.value)}_data_series_{child_name}',
            target_column='data_series_id'
        ),
        declare_ownership_cascade_delete(
            relation_table=f'_{str(Module.DATA_SERIES.value)}_data_series_{child_name}',
            child_foreign_key=child_foreign_key,
            child_table=f'_{str(Module.DATA_SERIES.value)}_{child_name}',
            child_primary_key='id'
        ),
        add_simple_foreign_key_constraint_with_soft_delete(
            source_table=f'_{str(Module.DATA_SERIES.value)}_{child_name}',
            source_column='id',
            target_table=f'_{str(Module.DATA_SERIES.value)}_data_series_{child_name}',
            target_column=child_foreign_key
        ),
        fix_unique_constraint_for_soft_delete(
            table=f'_{str(Module.DATA_SERIES.value)}_data_series_{child_name}',
            columns=[child_foreign_key]
        ),
    ]

def ensure_indexes_materialized_old(
        data_series_id: Union[str, uuid.UUID],
        data_series_external_id: str,
        tenant_name: str
) -> None:
    schema_name = escaped_tenant_schema(tenant_name)
    ensure_schema(schema_name, connection_name=DATA_SERIES_DYNAMIC_SQL_DB)
    table_name_unescaped = materialized_table_name(data_series_id, data_series_external_id)
    table_name = escape.escape(table_name_unescaped)
    with connections[DATA_SERIES_DYNAMIC_SQL_DB].cursor() as cursor:
        queries = [
            f"""
            DROP INDEX IF EXISTS {escape.escape(f'_mat_inserted_at_{str(data_series_id)}_{data_series_external_id}')};
            """,
            # for ordering
            f"""
            CREATE INDEX IF NOT EXISTS {escape.escape(f'_mat_inserted_at_id_alive_{str(data_series_id)}_{data_series_external_id}')}
            ON {schema_name}.{table_name} USING btree (inserted_at ASC NULLS LAST, id ASC NULLS LAST)
            WHERE deleted_at IS NULL;
            """,
            # for changes since
            f"""
            CREATE INDEX IF NOT EXISTS {escape.escape(f'_mat_point_in_time_{str(data_series_id)}_{data_series_external_id}')}
            ON {schema_name}.{table_name} USING btree
            (point_in_time ASC NULLS LAST)
            TABLESPACE pg_default;
            """
        ]

        for query in queries:
            cursor.execute(query)


def ensure_indexes_materialized_v2(
        data_series_id: Union[str, uuid.UUID],
        data_series_external_id: str,
        tenant_name: str
) -> None:
    schema_name = escaped_tenant_schema(tenant_name)
    ensure_schema(schema_name, connection_name=DATA_SERIES_DYNAMIC_SQL_DB)
    table_name_unescaped = materialized_table_name(data_series_id, data_series_external_id)
    table_name = escape.escape(table_name_unescaped)
    with connections[DATA_SERIES_DYNAMIC_SQL_DB].cursor() as cursor:
        queries = [
            f"""
            DROP INDEX IF EXISTS {escape.escape(f'_mat_inserted_at_{str(data_series_id)}_{data_series_external_id}')};
            """,
            f"""
            DROP INDEX IF EXISTS {escape.escape(f'_mat_inserted_at_id_alive_{str(data_series_id)}_{data_series_external_id}')};
            """,
            # for ordering in the rest api we only need an index on all active data
            f"""
            CREATE INDEX IF NOT EXISTS {escape.escape(f'_mat_inserted_at_id_alive_{str(data_series_id)}_{data_series_external_id}')}
            ON {schema_name}.{table_name}
            USING btree (inserted_at ASC NULLS LAST, id ASC NULLS LAST)
            WHERE deleted_at IS NULL;
            """,
#            disabled, we do not support history queries, on the materialized table directly
#            # for ordering in the rest api we only need an index on all dead data
#            f"""
#            CREATE INDEX IF NOT EXISTS {escape.escape(f'_mat_inserted_at_id_dead_{str(data_series_id)}_{data_series_external_id}')}
#            ON {schema_name}.{table_name}
#            USING btree (inserted_at ASC NULLS LAST, id ASC NULLS LAST)
#            WHERE deleted_at IS NOT NULL;
#            """,
            # for changes since
            f"""
            CREATE INDEX IF NOT EXISTS {escape.escape(f'_mat_point_in_time_{str(data_series_id)}_{data_series_external_id}')}
            ON {schema_name}.{table_name} USING btree
            (point_in_time ASC NULLS LAST)
            TABLESPACE pg_default;
            """
        ]

        for query in queries:
            cursor.execute(query)
