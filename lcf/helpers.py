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

def get_prices(s, scenario_form):
    new_wp = dfh.new_wp
    excel_wp = dfh.excel_wp
    wp_dict = {"new": new_wp, "excel": excel_wp, "other": None}
    wholesale_prices = wp_dict[scenario_form.cleaned_data['wholesale_prices']]
    if wholesale_prices == None:
        wholesale_prices = [float(w) for w in list(filter(None, re.split("[, \-!?:\t]+",scenario_form.cleaned_data['wholesale_prices_other'])))]
    excel_gas = [85.0, 87.0, 89.0, 91.0, 93.0, 95.0, 95.0, 95.0, 95.0, 95.0, 95.0]
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
    # or start_of_notes = df.index[df.pot_name.isnull()][-1]+1
    start_of_notes = df.index[df.pot_name.isin(["Notes", "notes"])][0]+1
    notes = df.copy()[start_of_notes:]
    notes.columns = pd.Index(notes.iloc[0].values,name = None)
    for col in dfh.note_cols:
        notes[col] = notes[col].astype(str)
    notes = notes.iloc[1:]
    notes = notes.dropna(how="all",axis=1)
    notes.index = np.arange(0,len(notes))
    return notes

def parse_file(file):
    df = pd.read_csv(file)
    try:
        end_of_techs = df.index[df.pot_name.isnull()][0]
    except IndexError:
        tech_df = df
        original_tech_df_with_note_columns = tech_df.reindex(columns = dfh.note_and_tech_keys)
        notes = DataFrame(columns = dfh.note_cols_inc_index)
        tech_df = interpolate_tech_df(tech_df)
        return tech_df, original_tech_df_with_note_columns, notes
    else:
        original_tech_df_with_note_columns = df.copy()[0:end_of_techs]
        original_tech_df_with_note_columns.year, original_tech_df_with_note_columns.included = original_tech_df_with_note_columns.year.astype(int), original_tech_df_with_note_columns.included.astype(bool)
        for col in dfh.note_columns:
            original_tech_df_with_note_columns[col] = original_tech_df_with_note_columns[col].astype(str)
        else:
            notes = get_notes(df)
            original_tech_df_with_note_columns.min_levelised_cost = original_tech_df_with_note_columns.min_levelised_cost.astype(float)
            tech_df = original_tech_df_with_note_columns[dfh.tech_inputs_keys]
            tech_df = interpolate_tech_df(tech_df)
            return tech_df, original_tech_df_with_note_columns, notes



# @lru_cache(maxsize=1024)
def process_scenario_form(scenario_form):
    s = scenario_form.save()
    prices_df = get_prices(s, scenario_form)
    create_auctionyear_and_pot_objects(prices_df,s)
    policies = s.policies.all()
    file = scenario_form.cleaned_data['file']
    try:
        tech_df, original_tech_df_with_note_columns, notes = parse_file(file)
    except (KeyError, AttributeError):
        s.delete()
        raise
    else:
        s.csv_inc_notes = original_tech_df_with_note_columns.to_json()
        s.notes = notes.to_json()
        s.save()
        try:
            updated_tech_df = update_tech_with_policies(tech_df,policies)
            create_technology_objects(updated_tech_df,s)
        except PolicyMethodError:
            s.delete()
            raise
