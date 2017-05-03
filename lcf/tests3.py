from django.test import TestCase
import time
from django.core.urlresolvers import reverse
from django.forms import modelformset_factory, formset_factory

import pandas as pd
import numpy as np
from pandas import DataFrame, Series
from pandas.util.testing import assert_frame_equal, assert_series_equal

import lcf.dataframe_helpers as dhf
from .models import Scenario, AuctionYear, Pot, Technology, Policy
from .forms import ScenarioForm, PricesForm, PolicyForm
from .helpers import save_policy_to_db, get_prices, update_prices_with_policies, create_auctionyear_and_pot_objects, update_tech_with_policies, create_technology_objects

# all tests have to be run individually!
# python manage.py test lcf.tests3.TestCumProj.test_num_projects
# python manage.py test lcf.tests3.TestCumProj.test_run_auction
# python manage.py test lcf.tests3.TestCumProj.test_run_auction_budget
# python manage.py test lcf.tests3.TestCumProj.test_accounting_cost
# python manage.py test lcf.tests3.TestCumProj.test_budget_period_2
#
# python manage.py test lcf.tests3.TestCumProj.test_fit_cost_individual_quirks
# python manage.py test lcf.tests3.TestCumProj.test_fit_cost_lumped_quirks
#
# python manage.py test lcf.tests3.TestNonCumProj.test_non_cum_num_projects
# python manage.py test lcf.tests3.TestNonCumProj.test_non_cum_levelised_cost_distribution
# python manage.py test lcf.tests3.TestNonCumProj.test_non_cum_projects_index
# python manage.py test lcf.tests3.TestNonCumProj.test_non_cum_projects
# python manage.py test lcf.tests3.TestNonCumProj.test_non_cum_concat_projects
# python manage.py test lcf.tests3.TestNonCumProj.test_non_cum_run_auction_max_deployment_cap
# python manage.py test lcf.tests3.TestNonCumProj.test_non_cum_run_auction_budget
# python manage.py test lcf.tests3.TestNonCumProj.test_non_cum_budget_period_2
#
# python manage.py test lcf.tests3.TestCumProjSimple.test_unspent_high
# python manage.py test lcf.tests3.TestCumProjSimple.test_unspent_normal
# python manage.py test lcf.tests3.TestCumProjSimple.test_unspent_low
# python manage.py test lcf.tests3.TestCumProjSimple.test_unspent_lower
#
# python manage.py test lcf.tests3.TestNonCumProjSimple.test_non_cum_unspent_high
# python manage.py test lcf.tests3.TestNonCumProjSimple.test_non_cum_unspent_normal
# python manage.py test lcf.tests3.TestNonCumProjSimple.test_non_cum_unspent_low
# python manage.py test lcf.tests3.TestNonCumProjSimple.test_non_cum_unspent_lower

# python manage.py test lcf.tests3.TestIP.test_nw_v_gas


