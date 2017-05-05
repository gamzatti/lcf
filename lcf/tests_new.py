from django.test import TestCase
import pandas as pd
import numpy as np
from pandas import DataFrame, Series
from pandas.util.testing import assert_frame_equal
from django.forms import modelformset_factory, formset_factory
import time
from django.core.urlresolvers import reverse
import lcf.dataframe_helpers as dfh
import numpy.testing as npt

from .models import Scenario, AuctionYear, Pot, Technology, Policy
from .forms import ScenarioForm, PricesForm, PolicyForm
# from .helpers import save_policy_to_db, get_prices, update_prices_with_policies, create_auctionyear_and_pot_objects, update_tech_with_policies, create_technology_objects
from .helpers import process_policy_form, get_prices, create_auctionyear_and_pot_objects, update_tech_with_policies, create_technology_objects

import math

# python manage.py test lcf.tests_new.PeriodTests.test_default_start_and_end_years
# python manage.py test lcf.tests_new.PeriodTests.test_periods
# python manage.py test lcf.tests_new.PeriodTests.test_charts_with_periods
# python manage.py test lcf.tests_new.PeriodTests.test_get_or_make_chart_data_with_period_arg
# python manage.py test lcf.tests_new.PeriodTests.test_scenario_detail_view
# python manage.py test lcf.tests_new.PeriodTests.test_auctionyear_period
# python manage.py test lcf.tests_new.PeriodTests.test_new_auctionyear_cum_years
# python manage.py test lcf.tests_new.PeriodTests.test_new_pot_cum_pots
# python manage.py test lcf.tests_new.PeriodTests.test_pot_period
# python manage.py test lcf.tests_new.PeriodTests.test_budget_for_each_period

# python manage.py test lcf.tests_new.ExcelCompareTests.test_budget

# python manage.py test lcf.tests_new.Prefetch.test_get_scenario
# python manage.py test lcf.tests_new.Prefetch.test_auctionyear
# python manage.py test lcf.tests_new.Prefetch.test_get_results


class PeriodTests(TestCase):
    fixtures = ['tests/new/data2.json']

    def setUp(self):
        clear_all()

    def test_default_start_and_end_years(self):
        clear_all()
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
        clear_all()
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
        clear_all()
        s = Scenario.objects.get(pk=281)
        self.assertEqual(s.cumulative_costs(1)['df'].index[0],'Accounting cost')
        self.assertEqual(s.cumulative_costs(2)['df'].columns[0],'2026')
        self.assertEqual(s.cum_awarded_gen_by_pot(1)['df'].columns[0],'2021')
        self.assertEqual(s.cum_awarded_gen_by_pot(2)['df'].index[0],'E')

    def test_get_or_make_chart_data_with_period_arg(self):
        clear_all()
        s = Scenario.objects.get(pk=281)
        s.get_or_make_chart_data("cumulative_costs",1)
        self.assertEqual(s._cumulative_costs1['df']['2025']['Accounting cost'],2.805)
        s.get_or_make_chart_data("cum_awarded_gen_by_pot",2)
        self.assertEqual(s._cum_awarded_gen_by_pot2['df'].index[0],'E')


    def test_scenario_detail_view(self):
        clear_all()
        s = Scenario.objects.get(pk=281)
        s.get_or_make_chart_data("cumulative_costs",1)
        df = s._cumulative_costs1['df'].to_html(classes="table table-striped table-condensed")
        resp = self.client.get(reverse('scenario_detail',kwargs={'pk': s.pk}))
        self.assertTrue('cumulative_costs_chart1' in resp.context)
        self.assertEqual(resp.context['cumulative_costs_df1'],df)
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get(reverse('scenario_detail',kwargs={'pk': 999}))
        self.assertEqual(resp.status_code, 404)

    def test_auctionyear_period(self):
        clear_all()
        s = Scenario.objects.get(pk=281)
        a = AuctionYear.objects.get(scenario=s, year=2024)
        self.assertEqual(a.period_num(), 1)
        self.assertEqual(set(list(a.period())), set(list(s.period(1))))
        b = AuctionYear.objects.get(scenario=s, year=2027)
        self.assertEqual(set(list(b.period())), set(list(s.period(2))))

    def test_new_auctionyear_cum_years(self):
        clear_all()
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
        clear_all()
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
        clear_all()
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
        clear_all()
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



