# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-06-24 12:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lcf', '0102_auto_20170624_1314'),
    ]

    operations = [
        migrations.AddField(
            model_name='scenario',
            name='intermediate_results',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='pot',
            name='name',
            field=models.CharField(choices=[('E', 'Emerging'), ('SN', 'Separate negotiations'), ('FIT', 'Feed-in-tariff'), ('M', 'Mature')], default='E', max_length=3),
        ),
        migrations.AlterField(
            model_name='technology',
            name='name',
            field=models.CharField(choices=[('ONW', 'Onshore wind'), ('WA', 'Wave'), ('PVLS', 'Solar PV'), ('NU', 'Nuclear'), ('NW', 'Negawatts'), ('TL', 'Tidal lagoon'), ('TS', 'Tidal stream'), ('OFW', 'Offshore wind')], default='OFW', max_length=4),
        ),
    ]
