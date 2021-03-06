from django.test import TestCase
import pandas as pd
import numpy as np
from pandas import DataFrame, Series
from django.forms import modelformset_factory, formset_factory

from django.core.urlresolvers import reverse

from .models import Scenario, AuctionYear, Pot, Technology
from .forms import ScenarioForm, PricesForm, TechnologyStringForm
import math

class TechnologyMethodTests(TestCase):
    fixtures = ['tests/old/test_data.json']

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
        #self.assertEqual(self.t0E.projects().funded[4],"no")

    def test_projects_affordable(self):
        self.assertEqual(self.t2E.projects().affordable[18],True)
        self.assertEqual(self.t1wave.projects().affordable[2],True)
        self.assertEqual(self.t2Ea.projects().strike_price[25],90)
        self.assertEqual(self.t2Ea.projects().affordable[25],False)
        self.assertEqual(self.t2Ea.min_levelised_cost, 70.8845549535604)

    def test_get_field_values(self):
        self.assertEqual(self.t2E.get_field_values()['name'],'OFW')

class PotMethodTests(TestCase):
    fixtures = ['tests/old/test_data.json']

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

    def test_previous_year(self):
        self.assertEqual(self.p1E.previous_year(),self.p0E)
        self.assertEqual(self.p2M.previous_year(),self.p1M)
        self.assertNotEqual(self.p1M.previous_year(),self.p1M)


    def test_combining_tech_projects(self):
        self.assertEqual(len(self.p0E.projects().index), len(self.t0E.projects())+len(self.t0wave.projects()))
        self.assertEqual(len(self.p0M.projects().index), len(self.t0M.projects()))
        self.assertEqual(len(self.p0E.projects().index), 8+3)
        self.assertEqual(len(self.p0M.projects().index), 59)
        self.assertEqual(len(self.p1E.projects().index),17+3)
        self.assertEqual(len(self.p1M.projects().index), 119)
        self.assertEqual(self.p0E.projects().index[0], 'OFW1')
        self.assertEqual(self.p0E.projects().index[8], 'WA1')
        self.assertEqual(len(self.p2E.projects().index),30)
        self.assertEqual(len(self.p2M.projects().index), 179)

    def test_run_auction_first_year(self):
        self.assertEqual(len(self.p0E.projects().index),8+3)
        self.assertEqual(self.p0E.projects()['funded_this_year']['OFW1'], True)
        self.assertEqual(self.p0E.projects()['funded_this_year']['OFW5'], True)
        self.assertEqual(self.p0E.projects()['funded_this_year']['OFW6'], False)
        #self.assertEqual(self.p0E.run_auction()['tech_gen']['OFW'], 832 * 5)
        self.assertEqual(self.p0E.projects()['funded_this_year'].value_counts()[True],5)
        self.assertEqual(self.p0M.projects()['funded_this_year'].value_counts()[True],59)

    def test_previously_funded_projects_index(self):
        self.assertTrue(self.p0E.previously_funded_projects().empty)
        self.assertTrue(self.p0M.previously_funded_projects().empty)
        self.assertEqual(len(self.p1E.previously_funded_projects().index), len(self.p0E.projects()[self.p0E.projects().funded_this_year==True].index))
        self.assertEqual(len(self.p1E.previously_funded_projects().index), 5)
        self.assertEqual(self.p1E.previously_funded_projects()['funded_this_year']['OFW5'], True)
        self.assertNotIn(['OFW6'], list(self.p1E.previously_funded_projects().index))
        self.assertNotIn(['WA1'], list(self.p1E.previously_funded_projects().index))

    def test_run_auction_second_year(self):
        self.assertEqual(self.p1E.projects()['previously_funded'].value_counts()[True],5)
        self.assertEqual(self.p1M.projects()['previously_funded'].value_counts()[True],59)
        self.assertEqual(self.p1E.projects()['funded_this_year'].value_counts()[True],8)
        self.assertEqual(self.p1M.projects()['funded_this_year'].value_counts()[True],54)
        self.assertEqual(self.p1E.projects()['previously_funded']['OFW5'], True)
        self.assertEqual(self.p1E.projects()['funded_this_year']['OFW5'], False)
        self.assertEqual(self.p1E.projects()['funded_this_year']['OFW6'], True)
        self.assertEqual(self.p1E.projects()['previously_funded']['OFW6'], False)
        self.assertEqual(self.p1E.projects()['funded_this_year']['OFW14'], False)
        self.assertEqual(self.p1E.projects()['previously_funded']['OFW14'], False)
        self.assertEqual(self.p1E.projects()['funded_this_year']['WA1'], False)
        self.assertEqual(self.p1E.projects()['previously_funded']['WA1'], False)

    def test_run_auction_third_year(self):
        self.assertEqual(self.p2E.projects()['previously_funded'].value_counts()[True],5+8)
        self.assertEqual(self.p2M.projects()['previously_funded'].value_counts()[True],59+54)
        self.assertEqual(self.p2E.projects()['funded_this_year'].value_counts()[True],12)
        self.assertEqual(self.p2M.projects()['funded_this_year'].value_counts()[True],49)
        self.assertEqual(self.p2E.projects()['previously_funded']['OFW13'], True)
        self.assertEqual(self.p2E.projects()['funded_this_year']['OFW13'], False)
        self.assertEqual(self.p2E.projects()['funded_this_year']['OFW14'], True)
        self.assertEqual(self.p2E.projects()['previously_funded']['OFW14'], False)
        self.assertEqual(self.p2E.projects()['funded_this_year']['OFW26'], False)
        self.assertEqual(self.p2E.projects()['previously_funded']['OFW26'], False)


    def test_awarded_cost(self):

        p0E = Pot.objects.get(auctionyear__year=2020, auctionyear__scenario=119, name="E")
        p0M = Pot.objects.get(auctionyear__year=2020, auctionyear__scenario=119, name="M")

        p1E = Pot.objects.get(auctionyear__year=2021, auctionyear__scenario=119, name="E")
        p1M = Pot.objects.get(auctionyear__year=2021, auctionyear__scenario=119, name="M")

        p2E = Pot.objects.get(auctionyear__year=2022, auctionyear__scenario=119, name="E")
        p2M = Pot.objects.get(auctionyear__year=2022, auctionyear__scenario=119, name="M")

        self.assertEqual(round(p0E.awarded_cost(),2), 272.62)
        self.assertEqual(round(p0M.awarded_cost(),2), 55.68)
        self.assertEqual(round(p1E.awarded_cost(),2), 385.05)
        self.assertEqual(round(p1M.awarded_cost(),2), 41.66)
        self.assertEqual(round(p2E.awarded_cost(),2), 516.4)
        self.assertEqual(round(p2M.awarded_cost(),2), 31.64)


