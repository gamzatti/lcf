from django.test import TestCase
import pandas as pd
import numpy as np
from pandas import DataFrame, Series

from .models import Scenario, AuctionYear, Pot, Technology


class TechnologyMethodTests(TestCase):

    def setUp(self):
        self.s = Scenario.objects.create(name="test1",
                                    budget = 3.3,
                                    percent_emerging = 0.6)

        self.a0 = AuctionYear.objects.create(scenario=self.s,
                                        year=2020,
                                        wholesale_price = 48.5400340402009,
                                        gas_price = 85)
        self.a1 = AuctionYear.objects.create(scenario=self.s,
                                        year=2021,
                                        wholesale_price = 54.285722954952,
                                        gas_price = 87)
        self.a2 = AuctionYear.objects.create(scenario=self.s,
                                        year=2022,
                                        wholesale_price = 58.4749297906221,
                                        gas_price = 89)

        self.p0 = Pot.objects.create(name="E", auctionyear=self.a0)
        self.p0M = Pot.objects.create(name="M", auctionyear=self.a0)
        self.p1 = Pot.objects.create(name="E", auctionyear=self.a1)
        self.p1M = Pot.objects.create(name="M", auctionyear=self.a1)
        self.p2 = Pot.objects.create(name="E", auctionyear=self.a2)



        self.t0 = Technology.objects.create(name="OFW",
                                        pot=self.p0,
                                        min_levelised_cost = 71.3353908668731,
                                        max_levelised_cost = 103.034791021672,
                                        strike_price = 114.074615384615,
                                        load_factor = .42,
                                        project_gen = 832,
                                        max_deployment_cap = 1.9)
        self.t0wave = Technology.objects.create(name="WA",
                                        pot=self.p0,
                                        min_levelised_cost = 260.75,
                                        max_levelised_cost = 298,
                                        strike_price = 305,
                                        load_factor = .31,
                                        project_gen = 27,
                                        max_deployment_cap = 0.034)
        self.t1 = Technology.objects.create(name="OFW",
                                        pot=self.p1,
                                        min_levelised_cost = 71.1099729102167,
                                        max_levelised_cost = 101.917093653251,
                                        strike_price = 112.136153846154,
                                        load_factor = .434,
                                        project_gen = 832,
                                        max_deployment_cap = 1.9)
        self.t1wave = Technology.objects.create(name="WA",
                                        pot=self.p1,
                                        min_levelised_cost = 245.875,
                                        max_levelised_cost = 281,
                                        strike_price = 305,
                                        load_factor = .31,
                                        project_gen = 27,
                                        max_deployment_cap = 0.0032)
        self.t2 = Technology.objects.create(name="OFW",
                                        pot=self.p2,
                                        min_levelised_cost = 70.8845549535604,
                                        max_levelised_cost = 100.79939628483,
                                        strike_price = 110.197692307692,
                                        load_factor = .448,
                                        project_gen = 832,
                                        max_deployment_cap = 1.9)
        self.t2a = Technology.objects.create(name="OFW",
                                        pot=self.p2,
                                        min_levelised_cost = 70.8845549535604,
                                        max_levelised_cost = 100.79939628483,
                                        strike_price = 90,
                                        load_factor = .448,
                                        project_gen = 832,
                                        max_deployment_cap = 1.9)
        self.t0M = Technology.objects.create(name="ONW",
                                        pot=self.p0M,
                                        min_levelised_cost = 61,
                                        max_levelised_cost = 80,
                                        strike_price = 80,
                                        load_factor = 0.278125,
                                        project_gen = 30,
                                        max_deployment_cap = 0.73)
        self.t1M = Technology.objects.create(name="ONW",
                                        pot=self.p1M,
                                        min_levelised_cost = 61.4,
                                        max_levelised_cost = 81,
                                        strike_price = 80,
                                        load_factor = 0.2803125,
                                        project_gen = 30,
                                        max_deployment_cap = 0.73)

    def test_previous_year(self):
        self.assertEqual(self.t0.previous_year(),None)
        self.assertEqual(self.t1.previous_year(),self.t0)
        self.assertEqual(self.t2.previous_year(),self.t1)
        self.assertEqual(self.t0wave.previous_year(),None)
        self.assertEqual(self.t1wave.previous_year(),self.t0wave)

    def test_previous_gen(self):
        self.assertEqual(round(self.t0.previous_gen()),0)
        self.assertEqual(round(self.t1.previous_gen()),6990)
        self.assertEqual(round(self.t2.previous_gen()),14214)
        self.assertEqual(round(self.t0wave.previous_gen()),0)
        self.assertEqual(round(self.t1wave.previous_gen()),92)


    def test_this_year_gen(self):
        self.assertEqual(round(self.t0.this_year_gen()),6990)
        self.assertEqual(round(self.t1.this_year_gen()),7223)
        self.assertEqual(round(self.t2.this_year_gen()),7457)
        self.assertEqual(round(self.t0wave.this_year_gen()),92)
        self.assertEqual(round(self.t1wave.this_year_gen()),9)

    def test_new_generation_available(self):
        self.assertEqual(round(self.t0.new_generation_available()), 6990)
        self.assertEqual(round(self.t0M.new_generation_available()), 1779)
        self.assertEqual(round(self.t1.new_generation_available()), 14214)
        self.assertEqual(round(self.t1M.new_generation_available()), 3571)
        self.assertEqual(round(self.t2.new_generation_available()), 21670)
        self.assertEqual(round(self.t0wave.new_generation_available()), 92)
        self.assertEqual(round(self.t1wave.new_generation_available()), 101)

    def test_num_projects(self):
        self.assertEqual(self.t0.num_projects(), 8)
        self.assertEqual(self.t1.num_projects(), 17)
        self.assertEqual(self.t1M.num_projects(), 119)
        self.assertEqual(self.t2.num_projects(), 26)
        self.assertEqual(self.t0wave.num_projects(), 3)
        self.assertEqual(self.t1wave.num_projects(), 3)

    def test_levelised_cost_distribution_length(self):
        self.assertEqual(len(self.t0.levelised_cost_distribution()), 8)
        self.assertEqual(len(self.t1.levelised_cost_distribution()), 17)
        self.assertEqual(len(self.t2.levelised_cost_distribution()), 26)
        self.assertEqual(len(self.t0wave.levelised_cost_distribution()), 3)
        self.assertEqual(len(self.t1wave.levelised_cost_distribution()), 3)

    def test_levelised_cost_distribution_min_max(self):
        self.assertGreaterEqual(self.t0.levelised_cost_distribution().min(), self.t0.min_levelised_cost)
        self.assertGreaterEqual(self.t1.levelised_cost_distribution().min(), self.t1.min_levelised_cost)
        self.assertGreaterEqual(self.t0wave.levelised_cost_distribution().min(), self.t0wave.min_levelised_cost)
        self.assertLessEqual(self.t0.levelised_cost_distribution().max(), self.t0.max_levelised_cost)
        self.assertLessEqual(self.t2.levelised_cost_distribution().max(), self.t2.max_levelised_cost)
        self.assertLessEqual(self.t1wave.levelised_cost_distribution().max(), self.t1wave.max_levelised_cost)

    def test_levelised_cost(self):
        self.assertEqual(round(self.t0.projects().levelised_cost[3],2), 85.42)
        self.assertEqual(round(self.t1.projects().levelised_cost[3],2), 77.96)
        self.assertEqual(round(self.t2.projects().levelised_cost[3],2), 75.32)
        self.assertEqual(round(self.t0wave.projects().levelised_cost[2],2), 288.69)
        self.assertEqual(round(self.t1wave.projects().levelised_cost[2],2), 272.22)


    def test_projects_index(self):
        self.assertEqual(self.t0.projects_index()[0],"OFW1")
        self.assertEqual(self.t1.projects_index()[1],"OFW2")
        self.assertEqual(self.t2.projects_index()[2],"OFW3")
        self.assertEqual(self.t0wave.projects_index()[1],"WA2")

    def test_projects(self):
        self.assertEqual(round(self.t0.projects().gen[1]),832)
        self.assertEqual(round(self.t0.projects().gen.sum()), 832*8)
        self.assertEqual(round(self.t0wave.projects().gen.sum()), 27*3)
        self.assertEqual(round(self.t1.projects().gen[5]),832)
        self.assertEqual(round(self.t2.projects().gen[13]),832)
        self.assertEqual(self.t0.projects().technology[4],"OFW")
        self.assertEqual(round(self.t1.projects().strike_price[8],2),112.14)
        self.assertEqual(self.t0.projects().funded[4],"no")

    def test_projects_affordable(self):
        self.assertEqual(self.t2.projects().affordable[18],True)
        self.assertEqual(self.t1wave.projects().affordable[2],True)
        self.assertEqual(self.t2a.projects().strike_price[25],90)
        self.assertEqual(self.t2a.projects().affordable[25],False)
        self.assertEqual(self.t2a.min_levelised_cost, 70.8845549535604)


