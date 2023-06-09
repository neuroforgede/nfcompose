# Generated by Django 3.1.2 on 2020-12-05 18:38

from django.db import migrations
import skipper.core.models.fields
import skipper.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('dataseries', '0048_auto_20201205_1250'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dataseries',
            name='extra_config',
            field=skipper.core.models.fields.EmptyDictNotBlankJSONField(default=dict, validators=[skipper.core.validators.JSONSchemaValidator(json_schema_data=skipper.core.validators.JSONSchemaData(definitions=None, schema={'$id': 'data_series.extra_config', '$schema': 'http://json-schema.org/draft-07/schema', 'additionalProperties': False, 'properties': {'auto_clean_history_after_days': {'$id': '#/properties/auto_clean_history_after_days', 'default': -1, 'type': 'integer'}, 'auto_clean_meta_model_after_days': {'$id': '#/properties/auto_clean_meta_model_after_days', 'default': -1, 'type': 'integer'}}, 'required': [], 'type': 'object'}))]),
        ),
    ]
