from django.test import TestCase
import pandas as pd
import numpy as np
from pandas import DataFrame, Series
from django.forms import modelformset_factory

from django.core.urlresolvers import reverse

from .models import Scenario, AuctionYear, Pot, Technology
from .forms import ScenarioForm, PricesForm

class TechnologyMethodTests(TestCase):
    fixtures = ['test_data.json']

    def setUp(self):
        self.s = Scenario.objects.get(pk=119)

        self.a0 = self.s.auctionyear_set.get(year=2020)
        self.a1 = self.s.auctionyear_set.get(year=2021)
        self.a2 = self.s.auctionyear_set.get(year=2022)

        self.p0E = self.a0.pot_set.get(name="E")
        self.p0M = self.a0.pot_set.get(name="M")
        self.p1E = self.a1.pot_set.get(name="E")
        self.p1M = self.a1.pot_set.get(name="M")
        self.p2E = self.a2.pot_set.get(name="E")
        self.p2M = self.a2.pot_set.get(name="M")

        self.t0E = self.p0E.technology_set.get(name="OFW")
        self.t0wave = self.p0E.technology_set.get(name="WA")
        self.t0M = self.p0M.technology_set.get(name="ONW")

        self.t1E = self.p1E.technology_set.get(name="OFW")
        self.t1wave = self.p1E.technology_set.get(name="WA")
        self.t1M = self.p1M.technology_set.get(name="ONW")

        self.t2E = self.p2E.technology_set.get(name="OFW")
        self.t2wave = self.p2E.technology_set.get(name="WA")
        self.t2M = self.p2M.technology_set.get(name="ONW")

        self.t2Ea = Technology.objects.create(name="OFW",
                                        pot=self.p2E,
                                        min_levelised_cost = 70.8845549535604,
                                        max_levelised_cost = 100.79939628483,
                                        strike_price = 90,
                                        load_factor = .448,
                                        project_gen = 832,
                                        max_deployment_cap = 1.9)

    def test_previous_year(self):
        self.assertEqual(self.t0E.previous_year(),None)
        self.assertEqual(self.t1E.previous_year(),self.t0E)
        self.assertEqual(self.t2E.previous_year(),self.t1E)
        self.assertEqual(self.t0wave.previous_year(),None)
        self.assertEqual(self.t1wave.previous_year(),self.t0wave)

    def test_previous_gen(self):
        self.assertEqual(round(self.t0E.previous_gen()),0)
        self.assertEqual(round(self.t1E.previous_gen()),6990)
        self.assertEqual(round(self.t2E.previous_gen()),14214)
        self.assertEqual(round(self.t0wave.previous_gen()),0)
        self.assertEqual(round(self.t1wave.previous_gen()),92)


    def test_this_year_gen(self):
        self.assertEqual(round(self.t0E.this_year_gen()),6990)
        self.assertEqual(round(self.t1E.this_year_gen()),7223)
        self.assertEqual(round(self.t2E.this_year_gen()),7457)
        self.assertEqual(round(self.t0wave.this_year_gen()),92)
        self.assertEqual(round(self.t1wave.this_year_gen()),9)

    def test_new_generation_available(self):
        self.assertEqual(round(self.t0E.new_generation_available()), 6990)
        self.assertEqual(round(self.t0M.new_generation_available()), 1779)
        self.assertEqual(round(self.t1E.new_generation_available()), 14214)
        self.assertEqual(round(self.t1M.new_generation_available()), 3571)
        self.assertEqual(round(self.t2E.new_generation_available()), 21670)
        self.assertEqual(round(self.t0wave.new_generation_available()), 92)
        self.assertEqual(round(self.t1wave.new_generation_available()), 101)

    def test_num_projects(self):
        self.assertEqual(self.t0E.num_projects(), 8)
        self.assertEqual(self.t1E.num_projects(), 17)
        self.assertEqual(self.t1M.num_projects(), 119)
        self.assertEqual(self.t2E.num_projects(), 26)
        self.assertEqual(self.t0wave.num_projects(), 3)
        self.assertEqual(self.t1wave.num_projects(), 3)

    def test_levelised_cost_distribution_length(self):
        self.assertEqual(len(self.t0E.levelised_cost_distribution()), 8)
        self.assertEqual(len(self.t1E.levelised_cost_distribution()), 17)
        self.assertEqual(len(self.t2E.levelised_cost_distribution()), 26)
        self.assertEqual(len(self.t0wave.levelised_cost_distribution()), 3)
        self.assertEqual(len(self.t1wave.levelised_cost_distribution()), 3)

    def test_levelised_cost_distribution_min_max(self):
        self.assertGreaterEqual(self.t0E.levelised_cost_distribution().min(), self.t0E.min_levelised_cost)
        self.assertGreaterEqual(self.t1E.levelised_cost_distribution().min(), self.t1E.min_levelised_cost)
        self.assertGreaterEqual(self.t0wave.levelised_cost_distribution().min(), self.t0wave.min_levelised_cost)
        self.assertLessEqual(self.t0E.levelised_cost_distribution().max(), self.t0E.max_levelised_cost)
        self.assertLessEqual(self.t2E.levelised_cost_distribution().max(), self.t2E.max_levelised_cost)
        self.assertLessEqual(self.t1wave.levelised_cost_distribution().max(), self.t1wave.max_levelised_cost)

    def test_levelised_cost(self):
        self.assertEqual(round(self.t0E.projects().levelised_cost[3],2), 85.42)
        self.assertEqual(round(self.t1E.projects().levelised_cost[3],2), 77.96)
        self.assertEqual(round(self.t2E.projects().levelised_cost[3],2), 75.32)
        self.assertEqual(round(self.t0wave.projects().levelised_cost[2],2), 288.69)
        self.assertEqual(round(self.t1wave.projects().levelised_cost[2],2), 272.22)


    def test_projects_index(self):
        self.assertEqual(self.t0E.projects_index()[0],"OFW1")
        self.assertEqual(self.t1E.projects_index()[1],"OFW2")
        self.assertEqual(self.t2E.projects_index()[2],"OFW3")
        self.assertEqual(self.t0wave.projects_index()[1],"WA2")

    def test_projects(self):
        self.assertEqual(round(self.t0E.projects().gen[1]),832)
        self.assertEqual(round(self.t0E.projects().gen.sum()), 832*8)
        self.assertEqual(round(self.t0wave.projects().gen.sum()), 27*3)
        self.assertEqual(round(self.t1E.projects().gen[5]),832)
        self.assertEqual(round(self.t2E.projects().gen[13]),832)
        self.assertEqual(self.t0E.projects().technology[4],"OFW")
        self.assertEqual(round(self.t1E.projects().strike_price[8],2),112.14)
        self.assertEqual(self.t0E.projects().funded[4],"no")

    def test_projects_affordable(self):
        self.assertEqual(self.t2E.projects().affordable[18],True)
        self.assertEqual(self.t1wave.projects().affordable[2],True)
        self.assertEqual(self.t2Ea.projects().strike_price[25],90)
        self.assertEqual(self.t2Ea.projects().affordable[25],False)
        self.assertEqual(self.t2Ea.min_levelised_cost, 70.8845549535604)

    def test_get_field_values(self):
        self.assertEqual(self.t2E.get_field_values()['name'],'OFW')

