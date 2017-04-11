from django.db import models
from django.utils import timezone
import pandas as pd
import numpy as np
from pandas import DataFrame, Series
from functools import lru_cache
import datetime
import time
from django_pandas.io import read_frame

from .auctionyear import AuctionYear
from .pot import Pot
from .technology import Technology
from .policy import Policy

class Scenario(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True, verbose_name="Description (optional)")
    date = models.DateTimeField(default=timezone.now)
    budget = models.FloatField(default=3.3, verbose_name="Budget period 1 (£bn)")
    budget2 = models.FloatField(blank=True, null=True, verbose_name="Budget period 2 (£bn) - leave blank to use same as period 1")
    percent_emerging = models.FloatField(default=0.6)
    set_strike_price =  models.BooleanField(default=False, verbose_name="Generate strike price ourselves?")
    start_year1 = models.IntegerField(default=2021)
    end_year1 = models.IntegerField(default=2025, verbose_name="End of LCF 1 period")
    start_year2 = models.IntegerField(default=2026)
    end_year2 = models.IntegerField(default=2030)
    excel_sp_error = models.BooleanField(default=False, verbose_name="Include the Excel error in the emerging pot strike price?")
    tidal_levelised_cost_distribution = models.BooleanField(default=True)
    excel_2020_gen_error = models.BooleanField(default=False, verbose_name="Include the Excel error that counts cumulative generation from 2020 for auction and negotiations (but not FIT)")
    excel_nw_carry_error = models.BooleanField(default=False, verbose_name="Include the Excel error that carries NWFIT into next year, even though it's been spent")
    excel_quirks = models.BooleanField(default=True, verbose_name="Include all Excel quirks")
    results = models.TextField(null=True,blank=True)
    policies = models.ManyToManyField(Policy, blank=True)

    def __str__(self):
        return self.name

    def __init__(self, *args, **kwargs):
        super(Scenario, self).__init__(*args, **kwargs)
        self.auctionyear_dict = { auctionyear.year : auctionyear for auctionyear in self.auctionyear_set.all() }
        self.flat_tech_dict = { t.name + str(t.pot.auctionyear.year) : t for a in self.auctionyear_dict.values() for p in a.pot_dict.values() for t in p.technology_dict.values() }
    #chart methods

    def period(self, num):
        if num == 1:
            ran = range(self.start_year1, self.end_year1+1)
        elif num == 2:
            ran = range(self.start_year2, self.end_year2+1)
        #return self.auctionyear_set.filter(year__range=ran).order_by("year")
        return [ auctionyear for auctionyear in self.auctionyear_dict.values() if auctionyear.year in ran ]

    def get_results(self):
        # self.apply_policies()
        columns = ['year',
                   'pot',
                   'name',
                   'awarded_gen',
                   'awarded_cap',
                   'awarded_cost',
                   'cum_awarded_gen',
                   'cum_owed_v_gas',
                   'cum_owed_v_wp',
                   'cum_owed_v_absolute']
        if self.results == None:
            # print('getting results')
            for a in self.auctionyear_dict.values():
                for p in a.pot_dict.values():
                    p.run_auction()
            results = DataFrame([ [t.pot.auctionyear.year,
                        t.pot.get_name_display(),
                        t.get_name_display(),
                        t.awarded_gen,
                        t.awarded_cap,
                        t.awarded_cost,
                        t.cum_awarded_gen,
                        t.cum_owed_v_gas,
                        t.cum_owed_v_wp,
                        t.cum_owed_v_absolute]
                        for t in self.flat_tech_dict.values() ],
                        columns = columns)
            results = results.sort_values(['year','pot','name'])
            results.index = range(0,len(results.index))
            self.results = results.to_json()
            self.save()
            return results
        else:
            # print('retrieving from db')
            results = pd.read_json(self.results).reindex(columns=columns).sort_index()
            return results

    def df_to_chart_data(self,column):
        df = self.get_results()
        df = df[['year','pot','name',column]]
        df = df.set_index(['year','pot','name']).sort_index()
        df = df.unstack(0)
        df.columns = df.columns.get_level_values(1)
        df.index = df.index.get_level_values(1)
        df = df.reset_index()
        df.loc['years_row'] = df.columns.astype('str')
        df = df.reindex(index = ['years_row']+list(df.index)[:-1])
        chart_data = df.T.values.tolist()
        units = {
                'awarded_cap': 'GW',
                'awarded_gen': 'TWh',
                'cum_owed_v_gas': '£bn',
                'cum_owed_v_wp': '£bn',
                'cum_owed_v_absolute': '£bn',
                'cum_awarded_gen': 'TWh',
                }
        options = {'title': None, 'vAxis': {'title': units[column]}, 'width':1000, 'height':400}
        return {'chart_data': chart_data, 'options': options}

    # @lru_cache(maxsize=128)
    def tech_pivot_table(self,period_num,column,title=None):
        # print('building pivot table')
        # auctionyears = self.period(period_num)
        #techs = { t.name + str(t.pot.auctionyear.year) : t for a in auctionyears for p in a.pot_dict.values() for t in p.technology_dict.values() }
        df = self.get_results()
        df = df[['year','pot','name',column]]
        if title:
            df.columns = ['year','pot','name', title]
        auctionyear_years = [auctionyear.year for auctionyear in self.period(period_num)]
        df = df.loc[df.year.isin(auctionyear_years)]