class PotMethodTests(TestCase):
    def setUp(self):
        self.s = Scenario.objects.create(name="test1",
                                    budget = 3.3,
                                    percent_emerging = 0.6)

        self.a0 = AuctionYear.objects.create(scenario=self.s,
                                        year=2020,
                                        wholesale_price = 48.5400340402009,
                                        gas_price = 85)
        self.a1 = AuctionYear.objects.create(scenario=self.s,
                                        year=2021,
                                        wholesale_price = 54.285722954952,
                                        gas_price = 87)
        self.a2 = AuctionYear.objects.create(scenario=self.s,
                                        year=2022,
                                        wholesale_price = 58.4749297906221,
                                        gas_price = 89)

        self.p0E = Pot.objects.create(name="E", auctionyear=self.a0)
        self.p1E = Pot.objects.create(name="E", auctionyear=self.a1)
        self.p2E = Pot.objects.create(name="E", auctionyear=self.a2)

        self.p0M = Pot.objects.create(name="M", auctionyear=self.a0)
        self.p1M = Pot.objects.create(name="M", auctionyear=self.a1)
        self.p2M = Pot.objects.create(name="M", auctionyear=self.a2)

        self.t0Ewave = Technology.objects.create(name="WA",
                                        pot=self.p0E,
                                        min_levelised_cost = 260.75,
                                        max_levelised_cost = 298,
                                        strike_price = 305,
                                        load_factor = .31,
                                        project_gen = 27,
                                        max_deployment_cap = 0.034)


        self.t0E = Technology.objects.create(name="OFW",
                                        pot=self.p0E,
                                        min_levelised_cost = 71.3353908668731,
                                        max_levelised_cost = 103.034791021672,
                                        strike_price = 114.074615384615,
                                        load_factor = .42,
                                        project_gen = 832,
                                        max_deployment_cap = 1.9)

        self.t1E = Technology.objects.create(name="OFW",
                                        pot=self.p1E,
                                        min_levelised_cost = 71.1099729102167,
                                        max_levelised_cost = 101.917093653251,
                                        strike_price = 112.136153846154,
                                        load_factor = .434,
                                        project_gen = 832,
                                        max_deployment_cap = 1.9)

        self.t1Ewave = Technology.objects.create(name="WA",
                                        pot=self.p1E,
                                        min_levelised_cost = 245.875,
                                        max_levelised_cost = 281,
                                        strike_price = 305,
                                        load_factor = .31,
                                        project_gen = 27,
                                        max_deployment_cap = 0.0032)

        self.t2E = Technology.objects.create(name="OFW",
                                        pot=self.p2E,
                                        min_levelised_cost = 70.8845549535604,
                                        max_levelised_cost = 100.79939628483,
                                        strike_price = 110.197692307692,
                                        load_factor = .448,
                                        project_gen = 832,
                                        max_deployment_cap = 1.9)

        self.t0M = Technology.objects.create(name="ONW",
                                        pot=self.p0M,
                                        min_levelised_cost = 61,
                                        max_levelised_cost = 80,
                                        strike_price = 80,
                                        load_factor = 0.278125,
                                        project_gen = 30,
                                        max_deployment_cap = 0.73)
        self.t1M = Technology.objects.create(name="ONW",
                                        pot=self.p1M,
                                        min_levelised_cost = 61.4,
                                        max_levelised_cost = 81,
                                        strike_price = 80,
                                        load_factor = 0.2803125,
                                        project_gen = 30,
                                        max_deployment_cap = 0.73)
        self.t2M = Technology.objects.create(name="ONW",
                                        pot=self.p2M,
                                        min_levelised_cost = 61.8,
                                        max_levelised_cost = 82,
                                        strike_price = 80,
                                        load_factor = 0.2825,
                                        project_gen = 30,
                                        max_deployment_cap = 0.73)

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
        #self.assertEqual(round(self.p2E.auctionyear.budget()), 893) #should work when I sort out 233 problem
        #self.assertEqual(round(self.p2E.budget()), 536)
        #self.assertEqual(round(self.p2M.budget()), 357)

    def test_previous_year(self):
        self.assertEqual(self.p1E.previous_year(),self.p0E)
        self.assertEqual(self.p2M.previous_year(),self.p1M)
        self.assertNotEqual(self.p1M.previous_year(),self.p1M)


    def test_combining_tech_projects(self):
        self.assertEqual(len(self.p0E.run_auction()['projects'].index), len(self.t0E.projects())+len(self.t0Ewave.projects()))
        self.assertEqual(len(self.p0M.run_auction()['projects'].index), len(self.t0M.projects()))
        self.assertEqual(len(self.p0E.run_auction()['projects'].index), 8+3)
        self.assertEqual(len(self.p0M.run_auction()['projects'].index), 59)
        self.assertEqual(len(self.p1E.run_auction()['projects'].index),17+3)
        self.assertEqual(len(self.p1M.run_auction()['projects'].index), 119)
        self.assertEqual(self.p0E.run_auction()['projects'].index[0], 'OFW1')
        self.assertEqual(self.p0E.run_auction()['projects'].index[8], 'WA1')
        self.assertEqual(len(self.p2E.run_auction()['projects'].index),26)
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

    def test_future_payouts(self):
