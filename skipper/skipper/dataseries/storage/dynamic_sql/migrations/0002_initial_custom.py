# Add database constraints foreign keys as django did not set them up properly

from django.db import migrations
from typing import List, cast

from skipper.dataseries.storage.dynamic_sql.migrations.custom_v1.helpers import data_point_id_column_def, \
    external_id_column_def, migrations_for_dataseries_child, migrations_for_datapoint_data_tables
from skipper.modules import Module


class Migration(migrations.Migration):
    atomic = True

    dependencies = [
        ('dataseries', '0001_initial'),
    ]

    replaces = [
        ('dataseries', '0002_initial_custom'),
        ('skipper.dataseries.storage.dynamic_sql', '0002_initial_custom')
    ]

    operations: List[migrations.operations.base.Operation] = (
            cast(List[migrations.operations.base.Operation], [migrations.RunSQL(
                f"""
                CREATE TABLE _3_data_point
                (
                    data_series_id uuid NOT NULL,
                    id {data_point_id_column_def} NOT NULL,
                    external_id {external_id_column_def} NOT NULL,
                    point_in_time timestamp with time zone NOT NULL,
                    deleted boolean NOT NULL
                ) PARTITION BY LIST(data_series_id);
                
                -- index on external id
                CREATE INDEX _3_data_point_external_id
                    ON _3_data_point USING btree
                    (data_series_id, external_id COLLATE pg_catalog."default");
                
                CREATE UNIQUE INDEX _3_data_point_pkey
                    ON _3_data_point USING btree
                    (data_series_id, id COLLATE pg_catalog."default", point_in_time);

                CREATE INDEX _3_data_point_pkey_insert_date
                    ON _3_data_point USING btree
                    (data_series_id, point_in_time, id COLLATE pg_catalog."default");

                -- FIXME: use PIT table to query this
                CREATE VIEW _{str(Module.DATA_SERIES.value)}_view_data_point AS
                SELECT tbl.id,
                    tbl.data_series_id,
                    tbl.external_id,
                    tbl.point_in_time,
                    tbl.deleted
                FROM _{str(Module.DATA_SERIES.value)}_data_point tbl
                LEFT OUTER JOIN _{str(Module.DATA_SERIES.value)}_data_point tbl2 ON (
                    tbl.data_series_id = tbl2.data_series_id AND
                    tbl.id = tbl2.id AND
                    tbl.point_in_time < tbl2.point_in_time
                )
                WHERE tbl2.id IS NULL
                AND tbl.deleted = false;

                -- inserting into the view
                CREATE FUNCTION _{str(Module.DATA_SERIES.value)}_insert_data_point()
                RETURNS trigger AS
                $BODY$
                BEGIN
                    INSERT INTO _{str(Module.DATA_SERIES.value)}_data_point(
                        id,
                        data_series_id,
                        external_id,
                        point_in_time,
                        deleted
                    ) VALUES (
                        NEW.id,
                        NEW.data_series_id,
                        NEW.external_id,
                        NEW.point_in_time,
                        NEW.deleted
                    );
                    RETURN NEW;
                END;
                $BODY$
                LANGUAGE plpgsql VOLATILE;

                CREATE TRIGGER _{str(Module.DATA_SERIES.value)}_view_data_point_insert
                INSTEAD OF INSERT ON _{str(Module.DATA_SERIES.value)}_view_data_point
                FOR EACH ROW EXECUTE PROCEDURE _{str(Module.DATA_SERIES.value)}_insert_data_point();

                -- deleting from the view should be the same as inserting a new entry with
                -- deleted = true
                CREATE FUNCTION _{str(Module.DATA_SERIES.value)}_delete_data_point()
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
                        deleted
                    ) VALUES (
                        OLD.id,
                        OLD.data_series_id,
                        OLD.external_id,
                        OLD.point_in_time,
                        true
                    );
                    RETURN NULL;
                END;
                $BODY$
                LANGUAGE plpgsql VOLATILE;
                
                CREATE TRIGGER _{str(Module.DATA_SERIES.value)}_view_data_point_delete
                INSTEAD OF DELETE ON _{str(Module.DATA_SERIES.value)}_view_data_point
                FOR EACH ROW EXECUTE PROCEDURE _{str(Module.DATA_SERIES.value)}_delete_data_point();

                -- updating the view
                CREATE FUNCTION _{str(Module.DATA_SERIES.value)}_update_data_point()
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
                        deleted
                    ) VALUES (
                        NEW.id,
                        NEW.data_series_id,
                        NEW.external_id,
                        NEW.point_in_time,
                        NEW.deleted
                    );
                    RETURN NEW;
                END;
                $BODY$
                LANGUAGE plpgsql VOLATILE;
                
                CREATE TRIGGER _{str(Module.DATA_SERIES.value)}_view_data_point_update
                INSTEAD OF UPDATE ON _{str(Module.DATA_SERIES.value)}_view_data_point
                FOR EACH ROW EXECUTE PROCEDURE _{str(Module.DATA_SERIES.value)}_update_data_point();  
"""
            )

            ]) +
            migrations_for_dataseries_child(child_name='dimension', child_foreign_key='dimension_id') +
            migrations_for_dataseries_child(child_name='float_fact', child_foreign_key='fact_id') +
            migrations_for_dataseries_child(child_name='image_fact', child_foreign_key='fact_id') +
            migrations_for_dataseries_child(child_name='json_fact', child_foreign_key='fact_id') +
            migrations_for_dataseries_child(child_name='string_fact', child_foreign_key='fact_id') +
            migrations_for_dataseries_child(child_name='timestamp_fact', child_foreign_key='fact_id') +
            migrations_for_dataseries_child(child_name='text_fact', child_foreign_key='fact_id') +


            migrations_for_datapoint_data_tables(data_name='dimension',
                                                 data_foreign_key='dimension_id',
                                                 value_column_def=data_point_id_column_def,
                                                 fact_or_dim_id='dimension_id',
                                                 value_name='value') +
            migrations_for_datapoint_data_tables(data_name='float_fact',
                                                 data_foreign_key='fact_id',
                                                 value_column_def='double precision') +
            migrations_for_datapoint_data_tables(data_name='image_fact',
                                                 data_foreign_key='fact_id',
                                                 value_column_def='TEXT COLLATE pg_catalog."default"') +
            migrations_for_datapoint_data_tables(data_name='json_fact',
                                                 data_foreign_key='fact_id',
                                                 value_column_def='jsonb') +
            migrations_for_datapoint_data_tables(data_name='string_fact',
                                                 data_foreign_key='fact_id',
                                                 value_column_def='character varying(256) COLLATE pg_catalog."default"') +
            migrations_for_datapoint_data_tables(data_name='timestamp_fact',
                                                 data_foreign_key='fact_id',
                                                 value_column_def='timestamp with time zone') +
            migrations_for_datapoint_data_tables(data_name='text_fact',
                                                 data_foreign_key='fact_id',
                                                 value_column_def='text') +
            []
    )