#        df = DataFrame([[t.pot.auctionyear.year, t.pot.get_name_display(), t.get_name_display(), getattr(t,column)] for t in techs.values()],columns=['year','pot','name',column])
        dfsum = df.groupby(['year','pot'],as_index=False).sum()
        dfsum['name']='_Subtotal'
        dfsum_outer = df.groupby(['year'],as_index=False).sum()
        dfsum_outer['name']='Total'
        dfsum_outer['pot']='Total'
        result = dfsum.append(df)
        result = dfsum_outer.append(result)
        if column == "cum_owed_v_gas":
            ip_df = df[df.pot != 'Feed-in-tariff']
            ip_df_sum_outer = ip_df.groupby(['year'],as_index=False).sum()
            ip_df_sum_outer['name'] = '__Innovation premium'
            ip_df_sum_outer['pot'] = '__Innovation premium'
            result = ip_df_sum_outer.append(result)
        result = result.set_index(['year','pot','name']).sort_index()
        result = result.unstack(0)
        if column == "cum_owed_v_wp" or column == "cum_owed_v_gas" or column == "cum_owed_v_absolute":
            result = result/1000
        if title:
            result.index.names = ['Pot','Technology']
            result.columns.names = ['', 'Year']
            #result.columns.names = [title,'Year']
            #result['column'] =
        return result



    def techs_df(self):
        techs = pd.concat([t.fields_df() for t in self.flat_tech_dict.values() ])
        techs = techs.set_index('id')
        return techs


    # @lru_cache(maxsize=128)
    def df_to_html(self,df):
        html = df.style.render()
        html = html.replace('<table id=', '<table class="table table-striped table-condensed" id=')
        return html

    # @lru_cache(maxsize=128)
    def pivot_to_html(self,df):
        def highlight_total(s):
            is_max = s == s.max()
            return ['font-weight: bold;' if v else '' for v in is_max]

        def highlight_subtotal(val):
            #print(row)
            #is_subtotal = [ row for ma in df.groupby(level=0).max() if row == ma ]
            #print(is_subtotal)
            return 'font-weight: bold;'

        #html = df.style.format('<input style="width:120px;" name="df" value="{}" />').render()
        #df = df.round(2)
        html = df.style.format("{:.3f}").applymap(highlight_subtotal, subset = pd.IndexSlice[pd.IndexSlice[:,['_Subtotal','Total', '__Innovation premium']],:]).render()
        #html = df.style.format("{:.2f}").apply(highlight_total).render()
        html = html.replace('<table id=', '<table class="table table-striped table-condensed" id=')
        html = html.replace('_Subtotal','Subtotal')
        html = html.replace('__Innovation', 'Innovation')
        return html

    #inputs

    # @lru_cache(maxsize=128)
    def techs_input(self):
        df = self.techs_df().sort_values(["pot_name", "name", "listed_year"]).drop('pot', axis=1)
        #df.set_index(["pot_name", 'name','listed_year'], inplace=True)
        #df.set_index(["pot_name", 'name','listed_year'],drop=False, inplace=True)
        df = df.reindex(columns =["pot_name", "name", "listed_year", 'included', 'min_levelised_cost', 'max_levelised_cost', 'strike_price', 'load_factor', 'max_deployment_cap', 'num_new_projects', 'project_gen'])
        #df.rename(columns={'pot_name': 'pot', 'listed_year': 'year'},inplace = True)
        df.rename(columns={'pot_name': 'pot', 'listed_year': 'year', 'strike_price': 'strike price', 'load_factor': 'load factor', 'project_gen': 'project size GWh', 'num_new_projects': 'number of new projects','min_levelised_cost': 'min LCOE', 'max_levelised_cost': 'max LCOE', 'max_deployment_cap': 'max GW pa'},inplace=True)
        df = round(df,2)
        return df


    # @lru_cache(maxsize=128)
    def prices_input(self):
        return DataFrame(
                    {
                    'wholesale prices': [round(a.wholesale_price,2) for a in self.auctionyear_set.all() ],
                    'gas prices': [round(a.gas_price,2) for a in self.auctionyear_set.all() ]
                    }, index=[a.year for a in self.auctionyear_set.all()]).T


    # @lru_cache(maxsize=128)
    def techs_input_html(self):
        df = self.techs_input()
        df.set_index(["pot", 'name','year'],inplace=True)
        return self.df_to_html(df)


    # @lru_cache(maxsize=128)
    def prices_input_html(self):
        df = self.prices_input()
        return self.df_to_html(df)
