# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-21 11:56
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lcf', '0032_scenario_set_strike_price'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='technology',
            name='cum_project_gen_incorrect',
        ),
    ]
