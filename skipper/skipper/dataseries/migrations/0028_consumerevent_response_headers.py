# Generated by Django 3.0.7 on 2020-07-29 22:46

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dataseries', '0027_auto_20200729_2240'),
    ]

    operations = [
        migrations.AddField(
            model_name='consumerevent',
            name='response_headers',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=dict, null=True),
        ),
    ]
