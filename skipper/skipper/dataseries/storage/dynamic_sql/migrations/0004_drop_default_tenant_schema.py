from django.db import migrations

class Migration(migrations.Migration):
    atomic = True

    dependencies = [
        ('skipper_dataseries_storage_dynamic_sql', '0003_create_default_tenant_schema'),
    ]

    replaces = [
        ('dataseries', '0004_drop_default_tenant_schema'),
        ('skipper.dataseries.storage.dynamic_sql', '0004_drop_default_tenant_schema')
    ]

    operations = (
            [migrations.RunSQL("""
            DROP SCHEMA "_3_tenant_default";
            """)]
    )
