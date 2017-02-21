import pandas as pd
import numpy as np
from pandas import DataFrame, Series
from lcf.models import Scenario, AuctionYear, Pot, Technology
import timeit

s = Scenario.objects.get(name="default")
a = s.auctionyear_set.get(year=2021)
p = a.pot_set.get(name="E")
t = p.technology_set.get(name="OFW")

a0 = s.auctionyear_set.get(year=2020)
p0 = a0.pot_set.get(name="E")
t0 = p0.technology_set.get(name="OFW")


a2 = s.auctionyear_set.get(year=2022)
p2 = a2.pot_set.get(name="E")
t2 = p2.technology_set.get(name="OFW")


def mini_auction(p):
    gen = 0
    cost = 0
    projects = DataFrame(columns=['levelised_cost', 'gen', 'technology', 'strike_price', 'clearing_price', 'affordable', 'funded'])
    if p.auctionyear.year == 2020:
        previous_year_projects = DataFrame()
    else:
        previous_year = p.auctionyear.scenario.auctionyear_set.get(year = p.auctionyear.year - 1).pot_set.get(name=p.name)
        previous_year_projects = previous_year.projects()[(previous_year.projects().funded == "this year") | (previous_year.projects().funded == "previously")]
    return previous_year_projects



t.project_gen = t.project_gen_incorrect / 1000
t.cum_project_gen = t.cum_project_gen_incorrect / 1000
t.project_cap = cap(t.project_gen,t.load_factor)
t.years_supported = 2031 - t.pot.auctionyear.year
t.max_deployment_gen = gen(t.max_deployment_cap,t.load_factor)
t.num_projects = round(t.max_deployment_gen / t.cum_project_gen) # change to truncate?

def load_factor(cap_gw,gen_twh):
    return gen_twh / (cap_gw * 8.760)


def cap(gen_twh,load_factor):
    return gen_twh / (load_factor * 8.760)


def gen(cap_gw,load_factor):
    return cap_gw * load_factor * 8.760


t.min_levelised_cost = 71
t.max_levelised_cost = 81
t.strike_price = 76
t.load_factor = .45
t.project_gen_incorrect = 700
t.max_deployment_cap = 1.2
t.cum_project_gen_incorrect = 700
t.cum_project_gen_incorrect = 1400
t.cum_project_gen_incorrect = 2100


t2.previous_year = None if t2.pot.auctionyear.year == 2020 else t2.pot.auctionyear.scenario.auctionyear_set.get(year=t2.pot.auctionyear.year-1).pot_set.get(name=t2.pot.name).technology_set.get(name=t2.name)








Tests:
    def test_new_generation_available(self):
        self.assertEqual(self.t0.new_generation_available(), 6990)
        self.assertEqual(self.t1.new_generation_available(), 14214)
        self.assertEqual(self.t2.new_generation_available(), 21670)

    def test_num_projects(self):
        self.assertEqual(self.t0.num_projects(), 8)
        self.assertEqual(self.t1.num_projects(), 17)
        self.assertEqual(self.t2.num_projects(), 26)