class ExcelCompareTests(TestCase):
    fixtures = ['tests/new/data2.json']

    def setUp(self):
        clear_all()

    def test_budget(self):
        clear_all()
        s = Scenario.objects.get(pk=281)
        a = AuctionYear.objects.get(scenario=s, year=2025)
        self.assertEqual(round(a.starting_budget()),660)
        t = Scenario.objects.get(pk=245)
        b = AuctionYear.objects.get(scenario=t, year=2025)
        self.assertEqual(round(b.starting_budget()),660)

        assert_frame_equal(s.cumulative_costs(1)['df'], t.cumulative_costs(1)['df'])
        print('\n',s.cumulative_costs(2)['df'])
        p = a.pot_set.get(name="E")
        q = b.pot_set.get(name="E")
        drop = ['gen', 'technology', 'attempted_project_gen', 'listed_year', 'affordable', 'pot', 'strike_price']
        pproj = p.projects().drop(drop,axis=1)
        qproj = q.projects().drop(drop,axis=1)
        v = Technology.objects.get(name="OFW",pot=p)
        u = Technology.objects.get(name="OFW",pot=q)
        t_set = Technology.objects.filter(name="TL", pot__auctionyear__scenario=s)










class Prefetch(TestCase):
    fixtures = ['tests/new/data2.json']

    def test_get_scenario(self):
        # self.assertNotEqual(id(s.auctionyear_set.all()),id(s.auctionyear_set.all()))
        s = Scenario.objects.get(id=281)
        s.results = None
        s.save()
        s = Scenario.objects.all().prefetch_related('auctionyear_set__pot_set__technology_set').get(pk=281)
        s.get_results()

        self.assertEqual(id(s.auctionyear_set.all()),id(s.auctionyear_set.all()))
        self.assertEqual(s.auctionyear_set.all()[3], s.auctionyear_set.all()[3])
        self.assertEqual(id(s.auctionyear_dict[2021]), id(s.auctionyear_dict[2021]))
        a = s.auctionyear_dict[2021]
        pot_dict = a.pot_dict
        pot_dict2 = a.pot_dict
        self.assertEqual(id(pot_dict),id(pot_dict2))
        p = a.pot_dict['E']
        t = p.technology_dict['OFW']
        t2 = s.auctionyear_dict[2021].pot_dict['E'].technology_dict['OFW']
        self.assertEqual(id(t),id(t2))
        self.assertEqual(id(t.pot),id(t2.pot))
        self.assertEqual(id(t.pot.auctionyear.scenario.auctionyear_dict[2025]),id(t2.pot.auctionyear.scenario.auctionyear_dict[2025]))
        #print(s.period(2))
        #resp = self.client.get(reverse('scenario_detail',kwargs={'pk': 281}))
        flat_t_dict = { t.name + str(t.pot.auctionyear.year) : t for a in s.auctionyear_dict.values() for p in a.pot_dict.values() for t in p.technology_dict.values() }
        flat_t_dict2 = { t.name + str(t.pot.auctionyear.year) : t for a in s.auctionyear_dict.values() for p in a.pot_dict.values() for t in p.technology_dict.values() }
        #print(s.flat_tech_dict)
        self.assertEqual(id(flat_t_dict['OFW2022']),id(s.flat_tech_dict['OFW2022']))
        #print(s.df_to_html(s.techs_df()))
        #print(s.pivot_to_html(s.tech_pivot_table(2,'min_levelised_cost')))
        #print(s.techs_input())
        #print(s.prices_input())
        #print(s.techs_input_html())

    def test_auctionyear(self):
        s = Scenario.objects.get(id=281)
        s.results = None
        s.save()
        s = Scenario.objects.all().prefetch_related('auctionyear_set__pot_set__technology_set').get(pk=281)
        s.get_results()
        # a = s.auctionyear_dict[2021]
        # a.foo = 400
        # a_again = s.auctionyear_dict[2021]
        # self.assertEqual(a.foo,a_again.foo)
        #for y in range(2020,2031):
        for y in [2030,2029,2028,2027,2026, 2025, 2024, 2023, 2022, 2021, 2020]:
            a = s.auctionyear_dict[y]
            for n in ['E', 'M', 'SN', 'FIT']:
                p = a.pot_dict[n]
                p.run_relevant_auction()
        print(s.tech_pivot_table(1,'cum_awarded_gen'))
        # p = a_again.pot_dict["E"]
        # print(p.cum_owed_v_gas)

    def test_get_results(self):
        s = Scenario.objects.get(id=281)
        s.results = None
        s.save()
        s = Scenario.objects.all().prefetch_related('auctionyear_set__pot_set__technology_set').get(pk=281)
        s.get_results()
        print(s.tech_pivot_table(1,'cum_awarded_gen'))
