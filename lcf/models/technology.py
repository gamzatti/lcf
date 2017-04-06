from django.db import models
from django.utils import timezone
import pandas as pd
import numpy as np
from pandas import DataFrame, Series
from functools import lru_cache
import datetime
import time

class Technology(models.Model):
    TECHNOLOGY_CHOICES = (
            ('OFW', 'Offshore wind'),
            ('ONW', 'Onshore wind'),
            ('NU', 'Nuclear'),
            ('TL', 'Tidal lagoon'),
            ('TS', 'Tidal stream'),
            ('WA', 'Wave'),
            ('PVLS', 'Solar PV'),
            ('NW', 'Negawatts')
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
    num_new_projects = models.FloatField(null=True,blank=True)

    def __init__(self, *args, **kwargs):
        super(Technology, self).__init__(*args, **kwargs)
        #print('new tech!, name:',self.name)
        self.awarded_gen = 0
        self.awarded_cap = 0
        self.awarded_cost = 0
        self.cum_owed_v_wp = 0
        self.cum_owed_v_gas = 0
        self.cum_owed_v_absolute = 0
        self.cum_awarded_gen = 0
        self._max_deployment_cap = self.max_deployment_cap if self.num_new_projects == None else self.num_new_projects * self.project_gen / self.load_factor / 8760


    def __str__(self):
        return str((self.pot.auctionyear,self.pot.name,self.name))


    #@lru_cache(maxsize=128)
    def get_field_values(self):
        fields = [f.name for f in Technology._meta.get_fields()]
        # fields.remove('awarded_gen')
        # fields.remove('awarded_cost')
        values = [getattr(self, f, None) for f in fields]
        di = dict(zip(fields,values))
        return di


    #@lru_cache(maxsize=128)
    def fields_df(self):
        df = DataFrame([self.get_field_values()])
        df['listed_year'] = self.pot.auctionyear.year
        df['pot_name'] = self.pot.name
        return df

    #@lru_cache(maxsize=128)
    def fields_df_html(self):
        df = self.fields_df().sort_values(["pot_name", "name", "listed_year"]).drop('pot', axis=1)
        #df = df.reindex(columns =["pot_name", "name", "listed_year", 'included', 'load_factor', 'min_levelised_cost', 'max_levelised_cost', 'max_deployment_cap', 'strike_price', 'project_gen'])
        df = round(df,2)
        df.set_index(["pot_name", 'name','listed_year'],inplace=True)
        return df.to_html(classes="table table-striped table-condensed")


    #@lru_cache(maxsize=128)
    def previous_year(self):
        if self.pot.auctionyear.year == 2020:
            return None
        else:
            previous_tech = self.pot.previous_year().technology_dict[self.name]
            return previous_tech

    #@lru_cache(maxsize=128)
    def this_year_gen(self):
        return self._max_deployment_cap * self.load_factor * 8.760 * 1000

    #@lru_cache(maxsize=128)
    def previous_gen(self):
        res = 0 if self.pot.auctionyear.year == 2020 else self.previous_year().new_generation_available()
        return res

    @lru_cache(maxsize=128)
    def new_generation_available(self):
        p = self.previous_gen()
        t = self.this_year_gen()
        res = p + t
        return res

    @lru_cache(maxsize=128)
    def num_projects(self):
        if self.num_new_projects != None:
            if self.pot.auctionyear.year == 2020:
                return int(self.num_new_projects)
            else:
                res = int(self.num_new_projects) + self.previous_year().num_projects()
                return res
        else:
            res = int(self.new_generation_available() / self.project_gen)
            return res

    @lru_cache(maxsize=128)
    def projects_index(self):
        if self.num_projects() == 0:
            return []
        else:
            #print(self.num_projects())
            return [ self.name + str(i + 1) for i in range(self.num_projects()) ]

    #@lru_cache(maxsize=128)
    def levelised_cost_distribution(self):
        if self.num_projects == 0:
            return Series()
        if self.pot.auctionyear.scenario.tidal_levelised_cost_distribution == True and self.pot.auctionyear.year == 2025 and self.name == "TL":
            dist = Series(np.linspace(self.min_levelised_cost,150,self.num_projects()),name="levelised_cost", index=self.projects_index())
        else:
            minlc = self.min_levelised_cost
            maxlc = self.max_levelised_cost
            npr = self.num_projects()+2
            data = np.linspace(minlc,maxlc,npr)[1:-1]
            dist = Series(data,name="levelised_cost", index=self.projects_index())
        return dist

    #@lru_cache(maxsize=128)
    def projects(self):
        if self.num_projects == 0:
            return DataFrame()
        else:
            data = self.levelised_cost_distribution()
            index = self.projects_index()
            projects = DataFrame(data=data, index=index)
            #projects['gen'] = self.new_generation_available()
            projects['gen'] = self.project_gen
            projects['technology'] = self.name
            projects['strike_price'] = self.strike_price
            #projects['clearing_price'] = np.nan
            projects['affordable'] = projects.levelised_cost <= projects.strike_price
            projects['pot'] = self.pot.name
            projects['listed_year'] = self.pot.auctionyear.year
            return projects


    def cum_future_techs(self):
        if self.pot.auctionyear.year == 2020:
            return [self]
        else:
            return [ p.technology_dict[self.name] for p in self.pot.cum_future_pots() ]
