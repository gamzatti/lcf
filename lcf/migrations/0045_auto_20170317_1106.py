# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-17 11:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lcf', '0044_scenario_excel_2020_gen_error'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pot',
            name='name',
            field=models.CharField(choices=[('SN', 'Separate negotiations'), ('FIT', 'Feed-in-tariff'), ('E', 'Emerging'), ('M', 'Mature')], default='E', max_length=3),
        ),
    ]