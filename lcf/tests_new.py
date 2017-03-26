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
        t = Scenario.objects.create(name="test")
        self.assertEqual(t.start_year1,2021)
        self.assertEqual(t.end_year1,2025)
        self.assertEqual(t.start_year2,2026)
        self.assertEqual(t.end_year2,2030)

    def test_periods(self):
        s = Scenario.objects.get(pk=252)
        self.assertQuerysetEqual(s.period(1), ["<AuctionYear: 2021>",
                                               "<AuctionYear: 2022>",
                                               "<AuctionYear: 2023>",
                                               "<AuctionYear: 2024>",
                                               "<AuctionYear: 2025>"])
        self.assertQuerysetEqual(s.period(2), ["<AuctionYear: 2026>",
                                               "<AuctionYear: 2027>",
                                               "<AuctionYear: 2028>",
                                               "<AuctionYear: 2029>",
                                               "<AuctionYear: 2030>"])
        t = Scenario.objects.create(name="test")
        for y in range(2020,2040):
            AuctionYear.objects.create(year=y,scenario=t)
        self.assertQuerysetEqual(t.period(1), ["<AuctionYear: 2021>",
                                               "<AuctionYear: 2022>",
                                               "<AuctionYear: 2023>",
                                               "<AuctionYear: 2024>",
                                               "<AuctionYear: 2025>"])
        self.assertQuerysetEqual(t.period(2), ["<AuctionYear: 2026>",
                                               "<AuctionYear: 2027>",
                                               "<AuctionYear: 2028>",
                                               "<AuctionYear: 2029>",
                                               "<AuctionYear: 2030>"])

    def test_charts_with_periods(self):
        s = Scenario.objects.get(pk=252)
        self.assertEqual(s.accounting_cost(1)['df'].index[0],'Accounting cost')
        self.assertEqual(s.accounting_cost(2)['df'].columns[0],'2026')
        self.assertEqual(s.cum_awarded_gen_by_pot(1)['df'].columns[0],'2021')
        self.assertEqual(s.cum_awarded_gen_by_pot(2)['df'].index[0],'E')

    def test_get_or_make_chart_data_with_period_arg(self):
        s = Scenario.objects.get(pk=252)
        s.get_or_make_chart_data("accounting_cost",1)
        self.assertEqual(s._accounting_cost1['df']['2025']['Accounting cost'],3.668)
        s.get_or_make_chart_data("cum_awarded_gen_by_pot",2)
        self.assertEqual(s._cum_awarded_gen_by_pot2['df'].index[0],'E')


    def test_scenario_detail_view(self):
        s = Scenario.objects.get(pk=252)
        s.get_or_make_chart_data("accounting_cost",1)
        df = s._accounting_cost1['df'].to_html(classes="table table-striped table-condensed")
        resp = self.client.get(reverse('scenario_detail',kwargs={'pk': s.pk}))
        self.assertTrue('accounting_cost_chart1' in resp.context)
        self.assertEqual(resp.context['accounting_cost_df1'],df)
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get(reverse('scenario_detail',kwargs={'pk': 999}))
        self.assertEqual(resp.status_code, 404)
