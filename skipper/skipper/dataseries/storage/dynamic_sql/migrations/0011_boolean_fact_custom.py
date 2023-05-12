# Add database constraints foreign keys as django did not set them up properly

from typing import List, cast

from django.db import migrations

from skipper.dataseries.storage.dynamic_sql.migrations.custom_v1.helpers import data_point_id_column_def, \
    external_id_column_def, migrations_for_dataseries_child, migrations_for_datapoint_data_tables
from skipper.dataseries.storage.dynamic_sql.migrations.custom_v1.record_source_user import add_record_source_and_user_id
from skipper.modules import Module


class Migration(migrations.Migration):
    atomic = True

    dependencies = [
        ('skipper_dataseries_storage_dynamic_sql', '0010_datapoint_booleanfact_writabledatapoint_booleanfact'),
    ]

    replaces = [
        ('skipper.dataseries.storage.dynamic_sql', '0011_boolean_fact_custom')
    ]

    operations = (
            migrations_for_dataseries_child(child_name='boolean_fact', child_foreign_key='fact_id') +
            migrations_for_datapoint_data_tables(data_name='boolean_fact',
                                                 data_foreign_key='fact_id',
                                                 value_column_def='BOOLEAN') +
            add_record_source_and_user_id(data_name='boolean_fact') +
            []
    )
