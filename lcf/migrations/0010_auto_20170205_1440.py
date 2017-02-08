# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-05 14:40
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('lcf', '0009_auto_20170204_1917'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='TechnologyYearData',
            new_name='AuctionYearTechnology',
        ),
        migrations.RenameField(
            model_name='project',
            old_name='technologyyeardata',
            new_name='auction_year_technology',
        ),
        migrations.RemoveField(
            model_name='scenario',
            name='auctionyearset',
        ),
        migrations.AlterField(
            model_name='auctionyear',
            name='inputset',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='lcf.Scenario'),
        ),
        migrations.DeleteModel(
            name='AuctionYearSet',
        ),
    ]