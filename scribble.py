import pandas as pd
import numpy as np
from pandas import DataFrame, Series
from lcf.models import Scenario, AuctionYear, Pot, Technology

s = Scenario.objects.get(name="default")
a = s.auctionyear_set.get(year=2021)
p = a.pot_set.get(name="E")
t = p.technology_set.get(name="OFW")



new:
    @lru_cache(maxsize=None)
    def run_auction(self):
        gen = 0
        cost = 0
        projects = DataFrame(columns=['levelised_cost', 'gen', 'technology', 'strike_price', 'clearing_price', 'affordable', 'funded'])
        if self.auctionyear.year == 2020:
            previous_year_projects = DataFrame()
        else:
            previous_year = self.auctionyear.scenario.auctionyear_set.get(year = self.auctionyear.year - 1).pot_set.get(name=self.name)
            previous_year_projects = previous_year.projects()[(previous_year.projects().funded == "this year") or (previous_year.projects().funded == "previously")]
        for t in self.technology_set.all():
            t.create_projects()
            aff = t.projects[t.projects.affordable == True]
            unaff = t.projects[t.projects.affordable == False]
            actual_cost = 0
            for i in aff.index:
                if i in previous_year_projects.index:
                    aff.funded = "previously funded"
                else:
                    funded_gen = sum(aff.gen[aff.funded=="this year"])
                    attempted_gen = funded_gen + aff.gen[i]
                    attempted_clearing_price = aff.levelised_cost[i]
                    attempted_cost = attempted_gen * (attempted_clearing_price - self.auctionyear.wholesale_price)
                    if attempted_cost < self.budget() - cost:
                        aff.funded[i] = "this year"
                        actual_gen = attempted_gen
                        aff.clearing_price = attempted_clearing_price
                        actual_cost = attempted_cost
                    else:
                        break
            projects = pd.concat([projects,aff,unaff])
            cost += actual_cost
            gen += actual_gen

        return {'cost': cost, 'gen': gen, 'projects': projects}

old:
class Pot:
    def run_auction(self):
        gen = 0
        cost = 0
        projects = DataFrame(columns=['levelised_cost', 'gen', 'technology', 'strike_price', 'clearing_price', 'affordable', 'funded'])
        for t in self.technology_set.all():
            t.create_projects()
            aff = t.projects[t.projects.affordable == True]
            unaff = t.projects[t.projects.affordable == False]
            actual_cost = 0
            for i in aff.index:
                funded_gen = sum(aff.gen[aff.funded=="this year"])
                attempted_gen = funded_gen + aff.gen[i]
                attempted_clearing_price = aff.levelised_cost[i]
                attempted_cost = attempted_gen * (attempted_clearing_price - self.auctionyear.wholesale_price)
                if attempted_cost < self.budget() - cost:
                    aff.funded[i] = "this year"
                    actual_gen = attempted_gen
                    aff.clearing_price = attempted_clearing_price
                    actual_cost = attempted_cost
                else:
                    break
            projects = pd.concat([projects,aff,unaff])
            cost += actual_cost
            gen += actual_gen

        return {'cost': cost, 'gen': gen, 'projects': projects}
