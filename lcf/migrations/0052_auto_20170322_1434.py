# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-03-22 14:34
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lcf', '0051_auctionyear_budget'),
    ]

    operations = [
        migrations.AlterField(
            model_name='auctionyear',
            name='budget',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
