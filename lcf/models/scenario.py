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
from lcf.exceptions import ScenarioError

class Scenario(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True, verbose_name="Description (optional)")
    date = models.DateTimeField(default=timezone.now)
    budget = models.FloatField(default=3.3, verbose_name="Budget period 1 (£bn)")
    budget2 = models.FloatField(blank=True, null=True, verbose_name="Budget period 2 (£bn) - leave blank to use same as period 1")
    percent_emerging = models.FloatField(default=0.6, verbose_name="Proportion in emerging pot")
    set_strike_price =  models.BooleanField(default=False, verbose_name="Generate strike price ourselves?")
    start_year1 = models.IntegerField(default=2021)
    end_year1 = models.IntegerField(default=2025, verbose_name="End of period 1")
    start_year2 = models.IntegerField(default=2026)
    end_year2 = models.IntegerField(default=2030)
    subsidy_free_p2 = models.BooleanField(default=False, verbose_name="Only subsidy-free CFDs for period 2")
    tidal_levelised_cost_distribution = models.BooleanField(default=True)
    excel_sp_error = models.BooleanField(default=False, verbose_name="Excel quirk: use future strike price rather than year contract agreed")
    excel_2020_gen_error = models.BooleanField(default=False, verbose_name="Excel quirk: count cumulative generation from 2020 but cumulative costs from 2021")
    excel_nw_carry_error = models.BooleanField(default=False, verbose_name="Excel quirk: add an extra £89m to the budget each year, forgetting it's been spent on the previous year's negawatts FIT")
    excel_include_previous_unsuccessful_nuclear = models.BooleanField(default=True, verbose_name="Excel quirk: allow previously unsuccessful projects in separate negotiations to be considered in future years")
    excel_include_previous_unsuccessful_all = models.BooleanField(default=False, verbose_name="Excel quirk: allow previously unsuccessful projects for ALL technologies to be considered in future years")

    excel_external_clearing_price = models.BooleanField(default=False, verbose_name="Excel quirk: take clearing price as external input rather than calculating ourselves")

    excel_quirks = models.BooleanField(default=False, verbose_name="Include all Excel quirks")

    results = models.TextField(null=True,blank=True)
    intermediate_results = models.TextField(null=True, blank=True)
    intermediate_budget_results = models.TextField(null=True, blank=True)

    policies = models.ManyToManyField(Policy, blank=True)

    csv_inc_notes = models.TextField(null=True,blank=True)
    prices_inc_notes = models.TextField(null=True,blank=True)
    notes = models.TextField(null=True, blank=True)


    def __str__(self):
        return self.name

    def __init__(self, *args, **kwargs):
        super(Scenario, self).__init__(*args, **kwargs)
        self.auctionyear_dict = { auctionyear.year : auctionyear for auctionyear in self.auctionyear_set.all() }
        self.flat_tech_dict = { t.name + str(t.pot.auctionyear.year) : t for a in self.auctionyear_dict.values() for p in a.pot_dict.values() for t in p.technology_dict.values() }
        # if self.excel_quirks == True:
            # self.excel_sp_error = True
            # self.excel_2020_gen_error = True
            # self.excel_nw_carry_error = True
            # self.excel_include_previous_unsuccessful_nuclear = True
            # self.excel_include_previous_unsuccessful_all = True
            # self.excel_external_clearing_price = True
            # self.save()



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
                p.run_relevant_auction()



    def get_results(self,column=None):
        column_names = dfh.tech_results_keys
        if self.results == None:
            print('calculating')
            try:
                self.run_auctions()
            except ValueError:
                raise ScenarioError("Possible problem: your template included/excluded technologies in individual years, yet you didn't switch OFF the 'allow previously unsuccessful projects for all technologies' quirk.")
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
            if len(results) == 0:
                raise ScenarioError('Problem unknown, sorry!')
            else:
                self.results = results.to_json()
                self.save()
        else:
            print('retrieving from db')
            results = pd.read_json(self.results)
            if 'tech_name' not in results.columns:
                results = results.rename(columns={'name':'tech_name'})
            results = results.reindex(columns=column_names).sort_index()

            if len(results) == 0:
                print('scenario not created correctly')
                raise ScenarioError('scenario not created correctly')
        if column:
            results = results[dfh.tech_results_index['keys']+[column]]
        return results


    def df_to_chart_data(self,column,summary=False):
        df = self.get_results(column)
        df = df[df.year != 2020]
        # print(column,df)
        if column in ['cum_owed_v_wp', 'cum_owed_v_gas', 'cum_owed_v_absolute']:
            df[column] = df[column]/1000
        df = df.set_index(dfh.tech_results_index['keys']).sort_index()
        df = df.unstack(0)
        df.columns = df.columns.get_level_values(1)
        df.index = df.index.get_level_values(1)
        df = df.reset_index()
        if summary==True:
            df.loc['summary'] = df.sum()
            df.tech_name['summary'] = "Total"
            df = df['summary':'summary']
        #     df = DataFrame(df.loc['summary']).T
        df.loc['years_row'] = df.columns.astype('str')
        df = df.sort_values('tech_name') # annoying?
        df = df.reindex(index = ['years_row']+list(df.index)[:-1])
        chart_data = df.T.values.tolist()
        unit = dfh.abbrev[column]['unit']
        options = {'title': None, 'vAxis': {'title': unit}, 'width':1500, 'height':400}
        options_small = {'title': None, 'vAxis': {'title': unit}, 'width':800, 'height':400, 'legend': 'bottom'}
        if summary==True:
            options_small['legend'] = {'position': 'none'}

        return {'chart_data': chart_data, 'options': options, 'options_small': options_small}


    # @lru_cache(maxsize=128)
    def pivot(self,column,period_num=None):
        df = self.get_results(column)
        df[column] = df[column]/1000 if dfh.abbrev.loc['unit',column] == '£bn' else df[column]
        title = dfh.abbrev.loc['title+unit',column]
        df.columns = dfh.tech_results_index['keys'] + [title]
        auctionyear_years = [auctionyear.year for auctionyear in self.period(period_num)]
        df = df.loc[df.year.isin(auctionyear_years)]
        dfsum = df.groupby(['year','pot_name'],as_index=False).sum()
        dfsum['tech_name']='_Subtotal'
        dfsum_outer = df.groupby(['year'],as_index=False).sum()
        dfsum_outer['tech_name']='Total'
        dfsum_outer['pot_name']='Total'
        result = dfsum.append(df)
        result = dfsum_outer.append(result)
        if column == "cum_owed_v_gas":
            dfsum_outer['tech_name']='Total'
            dfsum_outer['pot_name']='Total'
            ip_df = df[df.pot_name != 'Feed-in-tariff']
            ip_df_sum_outer = ip_df.groupby(['year'],as_index=False).sum()
            ip_df_sum_outer['tech_name'] = '__Innovation premium (ignores negawatts)'
            ip_df_sum_outer['pot_name'] = '__Innovation premium (ignores negawatts)'
            result = ip_df_sum_outer.append(result)
        result = result.set_index(dfh.tech_results_index['keys']).sort_index()
        result = result.unstack(0)
        result.index.names = ['Pot','Technology']
        result.columns.names = ['', 'Year']

        return result





    def techs_input(self):
        techs = pd.concat([t.fields_df() for t in self.flat_tech_dict.values() ])
        techs = techs.set_index('id')
        df = techs.sort_values(dfh.tech_inputs_index['keys']).drop(['pot','name'], axis=1)
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
        html = df.style.format("{:.3f}").applymap(highlight_subtotal, subset = pd.IndexSlice[pd.IndexSlice[:,['_Subtotal','Total', '__Innovation premium (ignores negawatts)']],:]).render()
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
        print('techs input returned')
        return self.df_to_html(df)


    # @lru_cache(maxsize=128)
    def prices_input_html(self):
        df = self.prices_input()
        df.index = dfh.prices_columns
        return self.df_to_html(df)

    def get_original_data_inc_sources(self):
        sources = pd.read_json(self.csv_inc_notes)
        sources = sources.reindex(columns = dfh.note_and_tech_keys).sort_index()
        return sources

    def get_original_prices_inc_sources(self):
        prices = pd.read_json(self.prices_inc_notes)
        prices = prices.reindex(columns = dfh.note_and_prices_keys).sort_index()
        return prices

    def inputs_download(self):
        try:
            tech = self.get_original_data_inc_sources()
            tech.columns = dfh.note_and_tech_columns
        except TypeError:
            tech = self.techs_input()
            tech.columns = dfh.tech_inputs_columns
        headers = DataFrame(tech.columns).T
        headers.columns = tech.columns
        tech = pd.concat([headers,tech])
        tech = tech.replace(np.nan,"")

        tech = tech.values

        try:
            prices = self.get_original_prices_inc_sources()
        except TypeError:
            prices = self.prices_input().T
            prices.columns = dfh.prices_columns
            prices['Year'] = prices.index
            prices = prices.reindex(columns=['Year'] +  dfh.prices_columns)
        else:
            prices.columns = dfh.prices_and_notes_columns

        headers = DataFrame(prices.columns).T
        headers.columns = prices.columns
        prices = pd.concat([headers,prices]).T
        prices = prices.replace(np.nan,"")
        prices = prices.values

        try:
            notes = self.get_notes()

        except TypeError:
            notes = DataFrame()
        else:
            notes.columns = dfh.note_titles_inc_index
            headers = DataFrame(notes.columns).T
            headers.columns = notes.columns
            notes = pd.concat([headers,notes])
            notes = notes.values
            # notes = notes.replace(np.nan,"")

        return tech, prices, notes

    def original_html(self,data_type):
        if data_type == 'prices':
            cols = dfh.prices_keys
            notes = dfh.prices_notes
            try:
                sources = self.get_original_prices_inc_sources()
            except (TypeError, ValueError):
                print('no csv_inc_notes field found')
                return self.prices_input_html()

        elif data_type == 'techs':
            cols = dfh.note_pair_columns
            notes = dfh.note_columns
            try:
                sources = self.get_original_data_inc_sources()
                # print(sources)
            except TypeError:
                print('no csv_inc_notes field found')
                return self.techs_input_html()

        sources[notes] = sources[notes].replace('nan', 0)
        sources[notes] = sources[notes].astype(int)
        sources[cols] = sources[cols].round(2).astype(str)
        sources[notes] = np.where(sources[notes] != 0, " [" + sources[notes].astype(str) + "]", "")
        col_pairs = list(zip(cols,notes))
        for pair in col_pairs:
            col, note = pair
            sources[col] = sources[col] + "<a href='#refs'><span class='note'>" + sources[note] + "</span></a>"
        sources = sources.drop(notes,axis=1)
        if data_type == 'techs':
            sources.columns = dfh.tech_inputs_columns
            sources = sources.set_index(dfh.tech_inputs_index['titles'])
            return self.df_to_html(sources)
        elif data_type == 'prices':
            sources.columns = ['Year'] + dfh.prices_columns
            sources = sources.set_index('Year')
            # print(sources)
            sources = sources.T
            return self.df_to_html(sources)



    def original_data_inc_sources_html(self):
        return self.original_html('techs')


    def original_prices_inc_sources_html(self):
        return self.original_html('prices')


    def get_notes(self):
        notes = pd.read_json(self.notes)
        notes = notes.reindex(columns = dfh.note_cols_inc_index).sort_index()
        notes = notes.replace('nan', '')
        return notes

    def notes_html(self):
        try:
            notes = self.get_notes()
            notes = notes.set_index('num')
            notes.link = "<a href=" + notes.link + ">" + notes.link + "</a>"
            # local_path = "\\\\victoria\public\Themes\Climate and Energy Futures\DR0145 Decarbonisation - 2015-17 Consortium\LCF future\LCF analysis\Modelling\\"
            # local_path = "file:///victoria/public/Themes/Climate and Energy Futures/DR0145 Decarbonisation - 2015-17 Consortium/LCF future/LCF analysis/Modelling/"
            local_path = "file:///P:/Themes/Climate and Energy Futures/DR0145 Decarbonisation - 2015-17 Consortium/LCF future/LCF analysis/Modelling/"
            notes.local_link = "<a href=\"" + local_path + notes.local_link + "\">" + notes.local_link + "</a>"
            notes.columns = dfh.note_titles
            notes.index.name = 'Ref num'
            return self.df_to_html(notes)
        except:
            print('no notes found')
            return None

    def quirks(self):
        quirks = ['excel_sp_error', 'excel_2020_gen_error', 'excel_nw_carry_error', 'excel_include_previous_unsuccessful_nuclear', 'excel_include_previous_unsuccessful_all', 'excel_external_clearing_price']
        verbose_quirks = [Scenario._meta.get_field(quirk).verbose_name.replace('Excel quirk: ', '') for quirk in quirks ]
        quirk_dict = dict(zip(quirks, verbose_quirks))
        if self.excel_quirks == True:
            return verbose_quirks
        else:
            quirks = [ quirk_dict[quirk] for quirk in quirks if getattr(self, quirk)]
            if len(quirks) == 0:
                return None
            else:
                return quirks

    def emerging(self):
        return int(self.percent_emerging * 100)

    def mature(self):
        return int((1 - self.percent_emerging) * 100)


    def get_intermediate_results(self):
        column_names = dfh.tech_results_keys
        if self.intermediate_results == None:
            print('calculating intermediate results')
            # try:
            years, pots, pot_budgets, technologies, t_objects = [], [], [], [], []
            # for t in self.flat_tech_dict.values():
            for a in self.auctionyear_dict.values():
                for p in a.pot_dict.values():
                    for t in p.technology_dict.values():
                        years.append(t.pot.auctionyear.year)
                        pots.append(t.pot.name)
                        pot_budgets.append(round(t.pot.budget(),2))
                        technologies.append(t.name)
                        t_objects.append(t)

            frame = DataFrame({'Year': years, 'Pot': pots, 'Pot budget': pot_budgets, 'Technology': technologies, 't_object': t_objects})
            frame = frame.reindex(columns = ['Year', 'Pot', 'Pot budget', 'Technology', 't_object'])
            available = frame.copy()
            available['Stage'] = 'available'

            eligible = frame.copy()
            eligible['Stage'] = 'eligible'

            successful = frame.copy()
            successful['Stage'] = 'successful'

            frame = pd.concat([available, eligible, successful])
            frame['Stage'] = frame['Stage'].astype('category', categories = ['available', 'eligible', 'successful'], ordered=True)
            frame['Number of projects'] = frame.apply( lambda t : t.t_object.project_summary(t.Stage, 'num'), axis=1 )
            frame['Equivalent generation (GWh)'] = frame.apply( lambda t : t.t_object.project_summary(t.Stage, 'gen'), axis=1 )
            frame['Equivalent cost (£m)'] = frame.apply( lambda t : t.t_object.project_summary(t.Stage, 'cost'), axis=1 )
            frame['Max bid (£/MWh)'] = frame.apply( lambda t : t.t_object.project_summary(t.Stage, 'max_bid'), axis=1 )
            frame['Clearing price (£/MWh)'] = frame.apply( lambda t : t.t_object.project_summary(t.Stage, 'clearing_price'), axis=1 )
            frame = frame.drop('t_object', axis=1)
            frame = frame.replace('nan', 'N/A')
            intermediate_results = frame
            intermediate_results.index = range(0,len(intermediate_results.index))

            self.intermediate_results = frame.to_json()
            self.save()
        else:
            print('retrieving intermediate_results from db')
            intermediate_results = pd.read_json(self.intermediate_results)
        intermediate_results = intermediate_results.set_index(['Year', 'Pot', 'Pot budget', 'Technology', 'Stage'])
        intermediate_results = intermediate_results.sort_index()
        intermediate_results = intermediate_results.reindex(columns = ['Number of projects' ,'Equivalent generation (GWh)', 'Equivalent cost (£m)', 'Max bid (£/MWh)', 'Clearing price (£/MWh)'])

        return intermediate_results

    def intermediate_results_html(self):
        frame = self.get_intermediate_results()
        return self.df_to_html(frame)

    def clear(self):
        self.results = None
        self.intermediate_results = None
        self.intermediate_budget_results = None
        self.save()
        # self.get_results()
        # self.get_intermediate_results()
        # self.get_intermediate_budget_results()

    def get_intermediate_budget_results(self):
        columns = ["year", "starting budget", "carried from previous year", "sum of starting and carried over",
                   "spent on negotiations", "spent on FIT", "remaining for auction",
                   "budget emerging ({}%)".format(round(self.percent_emerging * 100)), "spent on emerging", "unspent emerging", "budget for mature", "spent on mature",  "unspent mature", "total unspent"]
        if self.intermediate_budget_results == None:
            print('calculating intermediate budget results')
            intermediate_budget_results = DataFrame([[a.year,
                                          a.starting_budget(),
                                          a.previous_year_unspent(),
                                          a.budget_all(),
                                          a.pot_dict['SN'].awarded_cost(),
                                          a.pot_dict['FIT'].awarded_cost(),
                                          a.budget(),
                                          a.pot_dict['E'].budget(),
                                          a.pot_dict['E'].awarded_cost(),
                                          a.pot_dict['E'].unspent(),
                                          a.pot_dict['M'].budget(),
                                          a.pot_dict['M'].awarded_cost(),
                                          a.pot_dict['M'].unspent(),
                                          a.unspent() ]
                                          for a in self.auctionyear_dict.values() ],
                                          columns = columns)
            intermediate_budget_results.index = range(0,len(intermediate_budget_results.index))
            intermediate_budget_results = intermediate_budget_results.drop(0)
            self.intermediate_budget_results = intermediate_budget_results.to_json()
            self.save()
        else:
            print('retrieving budget results from db')
            intermediate_budget_results = pd.read_json(self.intermediate_budget_results)
        intermediate_budget_results = intermediate_budget_results.reindex(columns=columns).sort_index()
        intermediate_budget_results = intermediate_budget_results.set_index("year")
        # intermediate_budget_results = round(intermediate_budget_results,2)
        return intermediate_budget_results

    def intermediate_budget_results_html(self):
        return self.df_to_html(self.get_intermediate_budget_results())
