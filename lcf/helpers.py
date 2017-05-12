from django.forms import modelformset_factory, formset_factory
from .forms import ScenarioForm, PricesForm
from .models import Scenario, AuctionYear, Pot, Technology
import time
import pandas as pd
import numpy as np
from pandas import DataFrame, Series
import csv
import io
from django.conf import settings
from functools import reduce, lru_cache
import lcf.dataframe_helpers as dfh


class PolicyMethodError(Exception):
    pass

def process_policy_form(policy_form):
    pl = policy_form.save()
    file = policy_form.cleaned_data['file']
    df = DataFrame(pd.read_csv(file))
    #df = df.dropna(axis=1,how="all")
    pl.effects = df.to_json()
    pl.save()
    return pl

def get_prices_from_form(s, scenario_form):
    new_wp = dfh.new_wp
    excel_wp = dfh.excel_wp
    wp_dict = {"new": new_wp, "excel": excel_wp, "other": None}
    wholesale_prices = wp_dict[scenario_form.cleaned_data['wholesale_prices']]
    if wholesale_prices == None:
        wholesale_prices = [float(w) for w in list(filter(None, re.split("[, \-!?:\t]+",scenario_form.cleaned_data['wholesale_prices_other'])))]
    excel_gas = dfh.excel_gas
    gas_dict = {"excel": excel_gas, "other": None}
    gas_prices = gas_dict[scenario_form.cleaned_data['gas_prices']]
    if gas_prices == None:
        gas_prices = [float(g) for g in list(filter(None, re.split("[, \-!?:\t]+",scenario_form.cleaned_data['gas_prices_other'])))]
    prices_df = DataFrame({'gas_prices': gas_prices, 'wholesale_prices': wholesale_prices},index=range(2020,2031))
    return prices_df



def create_auctionyear_and_pot_objects(prices_df,s):
    gas_prices = prices_df.gas_prices
    wholesale_prices = prices_df.wholesale_prices
    for i, y in enumerate(range(2020,s.end_year2+1)):
        a = AuctionYear.objects.create(year=y, scenario=s, gas_price=gas_prices[y], wholesale_price=wholesale_prices[y])
        for p in ['E', 'M', 'SN', 'FIT']:
            Pot.objects.create(auctionyear=a,name=p)


def interpolate_tech_df(tech_df):
    tech_df = tech_df.set_index(dfh.tech_policy_index['keys'])
    techs = list(tech_df.index.levels[0])
    new_index = [(t, y) for t in techs for y in range(2020,2031) ]
    tech_df = tech_df.reindex(index=new_index)
    try:
        tech_df[dfh.to_interpolate] = tech_df[dfh.to_interpolate].interpolate()
    except KeyError:
        raise
    else:
        tech_df[['pot_name', 'included']] = tech_df[['pot_name', 'included']].fillna(method="ffill")
        tech_df = tech_df.reset_index()
        return tech_df

def update_tech_with_policies(tech_df,policies):
    if len(policies) == 0:
        return tech_df
    else:
        tech_df.set_index(dfh.tech_policy_index['keys'], inplace=True)
        tech_df = tech_df[tech_df.included == True]
        included = tech_df.included
        tech_df = tech_df.drop('included',axis=1)
        pots = tech_df.pot_name
        tech_df = tech_df.drop('pot_name',axis=1)
        dfs = []
        for policy in policies:
            if policy.method != policies[0].method:
                raise PolicyMethodError("Unable to combine multiplication and subtraction policies in same scenario")
        for policy in policies:
            policy_df = policy.df().copy()
            policy_df = policy_df.set_index(dfh.tech_policy_index['keys'])
            policy_techs = list(policy_df.index.levels[0])
            index = [(t, y) for t in policy_techs for y in range(2020,2031) ]
            interpolated = policy_df.reindex(index=index).interpolate()
            fillna = 1 if policies[0].method == 'MU' else 0
            interpolated = interpolated.reindex(index=tech_df.index).fillna(fillna)
            interpolated.columns = tech_df.columns
            dfs.append(interpolated)
        if policies[0].method == 'MU':
            updated_tech_df = tech_df * reduce((lambda x, y : x * y), dfs)
        elif policies[0].method == 'SU':
            updated_tech_df = tech_df - reduce((lambda x, y : x + y), dfs)
        updated_tech_df['pot_name'] = pots
        updated_tech_df['included'] = included
        updated_tech_df = updated_tech_df.reset_index()
        return updated_tech_df

def create_technology_objects(df,s):
    print("creating technology objects")
    # df = df.reset_index()
    for index, row in df.iterrows():
        a = AuctionYear.objects.get(year = row.year, scenario = s)
        p = Pot.objects.get(name=row.pot_name, auctionyear = a)
        t = Technology.objects.create(
            name = row.tech_name,
            pot = p,
            included = row.included,
            min_levelised_cost = row.min_levelised_cost,
            max_levelised_cost = row.max_levelised_cost,
            strike_price = row.strike_price,
            load_factor = row.load_factor,
            max_deployment_cap = row.max_deployment_cap if pd.notnull(row.max_deployment_cap) else None,
            num_new_projects = row.num_new_projects if pd.notnull(row.num_new_projects) else None,
            project_gen = row.project_gen
        )


def get_notes(df):
    notes = df.copy()[1:]
    notes.columns = pd.Index(notes.iloc[0].values,name = None)
    notes = notes.dropna(how="all",axis=0)
    notes = notes.dropna(how="all",axis=1)
    notes = notes.iloc[1:]
    for col in dfh.note_cols:
        notes[col] = notes[col].astype(str)
    notes.index = np.arange(0,len(notes))
    return notes

