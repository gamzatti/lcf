from django.db import models
from django.utils import timezone
import pandas as pd
import numpy as np
from pandas import DataFrame, Series
from functools import lru_cache
import datetime
import time

from .auctionyear import AuctionYear
from .pot import Pot
from .technology import Technology

class Scenario(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True, verbose_name="Description (optional)")
    date = models.DateTimeField(default=timezone.now)
    budget = models.FloatField(default=3.3, verbose_name="Budget period 1 (£bn)")
    budget2 = models.FloatField(blank=True, null=True, verbose_name="Budget period 2 (£bn) - leave blank to use same as period 1")
    percent_emerging = models.FloatField(default=0.6)
    rank_by_levelised_cost = models.BooleanField(default=True)
    set_strike_price =  models.BooleanField(default=False, verbose_name="Generate strike price ourselves?")
    start_year1 = models.IntegerField(default=2021)
    end_year1 = models.IntegerField(default=2025)
    start_year2 = models.IntegerField(default=2026)
    end_year2 = models.IntegerField(default=2030)
    excel_sp_error = models.BooleanField(default=True, verbose_name="Include the Excel error in the emerging pot strike price?")
    tidal_levelised_cost_distribution = models.BooleanField(default=False)
    excel_2020_gen_error = models.BooleanField(default=True, verbose_name="Include the Excel error that counts cumulative generation from 2020 for auction and negotiations (but not FIT)")
    excel_nw_carry_error = models.BooleanField(default=True, verbose_name="Include the Excel error that carries NWFIT into next year, even though it's been spent")

    def __str__(self):
        return self.name

    def __init__(self, *args, **kwargs):
        super(Scenario, self).__init__(*args, **kwargs)
        self._cumulative_costs1 = None
        self._cumulative_costs2 = None
        self._cum_awarded_gen_by_pot1 = None
        self._cum_awarded_gen_by_pot2 = None
        self._awarded_cost_by_tech1 = None
        self._awarded_cost_by_tech2 = None
        self._gen_by_tech1 = None
        self._gen_by_tech2 = None
        self._cap_by_tech1 = None
        self._cap_by_tech2 = None


    #chart methods

    def period(self, num):
        if num == 1:
            ran = (self.start_year1, self.end_year1)
        elif num == 2:
            ran = (self.start_year2, self.end_year2)
        return self.auctionyear_set.filter(year__range=ran).order_by("year")

    @lru_cache(maxsize=None)
    def cumulative_costs(self, period_num):
        index = ['Accounting cost', 'Cost v gas', 'Innovation premium', 'Absolute cost']
        auctionyears = self.period(period_num)
        columns = [str(a.year) for a in auctionyears]
        accounting_costs = [round(a.cum_owed_v("wp")/1000,3) for a in auctionyears]
        cost_v_gas = [round(a.cum_owed_v("gas")/1000,3) for a in auctionyears]
        innovation_premium = [round(a.innovation_premium()/1000,3) for a in auctionyears]
        absolute_cost = [round(a.cum_owed_v("absolute")/1000,3) for a in auctionyears]
        df = DataFrame([accounting_costs, cost_v_gas, innovation_premium, absolute_cost], index=index, columns=columns)
        options = {'title': None, 'vAxis': {'title': '£bn'}}
        return {'df': df, 'options': options}

    @lru_cache(maxsize=None)
    def cum_awarded_gen_by_pot(self,period_num):
        auctionyears = self.period(period_num)
        index = [pot.name for pot in auctionyears[0].active_pots()]
        data = { str(a.year) : [round(p.cum_awarded_gen(),2) for p in a.active_pots()] for a in auctionyears }
        df = DataFrame(data=data, index=index)
        options = {'vAxis': {'title': 'TWh'}, 'title': None}
        return {'df': df, 'options': options}


    @lru_cache(maxsize=None)
    def awarded_cost_by_tech(self,period_num):
        auctionyears = self.period(period_num)
        index = [t.name for pot in auctionyears[0].active_pots() for t in pot.tech_set().order_by("name")]
        data = { str(a.year) : [round(t.awarded_cost,2) for p in a.active_pots() for t in p.tech_set().order_by("name")] for a in auctionyears }
        df = DataFrame(data=data, index=index)
        options = {'vAxis': {'title': '£m'}, 'title': None}
        return {'df': df, 'options': options}


    @lru_cache(maxsize=None)
    def gen_by_tech(self,period_num):
        auctionyears = self.period(period_num)
        index = [t.name for pot in auctionyears[0].active_pots() for t in pot.tech_set().order_by("name")]
        data = { str(a.year) : [round(t.awarded_gen,2) for p in a.active_pots() for t in p.tech_set().order_by("name")] for a in auctionyears }
        df = DataFrame(data=data, index=index)
        options = {'vAxis': {'title': 'TWh'}, 'title': None}
        return {'df': df, 'options': options}


    @lru_cache(maxsize=None)
    def cap_by_tech(self,period_num):
        auctionyears = self.period(period_num)
        index = [t.name for pot in auctionyears[0].active_pots() for t in pot.tech_set().order_by("name")]
        data = { str(a.year) : [round(t.awarded_gen/8.760/t.load_factor,2) for p in a.active_pots() for t in p.tech_set().order_by("name")] for a in auctionyears }
        df = DataFrame(data=data, index=index)
        options = {'vAxis': {'title': 'GW'}, 'title': None}
        return {'df': df, 'options': options}

    #helper methods

    def df_to_chart_data(self,df):
        chart_data = df['df'].copy()
        chart_data['index_column'] = chart_data.index
        chart_data.loc['years_row'] = chart_data.columns
        chart_data = chart_data.reindex(index = ['years_row']+list(chart_data.index)[:-1], columns = ['index_column'] +list(chart_data.columns)[:-1])
        chart_data = chart_data.T.values.tolist()
        return {'data': chart_data, 'df': df['df'], 'options': df['options']}

    def get_or_make_chart_data(self, method, period_num):
        attr_name = ("").join(["_",method,str(period_num)])
        if self.__getattribute__(attr_name) == None:
            methods = globals()['Scenario']
            meth = getattr(methods,method)
            df = meth(self, period_num)
            chart_data = self.df_to_chart_data(df)
            self.__setattr__(attr_name, chart_data)
            return self.__getattribute__(attr_name)
        elif self.__getattribute__(attr_name) != None:
            return self.__getattribute__(attr_name)

    @lru_cache(maxsize=None)
    def technology_form_helper(self):
        techs = [t for p in self.auctionyear_set.all()[0].pot_set.all() for t in p.technology_set.all() ]
        t_form_data = { t.name : {} for t in techs}
        for t in techs:
            #creating subset is the slow bit. speed up by directly accessing database?
            subset = self.techs_df()[self.techs_df().name == t.name]
            for field, value in techs[0].get_field_values().items():
                if field == "id":
                    pass
                elif field == "name":
                    t_form_data[t.name][field] = t.name
                elif field == "included":
                    t_form_data[t.name][field] = t.included
                elif field == "pot":
                    t_form_data[t.name][field] = t.pot.name
                else:
                    if value == None:
                        t_form_data[t.name][field] = ""
                    else:
                        li = list(subset[field])
                        #li = ['{:.2f}'.format(x) for x in li]
                        t_form_data[t.name][field] = str(li).strip('[]').replace("'",'')

        initial_technologies = list(t_form_data.values())
        t_names = [t.name for t in techs]
        return t_names, initial_technologies


    def techs_df(self):
        techs = pd.concat([t.fields_df() for a in self.auctionyear_set.all() for p in a.active_pots().all() for t in p.technology_set.all() ])
        techs = techs.set_index('id')
        return techs


    def df_to_html(self,df):
        #html = df.style.format('<input style="width:120px;" name="df" value="{}" />').render()
        html = df.style.render()
        html = html.replace('<table id=', '<table class="table table-striped table-condensed" id=')
        return html


    #inputs

    def techs_input(self):
        df = self.techs_df().sort_values(["pot_name", "name", "listed_year"]).drop('pot', axis=1)
        df.set_index(["pot_name", 'name','listed_year'],drop=False, inplace=True)
        df = df.reindex(columns =["pot_name", "name", "listed_year", 'included', 'min_levelised_cost', 'max_levelised_cost', 'strike_price', 'load_factor', 'max_deployment_cap', 'num_new_projects', 'project_gen'])
        df.rename(columns={'pot_name': 'pot', 'listed_year': 'year', 'strike_price': 'strike price', 'load_factor': 'load factor', 'project_gen': 'project size GWh', 'num_new_projects': 'number of new projects','min_levelised_cost': 'min LCOE', 'max_levelised_cost': 'max LCOE', 'max_deployment_cap': 'max GW pa'},inplace=True)
        df = round(df,2)
        return df


    def prices_input(self):
        return DataFrame(
                    {
                    'wholesale prices': [round(a.wholesale_price,2) for a in self.auctionyear_set.all() ],
                    'gas prices': [round(a.gas_price,2) for a in self.auctionyear_set.all() ]
                    }, index=[a.year for a in self.auctionyear_set.all()]).T


    def techs_input_html(self):
        df = self.techs_input()
        df.set_index(["pot", 'name','year'],inplace=True)
        return self.df_to_html(df)


    def prices_input_html(self):
        df = self.prices_input()
        return self.df_to_html(df)

#if I separate inputs by technology for display on detail page. needs to be grouped by technology rather than just be individual dfs for all years.
    def tech_df_list(self):
        dfs = [t.fields_df_html() for a in self.auctionyear_set.all() for p in a.active_pots().all() for t in p.technology_set.all() ]
        return dfs

    def clear_all(self):
        for a in AuctionYear.objects.filter(scenario = self):
            a.budget_result = None
            a.save()
            for p in Pot.objects.filter(auctionyear = a):
                p.auction_has_run = False
                p.budget_result = None
                p.awarded_cost_result
                p.awarded_gen_result
                p.auction_results
                p.save()
                for t in Technology.objects.filter(pot=p):
                    t.awarded_gen = None
                    t.awarded_cost = 0
