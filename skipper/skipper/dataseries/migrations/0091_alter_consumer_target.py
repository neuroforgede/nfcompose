# Generated by Django 4.0.3 on 2022-04-23 11:15

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dataseries', '0090_metamodeltaskdata'),
    ]

    operations = [
        migrations.AlterField(
            model_name='consumer',
            name='target',
            field=models.URLField(max_length=1024, validators=[django.core.validators.URLValidator(schemes=['https', 'http'])]),
        ),
    ]