class TestCumProj(TestCase):
    fixtures = ['tests/3/data2.json'] # old TS gen, but with new 'false cum proj'


    def test_num_projects(self):
        s = Scenario.objects.all().prefetch_related('auctionyear_set__pot_set__technology_set').get(pk=281)
        s.excel_include_previous_unsuccessful_all = True
        s.save()
        ofw_list = [s.auctionyear_dict[i].pot_dict['E'].technology_dict['OFW'] for i in range(2020,2031) ]
        self.assertEqual([ofw.num_projects() for ofw in ofw_list], [8, 17, 26, 35, 44, 54, 64, 74, 84, 93, 103])

    def test_run_auction(self):
        s = Scenario.objects.all().prefetch_related('auctionyear_set__pot_set__technology_set').get(pk=281)
        s.excel_include_previous_unsuccessful_all = True
        s.save()
        p = s.auctionyear_dict[2022].pot_dict['E']
        p.cum_run_auction() # note doesn't need to run 2020 auction because it needs only the previous year unspent not all the projects generated
        # print(p.projects())
        s.get_results()
        # print(s.pivot('awarded_cap',2))

    def test_run_auction_budget(self):
        s = Scenario.objects.all().get(pk=281)
        s.excel_include_previous_unsuccessful_all = True
        s.save()
        e_list = [ s.auctionyear_dict[y].pot_dict['E'] for y in range(2020,2031)]
        # p = s.auctionyear_dict[2027].pot_dict['E']
        for p in e_list:
            p.cum_run_auction()
            # print(p.projects()[p.projects().eligible == True])
            # print('year', p.auctionyear.year)
            # print('budget', p.budget(), 'auctionyear_budget_all', p.auctionyear.budget_all())
            # print('spent', p.awarded_cost_result)
            # print('unspent',p.unspent(), '\n\n')
            self.assertTrue(p.awarded_cost_result < p.budget())


    def test_budget_period_2(self):
        s = Scenario.objects.all().get(pk=281)
        s.excel_include_previous_unsuccessful_all = True
        s.save()
        a1 = s.auctionyear_dict[2021]
        a6 = s.auctionyear_dict[2026]
        self.assertEqual(a1.budget_all(), a1.starting_budget())
        self.assertEqual(a6.budget_all(), a6.starting_budget())


    def test_accounting_cost(self):
        s = Scenario.objects.all().prefetch_related('auctionyear_set__pot_set__technology_set').get(pk=281)
        s.excel_include_previous_unsuccessful_all = True
        s.save()
        results = s.pivot('cum_owed_v_wp',1)
        # print(results)
        self.assertEqual(round(results.loc[('Total', 'Total'),('Accounting cost (£bn)', 2025)],3), 2.805)


    def test_fit_cost_individual_quirks(self):
        s = Scenario.objects.all().prefetch_related('auctionyear_set__pot_set__technology_set').get(pk=281)
        s.excel_include_previous_unsuccessful_all = True
        s.excel_nw_carry_error = True
        s.excel_sp_error = True
        s.excel_2020_gen_error = True
        s.excel_quirks = False
        s.save()
        s.get_results()
        p = s.auctionyear_dict[2021].pot_dict['FIT']
        self.assertEqual(p.awarded_cost_result, 89)

    def test_fit_cost_lumped_quirks(self):
        s = Scenario.objects.all().prefetch_related('auctionyear_set__pot_set__technology_set').get(pk=281)
        s.excel_include_previous_unsuccessful_all = False
        s.excel_nw_carry_error = False
        s.excel_sp_error = False
        s.excel_2020_gen_error = False
        s.excel_quirks = True
        s.save()
        s.get_results()
        p = s.auctionyear_dict[2021].pot_dict['FIT']
        self.assertEqual(p.awarded_cost_result, 89)