def get_prices(df):
    df = df.copy()[1:13]
    df.columns = pd.Index(df.iloc[0].values,name = None)
    df = df.iloc[1:]
    df = df.dropna(how="all",axis=1)
    df = df.dropna(how="all",axis=0)
    df = df.copy().reindex(columns=dfh.note_and_prices_keys)
    for col in dfh.prices_keys:
        df[col] = df[col].astype(float)
    for col in dfh.prices_notes:
        df[col] = df[col].astype(str)
    df['year'] = df['year'].astype(int)
    df.index = np.arange(2020,2031)
    prices_df = df.copy().reindex(columns=[dfh.prices_keys])
    # print(prices_df.dtypes)
    return prices_df, df

def get_default_prices(new_wp=True):
    wp = dfh.new_wp if new_wp == True else dfh.excel_wp
    df = DataFrame({'year': np.arange(2020,2031), 'wholesale_prices': wp, 'gas_prices': dfh.excel_gas},index=range(2020,2031))
    # reindex(columns=dfh.prices_keys)
    df = df.copy().reindex(columns = dfh.note_and_prices_keys)

    for col in dfh.prices_keys:
        df[col] = df[col].astype(float)
    for col in dfh.prices_notes:
        df[col] = df[col].astype(str)
    # print(df)
    df['year'] = df['year'].astype(int)
    prices_df = df.copy().reindex(columns=[dfh.prices_keys])

    return prices_df, df


def get_techs(df):
    df = df.copy().dropna(how='all')
    for error in df.columns[-df.columns.isin(dfh.note_and_tech_keys)]:
        if not error.startswith('Unnamed'):
            raise KeyError("{} shouldn't be in column headers".format(error))
    df = df.reindex(columns = dfh.note_and_tech_keys)
    df.year, df.included, df.min_levelised_cost = df.year.astype(int), df.included.astype(bool), df.min_levelised_cost.astype(float)
    for col in dfh.note_columns:
        df[col] = df[col].astype(str)
    tech_df = df[dfh.tech_inputs_keys]
    tech_df = interpolate_tech_df(tech_df)
    # print(df)
    return tech_df, df


def parse_file(file,new_wp=True):
    df = pd.read_csv(file)

    if 'name' in df.columns:
        df.rename(columns={'name':'tech_name'}, inplace=True)
    try:
        end_of_techs = df.index[df.isin(['Prices','prices']).any(axis=1)][0]-1
    except IndexError:
        try:
            end_of_techs = df.index[df.isin(['Notes','notes']).any(axis=1)][0]-1
        except IndexError:
            # end_of_techs = df.index[df.isnull().all(axis=1)][0]
            end_of_techs = len(df)
    tech_df, original_tech_df_with_note_columns = get_techs(df[0:end_of_techs])
    try:
        start_of_prices = df.index[df.isin(['Prices','prices']).any(axis=1)][0]
    except IndexError:
        prices_df, original_prices_df_with_note_columns = get_default_prices(new_wp)
    else:
        prices_df, original_prices_df_with_note_columns = get_prices(df[start_of_prices:])

    try:
        start_of_notes = df.index[df.isin(['Notes', 'notes']).any(axis=1)][0]
    except IndexError:
        notes = DataFrame(columns = dfh.note_cols_inc_index) #blank dataframe
    else:
        notes = get_notes(df.loc[start_of_notes:])
    return tech_df, original_tech_df_with_note_columns, prices_df, original_prices_df_with_note_columns, notes
    # else:
    #
    #     original_tech_df_with_note_columns = df.copy()[0:end_of_techs]
    #     original_tech_df_with_note_columns.year, original_tech_df_with_note_columns.included = original_tech_df_with_note_columns.year.astype(int), original_tech_df_with_note_columns.included.astype(bool)
    #     for col in dfh.note_columns:
    #         original_tech_df_with_note_columns[col] = original_tech_df_with_note_columns[col].astype(str)
    #     else:
    #         notes = get_notes(df)
    #         original_tech_df_with_note_columns.min_levelised_cost = original_tech_df_with_note_columns.min_levelised_cost.astype(float)
    #         tech_df = original_tech_df_with_note_columns[dfh.tech_inputs_keys]
    #         tech_df = interpolate_tech_df(tech_df)
    #         return tech_df, original_tech_df_with_note_columns, prices_df, original_prices_df_with_note_columns, notes



# @lru_cache(maxsize=1024)
def process_scenario_form(scenario_form, new_wp=True):
    s = scenario_form.save()
    # prices_df = get_prices(s, scenario_form)
    policies = s.policies.all()
    file = scenario_form.cleaned_data['file']
    # print(pd.read_csv(file))
    try:
        tech_df, original_tech_df_with_note_columns, prices_df, original_prices_df_with_note_columns, notes = parse_file(file, new_wp)
    except (KeyError, AttributeError):
        s.delete()
        raise
    else:
        create_auctionyear_and_pot_objects(prices_df,s)
        s.csv_inc_notes = original_tech_df_with_note_columns.to_json()
        s.prices_inc_notes = original_prices_df_with_note_columns.to_json()
        s.notes = notes.to_json()
        s.save()
        try:
            updated_tech_df = update_tech_with_policies(tech_df,policies)
            create_technology_objects(updated_tech_df,s)
        except PolicyMethodError:
            s.delete()
            raise
