from django.test import TestCase
import pandas as pd
import numpy as np
from pandas import DataFrame, Series
from django.forms import modelformset_factory, formset_factory

from django.core.urlresolvers import reverse

from .models import Scenario, AuctionYear, Pot, Technology
from .forms import ScenarioForm, PricesForm, TechnologyStringForm
import math


class InputDisplayTests(TestCase):
    fixtures = ['all_data2.json']

    def test_techs_input(self):
        s = Scenario.objects.get(pk=245)
        val = s.techs_input().at[('E','OFW',2025),'min LCOE']
        self.assertEqual(val, 70.21)
        val = s.techs_input().at[('SN','NU',2024),'max GW pa']
        self.assertEqual(val, 2.9)

    def test_prices_input(self):
        s = Scenario.objects.get(pk=245)
        val = s.prices_input().at['wholesale prices', 2022]
        self.assertEqual(val, 58.47)
        #s = Scenario.objects.get(pk=250)
        #val = s.prices_input().at['wholesale prices', 2022]
        #self.assertEqual(val, 44.2)

class PeriodTests(TestCase):
    fixtures = ['testing_periods.json']

    def test_default_start_and_end_years(self):
        s = Scenario.objects.get(pk=252)
        self.assertEqual(s.start_year1,2021)
        self.assertEqual(s.end_year1,2025)
        self.assertEqual(s.start_year2,2026)
        self.assertEqual(s.end_year2,2030)
