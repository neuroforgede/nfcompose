# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from typing import List, Optional

from django.db import migrations

from skipper.modules import Module


def add_record_source_and_user_id(
        data_name: str,
        fact_or_dim_id: str = 'fact_id',
        value_name: str = 'value'
) -> List[migrations.RunSQL]:
    relevant_table_name = f'data_point_{data_name}'

    def tbl_name(prefix: Optional[str] = None) -> str:
        actual_prefix = ''
        if prefix is not None:
            actual_prefix = f'_{prefix}'
        return f'_{str(Module.DATA_SERIES.value)}{actual_prefix}_{relevant_table_name}'

    table_name = tbl_name()
    view_table_name = tbl_name('view')
    return [
        migrations.RunSQL(
            f"""          
                -- update the table with user id and record source
                ALTER TABLE {table_name} ADD COLUMN user_id character varying(256) COLLATE pg_catalog."default" NULL;
                ALTER TABLE {table_name} ADD COLUMN record_source character varying(256) COLLATE pg_catalog."default" NULL;

                -- update the view with the new columns
                CREATE OR REPLACE VIEW {view_table_name} AS
                SELECT tbl.data_point_id,
                    tbl.{fact_or_dim_id},
                    tbl.point_in_time,
                    tbl.{value_name},
                    tbl.user_id,
                    tbl.record_source
                FROM {table_name} tbl
                LEFT OUTER JOIN {table_name} tbl2 ON (
                    tbl.{fact_or_dim_id} = tbl2.{fact_or_dim_id} AND
                    tbl.data_point_id = tbl2.data_point_id AND
                    tbl.point_in_time < tbl2.point_in_time
                )
                WHERE tbl2.data_point_id IS NULL;
                -- don't check for value here, we do not always have an index on it

                -- update the trigger functions on the view

                CREATE OR REPLACE FUNCTION {table_name}_insert()
                RETURNS trigger AS
                $BODY$
                BEGIN
                    INSERT INTO {table_name}(
                        data_point_id,
                        {fact_or_dim_id},
                        point_in_time,
                        {value_name},
                        user_id,
                        record_source
                    ) VALUES (
                        NEW.data_point_id,
                        NEW.{fact_or_dim_id},
                        NEW.point_in_time,
                        NEW.{value_name},
                        NEW.user_id,
                        NEW.record_source
                    );
                    RETURN NEW;
                END;
                $BODY$
                LANGUAGE plpgsql VOLATILE;

                CREATE OR REPLACE FUNCTION {table_name}_delete()
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
                        {value_name},
                        user_id,
                        record_source
                    ) VALUES (
                        OLD.data_point_id,
                        OLD.{fact_or_dim_id},
                        clock_timestamp(),
                        NULL,
                        NULL, -- we can not determine the user here... :(, should not happen in normal production though
                        'deleted by trigger'
                    );
                    RETURN NULL;
                END;
                $BODY$
                LANGUAGE plpgsql VOLATILE;

                CREATE OR REPLACE FUNCTION {table_name}_update()
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
                        {value_name},
                        user_id,
                        record_source
                    ) VALUES (
                        NEW.data_point_id,
                        NEW.{fact_or_dim_id},
                        NEW.point_in_time,
                        NEW.{value_name},
                        NEW.user_id,
                        NEW.record_source
                    );
                    RETURN NEW;
                END;
                $BODY$
                LANGUAGE plpgsql VOLATILE;
    """
        )
        # no unique constraint here
    ]