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
from functools import reduce
import lcf.dataframe_helpers as dfh

def process_policy_form(policy_form):
    pl = policy_form.save()
    file = policy_form.cleaned_data['file']
    df = DataFrame(pd.read_csv(file))
    #df = df.dropna(axis=1,how="all")
    pl.effects = df.to_json()
    pl.save()
    return pl

def get_prices(s, scenario_form):
    new_wp = [38.5, 41.8, 44.2, 49.8, 54.6, 56.2, 53.5, 57.0, 54.5, 52.2, 55.8]
    excel_wp = [48.5400340402009, 54.285722954952, 58.4749297906221, 60.1487865144807, 64.9687482891174, 67.2664653151834, 68.6947628422952, 69.2053146319398, 66.3856598431318, 65.5255963446292, 65.5781764014488]
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
            policy_df = policy.df().copy()
            # method = policy.method
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
        #raise exception if policies have different methods
        updated_tech_df['pot_name'] = pots
        updated_tech_df['included'] = included
        return updated_tech_df

def create_technology_objects(df,s):
    t0 = time.time()
    print("creating technology objects")
    df = df.reset_index()
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

def process_scenario_form(scenario_form):
    s = scenario_form.save()
    prices_df = get_prices(s, scenario_form)
    create_auctionyear_and_pot_objects(prices_df,s)
    policies = s.policies.all()
    tech_df = pd.read_csv(scenario_form.cleaned_data['file'])
    updated_tech_df = update_tech_with_policies(tech_df,policies)
    create_technology_objects(updated_tech_df,s)
