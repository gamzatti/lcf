from django.shortcuts import render, redirect, get_object_or_404
from django.forms import modelformset_factory, formset_factory
from .forms import ScenarioForm, PricesForm, UploadFileForm, PolicyForm

from .models import Scenario, AuctionYear, Pot, Technology, Policy
import time
from .helpers import save_policy_to_db, get_prices, update_prices_with_policies, create_auctionyear_and_pot_objects, update_tech_with_policies, create_technology_objects
import lcf.dataframe_helpers as dfh
from django_pandas.io import read_frame

from django.http import HttpResponse
import pandas as pd
import numpy as np
from pandas import DataFrame, Series
import re
import csv
from graphos.sources.simple import SimpleDataSource
from graphos.renderers.gchart import LineChart, ColumnChart
from django.db import connection


def scenario_new(request):
    scenarios = Scenario.objects.all()
    print('d')
    recent_pk = Scenario.objects.all().order_by("-date")[0].pk
    scenario = Scenario.objects.all().order_by("-date")[0]
    if request.method == "POST":
        print("posting")
        upload_form = UploadFileForm(request.POST, request.FILES)
        scenario_form = ScenarioForm(request.POST)

        if upload_form.is_valid() and scenario_form.is_valid():
            s = scenario_form.save()
            prices_df = get_prices(s, scenario_form)
            policy_dfs = [ pl.df() for pl in s.policies.all() ]
            updated_prices_df = update_prices_with_policies(prices_df, policy_dfs)
            create_auctionyear_and_pot_objects(updated_prices_df,s)
            tech_df = pd.read_csv(request.FILES['file'])
            updated_tech_df = update_tech_with_policies(tech_df,policy_dfs)
            create_technology_objects(updated_tech_df,s)
            recent_pk = Scenario.objects.all().order_by("-date")[0].pk
            return redirect('scenario_detail', pk=recent_pk)
        else:
            print(scenario_form.errors)
            print(upload_form.errors)
    else:
        print("GETTING ")
        scenario_form = ScenarioForm()
        upload_form = UploadFileForm()
    context = {'scenario': scenario,
               'policies': Policy.objects.all(),
               'scenarios': scenarios,
               'scenario_form': scenario_form,
               'recent_pk': recent_pk,
               'upload_form' : upload_form,
               }
    return render(request, 'lcf/scenario_new.html', context)

def policy_new(request):
    print("don't  cache me")
    scenarios = Scenario.objects.all()
    recent_pk = Scenario.objects.all().order_by("-date")[0].pk
    scenario = Scenario.objects.all().order_by("-date")[0]
    if request.method == "POST":
        policy_form = PolicyForm(request.POST)
        upload_form = UploadFileForm(request.POST, request.FILES)
        print("posting")
        if policy_form.is_valid() and upload_form.is_valid():
            print('forms are valid')
            pl = policy_form.save()
            file = request.FILES['file']
            save_policy_to_db(file,pl)
            return redirect('policy_detail', pk=pl.pk)
        else:
            print(policy_form.errors)
            print(upload_form.errors)

    else:
        print("GETTING policy form")
        policy_form = PolicyForm()
        upload_form = UploadFileForm()

    context = {'scenario': scenario,
               'scenarios': scenarios,
               'policies': Policy.objects.all(),
               'policy_form': policy_form,
               'recent_pk': recent_pk,
               'upload_form' : upload_form,
               }
    return render(request, 'lcf/policy_new.html', context)

def policy_detail(request,pk):
    scenarios = Scenario.objects.all()
    recent_pk = Scenario.objects.all().order_by("-date")[0].pk
    scenario = Scenario.objects.all().order_by("-date")[0]
    policy = Policy.objects.get(pk=pk)
    price_effects = policy.df_for_display('prices')
    techs_effects = policy.df_for_display('techs')
    print('dont cache')
    context = {'scenario': scenario,
               'scenarios': scenarios,
               'policies': Policy.objects.all(),
               'prices_effects': price_effects,
               'techs_effects': techs_effects,
               'policy': policy,
               'recent_pk': recent_pk,
               }
    return render(request, 'lcf/policy_detail.html', context)

def scenario_delete(request, pk):
    scenario = get_object_or_404(Scenario, pk=pk)
    scenario.delete()
    recent_pk = Scenario.objects.all().order_by("-date")[0].pk
    return redirect('scenario_detail', pk=recent_pk)

def policy_delete(request, pk):
    policy = get_object_or_404(Policy, pk=pk)
    policy.delete()
    recent_pk = Scenario.objects.all().order_by("-date")[0].pk
    return redirect('scenario_detail', pk=recent_pk)

