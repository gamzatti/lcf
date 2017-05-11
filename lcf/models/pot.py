from django.db import models
from django.utils import timezone
import pandas as pd
import numpy as np
from pandas import DataFrame, Series
from functools import lru_cache
import datetime
import inspect
import time
import timeit
import lcf.dataframe_helpers as dfh
from .technology import Technology
#from django_pandas.managers import DataFrameManager
from lcf.exceptions import ScenarioError

class Pot(models.Model):
    POT_CHOICES = [ (k, v) for k, v in dfh.pot_choices.items() ]
    auctionyear = models.ForeignKey('lcf.auctionyear', default=232)
    name = models.CharField(max_length=3, choices=POT_CHOICES, default='E')
    #objects = DataFrameManager()

    def __str__(self):
        return str((self.auctionyear, self.name))

    def __init__(self, *args, **kwargs):
        super(Pot, self).__init__(*args, **kwargs)
        self._percent = None
        self.awarded_gen = 0
        self.auction_has_run = False
        self.budget_result = None
        self.awarded_cost_result = None
        self.awarded_gen_result = None
        self.auction_results = None
        self.auction_budget_result = None
        self.cum_owed_v_wp = None
        self.cum_owed_v_gas = None
        self.cum_owed_v_absolute = None
        self.previously_funded_projects_results = None
        self.cum_awarded_gen_result = None
        self.technology_dict = { t.name : t for t in self.technology_set.all() }
        self.active_technology_dict = { t.name : t for t in self.technology_dict.values() if t.included == True }

    #helper methods
    def tech_set(self):
        #return self.technology_set.filter(included=True)
        return [ t for t in self.technology_dict.values() if t.included == True ]

    def period_pots_calc(self):
        if self.auctionyear.year == 2020:
            num = 0
            pots = [self]
        else:
            years = self.auctionyear.period()
            num = self.auctionyear.period_num()
            pots = [a.pot_dict[self.name] for a in years]
        return {'num': num, 'pots': pots}

    def period_pots(self):
        return self.period_pots_calc()['pots']

    def period_num(self):
        return self.period_pots_calc()['num']


    def cum_future_pots(self):
        if self.auctionyear.year == 2020:
            return [self]
        else:
            return [p for p in self.period_pots() if p.auctionyear.year >= self.auctionyear.year ]


    #budget methods
    #@lru_cache(maxsize=128)
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

    #@lru_cache(maxsize=128)
    def budget(self):
        if self.budget_result != None:
            return self.budget_result
        else:
            if self.name == "M" or self.name == "E":
                result = self.auction_budget() * self.percent()
            elif self.name == "SN" or self.name == "FIT":
                result = np.nan
            self.budget_result = result
            return result

    #@lru_cache(maxsize=128)
    def auction_budget(self):
        if self.auction_budget_result:
            return self.auction_budget_result
        else:
            self.auction_budget_result = self.auctionyear.budget()
            if self.name == "E":
                #sister_pot = Pot.objects.get(auctionyear=self.auctionyear,name="M")
                sister_pot = self.auctionyear.pot_dict["M"]
            elif self.name == "M":
                #sister_pot = Pot.objects.get(auctionyear=self.auctionyear,name="M")
                sister_pot = self.auctionyear.pot_dict["M"] # should be E surely?
            sister_pot.auction_budget_result = self.auctionyear.budget()
            return self.auction_budget_result


    #@lru_cache(maxsize=128)
    def unspent(self):
        if self.name == "SN" or self.name == "FIT":
            return 0
        if self.auctionyear.year == 2020:
            return 0
        else:
            return self.budget() - self.awarded_cost()

    #auction methods
    def previous_year(self):
        return self.auctionyear.scenario.auctionyear_dict[self.auctionyear.year-1].pot_dict[self.name]

    @lru_cache(maxsize=128)
    def previously_funded_projects(self):
        if self.previously_funded_projects_results != None:
            return pd.read_json(self.previously_funded_projects_results)
        else:
            if self.auctionyear.year != 2020:
                previously_funded_projects = self.previous_year().cum_run_auction()[(self.previous_year().cum_run_auction().funded_this_year == True) | (self.previous_year().cum_run_auction().previously_funded == True)]
            else:
                previously_funded_projects = DataFrame()
            self.previously_funded_projects_results = previously_funded_projects.to_json()
        return previously_funded_projects

    # def projects(self):
    #     return self.run_relevant_auction()
    #

    @lru_cache(maxsize=128)
    def run_relevant_auction(self):
        if len(self.active_technology_dict) == 0:
            self.awarded_cost_result = 0
            self.awarded_gen_result = 0
            self.auction_has_run = "n/a"
            # self.auction_results = DataFrame().to_json()

        elif self.auction_has_run == True:
            # print('decoding json')
            # non_cum_column_order = ['levelised_cost', 'gen', 'technology', 'strike_price', 'affordable', 'pot', 'listed_year', 'eligible', 'difference', 'cost', 'attempted_cum_cost', 'funded_this_year', 'attempted_project_gen', 'attempted_cum_gen']
            non_cum_column_order = ['levelised_cost', 'gen', 'technology', 'strike_price', 'affordable', 'pot', 'year', 'eligible', 'difference', 'cost', 'attempted_cum_cost', 'funded_this_year', 'attempted_project_gen', 'attempted_cum_gen']
            # cum_column_order = ['levelised_cost', 'gen', 'technology', 'strike_price', 'affordable', 'pot', 'listed_year', 'previously_funded', 'eligible', 'difference', 'cost', 'attempted_cum_cost', 'funded_this_year', 'attempted_project_gen', 'attempted_cum_gen']
            cum_column_order = ['levelised_cost', 'gen', 'technology', 'strike_price', 'affordable', 'pot', 'year', 'previously_funded', 'eligible', 'difference', 'cost', 'attempted_cum_cost', 'funded_this_year', 'attempted_project_gen', 'attempted_cum_gen']
            if self.auctionyear.scenario.excel_quirks == True or self.auctionyear.scenario.excel_include_previous_unsuccessful_all == True or (self.auctionyear.scenario.excel_include_previous_unsuccessful_nuclear and self.name == "SN"):
                column_order = cum_column_order
            else:
                column_order = non_cum_column_order
            df = pd.read_json(self.auction_results).sort_values(['strike_price', 'levelised_cost']).reindex(columns=column_order)
            df.gen, df.attempted_project_gen, df.attempted_cum_gen = df.gen.astype(float), df.attempted_project_gen.astype(float), df.attempted_cum_gen.astype(float)
            return df

        else:
            if self.auctionyear.scenario.excel_quirks == True or self.auctionyear.scenario.excel_include_previous_unsuccessful_all == True or (self.auctionyear.scenario.excel_include_previous_unsuccessful_nuclear and self.name == "SN"):
                # print('running auction', self.name, self.auctionyear.year,'caller name:', inspect.stack()[1][3])
                return self.cum_run_auction()
            else:
                # print('running non_cum auction', self.name, self.auctionyear.year,'caller name:', inspect.stack()[1][3])
                return self.non_cum_run_auction()

    @lru_cache(maxsize=128)
    def cum_run_auction(self):
        gen = 0
        cost = 0
        budget = self.budget()
        previously_funded_projects = self.previously_funded_projects()
        projects = self.concat_projects()
        projects.sort_values(['strike_price', 'levelised_cost'],inplace=True)
        projects['previously_funded'] = np.where(projects.index.isin(previously_funded_projects.index),True,False)
        projects['eligible'] = (projects.previously_funded == False) & projects.affordable
        projects['difference'] = projects.strike_price if self.name == "FIT" else projects.strike_price - self.auctionyear.wholesale_price
        projects['cost'] = np.where(projects.eligible == True, projects.gen/1000 * projects.difference, 0)
        projects['attempted_cum_cost'] = np.cumsum(projects.cost)
        if self.name == "SN" or self.name == "FIT":
            projects['funded_this_year'] = (projects.eligible)
        elif self.name == "E" or self.name == "M":
            if self.period_num() == 2 and self.auctionyear.scenario.subsidy_free_p2 == True:
                print('applying subsidy free restriction')
                projects['funded_this_year'] = (projects.eligible) & (projects.attempted_cum_cost < budget) & (projects.strike_price < self.auctionyear.gas_price)
            else:
                projects['funded_this_year'] = (projects.eligible) & (projects.attempted_cum_cost < budget)
        projects['attempted_project_gen'] = np.where(projects.eligible == True, projects.gen, 0)
        projects['attempted_cum_gen'] = np.cumsum(projects.attempted_project_gen)
        self.update_variables(projects)
        return projects


    @lru_cache(maxsize=128)
    def non_cum_run_auction(self):
        gen = 0
        cost = 0
        budget = self.budget()
        projects = self.non_cum_concat_projects()
        projects.sort_values(['strike_price', 'levelised_cost'],inplace=True)
        projects['eligible'] = projects.affordable
        projects['difference'] = projects.strike_price if self.name == "FIT" else projects.strike_price - self.auctionyear.wholesale_price
        projects['cost'] = np.where(projects.eligible == True, projects.gen/1000 * projects.difference, 0)
        projects['attempted_cum_cost'] = np.cumsum(projects.cost)
        if self.name == "SN" or self.name == "FIT":
            projects['funded_this_year'] = (projects.eligible)
        elif self.name == "E" or self.name == "M":
            if self.period_num() == 2 and self.auctionyear.scenario.subsidy_free_p2 == True:
                print('applying subsidy free restriction')
                projects['funded_this_year'] = (projects.eligible) & (projects.attempted_cum_cost < budget) & (projects.strike_price < self.auctionyear.gas_price)
            else:
                projects['funded_this_year'] = (projects.eligible) & (projects.attempted_cum_cost < budget)
        projects['attempted_project_gen'] = np.where(projects.eligible == True, projects.gen, 0)
        projects['attempted_cum_gen'] = np.cumsum(projects.attempted_project_gen)
        self.update_variables(projects)
        return projects

    def concat_projects(self):
        try:
            res = pd.concat([t.projects() for t in self.active_technology_dict.values() ])
        except ValueError:
            raise
        else:
            return res

    def non_cum_concat_projects(self):
        res = pd.concat([t.non_cum_projects() for t in self.active_technology_dict.values() ])
        return res

    def update_variables(self,projects):
        successful_projects = projects[(projects.funded_this_year == True)]
        for t in self.technology_dict.values():
            t_projects = successful_projects[successful_projects.technology == t.name]
            t.awarded_gen = t_projects.attempted_project_gen.sum()/1000 if pd.notnull(t_projects.attempted_project_gen.sum()) else 0
            t.awarded_cap = t.awarded_gen/8.760/t.load_factor
            t.awarded_cost = sum(t_projects.cost)

            # if self.auctionyear.year == self.auctionyear.scenario.end_year1 + 1: #is this even doing anything?
            #     t.cum_owed_v_wp = 0
            #     t.cum_owed_v_gas = 0
            #     t.cum_owed_v_absolute = 0
            #     t.cum_awarded_gen = 0
            for future_t in t.cum_future_techs():
                gas = future_t.pot.auctionyear.gas_price
                if (self.auctionyear.scenario.excel_sp_error == True or self.auctionyear.scenario.excel_quirks == True) and (self.name == "E" or self.name == "SN" or self.name == "M"):
                    strike_price = future_t.strike_price
                else:
                    strike_price = t.strike_price
                if t.name == "NW":
                    wp = 0
                    # gas = 0
                else:
                    wp = future_t.pot.auctionyear.wholesale_price
                if self.auctionyear.year == self.auctionyear.scenario.start_year2:
                    tmid = self.auctionyear.scenario.auctionyear_dict[self.auctionyear.scenario.end_year1].pot_dict[t.pot.name].technology_dict[t.name]
                    future_t.cum_awarded_gen = tmid.cum_awarded_gen
                future_t.cum_owed_v_wp += t.awarded_gen * (strike_price - wp)
                future_t.cum_owed_v_gas += t.awarded_gen * (strike_price - gas)
                future_t.cum_owed_v_absolute += t.awarded_gen * strike_price
                future_t.cum_awarded_gen += t.awarded_gen ## need to deal with excel_2020_gen_error
                if (self.auctionyear.scenario.excel_2020_gen_error == True or self.auctionyear.scenario.excel_quirks == True) and self.auctionyear.year == self.auctionyear.scenario.start_year1 and t.pot.name != "FIT":
                    t2020 = self.auctionyear.scenario.auctionyear_dict[2020].pot_dict[t.pot.name].technology_dict[t.name]
                    future_t.cum_awarded_gen += t2020.awarded_gen
        self.awarded_cost_result = sum(successful_projects.cost)
        self.awarded_gen_result = sum(successful_projects.attempted_project_gen)/1000
        self.auction_has_run = True
        self.auction_results = projects.to_json()


    #@lru_cache(maxsize=128)
    def awarded_cost(self):
        if self.awarded_cost_result != None:
            res = self.awarded_cost_result
        else:
            self.run_relevant_auction()
            res = self.awarded_cost_result
            if res == None:
                raise ScenarioError('{} {} auction not running correctly'.format(self.name, self.auctionyear.year))
        return res
