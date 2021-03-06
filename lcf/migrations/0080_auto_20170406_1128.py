# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-04-06 11:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lcf', '0079_scenario_results'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scenario',
            name='end_year1',
            field=models.IntegerField(default=2025, verbose_name='End of LCF 1 period'),
        ),
        migrations.AlterField(
            model_name='scenario',
            name='tidal_levelised_cost_distribution',
            field=models.BooleanField(default=True),
        ),
    ]
