from django.db import models
from django.utils import timezone
import pandas as pd
import numpy as np
from pandas import DataFrame, Series
from functools import lru_cache
import datetime


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

    def __str__(self):
        return str((self.auctionyear, self.name))

    def __init__(self, *args, **kwargs):
        super(Pot, self).__init__(*args, **kwargs)
        self._percent = None

    #@lru_cache(maxsize=None)
    def budget(self):
        if self.name == "M" or self.name == "E":
            return (self.auctionyear.budget() * self.percent())
        elif self.name == "SN" or self.name == "FIT":
            return np.nan

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

    def previous_year(self):
        return self.auctionyear.scenario.auctionyear_set.get(year = self.auctionyear.year - 1).active_pots().get(name=self.name)

    def previously_funded_projects(self):
        if self.auctionyear.year == 2020:
            previously_funded_projects = DataFrame()
        else:
            previously_funded_projects = self.previous_year().projects()[(self.previous_year().projects().funded_this_year == True) | (self.previous_year().projects().previously_funded == True)]
        return previously_funded_projects


    @lru_cache(maxsize=None)
    def run_auction(self):
        print('running auction', self.name, self.auctionyear.year)
        gen = 0
        cost = 0
        tech_cost = {}
        tech_gen = {}
        previously_funded_projects = self.previously_funded_projects()
        projects = pd.concat([t.projects() for t in self.tech_set().all()])
        projects.sort_values(['strike_price', 'levelised_cost'],inplace=True)
        projects['previously_funded'] = np.where(projects.index.isin(previously_funded_projects.index),True,False)
        projects['eligible'] = (projects.previously_funded == False) & projects.affordable

        projects['difference'] = projects.strike_price - self.auctionyear.wholesale_price
        if self.name == "FIT":
            projects['difference'] = projects.strike_price

        projects['cost'] = np.where(projects.eligible == True, projects.gen/1000 * projects.difference, 0)

        projects['attempted_cum_cost'] = np.cumsum(projects.cost)
        if self.name == "SN" or self.name == "FIT":
            projects['funded_this_year'] = (projects.eligible)
        else:
            projects['funded_this_year'] = (projects.eligible) & (projects.attempted_cum_cost < self.budget())

        projects['attempted_project_gen'] = np.where(projects.eligible == True, projects.gen, 0)
        projects['attempted_cum_gen'] = np.cumsum(projects.attempted_project_gen)
        if projects[projects.funded_this_year].empty:
            cost = 0
            gen = 0
        else:
            cost = projects[projects.funded_this_year==True].attempted_cum_cost.max()
            gen = projects[projects.funded_this_year==True].attempted_cum_gen.max()

        self.update(projects)

        return {'cost': cost, 'gen': gen, 'projects': projects}

    def update(self,projects):
        for tech in self.tech_set().all():
            tech_projects = projects[(projects.funded_this_year == True) & (projects.technology == tech.name)]
            #tech.awarded_gen = 0
            #print(projects)
            tech.awarded_gen = tech_projects.attempted_project_gen.sum()/1000 if pd.notnull(tech_projects.attempted_project_gen.sum()) else 0

            tech.awarded_cost = sum(tech_projects.cost)
            tech.save(update_fields=['awarded_cost', 'awarded_gen'])
            self.auction_has_run = True
            self.save(update_fields=['auction_has_run'])

    #@lru_cache(maxsize=None)
    def awarded_cost(self):
        if self.auction_has_run == False:
            self.run_auction()
        return sum(t.awarded_cost for t in self.tech_set())

    #@lru_cache(maxsize=None)
    def unspent(self):
        if self.name == "SN" or self.name == "FIT":
            return 0
        if self.auctionyear.year == 2020:
            return 0
        else:
            return self.budget() - self.awarded_cost()

    #@lru_cache(maxsize=None)
    def awarded_gen(self):
        if self.auction_has_run == False:
            self.run_auction()
        return sum(t.awarded_gen for t in self.tech_set())


    def cum_awarded_gen(self):
        extra2020 = 0
        if self.auctionyear.scenario.excel_2020_gen_error and self.name != "FIT":
            pot2020 = self.auctionyear.scenario.auctionyear_set.get(year=2020).active_pots().get(name=self.name)
            #pot2020 = Pot.objects.get(auctionyear__scenario=self.auctionyear.scenario,auctionyear__year=2020,name=self.name) #which is faster?
            extra2020 = pot2020.awarded_gen()
        return sum([year.awarded_gen() for year in self.years()]) + extra2020

    def years(self):
        if self.auctionyear.year == 2020:
            return [self]
        else:
            years = Pot.objects.filter(auctionyear__scenario=self.auctionyear.scenario, name=self.name, auctionyear__year__range=(self.auctionyear.scenario.start_year, self.auctionyear.year)).order_by("auctionyear__year")
            return(years)

    #@lru_cache(maxsize=None)
    def funded_projects(self):
        return self.projects()[self.projects().funded == "this year"]

    @lru_cache(maxsize=None)
    def projects(self):
        return self.run_auction()['projects']

    def tech_set(self):
        return self.technology_set.filter(included=True)

    def nw_owed(self,previous_pot):
        if previous_pot.auction_has_run == False:
            previous_pot.run_auction()
        previous_t = Technology.objects.get(name="NW", pot=previous_pot)
        gen = previous_t.awarded_gen
        difference = previous_t.strike_price
        owed = gen * difference
        return owed
