from django.db import models
from django.utils import timezone
import pandas as pd
import numpy as np
from pandas import DataFrame, Series
from functools import lru_cache
import datetime
import inspect
import time
from .technology import Technology

class Pot(models.Model):
    POT_CHOICES = (
            ('SN', 'Separate negotiations'),
            ('FIT', 'Feed-in-tariff'),
            ('E', 'Emerging'),
            ('M', 'Mature'),
    )
    auctionyear = models.ForeignKey('lcf.auctionyear', default=232)
    name = models.CharField(max_length=3, choices=POT_CHOICES, default='E')
    auction_has_run = models.BooleanField(default=False)
    budget_result = models.FloatField(null=True, blank=True)
    awarded_cost_result = models.FloatField(null=True, blank=True)
    awarded_gen_result = models.FloatField(null=True, blank=True)
    auction_results = models.TextField(null=True,blank=True)
    auction_budget_result = models.FloatField(null=True, blank=True)

    def __str__(self):
        return str((self.auctionyear, self.name))

    def __init__(self, *args, **kwargs):
        super(Pot, self).__init__(*args, **kwargs)
        self._percent = None
        self.previously_funded_projects_results = None


    #helper methods
    def tech_set(self):
        return self.technology_set.filter(included=True)

    def period_pots_calc(self):
        if self.auctionyear.year == 2020:
            num = 0
            pots = [self]
        else:
            years = self.auctionyear.period()
            num = self.auctionyear.period_num()
            pots = Pot.objects.filter(name=self.name, auctionyear__in=years).order_by("auctionyear__year")
        return {'num': num, 'pots': pots}

    def period_pots(self):
        return self.period_pots_calc()['pots']

    def period_num(self):
        return self.period_pots_calc()['num']

    def cum_pots(self):
        if self.auctionyear.year == 2020:
            return [self]
        else:
            start_year = self.auctionyear.scenario.start_year1 if self.auctionyear.year <= self.auctionyear.scenario.end_year1 else self.auctionyear.scenario.start_year2
            cum_pots = Pot.objects.filter(auctionyear__scenario=self.auctionyear.scenario, name=self.name, auctionyear__year__range=(start_year, self.auctionyear.year)).order_by("auctionyear__year")
            return cum_pots


    #budget methods
    #@lru_cache(maxsize=None)
    def percent(self):
        if self._percent:
            return self._percent
        elif self.name == "E":
            self._percent = self.auctionyear.scenario.percent_emerging
            return self._percent
        elif self.name == "M":
            self._percent = 1 - self.auctionyear.scenario.percent_emerging
            return self._percent
        else:
            return 0

    #@lru_cache(maxsize=None)
    def budget(self):
        if self.budget_result != None:
            return self.budget_result
        else:
            if self.name == "M" or self.name == "E":
                result = self.auction_budget() * self.percent()
            elif self.name == "SN" or self.name == "FIT":
                result = np.nan
            self.budget_result = result
            self.save()
            return result

    #@lru_cache(maxsize=None)
    def auction_budget(self):
        if self.auction_budget_result:
            return self.auction_budget_result
        else:
            self.auction_budget_result = self.auctionyear.budget()
            self.save()
            if self.name == "E":
                sister_pot = Pot.objects.get(auctionyear=self.auctionyear,name="M")
            elif self.name == "M":
                sister_pot = Pot.objects.get(auctionyear=self.auctionyear,name="M")
            sister_pot.auction_budget_result = self.auctionyear.budget()
            sister_pot.save()
            return self.auction_budget_result



    #@lru_cache(maxsize=None)
    def unspent(self):
        if self.name == "SN" or self.name == "FIT":
            return 0
        if self.auctionyear.year == 2020:
            return 0
        else:
            return self.budget() - self.awarded_cost()

    #auction methods
    def previous_year(self):
        return self.auctionyear.scenario.auctionyear_set.get(year = self.auctionyear.year - 1).active_pots().get(name=self.name)

    @lru_cache(maxsize=None)
    def previously_funded_projects(self):
        if self.previously_funded_projects_results:
            return self.previously_funded_projects_results
        else:
            from .auctionyear import AuctionYear
            try:
                previously_funded_projects = self.previous_year().run_auction()[(self.previous_year().run_auction().funded_this_year == True) | (self.previous_year().run_auction().previously_funded == True)]
            except AuctionYear.objects.model.DoesNotExist:
                previously_funded_projects = DataFrame()
            return previously_funded_projects

    def projects(self):
        return self.run_auction()

    @lru_cache(maxsize=None)
    def run_auction(self):
        #print('called', self.name, self.auctionyear.year,'caller name:', inspect.stack()[1][3])
        if self.auction_has_run == True:
            print('decoding json')
            return pd.read_json(self.auction_results)
        else:
            print('running auction', self.name, self.auctionyear.year,'caller name:', inspect.stack()[1][3])
            gen = 0
            cost = 0
            budget = self.budget() ##slow
            previously_funded_projects = self.previously_funded_projects()
            projects = self.concat_projects() #less slow
            projects.sort_values(['strike_price', 'levelised_cost'],inplace=True)
            projects['previously_funded'] = np.where(projects.index.isin(previously_funded_projects.index),True,False)
            projects['eligible'] = (projects.previously_funded == False) & projects.affordable
            projects['difference'] = projects.strike_price if self.name == "FIT" else projects.strike_price - self.auctionyear.wholesale_price
            projects['cost'] = np.where(projects.eligible == True, projects.gen/1000 * projects.difference, 0)
            projects['attempted_cum_cost'] = np.cumsum(projects.cost)
            projects['funded_this_year'] = (projects.eligible) if self.name == "SN" or self.name == "FIT" else (projects.eligible) & (projects.attempted_cum_cost < budget)
            projects['attempted_project_gen'] = np.where(projects.eligible == True, projects.gen, 0)
            projects['attempted_cum_gen'] = np.cumsum(projects.attempted_project_gen)
            self.update_db(projects)
            return projects

    def concat_projects(self):
        res = pd.concat([t.projects() for t in self.tech_set().all()]) ##slow
        return res


    def update_db(self,projects):
        successful_projects = projects[(projects.funded_this_year == True)]
        for tech in self.tech_set().all():
            tech_projects = projects[(projects.funded_this_year == True) & (projects.technology == tech.name)]
            tech.awarded_gen = tech_projects.attempted_project_gen.sum()/1000 if pd.notnull(tech_projects.attempted_project_gen.sum()) else 0
            tech.awarded_cost = sum(tech_projects.cost)
            tech.save(update_fields=['awarded_cost', 'awarded_gen'])
        self.awarded_cost_result = sum(successful_projects.cost)
        self.awarded_gen_result = sum(successful_projects.attempted_project_gen)/1000
        self.auction_has_run = True
        self.auction_results = projects.to_json()
        self.save(update_fields=['auction_has_run', 'awarded_cost_result', 'awarded_gen_result', 'auction_results'])

    #summary methods
    #@lru_cache(maxsize=None)
    def awarded_cost(self):
        if self.awarded_cost_result != None:
            res = self.awarded_cost_result
            return res
        else:
            self.run_auction()
            res = self.awarded_cost_result
            return res


    #@lru_cache(maxsize=None)
    def awarded_gen(self):
        if self.awarded_gen_result:
            res = self.awarded_gen_result
            return res
        else:
            if self.auction_has_run == False:
                self.run_auction()
            res = self.awarded_gen_result
            return res

    @lru_cache(maxsize=None)
    def owed_v(self, comparison, previous_pot):
        di = {"gas": self.auctionyear.gas_price, "wp": self.auctionyear.wholesale_price, "absolute": 0}
        compare = di[comparison]
        if self.name == "FIT":
            compare = 0
        owed = 0
        if previous_pot.auction_has_run == False:
            previous_pot.run_auction()
        for t in previous_pot.tech_set().all():
            gen = t.awarded_gen
            strike_price = t.strike_price
            if self.auctionyear.scenario.excel_sp_error == True:
                #next 5 lines account for Angela's error
                if (self.name == "E") or (self.name == "SN"):
                    try:
                        strike_price = Technology.objects.get(name=t.name,pot=self).strike_price
                        #strike_price = self.auctionyear.active_pots().get(name=self.name).tech_set().get(name=t.name).strike_price
                    except:
                        break
            difference = strike_price - compare
            tech_owed = gen * difference
            owed += tech_owed
        return owed


    def nw_owed(self,previous_pot):
        if previous_pot.auction_has_run == False:
            previous_pot.run_auction()
        previous_t = Technology.objects.get(name="NW", pot=previous_pot)
        gen = previous_t.awarded_gen
        difference = previous_t.strike_price
        owed = gen * difference
        return owed

    #accumulating methods
    @lru_cache(maxsize=None)
    def cum_owed_v(self,comparison):
        return sum([self.owed_v(comparison, pot) for pot in self.cum_pots()])

    def nw_cum_owed(self):
        return sum([self.nw_owed(pot) for pot in self.cum_pots()])

    def cum_awarded_gen(self):
        extra2020 = 0
        if self.auctionyear.scenario.excel_2020_gen_error and self.name != "FIT" and self.period_num() == 1:
            pot2020 = self.auctionyear.scenario.auctionyear_set.get(year=2020).active_pots().get(name=self.name)
            #pot2020 = Pot.objects.get(auctionyear__scenario=self.auctionyear.scenario,auctionyear__year=2020,name=self.name) #which is faster?
            extra2020 = pot2020.awarded_gen()
        return sum([pot.awarded_gen() for pot in self.cum_pots()]) + extra2020
