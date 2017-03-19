from django.db import models
from django.utils import timezone
import pandas as pd
import numpy as np
from pandas import DataFrame, Series
from functools import lru_cache
import datetime


from .auctionyear import AuctionYear
from .pot import Pot
from .technology import Technology

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
    tidal_levelised_cost_distribution = models.BooleanField(default=False)
    excel_2020_gen_error = models.BooleanField(default=True, verbose_name="Include the Excel error that counts cumulative generation from 2020 for auction and negotiations (but not FIT)")
    excel_nw_carry_error = models.BooleanField(default=True, verbose_name="Include the Excel error that carries NWFIT into next year, even though it's been spent")

    def __str__(self):
        return self.name


    #form helper methods
    def projects_df(self):
        projects = pd.concat([t.projects() for a in self.auctionyear_set.all() for p in a.active_pots().all() for t in p.tech_set().all() ])
        #print(projects)
        return projects

    def techs_df(self):
        techs = pd.concat([t.fields_df() for a in self.auctionyear_set.all() for p in a.active_pots().all() for t in p.technology_set.all() ])
        techs = techs.set_index('id')
        #print('\n',techs)
        return techs

    def technology_form_helper(self):
        techs = [t for p in self.auctionyear_set.all()[0].pot_set.all() for t in p.technology_set.all() ]
        t_form_data = { t.name : {} for t in techs}
        for t in techs:
            subset = self.techs_df()[self.techs_df().name == t.name]
            for field in techs[0].get_field_values():
                if field == "id":
                    pass
                elif field == "name":
                    t_form_data[t.name][field] = t.name
                elif field == "included":
                    t_form_data[t.name][field] = t.included
                elif field == "pot":
                    t_form_data[t.name][field] = t.pot.name
                else:
                    t_form_data[t.name][field] = str(list(subset[field])).strip('[]')
        initial_technologies = list(t_form_data.values())
        t_names = [t.name for t in techs]
        return t_names, initial_technologies




    #end year summary data methods (because functions with arguments can't be called in templates)

    #graph/table methods
    def accounting_cost(self):
        title = [['year', 'Accounting cost', 'Cost v gas', 'Innovation premium']]
        auctionyears = self.auctionyear_set.filter(year__gte=self.start_year)
        years = [str(a.year) for a in auctionyears]
        accounting_costs = [round(a.paid()/1000,3) for a in auctionyears]
        cost_v_gas = [round(a.paid_v_gas()/1000,3) for a in auctionyears]
        innovation_premium = [round(a.innovation_premium()/1000,3) for a in auctionyears]
        ddf = DataFrame([years,accounting_costs, cost_v_gas, innovation_premium])
        df = ddf.copy()
        df.columns = years
        df.index = title
        df = df.drop('year')
        data = ddf.T.values.tolist()
        title.extend(data)
        return {'title': title, 'df': df}


    def accounting_cost_comparison(self):
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
        tech_names = sorted(self.technology_form_helper()[0])
        title = ['year']
        title.extend(tech_names)
        df = DataFrame(columns=title, index=years)
        for a in auctionyears:
            for p in a.active_pots().all():
                p.run_auction()
                for t in p.tech_set().all():
                    #df.at[a.year,t.name] = p.summary_for_future()['gen'][t.name]
                    df.at[a.year,t.name] = t.awarded_gen
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
        tech_names = sorted(self.technology_form_helper()[0])
        title = ['year']
        title.extend(tech_names)
        df = DataFrame(columns=title, index=years)
        for a in auctionyears:
            for p in a.active_pots().all():
                for t in p.tech_set().all():
                    #df.at[a.year,t.name] = p.summary_for_future()['gen'][t.name]/8.760/t.load_factor
                    df.at[a.year,t.name] = t.awarded_gen/8.760/t.load_factor

        ddf = df.copy()
        ddf['year'] = ddf.index
        #df['year'] = [datetime.date(i,1,1) for i in df.index]
        ddf['year'] = [str(i) for i in ddf.index]
        data = ddf.values.tolist()
        title = [title]
        title.extend(data)
        df = df.drop('year',axis=1).T
        return {'title': title, 'df': df}
