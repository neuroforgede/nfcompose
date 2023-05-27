# Add database constraints foreign keys as django did not set them up properly

from django.db import migrations


class Migration(migrations.Migration):
    atomic = True

    dependencies = [
        ('skipper_dataseries_storage_dynamic_sql', '0004_drop_default_tenant_schema'),
    ]

    replaces = [
        ('dataseries', '0006_add_record_source_and_user_id'),
        ('skipper.dataseries.storage.dynamic_sql', '0006_add_record_source_and_user_id')
    ]

    operations = [] # type: ignore
