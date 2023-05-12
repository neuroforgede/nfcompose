# Add database constraints foreign keys as django did not set them up properly

from django.db import migrations
from skipper.dataseries.storage.dynamic_sql.migrations.custom_v1.helpers import migrations_for_dataseries_child


class Migration(migrations.Migration):
    atomic = True

    dependencies = [
        ('skipper_dataseries_storage_dynamic_sql', '0024_drop_uniq_constraint_on_mat_table_external_id'),
        ('dataseries', '0079_index_initial'),
    ]

    operations = (
            migrations_for_dataseries_child(child_name='user_defined_index', child_foreign_key='user_defined_index_id') +
            []
    )