class PotMethodTests2(TestCase):
    fixtures = ['tests/old/test_data.json']

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

    def test_unspent(self):
        self.assertEqual(round(self.p0E.unspent()+self.p0M.unspent()),0)
        self.assertEqual(round(self.p1E.unspent()+self.p1M.unspent()),233)
        self.assertEqual(round(self.p2E.unspent()+self.p2M.unspent()),345)

class PotMethodTests3(TestCase):
    fixtures = ['tests/old/test_data.json']

    def test_awarded_gen(self):
        #p0E = Pot.objects.get(auctionyear__year=2020, auctionyear__scenario=119, name="E")
        #p0M = Pot.objects.get(auctionyear__year=2020, auctionyear__scenario=119, name="M")

        p1E = Pot.objects.get(auctionyear__year=2021, auctionyear__scenario=119, name="E")
        p1M = Pot.objects.get(auctionyear__year=2021, auctionyear__scenario=119, name="M")

        p2E = Pot.objects.get(auctionyear__year=2022, auctionyear__scenario=119, name="E")
        p2M = Pot.objects.get(auctionyear__year=2022, auctionyear__scenario=119, name="M")
        #self.assertEqual(round(p0E.awarded_gen(),3), 4.160)
        self.assertEqual(round(p1E.awarded_gen(),3), 6.656)
        self.assertEqual(round(p2E.awarded_gen(),3), 9.984)
        #self.assertEqual(round(p0M.awarded_gen(),3), 1.770)
        self.assertEqual(round(p1M.awarded_gen(),3), 1.620)
        self.assertEqual(round(p2M.awarded_gen(),3), 1.470)