class PotMethodTests(TestCase):
    fixtures = ['test_data.json']

    def setUp(self):
        self.s = Scenario.objects.get(pk=119)

        self.a0 = self.s.auctionyear_set.get(year=2020)
        self.a1 = self.s.auctionyear_set.get(year=2021)
        self.a2 = self.s.auctionyear_set.get(year=2022)

        self.p0E = self.a0.pot_set.get(name="E")
        self.p0M = self.a0.pot_set.get(name="M")
        self.p1E = self.a1.pot_set.get(name="E")
        self.p1M = self.a1.pot_set.get(name="M")
        self.p2E = self.a2.pot_set.get(name="E")
        self.p2M = self.a2.pot_set.get(name="M")

        self.t0E = self.p0E.technology_set.get(name="OFW")
        self.t0wave = self.p0E.technology_set.get(name="WA")
        self.t0M = self.p0M.technology_set.get(name="ONW")

        self.t1E = self.p1E.technology_set.get(name="OFW")
        self.t1wave = self.p1E.technology_set.get(name="WA")
        self.t1M = self.p1M.technology_set.get(name="ONW")

        self.t2E = self.p2E.technology_set.get(name="OFW")
        self.t2wave = self.p2E.technology_set.get(name="WA")
        self.t2M = self.p2M.technology_set.get(name="ONW")


    def test_percent(self):
        self.assertEqual(self.p0E.percent(),0.6)
        self.assertEqual(self.p1E.percent(),0.6)
        self.assertEqual(self.p2M.percent(),0.4)
        self.assertEqual(self.p1M.percent(),0.4)

    def test_budget(self):
        self.assertEqual(round(self.p0E.auctionyear.budget()), 481)
        self.assertEqual(round(self.p0E.budget()), 289)
        self.assertEqual(round(self.p0M.budget()), 193)
        self.assertEqual(round(self.p1E.auctionyear.budget()), 660)
        self.assertEqual(round(self.p1E.budget()), 396)
        self.assertEqual(round(self.p1M.budget()), 264)
        self.assertEqual(round(self.p2E.auctionyear.budget()), 893) #should work when I sort out 233 problem
        self.assertEqual(round(self.p2E.budget()), 536)
        self.assertEqual(round(self.p2M.budget()), 357)

    def test_previous_year(self):
        self.assertEqual(self.p1E.previous_year(),self.p0E)
        self.assertEqual(self.p2M.previous_year(),self.p1M)
        self.assertNotEqual(self.p1M.previous_year(),self.p1M)


    def test_combining_tech_projects(self):
        self.assertEqual(len(self.p0E.run_auction()['projects'].index), len(self.t0E.projects())+len(self.t0wave.projects()))
        self.assertEqual(len(self.p0M.run_auction()['projects'].index), len(self.t0M.projects()))
        self.assertEqual(len(self.p0E.run_auction()['projects'].index), 8+3)
        self.assertEqual(len(self.p0M.run_auction()['projects'].index), 59)
        self.assertEqual(len(self.p1E.run_auction()['projects'].index),17+3)
        self.assertEqual(len(self.p1M.run_auction()['projects'].index), 119)
        self.assertEqual(self.p0E.run_auction()['projects'].index[0], 'OFW1')
        self.assertEqual(self.p0E.run_auction()['projects'].index[8], 'WA1')
        self.assertEqual(len(self.p2E.run_auction()['projects'].index),30)
        self.assertEqual(len(self.p2M.run_auction()['projects'].index), 179)

    def test_run_auction_first_year(self):
        self.assertEqual(len(self.p0E.run_auction()['projects'].index),8+3)
        self.assertEqual(self.p0E.run_auction()['projects']['funded_this_year']['OFW1'], True)
        self.assertEqual(self.p0E.run_auction()['projects']['funded_this_year']['OFW5'], True)
        self.assertEqual(self.p0E.run_auction()['projects']['funded_this_year']['OFW6'], False)
        #self.assertEqual(self.p0E.run_auction()['tech_gen']['OFW'], 832 * 5)
        self.assertEqual(self.p0E.run_auction()['projects']['funded_this_year'].value_counts()[True],5)
        self.assertEqual(self.p0M.run_auction()['projects']['funded_this_year'].value_counts()[True],59)

    def test_previously_funded_projects_index(self):
        self.assertTrue(self.p0E.previously_funded_projects().empty)
        self.assertTrue(self.p0M.previously_funded_projects().empty)
        self.assertEqual(len(self.p1E.previously_funded_projects().index), len(self.p0E.run_auction()['projects'][self.p0E.run_auction()['projects'].funded_this_year==True].index))
        self.assertEqual(len(self.p1E.previously_funded_projects().index), 5)
        self.assertEqual(self.p1E.previously_funded_projects()['funded_this_year']['OFW5'], True)
        self.assertNotIn(['OFW6'], list(self.p1E.previously_funded_projects().index))
        self.assertNotIn(['WA1'], list(self.p1E.previously_funded_projects().index))

    def test_run_auction_second_year(self):
        self.assertEqual(self.p1E.run_auction()['projects']['previously_funded'].value_counts()[True],5)
        self.assertEqual(self.p1M.run_auction()['projects']['previously_funded'].value_counts()[True],59)
        self.assertEqual(self.p1E.run_auction()['projects']['funded_this_year'].value_counts()[True],8)
        self.assertEqual(self.p1M.run_auction()['projects']['funded_this_year'].value_counts()[True],54)
        self.assertEqual(self.p1E.run_auction()['projects']['previously_funded']['OFW5'], True)
        self.assertEqual(self.p1E.run_auction()['projects']['funded_this_year']['OFW5'], False)
        self.assertEqual(self.p1E.run_auction()['projects']['funded_this_year']['OFW6'], True)
        self.assertEqual(self.p1E.run_auction()['projects']['previously_funded']['OFW6'], False)
        self.assertEqual(self.p1E.run_auction()['projects']['funded_this_year']['OFW14'], False)
        self.assertEqual(self.p1E.run_auction()['projects']['previously_funded']['OFW14'], False)
        self.assertEqual(self.p1E.run_auction()['projects']['funded_this_year']['WA1'], False)
        self.assertEqual(self.p1E.run_auction()['projects']['previously_funded']['WA1'], False)

    def test_run_auction_third_year(self):
        self.assertEqual(self.p2E.run_auction()['projects']['previously_funded'].value_counts()[True],5+8)
        self.assertEqual(self.p2M.run_auction()['projects']['previously_funded'].value_counts()[True],59+54)
        self.assertEqual(self.p2E.run_auction()['projects']['funded_this_year'].value_counts()[True],12)
        self.assertEqual(self.p2M.run_auction()['projects']['funded_this_year'].value_counts()[True],49)
        self.assertEqual(self.p2E.run_auction()['projects']['previously_funded']['OFW13'], True)
        self.assertEqual(self.p2E.run_auction()['projects']['funded_this_year']['OFW13'], False)
        self.assertEqual(self.p2E.run_auction()['projects']['funded_this_year']['OFW14'], True)
        self.assertEqual(self.p2E.run_auction()['projects']['previously_funded']['OFW14'], False)
        self.assertEqual(self.p2E.run_auction()['projects']['funded_this_year']['OFW26'], False)
        self.assertEqual(self.p2E.run_auction()['projects']['previously_funded']['OFW26'], False)


    def test_cost(self):
        self.assertEqual(round(self.p0E.cost(),2), 272.62)
        self.assertEqual(round(self.p0M.cost(),2), 55.68)
        self.assertEqual(round(self.p1E.cost(),2), 385.05)
        self.assertEqual(round(self.p1M.cost(),2), 41.66)
        self.assertEqual(round(self.p2E.cost(),2), 516.4)
        self.assertEqual(round(self.p2M.cost(),2), 31.64)

    def test_gen(self):
        self.assertEqual(round(self.p0E.gen()), 4160)
        self.assertEqual(round(self.p1E.gen()), 6656)
        self.assertEqual(round(self.p2E.gen()), 9984)
        self.assertEqual(round(self.p0M.gen()), 1770)
        self.assertEqual(round(self.p1M.gen()), 1620)
        self.assertEqual(round(self.p2M.gen()), 1470)

    def test_unspent(self):
        self.assertEqual(round(self.p0E.unspent()+self.p0M.unspent()),0)
        self.assertEqual(round(self.p1E.unspent()+self.p1M.unspent()),233) #passes here but fails below!
        #self.assertEqual(round(self.p2E.unspent()+self.p2M.unspent()),345) #should work when I sort out 893 problem

