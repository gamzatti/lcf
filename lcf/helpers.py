from django.forms import modelformset_factory, formset_factory
from .forms import ScenarioForm, PricesForm, UploadFileForm
from .models import Scenario, AuctionYear, Pot, Technology
import time
import pandas as pd
import numpy as np
from pandas import DataFrame, Series
import csv
import io
from django.conf import settings
from functools import reduce


def create_technology_objects(df,s):
    t0 = time.time()
    print("creating technology objects")
    df = df.reset_index()
    for index, row in df.iterrows():
        a = AuctionYear.objects.get(year = row.listed_year, scenario = s)
        #print(a)
        p = Pot.objects.get(name=row.pot_name, auctionyear = a)
        #p = s.auctionyear_dict[year].pot_dict[pot_name]
        #print(p)
        #print(row.name)
        t = Technology.objects.create(
            name = row.tech_name,
            pot = p,
            #pot = s.auctionyear_dict[int(row.listed_year)].pot_dict[row.pot_name],
            included = row.included,
            min_levelised_cost = row.min_levelised_cost,
            max_levelised_cost = row.max_levelised_cost,
            strike_price = row.strike_price,
            load_factor = row.load_factor,
            max_deployment_cap = row.max_deployment_cap if pd.notnull(row.max_deployment_cap) else None,
            num_new_projects = row.num_new_projects if pd.notnull(row.num_new_projects) else None,
            project_gen = row.project_gen
        )
        #print(t.id)
    t1 = time.time()
    total = t1-t0
    print("iterrows",total)

def save_policy_to_db(file,pl):
    df = DataFrame(pd.read_csv(file))
    #df = df.dropna(axis=1,how="all")
    pl.effects = df.to_json()
    pl.save()

def update_tech_with_policies(tech_df,policy_dfs):
    if len(policy_dfs) == 0:
        return tech_df
    #tech_df = DataFrame(pd.read_csv("lcf/template.csv"))
    #policy_df = DataFrame(pd.read_csv("lcf/policy_template_no_sources_no_prices.csv"))
    #policy_df = DataFrame(pd.read_csv("lcf/policy_template_with_prices.csv"))
    tech_df.set_index(['tech_name','listed_year'], inplace=True)
    tech_df = tech_df[tech_df.included == True]
    included = tech_df.included
    tech_df = tech_df.drop('included',axis=1)
    pots = tech_df.pot_name
    tech_df = tech_df.drop('pot_name',axis=1)
    dfs = []
    for policy_df in policy_dfs:
        policy_df = policy_df[-policy_df.tech_name.isin(['wholesale_prices','gas_prices']) ]
        policy_df = policy_df.drop('price_change',axis=1)
        policy_df.set_index(['tech_name','listed_year'], inplace=True)
        policy_techs = list(policy_df.index.levels[0])
        index = [(t, y) for t in policy_techs for y in range(2020,2031) ]
        interpolated = policy_df.reindex(index=index).interpolate()
        interpolated = interpolated.reindex(index=tech_df.index).fillna(1)
        interpolated.columns = tech_df.columns
        dfs.append(interpolated)
    updated_tech_df = reduce((lambda x, y : x * y), dfs) * tech_df
    updated_tech_df['pot_name'] = pots
    updated_tech_df['included'] = included
    return updated_tech_df

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
    #print(prices_df)
    return prices_df

def update_prices_with_policies(prices_df,policy_dfs):
    if len(policy_dfs) == 0:
        return prices_df
    dfs = []
    for policy_df in policy_dfs:
        policy_df = policy_df[policy_df.tech_name.isin(['wholesale_prices','gas_prices']) ]
        policy_df = policy_df.reindex(columns=['tech_name', 'listed_year','price_change'])
        policy_df = policy_df.set_index(['tech_name','listed_year']).unstack(0)
        policy_df = policy_df.reindex(index=prices_df.index)
        interpolated = policy_df.interpolate()
        interpolated.columns = interpolated.columns.get_level_values(1)
        dfs.append(interpolated)
    updated_prices_df = reduce((lambda x, y : x * y), dfs) * prices_df
    return updated_prices_df

def create_auctionyear_and_pot_objects(updated_prices_df,s):
    gas_prices = updated_prices_df.gas_prices
    wholesale_prices = updated_prices_df.wholesale_prices
    for i, y in enumerate(range(2020,s.end_year2+1)):
        a = AuctionYear.objects.create(year=y, scenario=s, gas_price=gas_prices[y], wholesale_price=wholesale_prices[y])
        for p in ['E', 'M', 'SN', 'FIT']:
            Pot.objects.create(auctionyear=a,name=p)
    #s = Scenario.objects.all().prefetch_related('auctionyear_set__pot_set__technology_set').get(pk=s.pk)