class PotMethodTests4(TestCase):
    fixtures = ['tests/old/test_data.json']

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



class AuctionYearMethodTests(TestCase):
    fixtures = ['tests/old/test_data.json']

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
        self.assertEqual(self.a2.previous_year().awarded_from("total"), self.a1.awarded_from("total"))
        self.assertEqual(self.a1.unspent(),self.a2.previous_year().unspent())

    def test_years(self):
        self.assertQuerysetEqual(self.a1.cum_years(), ['<AuctionYear: 2021>'])
        self.assertQuerysetEqual(self.a2.cum_years(), ['<AuctionYear: 2021>', '<AuctionYear: 2022>'])

    def test_starting_budget(self):
        self.assertEqual(round(self.a0.starting_budget,2), 481.29)
        self.assertEqual(round(self.a1.starting_budget), 660)
        self.assertEqual(round(self.a2.starting_budget), 660)

    def budget(self):
        self.assertEqual(round(self.a0.budget()),round(481.29+0)) #481.29
        self.assertEqual(round(self.a1.budget()),round(660+0)) #660
        self.assertEqual(round(self.a2.budget()),round(660+233.29)) #893.29

    def test_awarded(self):
        self.assertEqual(round(self.a0.awarded_from("total")),round(272.62+55.68))#328.3
        self.assertEqual(round(self.a1.awarded_from("total")),round(385.05+41.66))#426.71
        self.assertEqual(round(self.a2.awarded_from("total")),round(516.4+31.64))#548.04



class AuctionYearMethodTests4(TestCase):
    fixtures = ['tests/old/test_data.json']

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


    def test_previous_year_unspent(self):
        self.assertEqual(round(self.a0.previous_year_unspent(),2),0)
        self.assertEqual(round(self.a1.previous_year_unspent(),2),0)
        self.assertEqual(round(self.a2.previous_year_unspent(),2),233.29)


    #def test_cum_owed_v(self):
        self.assertEqual(round(self.a0.cum_owed_v("wp"),2),round(self.a0.awarded_from("total"),2))
        self.assertEqual(self.a1.cum_owed_v("wp"),self.a1.awarded_from("total"))
        self.assertEqual(round(self.a2.cum_owed_v("wp"),2),round(self.a2.awarded_from("total") + self.a2.owed_v("wp",self.a1),2))
        self.assertEqual(round(self.a2.cum_owed_v("wp"),2),927.18)

    #def test_owed_v(self):
        self.assertEqual(round(self.a1.owed_v("wp",self.a0),2),286.17)
        self.assertEqual(round(self.a2.owed_v("wp",self.a1)),379)


class AuctionYearMethodTests5(TestCase):
    fixtures = ['tests/old/test_data.json']

    def setUp(self):
        self.s = Scenario.objects.get(pk=119)

        self.a0 = self.s.auctionyear_set.get(year=2020)
        self.a1 = self.s.auctionyear_set.get(year=2021)
        self.a2 = self.s.auctionyear_set.get(year=2022)

    def test_cum_awarded_gen(self):
        self.assertEqual(round(self.a1.cum_awarded_gen()+.428,3),14.634) #I can't remember why I was adding 428?!
        self.assertEqual(round(self.a2.cum_awarded_gen()+.428,3),26.088) #+428?

class AuctionYearMethodTests6(TestCase):
    fixtures = ['tests/old/test_data.json']

    def setUp(self):
        self.s = Scenario.objects.get(pk=119)

        self.a0 = self.s.auctionyear_set.get(year=2020)
        self.a1 = self.s.auctionyear_set.get(year=2021)
        self.a2 = self.s.auctionyear_set.get(year=2022)

    def test_cum_awarded_gen_with_excel_2020_gen_error(self):
        self.s.excel_2020_gen_error = False
        self.s.save()

        self.a1 = self.s.auctionyear_set.get(year=2021)
        self.a2 = self.s.auctionyear_set.get(year=2022)
        self.assertEqual(round(self.a1.cum_awarded_gen(),3),8.276)
        self.assertEqual(round(self.a2.cum_awarded_gen(),3),19.730)


