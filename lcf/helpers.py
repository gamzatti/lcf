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


def handle_uploaded_file(file,s):
    t0 = time.time()
    data = pd.read_csv(file)
    df = DataFrame(data)
    print("creating technology objects")
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

def handle_policy_file(file,pl):
    df = DataFrame(pd.read_csv(file))
    df = df.dropna(axis=1,how="all")
    print(df)
    pl.effects = df.to_json()
    pl.save()
