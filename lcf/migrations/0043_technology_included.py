# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-16 10:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lcf', '0042_auto_20170315_1345'),
    ]

    operations = [
        migrations.AddField(
            model_name='technology',
            name='included',
            field=models.BooleanField(default=True),
        ),
    ]