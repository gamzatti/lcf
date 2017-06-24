# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-06-24 12:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lcf', '0101_auto_20170622_2218'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pot',
            name='name',
            field=models.CharField(choices=[('E', 'Emerging'), ('M', 'Mature'), ('FIT', 'Feed-in-tariff'), ('SN', 'Separate negotiations')], default='E', max_length=3),
        ),
        migrations.AlterField(
            model_name='technology',
            name='name',
            field=models.CharField(choices=[('NU', 'Nuclear'), ('WA', 'Wave'), ('ONW', 'Onshore wind'), ('OFW', 'Offshore wind'), ('NW', 'Negawatts'), ('TL', 'Tidal lagoon'), ('TS', 'Tidal stream'), ('PVLS', 'Solar PV')], default='OFW', max_length=4),
        ),
    ]
