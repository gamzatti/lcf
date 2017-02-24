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
    start_year = models.IntegerField(default=2021)
    end_year = models.IntegerField(default=2025)


    def __init__(self, *args, **kwargs):
        super(Scenario, self).__init__(*args, **kwargs)
        self.tempvar = "foo"

    def __str__(self):
        return self.name

    #@lru_cache(maxsize=None)
    def cost(self):
        cost = 0
        for a in self.auctionyear_set.all():
            for p in a.pot_set.all():
                cost += p.cost()
        return cost

    #@lru_cache(maxsize=None)
    def cost_2020(self):
        cost = 0
        for a in self.auctionyear_set.filter(year__lte=2020):
            for p in a.pot_set.all():
                cost += p.cost()
        return cost

    #@lru_cache(maxsize=None)
    def cost_lcf2(self):
        cost = 0
        for a in self.auctionyear_set.filter(year__range=(2021,2025)):
            for p in a.pot_set.all():
                cost += p.cost()
        return cost

    #@lru_cache(maxsize=None)
    def cost_lcf3(self):
        cost = 0
        for a in self.auctionyear_set.filter(year__range=(2026,2030)):
            for p in a.pot_set.all():
                cost += p.cost()
        return cost

    #@lru_cache(maxsize=None)
    def gen(self):
        gen = 0
        for a in self.auctionyear_set.all():
            for p in a.pot_set.all():
                gen += p.gen()
        return gen

class AuctionYear(models.Model):
    scenario = models.ForeignKey('lcf.scenario', default=1)#http://stackoverflow.com/questions/937954/how-do-you-specify-a-default-for-a-django-foreignkey-model-or-adminmodel-field
    year = models.IntegerField(default=2020)
    wholesale_price = models.FloatField(default=53)
    gas_price = models.FloatField(default=85)

    def __str__(self):
        return str(self.year)

    def __init__(self, *args, **kwargs):
        super(AuctionYear, self).__init__(*args, **kwargs)
        self.starting_budget = 481.29 if self.year == 2020 else self.scenario.budget / 5 * 1000
        self._budget = None
        self._unspent = None
        self._previous_year_unspent = None

    #@lru_cache(maxsize=None)
    def budget(self):
        if self._budget:
            return self._budget
        else:
            self._budget = self.starting_budget + self.previous_year_unspent()
            return self._budget

    #@lru_cache(maxsize=None)
    def awarded(self):
        combined = 0
        for pot in self.pot_set.all():
            combined += pot.cost()
            #print("Auction year 'cost' method", combined)
        return combined

    #@lru_cache(maxsize=None)
    def unspent(self):
        if self._unspent:
            return self._unspent
        else:
            self._unspent = self.budget() - self.awarded()
            #print("Auction year 'unspent' method run on previous year", self._unspent)

            return self._unspent


    def previous_year(self):
        if self.year == 2020:
            return None
        return self.scenario.auctionyear_set.get(year=self.year-1)

    #@lru_cache(maxsize=None)
    def previous_year_unspent(self):
        if self._previous_year_unspent:
            return self._previous_year_unspent
        elif self.year == 2020 or self.year == 2021:
            return 0
        else:
            previous_year = self.previous_year()
            #print("Previous_year.unspent()",)
            self._previous_year_unspent = previous_year.unspent()
            #print("Auction year 'previous_year_unspent' method,",previous_year.unspent())
            #return self._previous_year_unspent
            return previous_year.unspent()

    def previous_years(self):
        if self.year == 2020:
            return None
        else:
            #print(type(self.scenario.auctionyear_set.filter(year__lt=self.year)))
            return self.scenario.auctionyear_set.filter(year__range=(self.scenario.start_year,self.year-1)).order_by('year')


    def paid(self):
        if self.year == 2020:
            return self.awarded()
        else:
            return self.awarded() + sum([self.owed(previous_year) for previous_year in self.previous_years()])

    def owed(self, previous_year):
        owed = {}
#        print('\n\n..............\n\npaying out year:', self.year)
#        print('year awarded:', previous_year)
        for pot in previous_year.pot_set.all():
            owed[pot.name] = 0
            data = pot.future_payouts()
            for t in pot.technology_set.all():
                gen = data['gen'][t.name]
                strike_price = data['strike_price'][t.name]
                #next 5 lines account for Angela's error
                if (pot.name == "E"):
                    try:
                        strike_price = self.pot_set.get(name=pot.name).technology_set.get(name=t.name).strike_price
                    except:
                        break
                difference = strike_price - self.wholesale_price
                tech_owed = gen * difference