class TestNonCumProj(TestCase):
    fixtures = ['tests/3/data2.json'] # old TS gen, but with new 'false cum proj'

    def test_non_cum_num_projects(self):
        s = Scenario.objects.all().get(pk=281)
        s.excel_quirks = False
        s.excel_include_previous_unsuccessful_all = False
        s.excel_nw_carry_error = True
        s.excel_sp_error = True
        s.excel_2020_gen_error = True
        s.save()
        #results = s.pivot('cum_owed_v_wp',1)
        ofw_list = [s.auctionyear_dict[i].pot_dict['E'].technology_dict['OFW'] for i in range(2020,2031) ]
        self.assertEqual([ofw.non_cum_num_projects() for ofw in ofw_list], [8, 8, 8, 9, 9, 9, 9, 9, 9, 9, 9])

    def test_non_cum_levelised_cost_distribution(self):
        s = Scenario.objects.all().get(pk=281)
        s.excel_quirks = False
        s.excel_include_previous_unsuccessful_all = False
        s.excel_nw_carry_error = True
        s.excel_sp_error = True
        s.excel_2020_gen_error = True
        s.save()
        #results = s.pivot('cum_owed_v_wp',1)
        ofw_list = [s.auctionyear_dict[i].pot_dict['E'].technology_dict['OFW'] for i in range(2020,2031) ]
        self.assertEqual([round(i) for i in ofw_list[1].non_cum_levelised_cost_distribution().values.tolist() ], [75, 78, 81, 85, 88, 92, 95, 98])

    def test_non_cum_projects_index(self):
        s = Scenario.objects.all().get(pk=281)
        s.excel_quirks = False
        s.excel_include_previous_unsuccessful_all = False
        s.excel_nw_carry_error = True
        s.excel_sp_error = True
        s.excel_2020_gen_error = True
        s.save()
        #results = s.pivot('cum_owed_v_wp',1)
        ofw_list = [s.auctionyear_dict[i].pot_dict['E'].technology_dict['OFW'] for i in range(2020,2031) ]
        ofw = ofw_list[1]
        self.assertEqual(ofw.non_cum_projects_index(), ['2021_OFW1', '2021_OFW2', '2021_OFW3', '2021_OFW4', '2021_OFW5', '2021_OFW6', '2021_OFW7', '2021_OFW8'])

    def test_non_cum_projects(self):
        s = Scenario.objects.all().get(pk=281)
        s.excel_quirks = False
        s.excel_include_previous_unsuccessful_all = False
        s.excel_nw_carry_error = True
        s.excel_sp_error = True
        s.excel_2020_gen_error = True
        s.save()
        ofw_list = [s.auctionyear_dict[i].pot_dict['E'].technology_dict['OFW'] for i in range(2020,2031) ]
        ofw = ofw_list[1]
        self.assertEqual(ofw.non_cum_projects().levelised_cost[3], ofw.non_cum_levelised_cost_distribution()[3])

    def test_non_cum_concat_projects(self):
        s = Scenario.objects.all().get(pk=281)
        s.excel_quirks = False
        s.excel_include_previous_unsuccessful_all = False
        s.excel_nw_carry_error = True
        s.excel_sp_error = True
        s.excel_2020_gen_error = True
        s.save()
        p = s.auctionyear_dict[2026].pot_dict['E']
        tech_index = [item for t in p.technology_dict.values() for item in t.non_cum_projects_index() ]
        tech_costs = [item for t in p.technology_dict.values() for item in t.non_cum_levelised_cost_distribution().tolist() ]
        self.assertEqual(sorted(p.non_cum_concat_projects().index.tolist()), sorted(tech_index))
        self.assertEqual(sorted(p.non_cum_concat_projects().levelised_cost.tolist()), sorted(tech_costs))

    def test_non_cum_run_auction_max_deployment_cap(self):
        s = Scenario.objects.all().get(pk=281)
        s.excel_quirks = False
        s.excel_include_previous_unsuccessful_all = False
        s.excel_nw_carry_error = True
        s.excel_sp_error = True
        s.excel_2020_gen_error = True
        s.save()
        results = s.get_results()
        ofw_max_deployment_caps = Series([ a.pot_dict['E'].technology_dict['OFW'].max_deployment_cap for a in s.auctionyear_dict.values() if a.year > 2020 ], index=range(2021,2031))
        ofw_caps = s.pivot('awarded_cap').loc[('Emerging', 'Offshore wind')]
        ofw_caps.index = range(2021,2031)
        self.assertTrue((ofw_max_deployment_caps > ofw_caps).all())

    def test_non_cum_run_auction_budget(self):
        s = Scenario.objects.all().get(pk=281)
        s.excel_quirks = False
        s.excel_include_previous_unsuccessful_all = False
        s.excel_nw_carry_error = True
        s.excel_sp_error = True
        s.excel_2020_gen_error = True
        s.save()
        e_list = [ s.auctionyear_dict[y].pot_dict['E'] for y in range(2020,2026)]
        # p = s.auctionyear_dict[2027].pot_dict['E']
        for p in e_list:
            p.non_cum_run_auction() # note doesn't need to run 2020 auction because it needs only the previous year unspent not all the projects generated
            # print(p.projects()[p.projects().eligible == True])
            # print('year', p.auctionyear.year)
            # print('budget', p.budget(), 'auctionyear_budget_all', p.auctionyear.budget_all())
            # print('spent', p.awarded_cost_result)
            # print('unspent',p.unspent(), '\n\n')
            self.assertTrue(p.awarded_cost_result < p.budget())

    def test_non_cum_budget_period_2(self):
        s = Scenario.objects.all().get(pk=281)
        s.excel_quirks = False
        s.excel_include_previous_unsuccessful_all = False
        s.excel_nw_carry_error = True
        s.excel_sp_error = True
        s.excel_2020_gen_error = True
        s.save()
        a1 = s.auctionyear_dict[2021]
        a6 = s.auctionyear_dict[2026]
        self.assertEqual(a1.budget_all(), a1.starting_budget())
        self.assertEqual(a6.budget_all(), a6.starting_budget())




