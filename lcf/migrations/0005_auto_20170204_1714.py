# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-04 17:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lcf', '0004_auto_20170204_1700'),
    ]

    operations = [
        migrations.AlterField(
            model_name='generalinputset',
            name='budget',
            field=models.DecimalField(decimal_places=3, default=3, max_digits=5),
        ),
        migrations.AlterField(
            model_name='generalinputset',
            name='percent_emerging',
            field=models.DecimalField(decimal_places=3, default=0.6, max_digits=4),
        ),
    ]
