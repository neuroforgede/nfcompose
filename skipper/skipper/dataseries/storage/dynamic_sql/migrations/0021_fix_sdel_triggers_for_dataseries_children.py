# This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0. 
# If a copy of the MPL was not distributed with this file, 
# You can obtain one at https://mozilla.org/MPL/2.0/.
# This file is part of NF Compose
# [2019] - [2023] © NeuroForge GmbH & Co. KG

from django.db import migrations

from skipper.dataseries.storage.dynamic_sql.migrations.custom_v1.helpers import migrations_for_dataseries_child


class Migration(migrations.Migration):
    atomic = True

    dependencies = [
        ('skipper_dataseries_storage_dynamic_sql', '0020_migrate_all_materialized_dataseries_add_del_bool_col'),
    ]

    replaces = [
        ('skipper.dataseries.storage.dynamic_sql', '0021_fix_sdel_triggers_for_dataseries_children')
    ]

    # simply re run this
    # TODO: for new installations we can ignore the original runs
    operations = (
            migrations_for_dataseries_child(child_name='dimension', child_foreign_key='dimension_id') +
            migrations_for_dataseries_child(child_name='float_fact', child_foreign_key='fact_id') +
            migrations_for_dataseries_child(child_name='string_fact', child_foreign_key='fact_id') +
            migrations_for_dataseries_child(child_name='text_fact', child_foreign_key='fact_id') +
            migrations_for_dataseries_child(child_name='timestamp_fact', child_foreign_key='fact_id') +
            migrations_for_dataseries_child(child_name='image_fact', child_foreign_key='fact_id') +
            migrations_for_dataseries_child(child_name='file_fact', child_foreign_key='fact_id') +
            migrations_for_dataseries_child(child_name='json_fact', child_foreign_key='fact_id') +
            migrations_for_dataseries_child(child_name='boolean_fact', child_foreign_key='fact_id') +
            migrations_for_dataseries_child(child_name='consumer', child_foreign_key='consumer_id')
    )