class TestCumProjSimple(TestCase):
    fixtures = ['tests/3/simple.json']

    def test_unspent(self,budget,expected_cost_2025):
        s = Scenario.objects.all().get(pk=586)
        s.excel_include_previous_unsuccessful_all = True
        s.budget = budget
        s.save()
        e_list = [ s.auctionyear_dict[y].pot_dict['E'] for y in range(2020,2026)]
        for p in e_list:
            p.cum_run_auction() # note doesn't need to run 2020 auction because it needs only the previous year unspent not all the projects generated
            # print(p.projects()[p.projects().eligible == True])
            # print('year', p.auctionyear.year)
            # print('budget', p.budget(), 'auctionyear_budget_all', p.auctionyear.budget_all(), 'starting auctionyear budget', p.auctionyear.starting_budget())
            # print('spent', p.awarded_cost_result)
            # print('unspent',p.unspent(), '\n\n')
        results = s.pivot('cum_owed_v_wp',1)
        # print('scenario budget', s.budget)
        # print('accounting cost 2025', results.loc[('Total', 'Total'),('Accounting cost (£bn)', 2025)])
        self.assertEqual(round(results.loc[('Total', 'Total'),('Accounting cost (£bn)', 2025)],2),expected_cost_2025)


    def test_unspent_high(self):
        self.test_unspent(5, 1.42)
        # constrained by (inaccurate) deployment

    def test_unspent_normal(self):
        self.test_unspent(2.9, 1.42)
        # constrained by (inaccurate) deployment

    def test_unspent_low(self):
        self.test_unspent(1.8, 1.42)
        # constrained by (inaccurate) deployment

    def test_unspent_lower(self):
        self.test_unspent(1.3, 1.05)
        # constrained by budget


class TestNonCumProjSimple(TestCase):
    fixtures = ['tests/3/simple.json']

    def test_non_cum_unspent(self,budget, expected_cost_2025):
        s = Scenario.objects.all().get(pk=586)
        s.excel_quirks = False
        s.excel_include_previous_unsuccessful_all = False
        s.excel_nw_carry_error = True
        s.excel_sp_error = True
        s.excel_2020_gen_error = True
        s.budget = budget
        s.save()
        e_list = [ s.auctionyear_dict[y].pot_dict['E'] for y in range(2020,2026)]
        for p in e_list:
            p.run_relevant_auction() # note doesn't need to run 2020 auction because it needs only the previous year unspent not all the projects generated
            # print(p.projects()[p.projects().eligible == True])
            # print('year', p.auctionyear.year)
            # print('budget', p.budget(), 'auctionyear_budget_all', p.auctionyear.budget_all(), 'starting auctionyear budget', p.auctionyear.starting_budget())
            # print('spent', p.awarded_cost_result)
            # print('unspent',p.unspent(), '\n\n')
        results = s.pivot('cum_owed_v_wp',1)
        # print('scenario budget', s.budget)
        # print('accounting cost 2025', results.loc[('Total', 'Total'),('Accounting cost (£bn)', 2025)])
        self.assertEqual(round(results.loc[('Total', 'Total'),('Accounting cost (£bn)', 2025)],2),expected_cost_2025)


    def test_non_cum_unspent_high(self):
        self.test_non_cum_unspent(5,1.33)
        # constrained by deployment

    def test_non_cum_unspent_normal(self):
        self.test_non_cum_unspent(2.9,1.33)
        # constrained by deployment

    def test_non_cum_unspent_low(self):
        self.test_non_cum_unspent(1.8,1.30)
        # constrained by deployment 2022-2025, constrained by budget in 2021

    def test_non_cum_unspent_lower(self):
        self.test_non_cum_unspent(1.3, 1.05)
        # constrained by budget

class TestIP(TestCase):
    fixtures = ['tests/3/data2.json']

    def test_nw_v_gas(self):
        s = Scenario.objects.all().prefetch_related('auctionyear_set__pot_set__technology_set').get(pk=281)
        s.excel_quirks = True
        s.save()
        p = s.auctionyear_dict[2021].pot_dict['FIT']

        p.run_relevant_auction()
        t = p.technology_dict['NW']
        self.assertEqual(t.cum_owed_v_gas, (t.awarded_gen * t.strike_price) - (t.awarded_gen * p.auctionyear.gas_price))
        self.assertEqual(t.cum_owed_v_gas, (t.awarded_gen * (t.strike_price - p.auctionyear.gas_price)))
        pivot = s.pivot('cum_owed_v_gas',1)
        print(pivot)

class TestPolicies(TestCase):
    fixtures = ['tests/3/data2.json']

    def test_policy_subtract(self):
        pass
