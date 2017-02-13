import pandas as pd
import numpy as np
from pandas import DataFrame, Series
from lcf.models import Scenario, AuctionYear, Pot, Technology

s = Scenario.objects.get(name="default")
a = s.auctionyear_set.get(year=2021)
p = a.pot_set.get(name="E")
t = p.technology_set.get(name="OFW")

def go(budget):
    projects['funded'] = False
    spent = 0
    gen = 0
    for i in projects[projects.affordable == True].index:
        print('spent',spent)
        print('gen', gen)
        print('cfd_payout',projects.cfd_payout[i])
        print('budget',budget,'\n')
        if spent + projects.cfd_payout[i] < budget:
            projects['funded'][i] = True
            spent += projects[projects.funded == True]['cfd_payout'][i]
            gen += projects[projects.funded == True]['gen'][i]
        else:
            break
    print(projects)



old version:
    @lru_cache(maxsize=None)
    def run_auction(self):
        projects = self.concat_projects()
        spent = 0
        gen = 0
        for i in projects[projects.affordable == True].index:
            if spent + projects.cfd_payout[i] < self.budget():
                projects['funded'][i] = True
                spent += projects[projects.funded == True]['cfd_payout'][i]
                gen += projects[projects.funded == True]['gen'][i]
            else:
                break
        return {'cost': spent, 'gen': gen, 'projects': projects}


    def concat_projects(self):
        if self.technology_set.count() == 0:
            projects = DataFrame(columns=['levelised_cost', 'gen', 'technology', 'strike_price', 'clearing_price', 'affordable', 'funded', 'cfd_unit_cost', 'cfd_payout', 'cum_cost', 'cum_gen'])
        else:
            projects = pd.concat([t.projects() for t in self.technology_set.all()])
            projects['affordable'] = projects.levelised_cost <= projects.strike_price
            projects['cfd_unit_cost'] = projects.strike_price - self.auctionyear.wholesale_price # not accurate - all projects get paid out the highest LCOE, not the strike price
            projects['cfd_payout'] = projects.cfd_unit_cost * projects.gen
            projects['funded'] = False
            if self.auctionyear.scenario.rank_by_levelised_cost == True:
                projects = projects.sort_values('levelised_cost')
            else:
                projects = projects.sort_values('cfd_payout')
        return projects











    def __init__(self, *args, **kwargs):
        super(Technology, self).__init__(*args, **kwargs)
        self.tempvar = ''








pot_cost = 0
all_projects = DataFrame(columns=['levelised_cost', 'gen', 'technology', 'strike_price', 'clearing_price', 'affordable', 'funded'])
for t in self.technology_set.all():
    aff = t.projects()[projects.affordable == True]
    unaff = t.projects()[projects.affordable == False]
    for i in aff.index:
        funded_gen = sum(aff.gen[aff.funded==True])
        attempted_gen = funded_gen + aff.gen[i]
        attempted_clearing_price = lev[i]
        attemted_cost = attempted_gen * (attempted_clearing_price - self.auctionyear.wholesale_price)
        if attempted_cost < self.budget - other_tech_funded:
            aff.funded[i] = True
            actual_gen = attempted_gen
            aff.clearing_price[i] = attempted_clearing_price
            actual_cost = attempted_cost
    projects = pd.concat([aff,unaff])

    pot_cost += actual_cost
    pot_gen += actual_gen



    """Attempt at new calculations that use clearing price."""
    @lru_cache(maxsize=None)
    def run_auction(self):
        gen = 0
        cost = 0
        projects = DataFrame(columns=['levelised_cost', 'gen', 'technology', 'strike_price', 'clearing_price', 'affordable', 'funded'])
        for t in self.technology_set.all():
            aff = t.projects()[projects.affordable == True]
            unaff = t.projects()[projects.affordable == False]
            for i in aff.index:
                funded_gen = sum(aff.gen[aff.funded==True])
                attempted_gen = funded_gen + aff.gen[i]
                attempted_clearing_price = lev[i]
                attemted_cost = attempted_gen * (attempted_clearing_price - self.auctionyear.wholesale_price)
                if attempted_cost < self.budget - other_tech_funded:
                    aff.funded[i] = True
                    actual_gen = attempted_gen
                    aff.clearing_price[i] = attempted_clearing_price
                    actual_cost = attempted_cost
                else:
                    break
            projects = pd.concat([projects,aff,unaff])
            cost += actual_cost
            gen += actual_gen

        return {'cost': cost, 'gen': gen, 'projects': projects}


        #projects['affordable'] = projects.levelised_cost <= projects.strike_price
