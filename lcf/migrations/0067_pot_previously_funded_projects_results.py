# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-04-01 16:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lcf', '0066_auto_20170401_1601'),
    ]

    operations = [
        migrations.AddField(
            model_name='pot',
            name='previously_funded_projects_results',
            field=models.TextField(blank=True, null=True),
        ),
    ]
