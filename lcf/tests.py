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
        self.p1 = Pot.objects.create(name="E", auctionyear=self.a1)
        self.p2 = Pot.objects.create(name="E", auctionyear=self.a2)



        self.t0 = Technology.objects.create(name="OFW",
                                        pot=self.p0,
                                        min_levelised_cost = 71.3353908668731,
                                        max_levelised_cost = 103.034791021672,
                                        strike_price = 114.074615384615,
                                        load_factor = .42,
                                        project_gen = 832,
                                        max_deployment_cap = 1.9)
        self.t1 = Technology.objects.create(name="OFW",
                                        pot=self.p1,
                                        min_levelised_cost = 71.1099729102167,
                                        max_levelised_cost = 101.917093653251,
                                        strike_price = 112.136153846154,
                                        load_factor = .434,
                                        project_gen = 832,
                                        max_deployment_cap = 1.9)
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

    def test_previous_year(self):
        self.assertEqual(self.t0.previous_year(),None)
        self.assertEqual(self.t1.previous_year(),self.t0)
        self.assertEqual(self.t2.previous_year(),self.t1)

    def test_previous_gen(self):
        self.assertEqual(round(self.t0.previous_gen()),0)
        self.assertEqual(round(self.t1.previous_gen()),6990)
        self.assertEqual(round(self.t2.previous_gen()),14214)


    def test_this_year_gen(self):
        self.assertEqual(round(self.t0.this_year_gen()),6990)
        self.assertEqual(round(self.t1.this_year_gen()),7223)
        self.assertEqual(round(self.t2.this_year_gen()),7457)


    def test_new_generation_available(self):
        self.assertEqual(round(self.t0.new_generation_available()), 6990)
        self.assertEqual(round(self.t1.new_generation_available()), 14214)
        self.assertEqual(round(self.t2.new_generation_available()), 21670)


    def test_num_projects(self):
        self.assertEqual(self.t0.num_projects(), 8)
        self.assertEqual(self.t1.num_projects(), 17)
        self.assertEqual(self.t2.num_projects(), 26)

    def test_levelised_cost_distribution_length(self):
        self.assertEqual(len(self.t0.levelised_cost_distribution()), 8)
        self.assertEqual(len(self.t1.levelised_cost_distribution()), 17)
        self.assertEqual(len(self.t2.levelised_cost_distribution()), 26)

    def test_levelised_cost_distribution_min_max(self):
        self.assertGreaterEqual(self.t0.levelised_cost_distribution().min(), self.t0.min_levelised_cost)
        self.assertGreaterEqual(self.t1.levelised_cost_distribution().min(), self.t1.min_levelised_cost)
        self.assertLessEqual(self.t0.levelised_cost_distribution().max(), self.t0.max_levelised_cost)
        self.assertLessEqual(self.t2.levelised_cost_distribution().max(), self.t2.max_levelised_cost)

    def test_levelised_cost(self):
        self.assertEqual(round(self.t0.projects().levelised_cost[3],2), 85.42)
        self.assertEqual(round(self.t1.projects().levelised_cost[3],2), 77.96)
        self.assertEqual(round(self.t2.projects().levelised_cost[3],2), 75.32)


    def test_projects_index(self):
        self.assertEqual(self.t0.projects_index()[0],"OFW1")
        self.assertEqual(self.t1.projects_index()[1],"OFW2")
        self.assertEqual(self.t2.projects_index()[2],"OFW3")

    def test_projects(self):
        self.assertEqual(round(self.t0.projects().gen[1]),832)
        self.assertEqual(round(self.t0.projects().gen.sum()), 832*8)
        self.assertEqual(round(self.t1.projects().gen[5]),832)
        self.assertEqual(round(self.t2.projects().gen[13]),832)
        self.assertEqual(self.t0.projects().technology[4],"OFW")
        self.assertEqual(round(self.t1.projects().strike_price[8],2),112.14)
        self.assertEqual(self.t0.projects().funded[4],"no")

    def test_projects_affordable(self):
        self.assertEqual(self.t2.projects().affordable[18],True)
        self.assertEqual(self.t2a.projects().affordable[25],False)


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
        self.t2E = Technology.objects.create(name="OFW",
                                        pot=self.p2E,
                                        min_levelised_cost = 70.8845549535604,
                                        max_levelised_cost = 100.79939628483,
                                        strike_price = 110.197692307692,
                                        load_factor = .448,
                                        project_gen = 30,
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
                                        project_gen = 832,
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
        #can't test latter years until auction process is working correctly

    def test_previous_year(self):
        self.assertEqual(self.p1E.previous_year(),self.p0E)
        self.assertEqual(self.p2M.previous_year(),self.p1M)
        self.assertNotEqual(self.p1M.previous_year(),self.p1M)

    def test_previous_year_projects_index(self):
        self.assertTrue(self.p0E.previous_year_projects().empty)
        #self.assertEqual(len(self.p1E.previous_year_projects().index), len(self.p0E.run_auction()['projects'][self.p0E.run_auction()['projects'].funded=="this year"].index))

    def test_run_auction_first_year(self):
        self.assertEqual(self.p0E.run_auction()['ofw_gen'], 832 * 5)
        self.assertEqual(self.p0E.run_auction()['ofw_cost'], (114.074615384615 - 48.5400340402009) * 832/1000 * 5)
        self.assertEqual(self.p0E.run_auction()['projects']['funded']['OFW1'], "this year")
        self.assertEqual(self.p0E.run_auction()['projects']['funded']['OFW5'], "this year")
        self.assertEqual(self.p0E.run_auction()['projects']['funded']['OFW6'], "no")
        self.assertEqual(self.p0E.run_auction()['projects']['funded']['OFW7'], "no")
        self.assertEqual(self.p0E.run_auction()['projects']['funded']['OFW8'], "no")
        self.assertEqual(len(self.p0E.run_auction()['projects'].index),8)
