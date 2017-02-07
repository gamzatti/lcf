# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-07 11:54
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lcf', '0017_auctionyeartechnology_load_factor'),
    ]

    operations = [
        migrations.AlterField(
            model_name='auctionyeartechnology',
            name='load_factor',
            field=models.FloatField(default=0.5),
        ),
        migrations.AlterField(
            model_name='auctionyeartechnology',
            name='max_deployment',
            field=models.FloatField(default=100),
        ),
        migrations.AlterField(
            model_name='auctionyeartechnology',
            name='max_levelised_cost',
            field=models.FloatField(default=100),
        ),
        migrations.AlterField(
            model_name='auctionyeartechnology',
            name='min_levelised_cost',
            field=models.FloatField(default=100),
        ),
        migrations.AlterField(
            model_name='auctionyeartechnology',
            name='project_size',
            field=models.FloatField(default=100),
        ),
        migrations.AlterField(
            model_name='auctionyeartechnology',
            name='strike_price',
            field=models.FloatField(default=100),
        ),
        migrations.AlterField(
            model_name='auctionyeartechnology',
            name='technology_name',
            field=models.CharField(choices=[('OFW', 'Offshore wind'), ('ONW', 'Onshore wind'), ('NU', 'Nuclear'), ('TL', 'Tidal lagoon'), ('TS', 'Tidal stream'), ('WA', 'Wave'), ('PVLS', 'Solar PV')], default='OFW', max_length=4),
        ),
        migrations.AlterField(
            model_name='project',
            name='levelised_cost',
            field=models.FloatField(default=100),
        ),
    ]
