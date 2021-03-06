# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-04-12 14:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lcf', '0084_auto_20170411_1019'),
    ]

    operations = [
        migrations.AddField(
            model_name='scenario',
            name='subsidy_free_p2',
            field=models.BooleanField(default=False, verbose_name='Only subsidy-free CFDs for period two'),
        ),
        migrations.AlterField(
            model_name='pot',
            name='name',
            field=models.CharField(choices=[('M', 'Mature'), ('E', 'Emerging'), ('SN', 'Separate negotiations'), ('FIT', 'Feed-in-tariff')], default='E', max_length=3),
        ),
        migrations.AlterField(
            model_name='technology',
            name='name',
            field=models.CharField(choices=[('OFW', 'Offshore wind'), ('TL', 'Tidal lagoon'), ('TS', 'Tidal stream'), ('WA', 'Wave'), ('PVLS', 'Solar PV'), ('NW', 'Negawatts'), ('ONW', 'Onshore wind'), ('NU', 'Nuclear')], default='OFW', max_length=4),
        ),
    ]