class AuctionYearMethodTests2(TestCase):
    fixtures = ['tests/old/test_data.json']

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


    def test_awarded_gen(self):
        self.assertEqual(round(self.a0.awarded_gen(),3),5.930)
        self.assertEqual(round(self.a1.awarded_gen(),3),8.276)
        self.assertEqual(round(self.a2.awarded_gen(),3),11.454)




class AuctionYearMethodTests3(TestCase):
    fixtures = ['tests/old/test_data.json']

    def setUp(self):
        self.s = Scenario.objects.get(pk=119)
        self.a0 = self.s.auctionyear_set.get(year=2020)
        self.a1 = self.s.auctionyear_set.get(year=2021)
        self.a2 = self.s.auctionyear_set.get(year=2022)


    def test_unspent0(self):
        self.assertEqual(round(self.a0.unspent()),round(481.3-328.3)) #153
        self.assertEqual(round(self.a1.unspent()),round(660-426.71)) #233.29
        self.assertEqual(round(self.a2.unspent()),round(893.29-548.04)) #345.25



class ScenarioMethodTests(TestCase):
    fixtures = ['tests/old/test_data.json']

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




    def test_techs_df(self):
        self.assertEqual(self.s.techs_df().listed_year[771],2020)

    def test_technology_form_helper(self):
        value1 = self.s.technology_form_helper()[1][0]['project_gen']
        value2 = self.s.technology_form_helper()[1][1]['project_gen']
        value3 = self.s.technology_form_helper()[1][2]['project_gen']
        self.assertTrue(set([value1, value2, value3]),set(['27.0, 27.0', '30.0', '30.0, 30.0', '832.0, 832.0, 832.0']))

    def test_accounting_cost(self):
        years = [2020,2021,2022]
        paid = [328.3, 426.71, 927.18]
        #self.assertEqual(self.s.accounting_cost()['title'][0][0],'year')
        #self.assertEqual(self.s.accounting_cost()['title'][1][0],str(2021))
        #self.assertEqual(round(self.s.accounting_cost()['title'][1][1],2),0.43)
        #self.assertEqual(round(self.s.accounting_cost()['title'][2][1],2),0.93)



class ExcelCompareTests(TestCase):
    #fixtures = ['tests/old/no_nuclear_data.json']
    fixtures = ['tests/old/all_data.json']

    def setUp(self):
        pass



    def test_solar_num_projects(self):
        pv_set = Technology.objects.filter(name="PVLS", pot__auctionyear__scenario__name="no nuclear")
        mature_pot_set = Pot.objects.filter(name="M", auctionyear__year__gte=2021, auctionyear__scenario__name="no nuclear")
        p2 = mature_pot_set[1]


    def test_wave_num_projects(self):
        wave_set = Technology.objects.filter(name="WA", pot__auctionyear__scenario__name="no nuclear")
        self.assertEqual(wave_set[1].num_projects(),3)
        self.assertEqual(wave_set[2].num_projects(),4)
        self.assertEqual(wave_set[3].num_projects(),4)
        self.assertEqual(wave_set[4].num_projects(),4)
        self.assertEqual(wave_set[5].num_projects(),5)


    def test_tl_num_projects(self):
        tl_set = Technology.objects.filter(name="TL", pot__auctionyear__scenario__name="no nuclear")

        self.assertEqual(round(tl_set[1].new_generation_available()),2200)
        self.assertEqual(round(tl_set[2].new_generation_available()),2200)
        self.assertEqual(round(tl_set[3].new_generation_available()),2200)
        self.assertEqual(round(tl_set[4].new_generation_available()),2200)
        self.assertEqual(round(tl_set[5].new_generation_available()),4400)
        self.assertEqual(tl_set[1].num_projects(),1)
        self.assertEqual(tl_set[2].num_projects(),1)
        self.assertEqual(tl_set[3].num_projects(),1)
        self.assertEqual(tl_set[4].num_projects(),1)
        self.assertEqual(tl_set[5].num_projects(),2)

    def test_ts_num_projects(self):
        ts_set = Technology.objects.filter(name="TS", pot__auctionyear__scenario__name="no nuclear")
        self.assertEqual(ts_set[1].num_projects(),3)
        self.assertEqual(ts_set[2].num_projects(),4)
        self.assertEqual(ts_set[3].num_projects(),4)
        self.assertEqual(ts_set[4].num_projects(),5)
        self.assertEqual(ts_set[5].num_projects(),5)

    def test_alt_scenario(self):
        p5 = Pot.objects.filter(name="E", auctionyear__scenario__name="no nuclear v2")[5]