class AuctionYearMethodTests(TestCase):
    fixtures = ['test_data.json']

    def setUp(self):
        self.s = Scenario.objects.get(pk=119)

        self.a0 = self.s.auctionyear_set.get(year=2020)
        self.a1 = self.s.auctionyear_set.get(year=2021)
        self.a2 = self.s.auctionyear_set.get(year=2022)

        self.p0E = self.a0.pot_set.get(name="E")
        self.p0M = self.a0.pot_set.get(name="M")
        self.p1E = self.a1.pot_set.get(name="E")
        self.p1M = self.a1.pot_set.get(name="M")
        self.p2E = self.a2.pot_set.get(name="E")
        self.p2M = self.a2.pot_set.get(name="M")

        self.t0E = self.p0E.technology_set.get(name="OFW")
        self.t0wave = self.p0E.technology_set.get(name="WA")
        self.t0M = self.p0M.technology_set.get(name="ONW")

        self.t1E = self.p1E.technology_set.get(name="OFW")
        self.t1wave = self.p1E.technology_set.get(name="WA")
        self.t1M = self.p1M.technology_set.get(name="ONW")

        self.t2E = self.p2E.technology_set.get(name="OFW")
        self.t2wave = self.p2E.technology_set.get(name="WA")
        self.t2M = self.p2M.technology_set.get(name="ONW")




    def test_previous_year(self):
        self.assertEqual(self.a0.previous_year(),None)
        self.assertEqual(self.a1.previous_year(),self.a0)
        self.assertEqual(self.a2.previous_year(),self.a1)
        self.assertEqual(self.a2.previous_year().awarded(), self.a1.awarded())
        self.assertEqual(self.a1.unspent(),self.a2.previous_year().unspent())

    def test_previous_years(self):
        self.assertEqual(self.a0.previous_years(), None)
        self.assertQuerysetEqual(self.a1.previous_years(), [])
        self.assertQuerysetEqual(self.a2.previous_years(), ['<AuctionYear: 2021>'])

    #first year tests
    def test_starting_budget0(self):
        self.assertEqual(round(self.a0.starting_budget,2), 481.29)

    def test_previous_year_unspent0(self):
        self.assertEqual(round(self.a0.previous_year_unspent(),2),0)

    def budget0(self):
        self.assertEqual(round(self.a0.budget()),round(481.29+0)) #481.29

    def test_awarded0(self):
        self.assertEqual(round(self.a0.awarded()),round(272.62+55.68))#328.3

    def test_unspent0(self):
        self.assertEqual(round(self.a0.unspent()),round(481.3-328.3)) #153

    def test_owed0(self):
        pass

    def test_paid0(self):
        self.assertEqual(self.a0.paid(),self.a0.awarded())


    #second year tests
    def test_starting_budget1(self):
        self.assertEqual(round(self.a1.starting_budget), 660)

    def test_previous_year_unspent1(self):
        self.assertEqual(round(self.a1.previous_year_unspent(),2),0)

    def budget1(self):
        self.assertEqual(round(self.a1.budget()),round(660+0)) #660

    def test_awarded1(self):
        self.assertEqual(round(self.a1.awarded()),round(385.05+41.66))#426.71

    def test_unspent1(self):
        self.assertEqual(round(self.a1.unspent()),round(660-426.71)) #233.29

    def test_paid1(self):
        self.assertEqual(self.a1.paid(),self.a1.awarded())

    def test_owed1(self):
        self.assertEqual(round(self.a1.owed(self.a0),2),286.17)

    #third year tests
    def test_starting_budget2(self):
        self.assertEqual(round(self.a2.starting_budget), 660)

    def test_previous_year_unspent2(self):
        self.assertEqual(round(self.a2.previous_year_unspent(),2),233.29)

    def budget2(self):
        self.assertEqual(round(self.a2.budget()),round(660+233.29)) #893.29

    def test_awarded2(self):
        self.assertEqual(round(self.a2.awarded()),round(516.4+31.64))#548.04

    def test_unspent2(self):
        self.assertEqual(round(self.a2.unspent()),round(893.29-548.04)) #345.25

    def test_paid2(self):
        self.assertEqual(round(self.a2.paid(),2),round(self.a2.awarded() + self.a2.owed(self.a1),2))
        self.assertEqual(round(self.a2.paid(),2),927.18)


    def test_owed2(self):
        self.assertEqual(round(self.a2.owed(self.a1)),379)


    def test_awarded_gen(self):
        self.assertEqual(round(self.a0.awarded_gen()),5930)
        self.assertEqual(round(self.a1.awarded_gen()),8276)
        self.assertEqual(round(self.a2.awarded_gen()),11454)


