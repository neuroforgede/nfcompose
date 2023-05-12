# Add database constraints foreign keys as django did not set them up properly
import operator
from functools import reduce
from typing import List, Optional

from django.db import migrations

from skipper.modules import Module


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
                    WHERE {target_table}.{target_column} = old.{source_column};
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
        # declare_ownership_with_all_cascade(
        #     relation_table=f'_{str(Module.DATA_SERIES.value)}_data_series_{child_name}',
        #     parent_foreign_key='data_series_id',
        #     child_foreign_key=child_foreign_key,
        #     parent_table=f'_{str(Module.DATA_SERIES.value)}_data_series',
        #     parent_primary_key='id',
        #     child_table=f'_{str(Module.DATA_SERIES.value)}_{child_name}',
        #     child_primary_key='id'
        # ),
        add_simple_foreign_key_constraint(
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
        add_simple_foreign_key_constraint(
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


def migrations_for_datapoint_data_tables(data_name: str, data_foreign_key: str, fact_or_dim_id: str = 'fact_id', value_name: str = 'value') -> List[migrations.RunSQL]:
    relevant_table_name = f'data_point_{data_name}'

    def tbl_name(prefix: Optional[str] = None) -> str:
        actual_prefix = ''
        if prefix is not None:
            actual_prefix = f'_{prefix}'
        return f'_{str(Module.DATA_SERIES.value)}{actual_prefix}_{relevant_table_name}'

    table_name = tbl_name()
    view_table_name = tbl_name('view')
    return [
        # even if we _SOFT_ delete structural data or the datapoint itself, we do not want to delete the data entries
        # remove auto generated key information django generated
        # we do not want it. it would only possibly generate collisions and slow down our import
        # and also, if we do not have the foreign keys on the data point,
        # we can import data in parallel properly as we do not have to wait for the data
        # point itself to be generated before we can create the actual attributes
        # this is however something that we do not support yet, but we should
        # be considering from the start
        # but generate index on it so that django does not break down in performance
        migrations.RunSQL(
            f"""
            ALTER TABLE {table_name}
            DROP CONSTRAINT _{str(Module.DATA_SERIES.value)}_data_point_{data_name}_pkey;

            CREATE INDEX {table_name}_data_point_fkey ON {table_name}(data_point_id);
            CREATE INDEX {table_name}_{data_name}_fkey ON {table_name}({data_foreign_key});

            -- FIXME: use PIT table to query this
            CREATE VIEW {view_table_name} AS
            SELECT tbl.data_point_id,
                tbl.{fact_or_dim_id},
                tbl.point_in_time,
                tbl.{value_name}
            FROM {table_name} tbl
            LEFT OUTER JOIN {table_name} tbl2 ON (tbl.data_point_id = tbl2.data_point_id AND
                tbl.point_in_time < tbl2.point_in_time)
            WHERE tbl2.data_point_id IS NULL
            AND tbl.{value_name} IS NOT NULL;

            -- inserting into the view
            CREATE FUNCTION {table_name}_insert()
            RETURNS trigger AS
            $BODY$
            BEGIN
                INSERT INTO {table_name}(
                    data_point_id,
                    {fact_or_dim_id},
                    point_in_time,
                    {value_name}
                ) VALUES (
                    NEW.data_point_id,
                    NEW.{fact_or_dim_id},
                    NEW.point_in_time,
                    NEW.{value_name}
                );
                RETURN NEW;
            END;
            $BODY$
            LANGUAGE plpgsql VOLATILE;

            CREATE TRIGGER {table_name}_insert
            INSTEAD OF INSERT ON {view_table_name}
            FOR EACH ROW EXECUTE PROCEDURE {table_name}_insert();

            -- deleting from the view is inserting a new entry with a null value
            -- into the actual table

            CREATE FUNCTION {table_name}_delete()
            RETURNS trigger AS
            $BODY$
            BEGIN
                -- clock_timestamp instead of now to make this work
                -- in the same transaction (if we dont handle deletes via 
                -- actual manual inserts)
                INSERT INTO {table_name}(
                    data_point_id,
                    {fact_or_dim_id},
                    point_in_time,
                    {value_name}
                ) VALUES (
                    OLD.data_point_id,
                    OLD.{fact_or_dim_id},
                    clock_timestamp(),
                    NULL
                );
                RETURN NULL;
            END;
            $BODY$
            LANGUAGE plpgsql VOLATILE;
            
            CREATE TRIGGER {table_name}_delete
            INSTEAD OF DELETE ON {view_table_name}
            FOR EACH ROW EXECUTE PROCEDURE {table_name}_delete();

            -- updating the view

            CREATE FUNCTION {table_name}_update()
            RETURNS trigger AS
            $BODY$
            BEGIN
                -- clock_timestamp instead of now to make this work
                -- in the same transaction (if we dont handle updates via 
                -- actual manual inserts)
                NEW.point_in_time := clock_timestamp();
                INSERT INTO {table_name}(
                    data_point_id,
                    {fact_or_dim_id},
                    point_in_time,
                    {value_name}
                ) VALUES (
                    NEW.data_point_id,
                    NEW.{fact_or_dim_id},
                    NEW.point_in_time,
                    NEW.{value_name}
                );
                RETURN NEW;
            END;
            $BODY$
            LANGUAGE plpgsql VOLATILE;
            
            CREATE TRIGGER {table_name}_update
            INSTEAD OF UPDATE ON {view_table_name}
            FOR EACH ROW EXECUTE PROCEDURE {table_name}_update();  
"""
        )
        # no unique constraint here
    ]


class Migration(migrations.Migration):
    atomic = True

    dependencies = [
        ('skipper_dataseries_storage_dynamic_sql', '0003_create_default_tenant_schema'),
    ]

    replaces = [
        ('dataseries', '0004_drop_default_tenant_schema'),
        ('skipper.dataseries.storage.dynamic_sql', '0004_drop_default_tenant_schema')
    ]

    operations = (
            [migrations.RunSQL("""
            DROP SCHEMA "_3_tenant_default";
            """)]
    )