class ExclusionTests(TestCase):
    fixtures = ['tests/old/all_data_inc_exclusions.json']

    def setUp(self):
        self.s = Scenario.objects.get(name="excl ofw and pvls")

    def test_pot_tech_set(self):
        p = self.s.auctionyear_set.get(year=2021).pot_set.get(name="E")
        tech_set = p.tech_set()
        self.assertQuerysetEqual(tech_set, ["<Technology: (<AuctionYear: 2021>, 'E', 'TS')>",
                                           "<Technology: (<AuctionYear: 2021>, 'E', 'TL')>",
                                           "<Technology: (<AuctionYear: 2021>, 'E', 'WA')>"], ordered=False)
        self.assertEqual(tech_set.get(name="TS").min_levelised_cost,143.125)
        self.assertEqual(set(p.projects().technology.unique()),{'TS','TL','WA'})

class ExclusionTests2(TestCase):
    fixtures = ['tests/old/all_data_inc_exclusions.json']

    def setUp(self):
        self.s = Scenario.objects.get(name="excl ofw and pvls")

    def test_scenario_methods(self):
        a1 = self.s.auctionyear_set.get(year=2021)
        a2 = self.s.auctionyear_set.get(year=2022)
        a3 = self.s.auctionyear_set.get(year=2023)
        a4 = self.s.auctionyear_set.get(year=2024)
        a5 = self.s.auctionyear_set.get(year=2025)

        self.assertEqual(round(a1.awarded_gen(),3),6.580)
        self.assertEqual(round(a2.awarded_gen(),3),4.307)
        self.assertEqual(round(a3.awarded_gen(),3),4.050)
        #self.assertEqual(round(a4.awarded_gen(),3),14.010)
        #self.assertEqual(round(a5.awarded_gen(),3),16.037)





class RefactorTests(TestCase):
    fixtures = ['tests/old/all_data2.json']

    def setUp(self):
        self.s = Scenario.objects.get(pk=245)

    def test_technology_cost(self):
        e2 = Pot.objects.get(auctionyear__year=2022, name="E", auctionyear__scenario=self.s)
        e5 = Pot.objects.get(auctionyear__year=2025, name="E", auctionyear__scenario=self.s)

    def test_innovation_premium(self):
        a2 = AuctionYear.objects.get(year=2022, scenario=245)
        a2.innovation_premium()


    def test_tech_awarded_gen(self):
        pass
        """
        p2 = Pot.objects.get(name="E", auctionyear__year=2022, auctionyear__scenario=245)
        p3 = Pot.objects.get(name="E", auctionyear__year=2023, auctionyear__scenario=245)
        t2 = Technology.objects.get(name="OFW", pot=p2)
        t3 = Technology.objects.get(name="OFW", pot=p3)
        self.assertEqual(t2.awarded_gen,0)
        self.assertEqual(t3.awarded_gen,0)

        p2.run_auction()
        p3.run_auction()
        t2 = Technology.objects.get(name="OFW", pot=p2)
        t3 = Technology.objects.get(name="OFW", pot=p3)

        self.assertEqual(t2.awarded_gen,9.152)
        self.assertEqual(t3.awarded_gen,10.816)

        """

    def test_owed_v_wp(self):
        a3 = AuctionYear.objects.get(scenario=245,year=2023)
        a4 = AuctionYear.objects.get(scenario=245,year=2024)
        a5 = AuctionYear.objects.get(scenario=245,year=2025)
        a5.owed_v("wp",a5)

