from django.forms import modelformset_factory, formset_factory
from .forms import ScenarioForm, PricesForm, TechnologyStringForm, UploadFileForm
from .models import Scenario, AuctionYear, Pot, Technology
import time
import pandas as pd
import numpy as np
from pandas import DataFrame, Series
import csv
import io
from django.conf import settings

def handle_uploaded_file2(file):
    t0 = time.time()
    csv_file = file
    decoded_file = csv_file.read().decode('utf-8')
    io_string = io.StringIO(decoded_file)
    s = Scenario.objects.create(name="test")
    for row in csv.DictReader(io_string, quotechar='|'):
        kwargs = {}
        pot_name = row['pot']
        year = int(row['year'])
        a,created = AuctionYear.objects.get_or_create(year = year, scenario = s)
        p,created = Pot.objects.get_or_create(name=pot_name, auctionyear = a)
        kwargs['pot'] = p
        kwargs['name'] = row['name']
        kwargs['min_levelised_cost'] = float(row['min LCOE'])
        kwargs['max_levelised_cost'] = float(row['max LCOE'])
        kwargs['strike_price'] = float(row['strike price'])
        kwargs['load_factor'] = float(row['load factor'])
        kwargs['max_deployment_cap'] = float(row['max GW pa'])
        kwargs['num_new_projects'] = int(row['number of new projects']) if row['number of new projects'] != "" else None
        kwargs['project_gen'] = float(row['project size GWh'])
        t = Technology.objects.create_technology(**kwargs)
        t.save()
    t1 = time.time()
    total = t1-t0
    print("csv.DictReader",total) #6.880906581878662

def handle_uploaded_file3(file):
    t0 =time.time()
    data = pd.read_csv(file)
    df = DataFrame(data)
    s = Scenario.objects.create(name="test")
    for index, row in df.iterrows():
        kwargs = {}
        pot_name = row['pot']
        year = int(row['year'])
        a,created = AuctionYear.objects.get_or_create(year = year, scenario = s)
        p,created = Pot.objects.get_or_create(name=pot_name, auctionyear = a)
        kwargs['pot'] = p
        kwargs['name'] = row['name']
        kwargs['min_levelised_cost'] = float(row['min LCOE'])
        kwargs['max_levelised_cost'] = float(row['max LCOE'])
        kwargs['strike_price'] = float(row['strike price'])
        kwargs['load_factor'] = float(row['load factor'])
        kwargs['max_deployment_cap'] = float(row['max GW pa'])
        kwargs['num_new_projects'] = int(row['number of new projects']) if pd.notnull(row['number of new projects']) else None
        kwargs['project_gen'] = float(row['project size GWh'])
        t = Technology.objects.create_technology(**kwargs)
        t.save()
    t1 = time.time()
    total = t1-t0
    print("pandas",total) #6.874750375747681

def handle_uploaded_file(file):
    t0 =time.time()
    data = pd.read_csv(file)
    df = DataFrame(data)
    s = Scenario.objects.create(name="test")
    for row_id, row in enumerate(df.values):
        kwargs = {}
        pot_name = row[0]
        year = int(row[2])
        a,created = AuctionYear.objects.get_or_create(year = year, scenario = s)
        p,created = Pot.objects.get_or_create(name=pot_name, auctionyear = a)
        kwargs['pot'] = p
        kwargs['name'] = row[1]
        kwargs['min_levelised_cost'] = float(row[4])
        kwargs['max_levelised_cost'] = float(row[5])
        kwargs['strike_price'] = float(row[6])
        kwargs['load_factor'] = float(row[7])
        kwargs['max_deployment_cap'] = float(row[8])
        kwargs['num_new_projects'] = int(row[9]) if pd.notnull(row[9]) else None
        kwargs['project_gen'] = float(row[10])
        t = Technology.objects.create_technology(**kwargs)
        t.save()
    t1 = time.time()
    total = t1-t0
    print("numpy",total) #6.731263160705566

#http://stackoverflow.com/questions/37688054/saving-a-pandas-dataframe-to-a-django-model
# def handle_uploaded_file(file):
#     t0 =time.time()
#     data = pd.read_csv(file)
#     df = DataFrame(data)
#     s = Scenario.objects.create(name="test")
#     for year in range(2020,2031):
#         a,created = AuctionYear.objects.get_or_create(year = year, scenario = s)
#         for pot_name in ["E", "M", "SN", "FIT"]
#             p,created = Pot.objects.get_or_create(name=pot_name, auctionyear = a)
#
#     user = settings.DATABASES['default']['USER']
#     password = settings.DATABASES['default']['PASSWORD']
#     database_name = settings.DATABASES['default']['NAME']
#
#     database_url = 'postgresql://{user}:{password}@localhost:5432/{database_name}'.format(
#         user=user,
#         password=password,
#         database_name=database_name,
#     )
#
#     engine = create_engine(database_url, echo=False)
#     df.to_sql(Technology, con=engine)
#     t1 = time.time()
#     total = t1-t0
#     print("SQL",total)
