# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-17 17:23
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lcf', '0048_auto_20170317_1535'),
    ]

    operations = [
        migrations.AlterField(
            model_name='technology',
            name='awarded_gen',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
