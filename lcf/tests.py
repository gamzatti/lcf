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
                                        wholesale_price = 61,
                                        gas_price = 58)
        self.a1 = AuctionYear.objects.create(scenario=self.s,
                                        year=2021,
                                        wholesale_price = 61,
                                        gas_price = 58)
        self.a2 = AuctionYear.objects.create(scenario=self.s,
                                        year=2022,
                                        wholesale_price = 61,
                                        gas_price = 58)

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
        self.assertEqual(len(self.t0.levelised_cost_distribution()), self.t0.num_projects())
        self.assertEqual(len(self.t1.levelised_cost_distribution()), self.t1.num_projects())
        self.assertEqual(len(self.t2.levelised_cost_distribution()), self.t2.num_projects())

    def test_levelised_cost_distribution_min_max(self):
        self.assertEqual(self.t0.levelised_cost_distribution().min() >= self.t0.min_levelised_cost)
        self.assertEqual(self.t0.levelised_cost_distribution().max() <= self.t0.max_levelised_cost)
