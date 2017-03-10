from django.db import models
from django.utils import timezone
import pandas as pd
import numpy as np
from pandas import DataFrame, Series
from functools import lru_cache
import datetime

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
    excel_wp_error = models.BooleanField(default=True, verbose_name="Include the Excel error in the emerging pot wholesale price?")


    def __init__(self, *args, **kwargs):
        super(Scenario, self).__init__(*args, **kwargs)
        self.tempvar = "foo"

    def __str__(self):
        return self.name

    def paid(self, year):
        a = self.auctionyear_set.get(year=year)
        return a.paid()

    def paid_end_year(self):
        return self.paid(self.end_year)

    def cum_gen(self, start_year, end_year):
        return sum([a.awarded_gen() for a in self.auctionyear_set.filter(year__range=(start_year,end_year))])

    def cum_gen_end_year(self):
        return self.cum_gen(2020,self.end_year)

    def projects_df(self):
        projects = pd.concat([t.projects() for a in self.auctionyear_set.all() for p in a.pot_set.all() for t in p.technology_set.all() ])
        #print(projects)
        return projects

    def techs_df(self):
        techs = pd.concat([t.fields_df() for a in self.auctionyear_set.all() for p in a.pot_set.all() for t in p.technology_set.all() ])
        techs = techs.set_index('id')
        #print('\n',techs)
        return techs

    def initial_technologies(self):
        techs = [t for p in self.auctionyear_set.all()[0].pot_set.all() for t in p.technology_set.all() ]
        t_form_data = { t.name : {} for t in techs}
        for t in techs:
            subset = self.techs_df()[self.techs_df().name == t.name]
            for field in techs[0].get_field_values():
                if field == "id":
                    pass
                elif field == "name":
                    t_form_data[t.name][field] = t.name
                elif field == "pot":
                    t_form_data[t.name][field] = t.pot.name
                else:
                    t_form_data[t.name][field] = str(list(subset[field])).strip('[]')
        initial_technologies = list(t_form_data.values())
        t_names = [t.name for t in techs]
        return t_names, initial_technologies


    def accounting_cost(self):
        title = [['year', 'Accounting cost: '+self.name, 'DECC 2015 w/TCCP', 'Meets 90TWh (no TCCP)', 'Meets 90TWh']]
        auctionyears = self.auctionyear_set.filter(year__gte=self.start_year)
        years = [str(a.year) for a in auctionyears]
        accounting_costs = [a.paid()/1000 for a in auctionyears]
        decc = [1.07055505120968, 1.49485703401083, 1.96202174324618, 2.49374812823629, 2.93865520551304]
        m_90_no_TCCP = [1.01677248921882, 1.45462660670601, 1.88986715668434, 2.50808000031501,	2.97952038924637]
        m_90 = [1.00594113294511, 1.40460686828232, 1.76626877818907, 2.23697361578951, 2.49061992003395]
        ddf = DataFrame([years,accounting_costs, decc, m_90_no_TCCP, m_90])
        df = ddf.copy()
        df.columns = years
        df.index = title
        df = df.drop('year')
        data = ddf.T.values.tolist()
        title.extend(data)
        return {'title': title, 'df': df}

    def summary_gen_by_tech(self):
        auctionyears = self.auctionyear_set.filter(year__gte=self.start_year)
        years = [a.year for a in auctionyears]
        tech_names = self.initial_technologies()[0]
        title = ['year']
        title.extend(tech_names)
        df = DataFrame(columns=title, index=years)
        for a in auctionyears:
            for p in a.pot_set.all():
                for t in p.technology_set.all():
                    df.at[a.year,t.name] = p.summary_for_future()['gen'][t.name]
        ddf = df.copy()
        ddf['year'] = ddf.index
        #df['year'] = [datetime.date(i,1,1) for i in df.index]
        ddf['year'] = [str(i) for i in ddf.index]
        data = ddf.values.tolist()
        title = [title]
        title.extend(data)
        df = df.drop('year',axis=1).T
        return {'title': title, 'df': df}

    def summary_cap_by_tech(self):
        auctionyears = self.auctionyear_set.filter(year__gte=self.start_year)
        years = [a.year for a in auctionyears]
        tech_names = self.initial_technologies()[0]
        title = ['year']
        title.extend(tech_names)
        df = DataFrame(columns=title, index=years)
        for a in auctionyears:
            for p in a.pot_set.all():
                for t in p.technology_set.all():
                    df.at[a.year,t.name] = p.summary_for_future()['gen'][t.name]/8.760/t.load_factor
        ddf = df.copy()
        ddf['year'] = ddf.index
        #df['year'] = [datetime.date(i,1,1) for i in df.index]
        ddf['year'] = [str(i) for i in ddf.index]
        data = ddf.values.tolist()
        title = [title]
        title.extend(data)
        df = df.drop('year',axis=1).T
        return {'title': title, 'df': df}



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
        awarded = 0
        for pot in self.pot_set.all():
            if pot.name == "E" or pot.name == "M":
                awarded += pot.cost()
        return awarded

    def awarded_gen(self):
        awarded_gen = 0
        for pot in self.pot_set.all():
            if pot.name == "E" or pot.name == "M":
                awarded_gen += pot.gen()
        return awarded_gen

    #@lru_cache(maxsize=None)
    def unspent(self):
        if self._unspent:
            return self._unspent
        else:
            self._unspent = self.budget() - self.awarded()
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
            self._previous_year_unspent = previous_year.unspent()
            return previous_year.unspent()

    def previous_years(self):
        if self.year == 2020:
            return None
        else:
            return self.scenario.auctionyear_set.filter(year__range=(self.scenario.start_year,self.year-1)).order_by('year')


    def paid(self):
        if self.year == 2020:
            return self.awarded()
        else:
            return self.awarded() + sum([self.owed(previous_year) for previous_year in self.previous_years()])


    def owed(self, previous_year):
        owed = {}
        for pot in previous_year.pot_set.all():
            owed[pot.name] = 0
            data = pot.summary_for_future()
            for t in pot.technology_set.all():
                gen = data['gen'][t.name]
                strike_price = data['strike_price'][t.name]
                if self.scenario.excel_wp_error == True:
                    #next 5 lines account for Angela's error
                    if (pot.name == "E"):
                        try:
                            strike_price = self.pot_set.get(name=pot.name).technology_set.get(name=t.name).strike_price
                        except:
                            break
                difference = strike_price - self.wholesale_price
                tech_owed = gen * difference
                owed[pot.name] += tech_owed
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

        return {'cost': cost, 'gen': gen, 'projects': projects, 'tech_cost': tech_cost, 'tech_gen': tech_gen}



    def summary_for_future(self):
        gen = {}
        strike_price = {}
        for tech in self.technology_set.all():
            tech_projects = self.projects()[(self.projects().funded_this_year == True) & (self.projects().technology == tech.name)]
            gen[tech.name] = tech_projects.attempted_project_gen.sum()/1000 if pd.notnull(tech_projects.attempted_project_gen.sum()) else 0
            strike_price[tech.name] = tech_projects.strike_price.max() if pd.notnull(tech_projects.strike_price.max()) else 0
        return {'gen': gen, 'strike_price': strike_price}

    def summary_gen_by_tech(self):
        return DataFrame([self.summary_for_future()['gen']],index=["Gen"]).T

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

    def get_field_values(self):
        fields = [f.name for f in Technology._meta.get_fields()]
        values = [getattr(self, f, None) for f in fields]
        return dict(zip(fields,values))


    def fields_df(self):
        df = DataFrame([self.get_field_values()])
        df['listed_year'] = self.pot.auctionyear.year
        return df

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
        projects['listed_year'] = self.pot.auctionyear.year
        return projects
