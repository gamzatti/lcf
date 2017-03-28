from django.test import TestCase
import pandas as pd
import numpy as np
from pandas import DataFrame, Series
from pandas.util.testing import assert_frame_equal
from django.forms import modelformset_factory, formset_factory

from django.core.urlresolvers import reverse

from .models import Scenario, AuctionYear, Pot, Technology
from .forms import ScenarioForm, PricesForm, TechnologyStringForm
import math


class InputDisplayTests(TestCase):
    fixtures = ['tests/new/data.json']

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

class PeriodTests(TestCase):
    fixtures = ['tests/new/data.json']

    def test_default_start_and_end_years(self):
        s = Scenario.objects.get(pk=281)
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
        s = Scenario.objects.get(pk=281)
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
        s = Scenario.objects.get(pk=281)
        self.assertEqual(s.accounting_cost(1)['df'].index[0],'Accounting cost')
        self.assertEqual(s.accounting_cost(2)['df'].columns[0],'2026')
        self.assertEqual(s.cum_awarded_gen_by_pot(1)['df'].columns[0],'2021')
        self.assertEqual(s.cum_awarded_gen_by_pot(2)['df'].index[0],'E')

    def test_get_or_make_chart_data_with_period_arg(self):
        s = Scenario.objects.get(pk=281)
        s.get_or_make_chart_data("accounting_cost",1)
        self.assertEqual(s._accounting_cost1['df']['2025']['Accounting cost'],2.805)
        s.get_or_make_chart_data("cum_awarded_gen_by_pot",2)
        self.assertEqual(s._cum_awarded_gen_by_pot2['df'].index[0],'E')


    def test_scenario_detail_view(self):
        s = Scenario.objects.get(pk=281)
        s.get_or_make_chart_data("accounting_cost",1)
        df = s._accounting_cost1['df'].to_html(classes="table table-striped table-condensed")
        resp = self.client.get(reverse('scenario_detail',kwargs={'pk': s.pk}))
        self.assertTrue('accounting_cost_chart1' in resp.context)
        self.assertEqual(resp.context['accounting_cost_df1'],df)
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get(reverse('scenario_detail',kwargs={'pk': 999}))
        self.assertEqual(resp.status_code, 404)

    def test_auctionyear_period(self):
        s = Scenario.objects.get(pk=281)
        a = AuctionYear.objects.get(scenario=s, year=2024)
        self.assertEqual(a.period_num(), 1)
        self.assertEqual(set(list(a.period())), set(list(s.period(1))))
        b = AuctionYear.objects.get(scenario=s, year=2027)
        self.assertEqual(set(list(b.period())), set(list(s.period(2))))

    def test_new_auctionyear_cum_years(self):
        s = Scenario.objects.get(pk=281)
        a = AuctionYear.objects.get(scenario=s, year=2024)
        self.assertQuerysetEqual(a.cum_years(), ["<AuctionYear: 2021>",
                                                 "<AuctionYear: 2022>",
                                                 "<AuctionYear: 2023>",
                                                 "<AuctionYear: 2024>"])
        b = AuctionYear.objects.get(scenario=s, year=2027)
        self.assertQuerysetEqual(b.cum_years(), ["<AuctionYear: 2026>",
                                                 "<AuctionYear: 2027>"])

    def test_new_pot_cum_pots(self):
        s = Scenario.objects.get(pk=281)
        a = AuctionYear.objects.get(scenario=s, year=2024)
        p = Pot.objects.get(auctionyear=a, name="E")
        self.assertQuerysetEqual(p.cum_pots(), ["<Pot: (<AuctionYear: 2021>, 'E')>",
                                                "<Pot: (<AuctionYear: 2022>, 'E')>",
                                                "<Pot: (<AuctionYear: 2023>, 'E')>",
                                                "<Pot: (<AuctionYear: 2024>, 'E')>",
                                                ])
        b = AuctionYear.objects.get(scenario=s, year=2027)
        q = Pot.objects.get(auctionyear=b, name="M")
        self.assertQuerysetEqual(q.cum_pots(), ["<Pot: (<AuctionYear: 2026>, 'M')>",
                                                "<Pot: (<AuctionYear: 2027>, 'M')>",
                                                ])


    def test_pot_period(self):
        s = Scenario.objects.get(pk=281)
        a = AuctionYear.objects.get(scenario=s, year=2024)
        p = Pot.objects.get(auctionyear=a, name="E")
        self.assertQuerysetEqual(p.period_pots(), ["<Pot: (<AuctionYear: 2021>, 'E')>",
                                                   "<Pot: (<AuctionYear: 2022>, 'E')>",
                                                   "<Pot: (<AuctionYear: 2023>, 'E')>",
                                                   "<Pot: (<AuctionYear: 2024>, 'E')>",
                                                   "<Pot: (<AuctionYear: 2025>, 'E')>",
                                                   ])


    def test_budget_for_each_period(self):
        s = Scenario.objects.get(pk=281)
        self.assertEqual(s.budget,3.3)
        self.assertIsNone(s.budget2)
        for a in s.period(1):
            self.assertEqual(round(a.starting_budget()),660)
        for a in s.period(2):
            self.assertEqual(round(a.starting_budget()),660)
        s.budget2 = 5
        s.save()
        for a in s.period(2):
            self.assertEqual(round(a.starting_budget()),1000)
        s.end_year1 = 2023
        s.start_year2 = 2024
        s.save()
        for a in s.period(1):
            self.assertEqual(round(a.starting_budget()),round(3300/3))
        for a in s.period(2):
            self.assertEqual(round(a.starting_budget()),round(5000/7))


