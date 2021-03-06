# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-04-20 14:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lcf', '0086_auto_20170420_1138'),
    ]

    operations = [
        migrations.AddField(
            model_name='scenario',
            name='excel_cum_project_distr',
            field=models.BooleanField(default=True, verbose_name='Include the Excel quirk that calculates number of projects cumulatively and then excludes previously successful ones (as opposed to just treating each year separately)'),
        ),
        migrations.AlterField(
            model_name='pot',
            name='name',
            field=models.CharField(choices=[('FIT', 'Feed-in-tariff'), ('SN', 'Separate negotiations'), ('E', 'Emerging'), ('M', 'Mature')], default='E', max_length=3),
        ),
        migrations.AlterField(
            model_name='technology',
            name='name',
            field=models.CharField(choices=[('NW', 'Negawatts'), ('TL', 'Tidal lagoon'), ('WA', 'Wave'), ('NU', 'Nuclear'), ('PVLS', 'Solar PV'), ('TS', 'Tidal stream'), ('ONW', 'Onshore wind'), ('OFW', 'Offshore wind')], default='OFW', max_length=4),
        ),
    ]
