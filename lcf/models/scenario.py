from django.db import models
from django.utils import timezone
import pandas as pd
import numpy as np
from pandas import DataFrame, Series
from functools import lru_cache
import datetime
import time
from django_pandas.io import read_frame
import lcf.dataframe_helpers as dfh

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
    percent_emerging = models.FloatField(default=0.6, verbose_name="Percentage in emerging pot")
    set_strike_price =  models.BooleanField(default=False, verbose_name="Generate strike price ourselves?")
    start_year1 = models.IntegerField(default=2021)
    end_year1 = models.IntegerField(default=2025, verbose_name="End of period 1")
    start_year2 = models.IntegerField(default=2026)
    end_year2 = models.IntegerField(default=2030)
    subsidy_free_p2 = models.BooleanField(default=False, verbose_name="Only subsidy-free CFDs for period 2")
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

    def period(self, num=None):
        if num == 1:
            ran = range(self.start_year1, self.end_year1+1)
        elif num == 2:
            ran = range(self.start_year2, self.end_year2+1)
        else:
            ran = range(self.start_year1, self.end_year2+1)
        return [ auctionyear for auctionyear in self.auctionyear_dict.values() if auctionyear.year in ran ]

    def run_auctions(self):
        for a in self.auctionyear_dict.values():
            for p in a.pot_dict.values():
                p.run_auction()

    def get_results(self,column=None):
        column_names = dfh.tech_results_keys
        if self.results == None:
            self.run_auctions()
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
                        columns = column_names)
            results = results.sort_values(dfh.tech_results_index['keys'])
            results.index = range(0,len(results.index))
            self.results = results.to_json()
            self.save()
        else:
            # print('retrieving from db')
            results = pd.read_json(self.results).reindex(columns=column_names).sort_index()
        if column:
            results = results[dfh.tech_results_index['keys']+[column]]
        return results


    def df_to_chart_data(self,column):
        df = self.get_results(column)
        df = df.set_index(dfh.tech_results_index['keys']).sort_index()
        df = df.unstack(0)
        df.columns = df.columns.get_level_values(1)
        df.index = df.index.get_level_values(1)
        df = df.reset_index()
        df.loc['years_row'] = df.columns.astype('str')
        df = df.sort_values('name') # annoying?
        df = df.reindex(index = ['years_row']+list(df.index)[:-1])
        chart_data = df.T.values.tolist()
        unit = dfh.abbrev[column]['unit']
        options = {'title': None, 'vAxis': {'title': unit}, 'width':1000, 'height':400}
        return {'chart_data': chart_data, 'options': options}

    # @lru_cache(maxsize=128)
    def pivot(self,column,period_num=None):
        # print('building pivot table')
        df = self.get_results(column)
        df[column] = df[column]/1000 if dfh.abbrev.loc['unit',column] == '£bn' else df[column]
        title = dfh.abbrev.loc['title+unit',column]
        df.columns = dfh.tech_results_index['keys'] + [title]
        auctionyear_years = [auctionyear.year for auctionyear in self.period(period_num)]
        df = df.loc[df.year.isin(auctionyear_years)]

        dfsum = df.groupby(['year','pot_name'],as_index=False).sum()
        dfsum['name']='_Subtotal'
        dfsum_outer = df.groupby(['year'],as_index=False).sum()
        dfsum_outer['name']='Total'
        dfsum_outer['pot_name']='Total'
        result = dfsum.append(df)
        result = dfsum_outer.append(result)
        if column == "cum_owed_v_gas":
            ip_df = df[df.pot_name != 'Feed-in-tariff']
            ip_df_sum_outer = ip_df.groupby(['year'],as_index=False).sum()
            ip_df_sum_outer['name'] = '__Innovation premium'
            ip_df_sum_outer['pot_name'] = '__Innovation premium'
            result = ip_df_sum_outer.append(result)
        result = result.set_index(dfh.tech_results_index['keys']).sort_index()
        result = result.unstack(0)
        result.index.names = ['Pot','Technology']
        result.columns.names = ['', 'Year']

        return result





    def techs_input(self):
        techs = pd.concat([t.fields_df() for t in self.flat_tech_dict.values() ])
        techs = techs.set_index('id')
        df = techs.sort_values(dfh.tech_inputs_index['keys']).drop('pot', axis=1)
        df = df.reindex(columns =dfh.tech_inputs_keys)
        df.columns = dfh.tech_inputs_columns
        df = round(df,2)
        return df


    def apply_table_classes(self, html):
        html = html.replace('<table id=', '<table class="table table-striped table-condensed" id=')
        return html

    # @lru_cache(maxsize=128)
    def df_to_html(self,df):
        html = df.style.render()
        html = self.apply_table_classes(html)
        return html

    # @lru_cache(maxsize=128)
    def pivot_to_html(self,df):
        def highlight_total(s):
            is_max = s == s.max()
            return ['font-weight: bold;' if v else '' for v in is_max]
        def highlight_subtotal(val):
            return 'font-weight: bold;'
        html = df.style.format("{:.3f}").applymap(highlight_subtotal, subset = pd.IndexSlice[pd.IndexSlice[:,['_Subtotal','Total', '__Innovation premium']],:]).render()
        html = self.apply_table_classes(html)
        html = html.replace('_Subtotal','Subtotal')
        html = html.replace('__Innovation', 'Innovation')
        return html


    # @lru_cache(maxsize=128)
    def prices_input(self):
        return DataFrame(
                    [[round(a.wholesale_price,2) for a in self.auctionyear_set.all() ],
                    [round(a.gas_price,2) for a in self.auctionyear_set.all() ]],
                    columns=[a.year for a in self.auctionyear_set.all()])


    # @lru_cache(maxsize=128)
    def techs_input_html(self):
        df = self.techs_input()
        df.set_index(dfh.tech_inputs_index['titles'],inplace=True)
        return self.df_to_html(df)


    # @lru_cache(maxsize=128)
    def prices_input_html(self):
        df = self.prices_input()
        df.index = dfh.prices_columns
        return self.df_to_html(df)
