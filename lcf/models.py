from django.db import models
from django.utils import timezone
import pandas as pd
import numpy as np
from pandas import DataFrame, Series
from functools import lru_cache


class Scenario(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True, verbose_name="Description (optional)")
    date = models.DateTimeField(default=timezone.now)
    budget = models.FloatField(default=3.3, verbose_name="Budget (£bn)")
    percent_emerging = models.FloatField(default=0.6)
    rank_by_levelised_cost = models.BooleanField(default=True)
    set_strike_price =  models.BooleanField(default=False, verbose_name="Generate strike price ourselves?")



    def __init__(self, *args, **kwargs):
        super(Scenario, self).__init__(*args, **kwargs)
        self.tempvar = "foo"

    def __str__(self):
        return self.name

    @lru_cache(maxsize=None)
    def cost(self):
        cost = 0
        for a in self.auctionyear_set.all():
            for p in a.pot_set.all():
                cost += p.cost()
        return round(cost,3)

    @lru_cache(maxsize=None)
    def cost_2020(self):
        cost = 0
        for a in self.auctionyear_set.filter(year__lte=2020):
            for p in a.pot_set.all():
                cost += p.cost()
        return round(cost,3)

    @lru_cache(maxsize=None)
    def cost_lcf2(self):
        cost = 0
        for a in self.auctionyear_set.filter(year__range=(2021,2025)):
            for p in a.pot_set.all():
                cost += p.cost()
        return round(cost,3)

    @lru_cache(maxsize=None)
    def cost_lcf3(self):
        cost = 0
        for a in self.auctionyear_set.filter(year__range=(2026,2030)):
            for p in a.pot_set.all():
                cost += p.cost()
        return round(cost,3)

    @lru_cache(maxsize=None)
    def gen(self):
        gen = 0
        for a in self.auctionyear_set.all():
            for p in a.pot_set.all():
                gen += p.gen()
        return round(gen,3)

class AuctionYear(models.Model):
    scenario = models.ForeignKey('lcf.scenario', default=1)#http://stackoverflow.com/questions/937954/how-do-you-specify-a-default-for-a-django-foreignkey-model-or-adminmodel-field
    year = models.IntegerField(default=2020)
    wholesale_price = models.IntegerField(default=53)
    gas_price = models.IntegerField(default=85)

    def __str__(self):
        return str(self.year)

    def __init__(self, *args, **kwargs):
        super(AuctionYear, self).__init__(*args, **kwargs)
        self.starting_budget = 481.29 if self.year == 2020 else self.scenario.budget / 5 * 1000
        self._budget = None
        self._unspent = None
        self._previous_year_unspent = None

    @lru_cache(maxsize=None)
    def budget(self):
        if self._budget:
            return self._budget
        else:
            self._budget = round(self.starting_budget + self.previous_year_unspent(),3)
            return self._budget

    @lru_cache(maxsize=None)
    def cost(self):
        combined = 0
        for pot in self.pot_set.all():
            combined += pot.cost()
        return combined

    @lru_cache(maxsize=None)
    def unspent(self):
        if self._unspent:
            return self._unspent
        else:
            self._unspent = self.budget() - self.cost()
            return self._unspent

    @lru_cache(maxsize=None)
    def previous_year_unspent(self):
        if self._previous_year_unspent:
            return self._previous_year_unspent
        elif self.year == 2020 or self.year == 2021:
            return 0
        else:
            previous_year = self.scenario.auctionyear_set.all().get(year=self.year-1)
            self._previous_year_unspent = previous_year.unspent()
            return self._previous_year_unspent