def scenario_detail(request, pk=None):
    if pk == None:
        pk = Scenario.objects.all().order_by("-date")[0].pk
    #scenario = get_object_or_404(Scenario,pk=pk)
    #print("without prefetching")
    scenario = Scenario.objects.prefetch_related('auctionyear_set__pot_set__technology_set', 'policies').get(id=pk)
    print('instantiating a scenario object with prefetched attributes')
    print(scenario.name)
    print("[lease sss don't c a che me!")
    scenario.get_results()

    recent_pk = Scenario.objects.all().order_by("-date")[0].pk
    scenarios = Scenario.objects.all()
    chart = {}
    df = {}
    context = {'scenario': scenario,
               'policies': Policy.objects.all(),
               'scenarios': scenarios,
               'recent_pk': recent_pk
               }
    context['techs_input_html'] = scenario.techs_input_html()
    context['prices_input_html'] = scenario.prices_input_html()
    context['tech_cap_pivot'] = scenario.pivot_to_html(scenario.pivot('awarded_cap',1))
    context['tech_cap_pivot2'] = scenario.pivot_to_html(scenario.pivot('awarded_cap',2))
    context['tech_gen_pivot'] = scenario.pivot_to_html(scenario.pivot('awarded_gen',1))
    context['tech_gen_pivot2'] = scenario.pivot_to_html(scenario.pivot('awarded_gen',2))
    context['tech_cum_owed_v_wp_pivot'] = scenario.pivot_to_html(scenario.pivot('cum_owed_v_wp',1))
    context['tech_cum_owed_v_wp_pivot2'] = scenario.pivot_to_html(scenario.pivot('cum_owed_v_wp',2))
    context['tech_cum_owed_v_gas_pivot'] = scenario.pivot_to_html(scenario.pivot('cum_owed_v_gas',1))
    context['tech_cum_owed_v_gas_pivot2'] = scenario.pivot_to_html(scenario.pivot('cum_owed_v_gas',2))
    context['tech_cum_owed_v_absolute_pivot'] = scenario.pivot_to_html(scenario.pivot('cum_owed_v_absolute',1))
    context['tech_cum_owed_v_absolute_pivot2'] = scenario.pivot_to_html(scenario.pivot('cum_owed_v_absolute',2))
    context['tech_cum_awarded_gen_pivot'] = scenario.pivot_to_html(scenario.pivot('cum_awarded_gen',1))
    context['tech_cum_awarded_gen_pivot2'] = scenario.pivot_to_html(scenario.pivot('cum_awarded_gen',2))


    for column in ["awarded_cap", "cum_awarded_gen"]:
        chart_data, options = scenario.df_to_chart_data(column)['chart_data'], scenario.df_to_chart_data(column)['options']
        data_source = SimpleDataSource(data=chart_data)
        context["".join([column,"_chart"])] = ColumnChart(data_source, options=options)


    print('rendering request')
    return render(request, 'lcf/scenario_detail.html', context)

def scenario_download(request,pk):
    print("downloading")
    scenario = get_object_or_404(Scenario,pk=pk)
    scenarios = Scenario.objects.all()
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="data.csv"'
    writer = csv.writer(response)
    auctionyears = scenario.period(1)
    df_techs = scenario.get_results()
    tech_data = df_techs.values.tolist()
    tech_col_names = dfh.tech_results_columns
    writer.writerow(["............Scenario details............"])
    writer.writerow(['Name', scenario.name])
    writer.writerow(['Description', scenario.description])
    writer.writerow(['Budget', scenario.budget])
    writer.writerow(['Percent in emerging pot', scenario.percent_emerging])
    writer.writerow([""])
    writer.writerow([""])
    writer.writerow(["............Inputs to model, after policies have been applied..........."])
    inputs = [
               ('Prices (£/MWh)', scenario.prices_input()),
               ('Technology data', scenario.techs_input()),
               ]
    for df_pair in inputs:
        title = [df_pair[0]]
        writer.writerow(title)
        if df_pair[0] == 'Prices (£/MWh)':
            headers = ['']
        else:
            headers = []
        headers.extend(df_pair[1].columns)
        writer.writerow(headers)
        for i in range(len(df_pair[1].index)):
            row = [df_pair[1].index[i]]
            row.extend(df_pair[1].iloc[i])
            if df_pair[0] == 'Technology data':
                row = row[1:]
            writer.writerow(row)
        writer.writerow([])
    writer.writerow(["............Policies............"])
    for pl in scenario.policies.all():
        writer.writerow([pl.name])
        writer.writerow([pl.description])
        df = pl.df_for_download()
        policy_column_names = list(df.columns)
        writer.writerow(policy_column_names)
        writer.writerows(df.values.tolist())
        writer.writerow([''])
    writer.writerow([''])
    writer.writerow(['............Raw output............'])
    writer.writerow(['Technology'])
    writer.writerow(tech_col_names)
    writer.writerows(tech_data)
    return response

def policy_template(request):
    print("downloading policy template")
    file = open('lcf/policy_template_with_prices.csv')
    response = HttpResponse(file, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="policy_template_with_prices.csv"'
    file.close()
    return response

def template(request):
    print("downloading template")
    file = open('lcf/template.csv')
    response = HttpResponse(file, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="template.csv"'
    file.close()
    return response
