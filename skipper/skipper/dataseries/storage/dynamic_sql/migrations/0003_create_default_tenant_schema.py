# Add database constraints foreign keys as django did not set them up properly
from django.db import migrations

class Migration(migrations.Migration):
    atomic = True

    dependencies = [
        ('skipper_dataseries_storage_dynamic_sql', '0002_initial_custom'),
    ]

    replaces = [
        ('dataseries', '0003_create_default_tenant_schema'),
        ('skipper.dataseries.storage.dynamic_sql', '0003_create_default_tenant_schema')
    ]

    operations = (
            [migrations.RunSQL("""
            CREATE SCHEMA "_3_tenant_default";
            """)]
    )
