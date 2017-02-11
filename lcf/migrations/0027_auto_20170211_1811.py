# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-11 18:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lcf', '0026_auto_20170210_1648'),
    ]

    operations = [
        migrations.AddField(
            model_name='scenario',
            name='rank_by_strike_price',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='scenario',
            name='budget',
            field=models.FloatField(default=3.3, verbose_name='Budget (£bn)'),
        ),
        migrations.AlterField(
            model_name='scenario',
            name='description',
            field=models.TextField(blank=True, null=True, verbose_name='Description (optional)'),
        ),
    ]
