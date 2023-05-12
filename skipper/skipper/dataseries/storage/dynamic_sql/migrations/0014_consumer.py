# Add database constraints foreign keys as django did not set them up properly

from django.db import migrations

from skipper.dataseries.storage.dynamic_sql.migrations.custom_v1.helpers import data_point_id_column_def, \
    external_id_column_def, migrations_for_dataseries_child, migrations_for_datapoint_data_tables
from skipper.dataseries.storage.dynamic_sql.migrations.custom_v1.record_source_user import add_record_source_and_user_id
from skipper.modules import Module

# TODO: this should really not be part of the dynamic sql backend
# but we have it here for simplicity (as we have the others here as well)


class Migration(migrations.Migration):
    atomic = True

    dependencies = [
        ('skipper_dataseries_storage_dynamic_sql', '0013_file_fact_custom'),
        ('dataseries', '0023_consumerevent'),
    ]

    replaces = [
        ('skipper.dataseries.storage.dynamic_sql', '0014_consumer')
    ]

    operations = (
            migrations_for_dataseries_child(child_name='consumer', child_foreign_key='consumer_id') +
            []
    )
