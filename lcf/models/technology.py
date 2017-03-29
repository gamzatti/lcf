from django.db import models
from django.utils import timezone
import pandas as pd
import numpy as np
from pandas import DataFrame, Series
from functools import lru_cache
import datetime

class TechnologyManager(models.Manager):
    def create_technology(self, **kwargs):
        t = self.create(**kwargs)
        if t.num_new_projects != None:
            t.fill_in_max_deployment_cap()
        elif t.max_deployment_cap == None:
            print("You must specify either num_new_projects or max_deployment_cap")
        return t

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
    max_deployment_cap = models.FloatField(null=True, blank=True)
    included = models.BooleanField(default=True)
    awarded_gen = models.FloatField(null=True, blank=True)
    awarded_cost = models.FloatField(default=0)
    num_new_projects = models.IntegerField(null=True, blank=True)
    objects = TechnologyManager()

    def __init__(self, *args, **kwargs):
        super(Technology, self).__init__(*args, **kwargs)


    def __str__(self):
        return str((self.pot.auctionyear,self.pot.name,self.name))


    #@lru_cache(maxsize=None)
    def get_field_values(self):
        fields = [f.name for f in Technology._meta.get_fields()]
        fields.remove('awarded_gen')
        fields.remove('awarded_cost')
        values = [getattr(self, f, None) for f in fields]
        di = dict(zip(fields,values))
        return di


    #@lru_cache(maxsize=None)
    def fields_df(self):
        df = DataFrame([self.get_field_values()])
        df['listed_year'] = self.pot.auctionyear.year
        df['pot_name'] = self.pot.name
        return df

    #@lru_cache(maxsize=None)
    def fields_df_html(self):
        df = self.fields_df().sort_values(["pot_name", "name", "listed_year"]).drop('pot', axis=1)
        #df = df.reindex(columns =["pot_name", "name", "listed_year", 'included', 'load_factor', 'min_levelised_cost', 'max_levelised_cost', 'max_deployment_cap', 'strike_price', 'project_gen'])
        df = round(df,2)
        df.set_index(["pot_name", 'name','listed_year'],inplace=True)
        return df.to_html(classes="table table-striped table-condensed")


    #@lru_cache(maxsize=None)
    def previous_year(self):
        if self.pot.auctionyear.year == 2020:
            return None
        else:
            previous_auctionyear = self.pot.auctionyear.scenario.auctionyear_set.get(year=self.pot.auctionyear.year-1)
            previous_pot = previous_auctionyear.active_pots().get(name=self.pot.name)
            previous_tech = previous_pot.tech_set().get(name=self.name)
            return previous_tech

    #@lru_cache(maxsize=None)
    def this_year_gen(self):
        return self.max_deployment_cap * self.load_factor * 8.760 * 1000

    #@lru_cache(maxsize=None)
    def previous_gen(self):
        return 0 if self.pot.auctionyear.year == 2020 else self.previous_year().new_generation_available()

    #@lru_cache(maxsize=None)
    def new_generation_available(self):
        return self.previous_gen() + self.this_year_gen()

    #@lru_cache(maxsize=None)
    def num_projects(self):
        if self.num_new_projects != None:
            if self.pot.auctionyear.year == 2020:
                return self.num_new_projects
            else:
                return self.num_new_projects + self.previous_year().num_projects()
        else:
            return int(self.new_generation_available() / self.project_gen)

    #@lru_cache(maxsize=None)
    def projects_index(self):
        return [ self.name + str(i + 1) for i in range(self.num_projects()) ]

    #@lru_cache(maxsize=None)
    def levelised_cost_distribution(self):
        if self.pot.auctionyear.scenario.tidal_levelised_cost_distribution == True and self.pot.auctionyear.year == 2025 and self.name == "TL":
            return Series(np.linspace(self.min_levelised_cost,150,self.num_projects()),name="levelised_cost", index=self.projects_index())
        else:
            return Series(np.linspace(self.min_levelised_cost,self.max_levelised_cost,self.num_projects()+2)[1:-1],name="levelised_cost", index=self.projects_index())

    #@lru_cache(maxsize=None)
    def projects(self):
        projects = DataFrame(data=self.levelised_cost_distribution(), index=self.projects_index())
        #projects['gen'] = self.new_generation_available()
        projects['gen'] = self.project_gen
        projects['technology'] = self.name
        projects['strike_price'] = self.strike_price
        #projects['clearing_price'] = np.nan
        projects['affordable'] = projects.levelised_cost <= projects.strike_price
        projects['pot'] = self.pot.name
        projects['listed_year'] = self.pot.auctionyear.year
        return projects

    def fill_in_max_deployment_cap(self):
        project_cap = self.project_gen / self.load_factor / 8760 # for tidal = 2200 / 0.22 / 8760 = 1.14155251141553
        self.max_deployment_cap = self.num_new_projects * project_cap # need to check that it's right to put num_new_projects rather than num_projects
        self.save()
