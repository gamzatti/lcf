# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-04-04 07:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lcf', '0072_auto_20170403_1841'),
    ]

    operations = [
        migrations.AddField(
            model_name='technology',
            name='cum_owed_v_wp',
            field=models.FloatField(default=0),
        ),
    ]