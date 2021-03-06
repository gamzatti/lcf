# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-05-06 19:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lcf', '0093_auto_20170506_1651'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pot',
            name='name',
            field=models.CharField(choices=[('M', 'Mature'), ('SN', 'Separate negotiations'), ('FIT', 'Feed-in-tariff'), ('E', 'Emerging')], default='E', max_length=3),
        ),
        migrations.AlterField(
            model_name='technology',
            name='name',
            field=models.CharField(choices=[('ONW', 'Onshore wind'), ('WA', 'Wave'), ('NU', 'Nuclear'), ('TL', 'Tidal lagoon'), ('OFW', 'Offshore wind'), ('PVLS', 'Solar PV'), ('NW', 'Negawatts'), ('TS', 'Tidal stream')], default='OFW', max_length=4),
        ),
    ]