#        self.assertEqual(self.p0E.future_payouts(),
#        self.assertEqual(self.p0M.future_payouts(),
        self.assertEqual(round(self.p1E.future_payouts(),2),385.05)
#        self.assertEqual(self.p1M.future_payouts(),



    def test_unspent(self):
        self.assertEqual(round(self.p0E.unspent()+self.p0M.unspent()),0)
        self.assertEqual(round(self.p1E.unspent()+self.p1M.unspent()),233) #passes here but fails below!
        #self.assertEqual(round(self.p2E.unspent()+self.p2M.unspent()),345) #should work when I sort out 893 problem

class AuctionYearMethodTests(TestCase):
    def setUp(self):
        self.s = Scenario.objects.create(name="test1",
                                    budget = 3.3,
                                    percent_emerging = 0.6)

        self.a0 = AuctionYear.objects.create(scenario=self.s,
                                        year=2020,
                                        wholesale_price = 48.5400340402009,
                                        gas_price = 85)
        self.a1 = AuctionYear.objects.create(scenario=self.s,
                                        year=2021,
                                        wholesale_price = 54.285722954952,
                                        gas_price = 87)
        self.a2 = AuctionYear.objects.create(scenario=self.s,
                                        year=2022,
                                        wholesale_price = 58.4749297906221,
                                        gas_price = 89)

        self.p0E = Pot.objects.create(name="E", auctionyear=self.a0)
        self.p1E = Pot.objects.create(name="E", auctionyear=self.a1)
        self.p2E = Pot.objects.create(name="E", auctionyear=self.a2)

        self.p0M = Pot.objects.create(name="M", auctionyear=self.a0)
        self.p1M = Pot.objects.create(name="M", auctionyear=self.a1)
        self.p2M = Pot.objects.create(name="M", auctionyear=self.a2)

        self.t0Ewave = Technology.objects.create(name="WA",
                                        pot=self.p0E,
                                        min_levelised_cost = 260.75,
                                        max_levelised_cost = 298,
                                        strike_price = 305,
                                        load_factor = .31,
                                        project_gen = 27,
                                        max_deployment_cap = 0.034)


        self.t0E = Technology.objects.create(name="OFW",
                                        pot=self.p0E,
                                        min_levelised_cost = 71.3353908668731,
                                        max_levelised_cost = 103.034791021672,
                                        strike_price = 114.074615384615,
                                        load_factor = .42,
                                        project_gen = 832,
                                        max_deployment_cap = 1.9)

        self.t1E = Technology.objects.create(name="OFW",
                                        pot=self.p1E,
                                        min_levelised_cost = 71.1099729102167,
                                        max_levelised_cost = 101.917093653251,
                                        strike_price = 112.136153846154,
                                        load_factor = .434,
                                        project_gen = 832,
                                        max_deployment_cap = 1.9)

        self.t1Ewave = Technology.objects.create(name="WA",
                                        pot=self.p1E,
                                        min_levelised_cost = 245.875,
                                        max_levelised_cost = 281,
                                        strike_price = 305,
                                        load_factor = .31,
                                        project_gen = 27,
                                        max_deployment_cap = 0.0032)

        self.t2E = Technology.objects.create(name="OFW",
                                        pot=self.p2E,
                                        min_levelised_cost = 70.8845549535604,
                                        max_levelised_cost = 100.79939628483,
                                        strike_price = 110.197692307692,
                                        load_factor = .448,
                                        project_gen = 832,
                                        max_deployment_cap = 1.9)

        self.t0M = Technology.objects.create(name="ONW",
                                        pot=self.p0M,
                                        min_levelised_cost = 61,
                                        max_levelised_cost = 80,
                                        strike_price = 80,
                                        load_factor = 0.278125,
                                        project_gen = 30,
                                        max_deployment_cap = 0.73)
        self.t1M = Technology.objects.create(name="ONW",
                                        pot=self.p1M,
                                        min_levelised_cost = 61.4,
                                        max_levelised_cost = 81,
                                        strike_price = 80,
                                        load_factor = 0.2803125,
                                        project_gen = 30,
                                        max_deployment_cap = 0.73)
        self.t2M = Technology.objects.create(name="ONW",
                                        pot=self.p2M,
                                        min_levelised_cost = 61.8,
                                        max_levelised_cost = 82,
                                        strike_price = 80,
                                        load_factor = 0.2825,
                                        project_gen = 30,
                                        max_deployment_cap = 0.73)

    def test_previous_year(self):
        self.assertEqual(self.a0.previous_year(),None)
        self.assertEqual(self.a1.previous_year(),self.a0)
        self.assertEqual(self.a2.previous_year(),self.a1)
        self.assertEqual(self.a2.previous_year().cost(), self.a1.cost())
        self.assertEqual(self.a1.unspent(),self.a2.previous_year().unspent())

    def test_starting_budget0(self):
        self.assertEqual(round(self.a0.starting_budget,2), 481.29)

    def test_previous_year_unspent0(self):
        self.assertEqual(round(self.a0.previous_year_unspent(),2),0)

    def budget0(self):
        self.assertEqual(round(self.a0.budget()),round(481.29+0)) #481.29

    def test_cost0(self):
        self.assertEqual(round(self.a0.cost()),round(272.62+55.68))#328.3

    def test_unspent0(self):
        self.assertEqual(round(self.a0.unspent()),round(481.3-328.3)) #153

    def test_starting_budget1(self):
        self.assertEqual(round(self.a1.starting_budget), 660)

    def test_previous_year_unspent1(self):
        self.assertEqual(round(self.a1.previous_year_unspent(),2),0)

    def budget1(self):
        self.assertEqual(round(self.a1.budget()),round(660+0)) #660

    def test_cost1(self):
        self.assertEqual(round(self.a1.cost()),round(385.05+41.66))#426.71

    def test_unspent1(self):
        self.assertEqual(round(self.a1.unspent()),round(660-426.71)) #233.29

    def test_starting_budget2(self):
        self.assertEqual(round(self.a2.starting_budget), 660)

    def test_previous_year_unspent2(self):
        self.assertEqual(round(self.a2.previous_year_unspent(),2),233.29)

    def budget2(self):
        self.assertEqual(round(self.a2.budget()),round(660+233.29)) #893.29

    def test_cost2(self):
        self.assertEqual(round(self.a2.cost()),round(516.4+31.64))#548.04

    def test_unspent2(self):
        self.assertEqual(round(self.a2.unspent()),round(893.29-548.04)) #345.25

