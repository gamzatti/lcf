# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-24 16:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lcf', '0037_scenario_end_year'),
    ]

    operations = [
        migrations.AddField(
            model_name='scenario',
            name='start_year',
            field=models.IntegerField(default=2021),
        ),
    ]