class ExcelQuirkTests(TestCase):
    fixtures = ['tests/new/data.json']

    def test_excel_2020_gen_error_true(self):
        s = Scenario.objects.get(pk=281)
        s.excel_2020_gen_error = True
        s.save()
        #period1
        a0 = s.auctionyear_set.get(year=2020)
        for p in a0.active_pots():
            p.run_auction()

        a1 = s.auctionyear_set.get(year=2021)
        for p in a1.active_pots():
            p.run_auction()

        a2 = s.auctionyear_set.get(year=2022)
        for p in a2.active_pots():
            p.run_auction()

        expected_cum_awarded_gen = a2.awarded_gen() + a1.awarded_gen() + a0.awarded_gen() - a0.pot_set.get(name="FIT").awarded_gen()
        self.assertEqual(round(a2.cum_awarded_gen(),3),round(expected_cum_awarded_gen,3))
        #period2
        a5 = s.auctionyear_set.get(year=2025)
        for p in a5.active_pots():
            p.run_auction()

        a6 = s.auctionyear_set.get(year=2026)
        for p in a6.active_pots():
            p.run_auction()

        expected_cum_awarded_gen = a6.awarded_gen()
        self.assertEqual(round(a6.cum_awarded_gen(),3),round(expected_cum_awarded_gen,3))

    def test_excel_2020_gen_error_false(self):
        s = Scenario.objects.get(pk=281)
        s.excel_2020_gen_error = False
        s.save()

        a0 = s.auctionyear_set.get(year=2020)
        for p in a0.active_pots():
            p.run_auction()

        a1 = s.auctionyear_set.get(year=2021)
        for p in a1.active_pots():
            p.run_auction()

        a2 = s.auctionyear_set.get(year=2022)
        for p in a2.active_pots():
            p.run_auction()

        expected_cum_awarded_gen = a2.awarded_gen() + a1.awarded_gen()
        self.assertEqual(round(a2.cum_awarded_gen(),3),round(expected_cum_awarded_gen,3))
        #period2
        a5 = s.auctionyear_set.get(year=2025)
        for p in a5.active_pots():
            p.run_auction()

        a6 = s.auctionyear_set.get(year=2026)
        for p in a6.active_pots():
            p.run_auction()

        expected_cum_awarded_gen = a6.awarded_gen()
        self.assertEqual(round(a6.cum_awarded_gen(),3),round(expected_cum_awarded_gen,3))

    def test_excel_sp_error_true(self):
        pass

    def test_excel_sp_error_false(self):
        pass

    def test_excel_nw_carry_error_true(self):
        pass

    def test_excel_nw_carry_error_false(self):
        pass

    def test_all_excel_quirks(self):
        s = Scenario.objects.get(pk=281)
        s.excel_sp_error = True
        s.excel_nw_carry_error = True
        s.excel_2020_gen_error = True
        s.save()
        self.assertEqual(round(s.accounting_cost(1)['df']['2025']['Accounting cost'],3), 2.805)

        s.excel_sp_error = False
        s.excel_nw_carry_error = False
        s.excel_2020_gen_error = False
        s.save()
        #self.assertEqual(round(s.accounting_cost(1)['df']['2025']['Accounting cost'],3), x)