class ScenarioMethodTests(TestCase):
    def setUp(self):
        self.s = Scenario.objects.create(name="test1",
                                    budget = 3.3,
                                    percent_emerging = 0.6)

        self.a0 = AuctionYear.objects.create(scenario=self.s,
                                        year=2020,
                                        wholesale_price = 48.5400340402009,
                                        gas_price = 85)
        self.a1 = AuctionYear.objects.create(scenario=self.s,
                                        year=2021,
                                        wholesale_price = 54.285722954952,
                                        gas_price = 87)
        self.a2 = AuctionYear.objects.create(scenario=self.s,
                                        year=2022,
                                        wholesale_price = 58.4749297906221,
                                        gas_price = 89)

        self.p0 = Pot.objects.create(name="E", auctionyear=self.a0)
        self.p0M = Pot.objects.create(name="M", auctionyear=self.a0)
        self.p1 = Pot.objects.create(name="E", auctionyear=self.a1)
        self.p1M = Pot.objects.create(name="M", auctionyear=self.a1)
        self.p2 = Pot.objects.create(name="E", auctionyear=self.a2)



        self.t0 = Technology.objects.create(name="OFW",
                                        pot=self.p0,
                                        min_levelised_cost = 71.3353908668731,
                                        max_levelised_cost = 103.034791021672,
                                        strike_price = 114.074615384615,
                                        load_factor = .42,
                                        project_gen = 832,
                                        max_deployment_cap = 1.9)
        self.t0wave = Technology.objects.create(name="WA",
                                        pot=self.p0,
                                        min_levelised_cost = 260.75,
                                        max_levelised_cost = 298,
                                        strike_price = 305,
                                        load_factor = .31,
                                        project_gen = 27,
                                        max_deployment_cap = 0.034)
        self.t1 = Technology.objects.create(name="OFW",
                                        pot=self.p1,
                                        min_levelised_cost = 71.1099729102167,
                                        max_levelised_cost = 101.917093653251,
                                        strike_price = 112.136153846154,
                                        load_factor = .434,
                                        project_gen = 832,
                                        max_deployment_cap = 1.9)
        self.t1wave = Technology.objects.create(name="WA",
                                        pot=self.p1,
                                        min_levelised_cost = 245.875,
                                        max_levelised_cost = 281,
                                        strike_price = 305,
                                        load_factor = .31,
                                        project_gen = 27,
                                        max_deployment_cap = 0.0032)
        self.t2 = Technology.objects.create(name="OFW",
                                        pot=self.p2,
                                        min_levelised_cost = 70.8845549535604,
                                        max_levelised_cost = 100.79939628483,
                                        strike_price = 110.197692307692,
                                        load_factor = .448,
                                        project_gen = 832,
                                        max_deployment_cap = 1.9)
        self.t2a = Technology.objects.create(name="OFW",
                                        pot=self.p2,
                                        min_levelised_cost = 70.8845549535604,
                                        max_levelised_cost = 100.79939628483,
                                        strike_price = 90,
                                        load_factor = .448,
                                        project_gen = 832,
                                        max_deployment_cap = 1.9)
        self.t0M = Technology.objects.create(name="ONW",
                                        pot=self.p0M,
                                        min_levelised_cost = 61,
                                        max_levelised_cost = 80,
                                        strike_price = 80,
                                        load_factor = 0.278125,
                                        project_gen = 30,
                                        max_deployment_cap = 0.73)
        self.t1M = Technology.objects.create(name="ONW",
                                        pot=self.p1M,
                                        min_levelised_cost = 61.4,
                                        max_levelised_cost = 81,
                                        strike_price = 80,
                                        load_factor = 0.2803125,
                                        project_gen = 30,
                                        max_deployment_cap = 0.73)

#    def test_auction_accumulation(self):
#        self.AssertEqual(self.s.)
        #I can produce the numbers in line 8 of the merit order sheets (MO and MOII). Now I need to produce line 6.
        #I need to take into account differnt wholesale prices