class Pot(models.Model):
    POT_CHOICES = (
            ('E', 'Emerging'),
            ('M', 'Mature'),
            ('NW', 'Negawatts'),
            ('SN', 'Separate negotiations'),
    )
    auctionyear = models.ForeignKey('lcf.auctionyear', default=232)
    name = models.CharField(max_length=1, choices=POT_CHOICES, default='E')

    def __str__(self):
        return str((self.auctionyear, self.name))

    def __init__(self, *args, **kwargs):
        super(Pot, self).__init__(*args, **kwargs)
        self._percent = None


    @lru_cache(maxsize=None)
    def budget(self):
        return round((self.auctionyear.budget() * self.percent()),3)

    @lru_cache(maxsize=None)
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

    @lru_cache(maxsize=None)
    def run_auction(self):
        gen = 0
        cost = 0
        projects = DataFrame(columns=['levelised_cost', 'gen', 'technology', 'strike_price', 'clearing_price', 'affordable', 'funded'])
        if self.auctionyear.year == 2020:
            previous_year_projects = DataFrame()
        else:
            previous_year = self.auctionyear.scenario.auctionyear_set.get(year = self.auctionyear.year - 1).pot_set.get(name=self.name)
            previous_year_projects = previous_year.projects()[(previous_year.projects().funded == "this year") | (previous_year.projects().funded == "previously funded")]
        for t in self.technology_set.all():
            aff = t.projects()[t.projects().affordable == True]
            unaff = t.projects()[t.projects().affordable == False]
            actual_cost = 0
            actual_gen = 0
            for i in aff.index:
                if i in previous_year_projects.index:
                    aff.funded = "previously funded"
                else:
                    funded_gen = sum(aff.gen[aff.funded=="this year"])
                    attempted_gen = funded_gen + aff.gen[i]
                    attempted_clearing_price = aff.levelised_cost[i] if self.auctionyear.scenario.set_strike_price == True else aff.strike_price[i]
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


    @lru_cache(maxsize=None)
    def cost(self):
        return round(self.run_auction()['cost'],3)

    @lru_cache(maxsize=None)
    def unspent(self):
        return round(self.budget() - self.cost(),3)

    @lru_cache(maxsize=None)
    def gen(self):
        return round(self.run_auction()['gen'],3)

    @lru_cache(maxsize=None)
    def funded_projects(self):
        return self.projects()[self.projects().funded == "this year"]

    @lru_cache(maxsize=None)
    def projects(self):
        return self.run_auction()['projects']





class Technology(models.Model):
    TECHNOLOGY_CHOICES = (
            ('OFW', 'Offshore wind'),
            ('ONW', 'Onshore wind'),
            ('NU', 'Nuclear'),
            ('TL', 'Tidal lagoon'),
            ('TS', 'Tidal stream'),
            ('WA', 'Wave'),
            ('PVLS', 'Solar PV'),
    )
    name = models.CharField(max_length=4, choices=TECHNOLOGY_CHOICES, default='OFW')
    pot = models.ForeignKey('lcf.pot', default='E')
    min_levelised_cost = models.FloatField(default=100)
    max_levelised_cost = models.FloatField(default=100)
    strike_price = models.FloatField(default=100)
    load_factor = models.FloatField(default=0.5)
    project_gen = models.FloatField(default=100, verbose_name="Average project generation") #"Average project pa (GWh)"
    max_deployment_cap = models.FloatField(default=100)



    def __init__(self, *args, **kwargs):
        super(Technology, self).__init__(*args, **kwargs)

    def __str__(self):
        return str((self.pot.auctionyear,self.pot.name,self.name))


    @lru_cache(maxsize=None)
    def previous_year(self):
        if self.pot.auctionyear.year == 2020:
            return None
        else:
            previous_year = self.pot.auctionyear.year-1
            previous_auctionyear = self.pot.auctionyear.scenario.auctionyear_set.get(year=previous_year)
            previous_pot = previous_auctionyear.pot_set.get(name=self.pot.name)
            previous_tech = previous_pot.technology_set.get(name=self.name)
            return previous_tech

    @lru_cache(maxsize=None)
    def this_year_gen(self):
        return self.max_deployment_cap * self.load_factor * 8.760 * 1000

    def previous_gen(self):
        if self.pot.auctionyear.year == 2020:
            return 0
        else:
            return self.previous_year().new_generation_available()


    @lru_cache(maxsize=None)
    def new_generation_available(self):
        return self.previous_gen() + self.this_year_gen()


    @lru_cache(maxsize=None)
    def num_projects(self):
        return round(self.new_generation_available() / self.project_gen)


    @lru_cache(maxsize=None)
    def levelised_cost_distribution(self):
        return Series(np.linspace(self.min_levelised_cost,self.max_levelised_cost,self.num_projects()+2)[1:-1],name="levelised_cost")

    def projects(self):
        dep = self.distribute_levelised_costs()
        gen = Series(np.repeat(self.new_generation_available(),len(dep)),name='gen')
        projects = pd.concat([dep,gen], axis=1)
        projects.index = [ self.name + str(i + 1) for i in range(len(dep)) ]
        projects['technology'] = self.name
        projects['strike_price'] = self.strike_price
        projects['clearing_price'] = np.nan
        projects['affordable'] = projects.levelised_cost <= projects.strike_price
        projects['funded'] = 'no'
        #self.projects = projects
        return projects



class StoredProject(models.Model):
    technology = models.ForeignKey('lcf.Technology', blank=True, null=True)
    levelised_cost = models.FloatField(default=100)
    affordable = models.BooleanField(default=False)
    successful = models.BooleanField(default=False)

    def __str__(self):
        return str((self.technology.pot.auctionyear, self.technology.name, str(self.levelised_cost), self.affordable, self.successful))
