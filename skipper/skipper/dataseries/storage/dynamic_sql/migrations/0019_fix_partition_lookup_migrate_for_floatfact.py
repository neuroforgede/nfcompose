# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG


from django.apps.registry import Apps
from django.db import migrations
from typing import Any, List


def migrate_fact_tables_into_tenant_schema(
        fact_name_ds_rel: str,
        fact_model_name: str,
        base_table_name: str
) -> List[Any]:
    def migrate(apps: Apps, schema_editor: Any) -> Any:
        from django.db import connections
        from skipper.dataseries.raw_sql import escape
        from skipper.settings import DATA_SERIES_DYNAMIC_SQL_DB
        from skipper.dataseries.raw_sql.tenant import escaped_tenant_schema, ensure_schema

        DataSeries = apps.get_model('dataseries', 'DataSeries')
        FactModel = apps.get_model('dataseries', fact_model_name)
        PartitionByUUID = apps.get_model('dataseries', 'PartitionByUUID')
        PostgresAnalyticsUser = apps.get_model('dataseries', 'PostgresAnalyticsUser')

        for dataseries in DataSeries.all_objects.all():
            tenant = dataseries.tenant
            schema_name = escaped_tenant_schema(tenant.name)

            for fact in FactModel.all_objects.filter(
                **{
                    f'dataseries_{fact_name_ds_rel}__data_series': dataseries
                }
            ).all():
                found_partitions = list(PartitionByUUID.objects.filter(
                    base_table=base_table_name,
                    child_table_schema__isnull=True,
                    partition_key=fact.id
                ).all())
                if len(found_partitions) == 1:
                    partition = found_partitions[0]
                    assert partition.child_table_schema is None

                    ensure_schema(schema_name, connection_name=DATA_SERIES_DYNAMIC_SQL_DB)
                    with connections[DATA_SERIES_DYNAMIC_SQL_DB].cursor() as cursor:
                        cursor.execute(
                            f"""
                            ALTER TABLE {escape.escape(partition.child_table)}
                            SET SCHEMA {schema_name};
                            """
                        )

                    for postgres_analytics_user in PostgresAnalyticsUser.objects.filter(
                        tenant=tenant,
                        tenant_global_read=True
                    ).all():
                        with connections[DATA_SERIES_DYNAMIC_SQL_DB].cursor() as cursor:
                            cursor.execute(
                                f"""
                                GRANT USAGE ON SCHEMA {schema_name}
                                    TO {escape.escape(postgres_analytics_user.role)};
                                GRANT SELECT ON TABLE {schema_name}.{escape.escape(partition.child_table)}
                                    TO {escape.escape(postgres_analytics_user.role)};
                                """
                            )
    return [
        migrations.RunPython(migrate)
    ]


def finalize_migration_of_fact_tables_into_tenant_schema(
        fact_name_ds_rel: str,
        fact_model_name: str,
        base_table_name: str
) -> List[Any]:
    def migrate(apps: Apps, schema_editor: Any) -> Any:
        from skipper.dataseries.raw_sql.tenant import tenant_schema_unescaped

        DataSeries = apps.get_model('dataseries', 'DataSeries')
        FactModel = apps.get_model('dataseries', fact_model_name)
        PartitionByUUID = apps.get_model('dataseries', 'PartitionByUUID')

        for dataseries in DataSeries.all_objects.all():
            tenant = dataseries.tenant

            for fact in FactModel.all_objects.filter(
                **{
                    f'dataseries_{fact_name_ds_rel}__data_series': dataseries
                }
            ).all():
                found_partitions = list(PartitionByUUID.objects.filter(
                    base_table=base_table_name,
                    child_table_schema__isnull=True,
                    partition_key=fact.id
                ).all())
                if len(found_partitions) == 1:
                    partition = found_partitions[0]
                    assert partition.child_table_schema is None

                    partition = found_partitions[0]
                    partition.child_table_schema = tenant_schema_unescaped(tenant.name)
                    partition.save()

    return [
        migrations.RunPython(migrate)
    ]


def finalize_migration_of_datapoint_tables_into_tenant_schema(apps: Apps, schema_editor: Any) -> Any:
    from skipper.dataseries.raw_sql.tenant import tenant_schema_unescaped

    DataSeries = apps.get_model('dataseries', 'DataSeries')
    PartitionByUUID = apps.get_model('dataseries', 'PartitionByUUID')

    base_table_name = '_3_data_point'

    for dataseries in DataSeries.all_objects.all():
        tenant = dataseries.tenant

        found_partitions = list(PartitionByUUID.objects.filter(
            base_table=base_table_name,
            child_table_schema__isnull=True,
            partition_key=dataseries.id
        ).all())

        if len(found_partitions) == 1:
            partition = found_partitions[0]
            assert partition.child_table_schema is None

            partition = found_partitions[0]
            partition.child_table_schema = tenant_schema_unescaped(tenant.name)
            partition.save()


class Migration(migrations.Migration):
    atomic = True

    dependencies = [
        ('skipper_dataseries_storage_dynamic_sql', '0018_widen_file_type_path_columns_and_recreate_dependents'),
        ('dataseries', '0049_auto_20201205_1838')
    ]

    replaces = [
        ('skipper.dataseries.storage.dynamic_sql', '0019_fix_partition_lookup_migrate_for_floatfact')
    ]

    operations = [
        migrations.RunPython(finalize_migration_of_datapoint_tables_into_tenant_schema),
        *finalize_migration_of_fact_tables_into_tenant_schema(
            fact_name_ds_rel='booleanfact',
            fact_model_name='BooleanFact',
            base_table_name='_3_data_point_boolean_fact'
        ),
        *finalize_migration_of_fact_tables_into_tenant_schema(
            fact_name_ds_rel='dimension',
            fact_model_name='Dimension',
            base_table_name='_3_data_point_dimension'
        ),
        *finalize_migration_of_fact_tables_into_tenant_schema(
            fact_name_ds_rel='filefact',
            fact_model_name='FileFact',
            base_table_name='_3_data_point_file_fact'
        ),
        *finalize_migration_of_fact_tables_into_tenant_schema(
            fact_name_ds_rel='imagefact',
            fact_model_name='ImageFact',
            base_table_name='_3_data_point_image_fact'
        ),
        *finalize_migration_of_fact_tables_into_tenant_schema(
            fact_name_ds_rel='jsonfact',
            fact_model_name='JsonFact',
            base_table_name='_3_data_point_json_fact'
        ),
        *finalize_migration_of_fact_tables_into_tenant_schema(
            fact_name_ds_rel='stringfact',
            fact_model_name='StringFact',
            base_table_name='_3_data_point_string_fact'
        ),
        *finalize_migration_of_fact_tables_into_tenant_schema(
            fact_name_ds_rel='textfact',
            fact_model_name='TextFact',
            base_table_name='_3_data_point_text_fact'
        ),
        *finalize_migration_of_fact_tables_into_tenant_schema(
            fact_name_ds_rel='timestampfact',
            fact_model_name='TimestampFact',
            base_table_name='_3_data_point_timestamp_fact'
        ),
        *migrate_fact_tables_into_tenant_schema(
            fact_name_ds_rel='floatfact',
            fact_model_name='FloatFact',
            base_table_name='_3_data_point_float_fact'
        ),
        *finalize_migration_of_fact_tables_into_tenant_schema(
            fact_name_ds_rel='floatfact',
            fact_model_name='FloatFact',
            base_table_name='_3_data_point_float_fact'
        ),
    ]
