# Generated by Django 3.2.7 on 2021-10-21 20:55

from django.db import migrations, models
import skipper.core.models.validation


class Migration(migrations.Migration):

    dependencies = [
        ('dataseries', '0077_auto_20210811_2019'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dataseries_consumer',
            name='external_id',
            field=models.CharField(max_length=256, validators=[skipper.core.models.validation.external_id_validator_url_safe]),
        ),
    ]
