import pandas as pd
import numpy as np
from pandas import DataFrame, Series
from lcf.models import Scenario, AuctionYear, Pot, Technology

s = Scenario.objects.get(name="default")
a = s.auctionyear_set.get(year=2021)
p = a.pot_set.get(name="E")
t = p.technology_set.get(name="OFW")




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
                funded_gen = sum(aff.gen[aff.funded==True])
                attempted_gen = funded_gen + aff.gen[i]
                attempted_clearing_price = aff.levelised_cost[i]
                attempted_cost = attempted_gen * (attempted_clearing_price - self.auctionyear.wholesale_price)
                if attempted_cost < self.budget() - cost:
                    aff.funded[i] = True
                    actual_gen = attempted_gen
                    aff.clearing_price = attempted_clearing_price
                    actual_cost = attempted_cost
                else:
                    break
            projects = pd.concat([projects,aff,unaff])
            cost += actual_cost
            gen += actual_gen

        return {'cost': cost, 'gen': gen, 'projects': projects}