#                print('\n\n', t.name,'generation', gen, '\nstrike_price', strike_price, '\nwholesale_price', self.wholesale_price, '\ntotal owed',tech_owed)
                owed[pot.name] += tech_owed
                #print(owed)
        owed = sum(owed.values())
        return owed


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

    #@lru_cache(maxsize=None)
    def budget(self):
        return (self.auctionyear.budget() * self.percent())

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
        return self.auctionyear.scenario.auctionyear_set.get(year = self.auctionyear.year - 1).pot_set.get(name=self.name)

    def previously_funded_projects(self):
        if self.auctionyear.year == 2020:
            previously_funded_projects = DataFrame()
        else:
            previously_funded_projects = self.previous_year().projects()[(self.previous_year().projects().funded_this_year == True) | (self.previous_year().projects().previously_funded == True)]
        return previously_funded_projects


    @lru_cache(maxsize=None)
    def run_auction(self):
        gen = 0
        cost = 0
        tech_cost = {}
        tech_gen = {}
        previously_funded_projects = self.previously_funded_projects()
        projects = pd.concat([t.projects() for t in self.technology_set.all()])
        projects.sort_values('levelised_cost',inplace=True)
        projects['previously_funded'] = np.where(projects.index.isin(previously_funded_projects.index),True,False)
        projects['eligible'] = (projects.previously_funded == False) & projects.affordable

        projects['difference'] = projects.strike_price - self.auctionyear.wholesale_price
        projects['cost'] = np.where(projects.eligible == True, projects.gen/1000 * projects.difference, 0)

        projects['attempted_cum_cost'] = np.cumsum(projects.cost)
        projects['funded_this_year'] = (projects.eligible) & (projects.attempted_cum_cost < self.budget())
        projects['attempted_project_gen'] = np.where(projects.eligible == True, projects.gen, 0)
        projects['attempted_cum_gen'] = np.cumsum(projects.attempted_project_gen)
        cost = projects[projects.funded_this_year==True].attempted_cum_cost.max()
        gen = projects[projects.funded_this_year==True].attempted_cum_gen.max()

        #if (self.auctionyear.year == 2021) & (self.name == "E"):
    #        print("\n\n\n\n\n", self.name,self.auctionyear.year, self.budget())
#            print(projects)
        return {'cost': cost, 'gen': gen, 'projects': projects, 'tech_cost': tech_cost, 'tech_gen': tech_gen}

    #def future_prices(self):
    #    years = list(range(self.auctionyear.year, self.auctionyear.scenario.end_year))
    #    values = [self.auctionyear.scenario.auctionyear_set.get(year=year).wholesale_price for year in years]
    #    return dict(zip(years,values))


    def future_payouts(self):
        gen = {}
        strike_price = {}
        for tech in self.technology_set.all():
            tech_projects = self.projects()[(self.projects().funded_this_year == True) & (self.projects().technology == tech.name)]
            gen[tech.name] = tech_projects.attempted_project_gen.sum()/1000 if pd.notnull(tech_projects.attempted_project_gen.sum()) else 0
            strike_price[tech.name] = tech_projects.strike_price.max() if pd.notnull(tech_projects.strike_price.max()) else 0
#        print('year', self.auctionyear.year)
#        print('generation',gen)
#        print('strike prices',strike_price)
        return {'gen': gen, 'strike_price': strike_price}



    #@lru_cache(maxsize=None)
    def cost(self):
        return self.run_auction()['cost']

    #@lru_cache(maxsize=None)
    def unspent(self):
        if self.auctionyear.year == 2020:
            return 0
        else:
            return self.budget() - self.cost()

    #@lru_cache(maxsize=None)
    def gen(self):
        return self.run_auction()['gen']

    #@lru_cache(maxsize=None)
    def funded_projects(self):
        return self.projects()[self.projects().funded == "this year"]

    #@lru_cache(maxsize=None)
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


    #@lru_cache(maxsize=None)
    def previous_year(self):
        if self.pot.auctionyear.year == 2020:
            return None
        else:
            previous_auctionyear = self.pot.auctionyear.scenario.auctionyear_set.get(year=self.pot.auctionyear.year-1)
            previous_pot = previous_auctionyear.pot_set.get(name=self.pot.name)
            previous_tech = previous_pot.technology_set.get(name=self.name)
            return previous_tech

    #@lru_cache(maxsize=None)
    def this_year_gen(self):
        return self.max_deployment_cap * self.load_factor * 8.760 * 1000

    #@lru_cache(maxsize=None)
    def previous_gen(self):
        if self.pot.auctionyear.year == 2020:
            return 0
        else:
            return self.previous_year().new_generation_available()

    #@lru_cache(maxsize=None)
    def new_generation_available(self):
        return self.previous_gen() + self.this_year_gen()

    #@lru_cache(maxsize=None)
    def num_projects(self):
        return int(self.new_generation_available() / self.project_gen)

    #@lru_cache(maxsize=None)
    def projects_index(self):
        return [ self.name + str(i + 1) for i in range(self.num_projects()) ]

    #@lru_cache(maxsize=None)
    def levelised_cost_distribution(self):
        return Series(np.linspace(self.min_levelised_cost,self.max_levelised_cost,self.num_projects()+2)[1:-1],name="levelised_cost", index=self.projects_index())

    #@lru_cache(maxsize=None)
    def projects(self):
        projects = DataFrame(data=self.levelised_cost_distribution(), index=self.projects_index())
        #projects['gen'] = self.new_generation_available()
        projects['gen'] = self.project_gen
        projects['technology'] = self.name
        projects['strike_price'] = self.strike_price
        projects['clearing_price'] = np.nan
        projects['affordable'] = projects.levelised_cost <= projects.strike_price
        projects['funded'] = 'no'
        return projects
