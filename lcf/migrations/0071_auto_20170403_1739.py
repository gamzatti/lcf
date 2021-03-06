# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-04-03 17:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lcf', '0070_pot_cum_awarded_gen_result'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pot',
            name='cum_awarded_gen_result',
            field=models.FloatField(blank=True, null=True, verbose_name='Cumulative generation'),
        ),
        migrations.AlterField(
            model_name='pot',
            name='cum_owed_v_wp',
            field=models.FloatField(blank=True, null=True, verbose_name='Accounting cost (£bn)'),
        ),
    ]
