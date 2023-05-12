# Add database constraints foreign keys as django did not set them up properly

from django.db import migrations

from skipper.dataseries.storage.dynamic_sql.migrations.custom_v1.helpers import migrations_for_dataseries_child, migrations_for_datapoint_data_tables
from skipper.dataseries.storage.dynamic_sql.migrations.custom_v1.record_source_user import add_record_source_and_user_id
from skipper.modules import Module


class Migration(migrations.Migration):
    atomic = True

    dependencies = [
        ('skipper_dataseries_storage_dynamic_sql', '0012_datapoint_filefact_writabledatapoint_filefact'),
    ]

    replaces = [
        ('skipper.dataseries.storage.dynamic_sql', '0013_file_fact_custom')
    ]

    operations = (
            migrations_for_dataseries_child(child_name='file_fact', child_foreign_key='fact_id') +
            migrations_for_datapoint_data_tables(data_name='file_fact',
                                                 data_foreign_key='fact_id',
                                                 value_column_def='TEXT COLLATE pg_catalog."default"') +
            add_record_source_and_user_id(data_name='file_fact') +
            []
    )