class ExcelCompareTests(TestCase):
    fixtures = ['tests/new/data.json']

    def test_budget(self):
        s = Scenario.objects.get(pk=281)
        a = AuctionYear.objects.get(scenario=s, year=2025)
        self.assertEqual(round(a.starting_budget()),660)
        t = Scenario.objects.get(pk=245)
        b = AuctionYear.objects.get(scenario=t, year=2025)
        self.assertEqual(round(b.starting_budget()),660)

        assert_frame_equal(s.accounting_cost(1)['df'], t.accounting_cost(1)['df'])
        print('\n',s.accounting_cost(2)['df'])
        p = a.pot_set.get(name="E")
        q = b.pot_set.get(name="E")
        drop = ['gen', 'technology', 'attempted_project_gen', 'listed_year', 'affordable', 'pot', 'strike_price']
        pproj = p.projects().drop(drop,axis=1)
        qproj = q.projects().drop(drop,axis=1)
        v = Technology.objects.get(name="OFW",pot=p)
        u = Technology.objects.get(name="OFW",pot=q)
        t_set = Technology.objects.filter(name="TL", pot__auctionyear__scenario=s)

class TestViews(TestCase):
    fixtures = ['tests/new/data.json']

    def test_scenario_new_view(self):
        s = Scenario.objects.get(pk=281)
        resp = self.client.get(reverse('scenario_new',kwargs={'pk': s.pk}))
        self.assertTrue('scenario_form' in resp.context)
        self.assertEqual(resp.status_code, 200)

    def test_good_post(self):
        #sanity check
        test_scenario = Scenario.objects.get(pk=281)
        a2020 = test_scenario.auctionyear_set.get(year=2020)
        self.assertEqual(a2020.gas_price, 85)
        post_data = {'name': 'test2',
                    'percent_emerging': 0.5,
                    'budget': 2,
                    'start_year1': 2020,
                    'end_year1': 2022,
                    'wholesale_prices': "50 51 52 50 51 52 50 51 52 50 51",
                    'gas_prices': "60 61 62 60 61 62 60 61 62 60 61",
                    'form-TOTAL_FORMS': "1",
                    'form-INITIAL_FORMS': "1",
                    'form-MIN_NUM_FORMS': "0",
                    'form-MAX_NUM_FORMS': "1",
                    'form-0-name': "OFW",
                    'form-0-pot': "E",
                    'form-0-included': "on",
                    'form-0-min_levelised_cost': "50 51 52 50 51 52 50 51 52 50 51",
                    'form-0-max_levelised_cost': "60 61 62 60 61 62 60 61 62 60 61",
                    'form-0-strike_price': "43 45 34 43 45 34 43 45 34 43 45",
                    'form-0-load_factor': "33 34 34 33 34 34 33 34 34 33 34",
                    'form-0-project_gen': "44 34 34 44 34 34 44 34 34 44 34",
                    'form-0-max_deployment_cap': "3 23 23 3 23 23 3 23 23 3 23"
                    }
        resp = self.client.post(reverse('scenario_new',kwargs={'pk': 281}), post_data)
        self.assertEqual(resp.status_code, 302)

    def test_valid_stringformset(self):
        data = {
                'form-TOTAL_FORMS': "1",
                'form-INITIAL_FORMS': "1",
                'form-MIN_NUM_FORMS': "0",
                'form-MAX_NUM_FORMS': "1",
                'form-0-name': "OFW",
                'form-0-pot': "E",
                'form-0-included': "on",
                'form-0-min_levelised_cost': "50 51 52",
                'form-0-max_levelised_cost': "60 61 62",
                'form-0-strike_price': "43 45 34",
                'form-0-load_factor': "33 34 34",
                'form-0-project_gen': "44 34 34",
                'form-0-max_deployment_cap': "3 23 23"
                }
        TechnologyStringFormSet = formset_factory(TechnologyStringForm, extra=0, max_num=1)
        string_formset = TechnologyStringFormSet(data)
        self.assertTrue(string_formset.is_valid())
        data = {
                'form-TOTAL_FORMS': "1",
                'form-INITIAL_FORMS': "1",
                'form-MIN_NUM_FORMS': "0",
                'form-MAX_NUM_FORMS': "1",
                'form-0-name': "OFW",
                'form-0-pot': "E",
                'form-0-min_levelised_cost': "50 51 52",
                'form-0-max_levelised_cost': "60 61 62",
                'form-0-strike_price': "43 45 34",
                'form-0-load_factor': "33 34 34",
                'form-0-project_gen': "44 34 34",
                'form-0-max_deployment_cap': "3 23 23"
                }
        string_formset = TechnologyStringFormSet(data)
        self.assertTrue(string_formset.is_valid())
