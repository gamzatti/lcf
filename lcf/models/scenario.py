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

    def __init__(self, *args, **kwargs):
        super(Scenario, self).__init__(*args, **kwargs)
        self._accounting_cost = None
        self._cum_awarded_gen_by_pot = None
        self._awarded_cost_by_tech = None
        self._gen_by_tech = None
        self._cap_by_tech = None

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



    def df_to_chart_data(self,df):
        chart_data = df.copy()
        chart_data['index_column'] = chart_data.index
        chart_data.loc['years_row'] = chart_data.columns
        chart_data = chart_data.reindex(index = ['years_row']+list(chart_data.index)[:-1], columns = ['index_column'] +list(chart_data.columns)[:-1])
        chart_data = chart_data.T.values.tolist()
        #print(chart_data)
        return {'title': chart_data, 'df': df}


    def get_or_make_chart_data(self,attribute, method):
        if self.__getattribute__(attribute) == None:
            methods = globals()['Scenario']
            meth = getattr(methods,method)
            df = meth(self)
            chart_data = self.df_to_chart_data(df)
            self.__setattr__(attribute, chart_data)
            return self.__getattribute__(attribute)
        elif self.__getattribute__(attribute) != None:
            return self.__getattribute__(attribute)


    def accounting_cost_df(self):
        index = ['Accounting cost', 'Cost v gas', 'Innovation premium']
        auctionyears = self.auctionyear_set.filter(year__gte=self.start_year)
        columns = [str(a.year) for a in auctionyears]
        accounting_costs = [round(a.cum_owed_v("wp")/1000,3) for a in auctionyears]
        cost_v_gas = [round(a.cum_owed_v("gas")/1000,3) for a in auctionyears]
        innovation_premium = [round(a.innovation_premium()/1000,3) for a in auctionyears]
        df = DataFrame([accounting_costs, cost_v_gas, innovation_premium], index=index, columns=columns)
        return df

    def cum_awarded_gen_by_pot_df(self):
        auctionyears = self.auctionyear_set.filter(year__gte=self.start_year)
        index = [pot.name for pot in auctionyears[0].active_pots()]
        data = { str(a.year) : [p.cum_awarded_gen() for p in a.active_pots()] for a in auctionyears }
        df = DataFrame(data=data, index=index)
        return df


    def awarded_cost_by_tech_df(self):
        auctionyears = self.auctionyear_set.filter(year__gte=self.start_year)
        index = [t.name for pot in auctionyears[0].active_pots() for t in pot.tech_set().order_by("name")]
        data = { str(a.year) : [t.awarded_cost for p in a.active_pots() for t in p.tech_set().order_by("name")] for a in auctionyears }
        df = DataFrame(data=data, index=index)
        return df



    def summary_gen_by_tech(self):
        if self._gen_by_tech:
            return self._gen_by_tech
        else:
            print('generating chart4')
            auctionyears = self.auctionyear_set.filter(year__gte=self.start_year)
            years = [a.year for a in auctionyears]
            tech_names = sorted(self.technology_form_helper()[0])
            title = ['year']
            title.extend(tech_names)
            df = DataFrame(columns=title, index=years)
            for a in auctionyears:
                for p in a.active_pots().all():
                    if p.auction_has_run == False:
                        p.run_auction()
                    for t in p.tech_set().all():
                        df.at[a.year,t.name] = t.awarded_gen
            ddf = df.copy()
            ddf['year'] = ddf.index
            #df['year'] = [datetime.date(i,1,1) for i in df.index]
            ddf['year'] = [str(i) for i in ddf.index]
            data = ddf.values.tolist()
            title = [title]
            title.extend(data)
            df = df.drop('year',axis=1).T
            self._gen_by_tech = {'title': title, 'df': df}
            return {'title': title, 'df': df}

    def summary_cap_by_tech(self):
        if self._cap_by_tech:
            return self._cap_by_tech
        else:
            print('generating chart5')
            auctionyears = self.auctionyear_set.filter(year__gte=self.start_year)
            years = [a.year for a in auctionyears]
            tech_names = sorted(self.technology_form_helper()[0])
            title = ['year']
            title.extend(tech_names)
            df = DataFrame(columns=title, index=years)
            for a in auctionyears:
                for p in a.active_pots().all():
                    for t in p.tech_set().all():
                        df.at[a.year,t.name] = t.awarded_gen/8.760/t.load_factor

            ddf = df.copy()
            ddf['year'] = ddf.index
            #df['year'] = [datetime.date(i,1,1) for i in df.index]
            ddf['year'] = [str(i) for i in ddf.index]
            data = ddf.values.tolist()
            title = [title]
            title.extend(data)
            df = df.drop('year',axis=1).T
            self._cap_by_tech = {'title': title, 'df': df}
            return {'title': title, 'df': df}

    def wholesale_prices(self):
        return str([round(a.wholesale_price,2) for a in self.auctionyear_set.all() ]).strip('[]')


    def accounting_cost_comparison(self):
        title = [['year', 'Accounting cost: '+self.name, 'DECC 2015 w/TCCP', 'Meets 90TWh (no TCCP)', 'Meets 90TWh']]
        auctionyears = self.auctionyear_set.filter(year__gte=self.start_year)
        years = [str(a.year) for a in auctionyears]
        accounting_costs = [a.cum_owed_v("wp")/1000 for a in auctionyears]
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
