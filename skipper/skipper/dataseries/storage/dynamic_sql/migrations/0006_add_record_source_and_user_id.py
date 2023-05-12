# Add database constraints foreign keys as django did not set them up properly

from django.db import migrations
from typing import List, cast

from skipper.dataseries.storage.dynamic_sql.migrations.custom_v1.record_source_user import add_record_source_and_user_id
from skipper.modules import Module

data_point_id_column_def = 'character varying(512) COLLATE pg_catalog."default"'
external_id_column_def = 'character varying(256) COLLATE pg_catalog."default"'


class Migration(migrations.Migration):
    atomic = True

    dependencies = [
        ('skipper_dataseries_storage_dynamic_sql', '0004_drop_default_tenant_schema'),
    ]

    replaces = [
        ('dataseries', '0006_add_record_source_and_user_id'),
        ('skipper.dataseries.storage.dynamic_sql', '0006_add_record_source_and_user_id')
    ]

    operations = (
            cast(List[migrations.operations.base.Operation], [migrations.RunSQL(
                f"""
                ALTER TABLE _3_data_point ADD COLUMN user_id character varying(256) COLLATE pg_catalog."default" NULL;
                ALTER TABLE _3_data_point ADD COLUMN record_source character varying(256) COLLATE pg_catalog."default" NULL;

                -- update view with new columns
                CREATE OR REPLACE VIEW _{str(Module.DATA_SERIES.value)}_view_data_point AS
                SELECT tbl.id,
                    tbl.data_series_id,
                    tbl.external_id,
                    tbl.point_in_time,
                    tbl.deleted,
                    tbl.user_id,
                    tbl.record_source
                FROM _{str(Module.DATA_SERIES.value)}_data_point tbl
                LEFT OUTER JOIN _{str(Module.DATA_SERIES.value)}_data_point tbl2 ON (
                    tbl.data_series_id = tbl2.data_series_id AND
                    tbl.id = tbl2.id AND
                    tbl.point_in_time < tbl2.point_in_time
                )
                WHERE tbl2.id IS NULL
                AND tbl.deleted = false;

                -- inserting into the view
                CREATE OR REPLACE FUNCTION _{str(Module.DATA_SERIES.value)}_insert_data_point()
                RETURNS trigger AS
                $BODY$
                BEGIN
                    INSERT INTO _{str(Module.DATA_SERIES.value)}_data_point(
                        id,
                        data_series_id,
                        external_id,
                        point_in_time,
                        deleted,
                        user_id,
                        record_source
                    ) VALUES (
                        NEW.id,
                        NEW.data_series_id,
                        NEW.external_id,
                        NEW.point_in_time,
                        NEW.deleted,
                        NEW.user_id,
                        NEW.record_source
                    );
                    RETURN NEW;
                END;
                $BODY$
                LANGUAGE plpgsql VOLATILE;


                -- deleting from the view should be the same as inserting a new entry with
                -- deleted = true
                CREATE OR REPLACE FUNCTION _{str(Module.DATA_SERIES.value)}_delete_data_point()
                RETURNS trigger AS
                $BODY$
                BEGIN
                    -- clock_timestamp instead of now to make this work
                    -- in the same transaction (if we dont handle deletes via 
                    -- actual manual inserts)
                    OLD.point_in_time := clock_timestamp();
                    INSERT INTO _{str(Module.DATA_SERIES.value)}_data_point(
                        id,
                        data_series_id,
                        external_id,
                        point_in_time,
                        deleted,
                        user_id,
                        record_source
                    ) VALUES (
                        OLD.id,
                        OLD.data_series_id,
                        OLD.external_id,
                        OLD.point_in_time,
                        true,
                        NULL, -- can not determine user here
                        'deleted by trigger'
                    );
                    RETURN NULL;
                END;
                $BODY$
                LANGUAGE plpgsql VOLATILE;

                -- updating the view
                CREATE OR REPLACE FUNCTION _{str(Module.DATA_SERIES.value)}_update_data_point()
                RETURNS trigger AS
                $BODY$
                BEGIN
                    -- clock_timestamp instead of now to make this work
                    -- in the same transaction (if we dont handle updates via 
                    -- actual manual inserts)
                    NEW.point_in_time := clock_timestamp();
                    INSERT INTO _{str(Module.DATA_SERIES.value)}_data_point(
                        id,
                        data_series_id,
                        external_id,
                        point_in_time,
                        deleted,
                        user_id,
                        record_source
                    ) VALUES (
                        NEW.id,
                        NEW.data_series_id,
                        NEW.external_id,
                        NEW.point_in_time,
                        NEW.deleted,
                        NEW.user_id,
                        NEW.record_source
                    );
                    RETURN NEW;
                END;
                $BODY$
                LANGUAGE plpgsql VOLATILE;
"""
            )

            ]) +

            add_record_source_and_user_id(data_name='dimension',
                                          fact_or_dim_id='dimension_id',
                                          value_name='value') +
            add_record_source_and_user_id(data_name='float_fact') +
            add_record_source_and_user_id(data_name='image_fact') +
            add_record_source_and_user_id(data_name='json_fact') +
            add_record_source_and_user_id(data_name='string_fact') +
            add_record_source_and_user_id(data_name='timestamp_fact') +
            add_record_source_and_user_id(data_name='text_fact') +
            []
    )
