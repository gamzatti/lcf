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
    tech_df = DataFrame(pd.read_csv("lcf/template.csv"))
    policy_df = DataFrame(pd.read_csv("lcf/policy_template_no_sources_no_prices.csv"))

    tech_df.set_index(['tech_name','listed_year'], inplace=True)
    tech_df = tech_df[tech_df.included == True]
    included = tech_df.included
    tech_df = tech_df.drop('included',axis=1)
    pots = tech_df.pot_name
    tech_df = tech_df.drop('pot_name',axis=1)

    dfs = []
    for policy_df in policy_dfs:
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