class ScenarioMethodTests(TestCase):
    fixtures = ['test_data.json']

    def setUp(self):
        self.s = Scenario.objects.get(pk=119)

        self.a0 = self.s.auctionyear_set.get(year=2020)
        self.a1 = self.s.auctionyear_set.get(year=2021)
        self.a2 = self.s.auctionyear_set.get(year=2022)

        self.p0E = self.a0.pot_set.get(name="E")
        self.p0M = self.a0.pot_set.get(name="M")
        self.p1E = self.a1.pot_set.get(name="E")
        self.p1M = self.a1.pot_set.get(name="M")
        self.p2E = self.a2.pot_set.get(name="E")
        self.p2M = self.a2.pot_set.get(name="M")

        self.t0E = self.p0E.technology_set.get(name="OFW")
        self.t0wave = self.p0E.technology_set.get(name="WA")
        self.t0M = self.p0M.technology_set.get(name="ONW")

        self.t1E = self.p1E.technology_set.get(name="OFW")
        self.t1wave = self.p1E.technology_set.get(name="WA")
        self.t1M = self.p1M.technology_set.get(name="ONW")

        self.t2E = self.p2E.technology_set.get(name="OFW")
        self.t2wave = self.p2E.technology_set.get(name="WA")
        self.t2M = self.p2M.technology_set.get(name="ONW")



    def test_paid(self):
        self.assertEqual(round(self.s.paid(2021),2),426.71)
        self.assertEqual(round(self.s.paid(2022),2),927.18)

    def test_cum_gen(self):
        self.assertEqual(round(self.s.cum_gen(2021,2021)),8276)
        self.assertEqual(round(self.s.cum_gen(2021,2022)),19730)
        self.assertEqual(round(self.s.cum_gen(2020,2021)+428),14634)
        self.assertEqual(round(self.s.cum_gen(2020,2022)+428),26088)

    def test_paid_end_year(self):
        self.assertEqual(round(self.s.paid_end_year(),2),927.18)

    def test_cum_gen_end_year(self):
        self.assertEqual(round(self.s.cum_gen_end_year()+428),26088)

    def test_projects_df(self):
        self.assertEqual(self.s.projects_df().listed_year[0],2020)

    def test_techs_df(self):
        self.assertEqual(self.s.techs_df().listed_year[771],2020)

    def test_initial_technologies(self):
        value1 = self.s.initial_technologies()[1][0]['project_gen']
        value2 = self.s.initial_technologies()[1][1]['project_gen']
        value3 = self.s.initial_technologies()[1][2]['project_gen']
        self.assertTrue(set([value1, value2, value3]),set(['27.0, 27.0', '30.0', '30.0, 30.0', '832.0, 832.0, 832.0']))


