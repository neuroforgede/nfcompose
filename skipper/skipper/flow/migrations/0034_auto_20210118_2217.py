# Generated by Django 3.1.2 on 2021-01-18 22:17

from django.db import migrations, models
import skipper.core.models.validation


class Migration(migrations.Migration):

    dependencies = [
        ('flow', '0033_auto_20210115_1143'),
    ]

    operations = [
        migrations.AlterField(
            model_name='engine',
            name='external_id',
            field=models.CharField(max_length=256, validators=[skipper.core.models.validation.external_id_validator_url_safe]),
        ),
        migrations.AlterField(
            model_name='httpendpoint',
            name='external_id',
            field=models.CharField(max_length=256, validators=[skipper.core.models.validation.external_id_validator_url_safe]),
        ),
    ]
