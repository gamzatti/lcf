# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-04-07 17:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lcf', '0082_policy_effects'),
    ]

    operations = [
        migrations.AddField(
            model_name='scenario',
            name='policies',
            field=models.ManyToManyField(to='lcf.Policy'),
        ),
    ]