class LcfViewsTestCase(TestCase):
    fixtures = ['test_data.json']

    def test_new(self):
        resp = self.client.get(reverse('scenario_new', kwargs={'pk': 119}))
        self.assertEqual(resp.status_code,200)
        self.assertTrue('scenarios' in resp.context)
        test_scenario = resp.context['scenarios'][0]
        self.assertEqual(test_scenario.auctionyear_set.count(), 3)
        #self.assertTrue('formset' in resp.context)
        self.assertTrue('scenario_form' in resp.context)
        self.assertEqual([scenario.pk for scenario in resp.context['scenarios']], [119])

    def test_detail(self):
        resp = self.client.get(reverse('scenario_detail',kwargs={'pk': 119}))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['scenario'].pk, 119)
        self.assertEqual(resp.context['scenario'].name, 'test1')
        #ensure non-existent scenario throws 404
        resp = self.client.get(reverse('scenario_detail',kwargs={'pk': 999}))
        self.assertEqual(resp.status_code, 404)

    """def test_good_scenario(self):
        #sanity check
        test_scenario = Scenario.objects.get(pk=119)
        a2020 = test_scenario.auctionyear_set.get(year=2020)
        self.assertEqual(a2020.gas_price, 85)
        self.assertEqual(Scenario.objects.count(), 1)
        resp = self.client.post(reverse('scenario_new',kwargs={'pk': 119}), {'name': 'test2', 'percent_emerging': 0.5, 'budget': 2})
        self.assertEqual(resp.status_code, 302)
        #don't know how to check location
        #self.assertEqual(resp['Location'],'scenario/2/')
        self.assertEqual(Scenario.objects.count(), 2)

    def test_bad_scenario(self):
        #Ensure a non-existent pk throws a not found
        resp = self.client.post(reverse('scenario_new',kwargs={'pk': 999}))
        self.assertEqual(resp.status_code, 404)

        #sanity check
        test_scenario = Scenario.objects.get(pk=119)
        a2020 = test_scenario.auctionyear_set.get(year=2020)
        self.assertEqual(a2020.gas_price, 85)

        #send no post data
        resp = self.client.post(reverse('scenario_new',kwargs={'pk': 119}))
        self.assertEqual(resp.status_code, 200)

        #send junk post data
        resp = self.client.post(reverse('scenario_new',kwargs={'pk': 119}),  {'foo': 'bar'})
        self.assertEqual(resp.status_code, 200)"""
        #self.assertEqual(resp.context['error_message'], "You didn't select a choice.")

    def test_valid_scenarioform(self):
        s = Scenario.objects.create(name="test_form", budget=4, percent_emerging=0.9, end_year=2022)
        data = {'name': s.name, 'budget': s.budget, 'percent_emerging': s.percent_emerging, 'end_year': s.end_year}
        form = ScenarioForm(data)
        self.assertTrue(form.is_valid())
        #s.delete()

    def test_invalid_scenarioform(self):
        data = {'name': "test_form", 'budget': "foo", 'percent_emerging': "bar"}
        form = ScenarioForm(data)
        self.assertFalse(form.is_valid())

    def test_valid_pricesform(self):
        data = {'wholesale_prices': "50 51 52", 'gas_prices': "60 61 62"}
        form = PricesForm(data)
        self.assertTrue(form.is_valid())

    def test_invalid_pricesform(self):
        data = {'foo': "50 51 52", 'bar': "60 61 62"}
        form = PricesForm(data)
        self.assertFalse(form.is_valid())