class LcfViewsTestCase(TestCase):
    fixtures = ['tests/old/test_data.json']

    def test_new(self):
        resp = self.client.get(reverse('scenario_new', kwargs={'pk': 119}))
        self.assertEqual(resp.status_code,200)
        self.assertTrue('scenarios' in resp.context)
        test_scenario = resp.context['scenarios'][0]
        self.assertEqual(test_scenario.auctionyear_set.count(), 3)
        #self.assertTrue('formset' in resp.context)
        self.assertTrue('scenario_form' in resp.context)
        self.assertEqual([scenario.pk for scenario in resp.context['scenarios']], [119])

    """def test_detail(self):
        resp = self.client.get(reverse('scenario_detail',kwargs={'pk': 119}))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['scenario'].pk, 119)
        self.assertEqual(resp.context['scenario'].name, 'test1')
        #ensure non-existent scenario throws 404
        resp = self.client.get(reverse('scenario_detail',kwargs={'pk': 999}))
        self.assertEqual(resp.status_code, 404)"""

    def test_good_post(self):
        #sanity check
        test_scenario = Scenario.objects.get(pk=119)
        a2020 = test_scenario.auctionyear_set.get(year=2020)
        self.assertEqual(a2020.gas_price, 85)
        self.assertEqual(Scenario.objects.count(), 1)
        post_data = {'name': 'test2',
                    'percent_emerging': 0.5,
                    'budget': 2,
                    'start_year1': 2020,
                    'end_year1': 2022,
                    'wholesale_prices': "50 51 52",
                    'gas_prices': "60 61 62",
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
        resp = self.client.post(reverse('scenario_new',kwargs={'pk': 119}), post_data)
        self.assertEqual(resp.status_code, 302)
        #don't know how to check location
        #max pk + 1?
        #self.assertEqual(resp['Location'],'scenario/2/')
        self.assertEqual(Scenario.objects.count(), 2)

    """def test_bad_post(self):
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
        self.assertEqual(resp.status_code, 200)
        #self.assertEqual(resp.context['error_message'], "You didn't select a choice.")"""

    def test_valid_scenarioform(self):
        s = Scenario.objects.create(name="test_form", budget=4, percent_emerging=0.9, start_year1= 2021, end_year1=2022)
        data = {'name': s.name, 'budget': s.budget, 'percent_emerging': s.percent_emerging, 'start_year1': s.start_year1, 'end_year1': s.end_year1, 'excel_sp_error': 'on'}
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


class NuclearTests(TestCase):
    fixtures = ['tests/old/nuclear_data.json']

    def test_nuclear_num_projects(self):
        nu_set = Technology.objects.filter(name="NU")
        self.assertEqual(nu_set[0].num_projects(),0)
        self.assertEqual(nu_set[1].num_projects(),0)
        self.assertEqual(nu_set[2].num_projects(),0)
        self.assertEqual(nu_set[3].num_projects(),0)
        self.assertEqual(nu_set[4].num_projects(),2)
        self.assertEqual(nu_set[5].num_projects(),2)


    def test_awarded(self):
        a3 = AuctionYear.objects.get(year=2023)
        a4 = AuctionYear.objects.get(year=2024)
        a5 = AuctionYear.objects.get(year=2025)
        p3e = a3.pot_set.get(name="E")
        p4e = a4.pot_set.get(name="E")
        self.assertEqual(round(a3.awarded_from("auction")),450)
        self.assertEqual(round(a4.awarded_from("auction")),621)
        self.assertEqual(round(a5.awarded_from("auction")),471)
        p5e = a5.pot_set.get(name="E")
        p5m = a5.pot_set.get(name="M")
        s = Scenario.objects.get(name="with nuclear")
        self.assertEqual(round(p5m.awarded_cost()),52)
        self.assertEqual(round(p5e.awarded_cost()),419)
        self.assertEqual(round(a4.awarded_from("total")),871)
        self.assertEqual(round(a5.awarded_from("total")),723)

class NuclearTests5(TestCase):
    fixtures = ['tests/old/nuclear_data.json']

    def test_sn_auction(self):
        sn_pot_set = Pot.objects.filter(name="SN")
        self.assertTrue(math.isnan(sn_pot_set[0].budget()))
        self.assertTrue(sn_pot_set[0].projects().empty)
        self.assertTrue(sn_pot_set[1].projects().empty)
        self.assertTrue(sn_pot_set[2].projects().empty)
        self.assertTrue(sn_pot_set[3].projects().empty)
        self.assertFalse(sn_pot_set[4].projects().empty)
        self.assertFalse(sn_pot_set[5].projects().empty)
        self.assertEqual(len(sn_pot_set[4].projects().index),2)
        self.assertEqual(len(sn_pot_set[5].projects().index),2)
        #self.assertEqual(sn_pot_set[4].summary_gen_by_tech().at['NU','Gen'],10)
        #self.assertEqual(sn_pot_set[5].summary_gen_by_tech().at['NU','Gen'],10)
        #self.assertEqual(sn_pot_set[4].summary_for_future()['strike_price']['NU'],90)
        #self.assertEqual(sn_pot_set[5].summary_for_future()['strike_price']['NU'],92.5)
        self.assertEqual(sn_pot_set[4].unspent(),0)
        self.assertEqual(round(sn_pot_set[4].awarded_cost(),2),250.31)#10*(90-64.9687482891174)
        self.assertEqual(round(sn_pot_set[5].awarded_cost(),2),252.34)#10*(92.5-67.2664653151834)

class NuclearTests4(TestCase):
    fixtures = ['tests/old/nuclear_data.json']


    def test_other_pots(self):
        a3 = AuctionYear.objects.get(year=2023)
        a4 = AuctionYear.objects.get(year=2024)
        a5 = AuctionYear.objects.get(year=2025)
        self.assertEqual(round(a3.pot_set.get(name="E").budget()),601)
        self.assertEqual(round(a3.pot_set.get(name="M").budget()),401)

        self.assertEqual(round(a4.pot_set.get(name="E").budget()),577)
        self.assertEqual(round(a4.pot_set.get(name="M").budget()),385)

        self.assertEqual(round(a5.pot_set.get(name="E").budget()),449)
        self.assertEqual(round(a5.pot_set.get(name="M").budget()),300)


class NuclearTests3(TestCase):
    fixtures = ['tests/old/nuclear_data.json']

    def test_unspent(self):
        a3 = AuctionYear.objects.get(year=2023)
        a4 = AuctionYear.objects.get(year=2024)
        a5 = AuctionYear.objects.get(year=2025)
        self.assertEqual(round(a3.unspent()),553)
        self.assertEqual(round(a4.unspent()),341)
        p3e = a3.pot_set.get(name="E")
        p4e = a4.pot_set.get(name="E")


class NuclearTests2(TestCase):
    fixtures = ['tests/old/nuclear_data.json']

    def test_paid(self):
        a3 = AuctionYear.objects.get(year=2023)
        a4 = AuctionYear.objects.get(year=2024)
        a5 = AuctionYear.objects.get(year=2025)
        s = Scenario.objects.get(name="with nuclear")
        self.assertEqual(round(a4.cum_owed_v("wp")/1000,3),1.989)

        self.assertEqual(round(a4.owed_v("wp",a3),2),381.55)
        self.assertEqual(round(a5.owed_v("wp",a3),2),340.58)
        self.assertEqual(round(a5.owed_v("wp",a4),1), 661.5)


        self.assertEqual(round(a5.cum_owed_v("wp")/1000,3),2.384)


class FITTests(TestCase):
    fixtures = ['tests/old/fit_data.json']

    def test_other_pots(self):
        a1 = AuctionYear.objects.get(year=2021)
        a2 = AuctionYear.objects.get(year=2022)
        a3 = AuctionYear.objects.get(year=2023)
        a4 = AuctionYear.objects.get(year=2024)
        a5 = AuctionYear.objects.get(year=2025)
        self.assertEqual(round(a1.budget()),571)

        e1 = a1.pot_set.get(name="E")
        m1 = a1.pot_set.get(name="M")
        self.assertEqual(round(a1.unspent()),281)
        #self.assertEqual(round(m1.unspent()),130)
        #self.assertEqual(round(e1.unspent()),15)

        self.assertEqual(round(a2.previous_year_unspent()),281)
        self.assertEqual(round(a1.budget()),571)
        self.assertEqual(round(a2.budget()),852)
        self.assertEqual(round(a3.budget()),1005)
        self.assertEqual(round(a4.budget()),844)
        self.assertEqual(round(a5.budget()),894)

    def test_paid(self):
        s = Scenario.objects.get(name="with nuclear and negawatts")
        #self.assertEqual(round(s.paid_end_year1()/1000,3),2.805)
        a1 = AuctionYear.objects.get(year=2021)
        a2 = AuctionYear.objects.get(year=2022)
        a3 = AuctionYear.objects.get(year=2023)
        a4 = AuctionYear.objects.get(year=2024)
        a5 = AuctionYear.objects.get(year=2025)


    def test_generation(self):
        s = Scenario.objects.get(name="with nuclear and negawatts")

class FITTests3(TestCase):
    fixtures = ['tests/old/fit_data.json']
    def test_spent_fit(self):
        a1 = AuctionYear.objects.get(year=2021)
        a2 = AuctionYear.objects.get(year=2022)
        a3 = AuctionYear.objects.get(year=2023)
        a4 = AuctionYear.objects.get(year=2024)
        a5 = AuctionYear.objects.get(year=2025)
        p1 = a1.pot_set.get(name="FIT")
        p2 = a2.pot_set.get(name="FIT")
        p3 = a3.pot_set.get(name="FIT")
        p4 = a4.pot_set.get(name="FIT")
        p5 = a5.pot_set.get(name="FIT")

        #for p in [p1,p2,p3,p4,p5]:
        #    p.run_auction()

        self.assertEqual(p1.awarded_cost(),89)
        self.assertEqual(p2.awarded_cost(),89)
        self.assertEqual(p3.awarded_cost(),89)
        self.assertEqual(p4.awarded_cost(),89)
        self.assertEqual(p5.awarded_cost(),89)


        t1 = p1.technology_set.get(name="NW")
        t2 = p2.technology_set.get(name="NW")
        t3 = p3.technology_set.get(name="NW")
        t4 = p4.technology_set.get(name="NW")
        t5 = p5.technology_set.get(name="NW")


class FITTests2(TestCase):
    fixtures = ['tests/old/fit_data.json']
    def test_owed(self):
        s = Scenario.objects.get(name="with nuclear and negawatts")
        #s.tidal_levelised_cost_distribution = True
        #s.save()
        a1 = AuctionYear.objects.get(year=2021)
        a2 = AuctionYear.objects.get(year=2022)
        a3 = AuctionYear.objects.get(year=2023)
        a4 = AuctionYear.objects.get(year=2024)
        a5 = AuctionYear.objects.get(year=2025)

        e5 = a5.pot_set.get(name="E")
        m5 = a5.pot_set.get(name="M")
        sn5 = a5.pot_set.get(name="SN")
        e5.run_auction()
        m5.run_auction()
        sn5.run_auction()

        for t in e5.tech_set():
            print(t.awarded_cost)

        print(a5.owed_v("wp",a5))
        self.assertEqual(round(a4.owed_v("wp",a3)),round(447.26+37.504+89))
        self.assertEqual(round(a5.owed_v("wp",a3)),round(401.44+31.77+89))
        self.assertEqual(round(a5.owed_v("wp",a4)),round(277.92+41.20+89+252.34))


        self.assertEqual(round(a3.cum_owed_v("wp")/1000,3),1.621)
        self.assertEqual(round(a4.cum_owed_v("wp")/1000,3),2.117)
        #tidal issue still not resolved!!!!!
        #self.assertEqual(round(a5.cum_owed_v("wp")/1000,3),2.805)
##Failing tests:

class GasCompareTests(TestCase):
    fixtures = ['tests/old/fit_data.json']

    def test_owed_v_gas(self):
        a1 = AuctionYear.objects.get(year=2021)
        self.assertEqual(round(a1.owed_v("gas",a1)/1000,3),0.266)
