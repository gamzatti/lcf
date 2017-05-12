from django.shortcuts import render, redirect, get_object_or_404
from django.forms import modelformset_factory, formset_factory
from .forms import ScenarioForm, PricesForm, PolicyForm
from django.core.exceptions import ObjectDoesNotExist
from .models import Scenario, AuctionYear, Pot, Technology, Policy
import time

from .helpers import process_policy_form, process_scenario_form
import lcf.dataframe_helpers as dfh
from lcf.exceptions import ScenarioError

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

from django.shortcuts import render_to_response
from django.template import RequestContext


# def handler404(request):
#     response = render_to_response('404.html', {},
#                                   context_instance=RequestContext(request))
#     response.status_code = 404
#     return response

# def error404(request):
#     scenarios = Scenario.objects.all()
#     recent_pk = Scenario.objects.all().order_by("-date")[0].pk
#     scenario = Scenario.objects.all().order_by("-date")[0]
#     context = {'scenario': scenario,
#                'policies': Policy.objects.all(),
#                'scenarios': scenarios,
#                'recent_pk': recent_pk,
#                }
#     template = loader.get_template('404.html')
#     return HttpResponse(content=template.render(context), content_type='text/html; charset=utf-8', status=404)

def scenario_new(request):
    file_error = None
    scenarios = Scenario.objects.all()
    recent_pk = Scenario.objects.all().order_by("-date")[0].pk
    scenario = Scenario.objects.all().order_by("-date")[0]
    if request.method == "POST":
        print("posting")
        scenario_form = ScenarioForm(request.POST, request.FILES)
        if scenario_form.is_valid():
            # process_scenario_form(scenario_form)
            # recent_pk = Scenario.objects.all().order_by("-date")[0].pk
            # return redirect('scenario_detail', pk=recent_pk)
            try:
                process_scenario_form(scenario_form)
            except Exception as e:
                file_error = e
                # print(e)
            else:
                recent_pk = Scenario.objects.all().order_by("-date")[0].pk
                return redirect('scenario_detail', pk=recent_pk)
    else:
        print("GETTING ")
        scenario_form = ScenarioForm()
    context = {'scenario': scenario,
               'policies': Policy.objects.all(),
               'scenarios': scenarios,
               'scenario_form': scenario_form,
               'recent_pk': recent_pk,
               'file_error': file_error
               }
    return render(request, 'lcf/scenario_new.html', context)

def policy_new(request):
    print("don't  cache me")
    scenarios = Scenario.objects.all()
    recent_pk = Scenario.objects.all().order_by("-date")[0].pk
    scenario = Scenario.objects.all().order_by("-date")[0]
    if request.method == "POST":
        policy_form = PolicyForm(request.POST, request.FILES)
        print("posting")
        if policy_form.is_valid():
            pl = process_policy_form(policy_form)
            return redirect('policy_detail', pk=pl.pk)
        else:
            print(policy_form.errors)

    else:
        print("GETTING policy form")
        policy_form = PolicyForm()

    context = {'scenario': scenario,
               'scenarios': scenarios,
               'policies': Policy.objects.all(),
               'policy_form': policy_form,
               'recent_pk': recent_pk,
               }
    return render(request, 'lcf/policy_new.html', context)

def policy_detail(request,pk):
    scenarios = Scenario.objects.all()
    recent_pk = Scenario.objects.all().order_by("-date")[0].pk
    scenario = Scenario.objects.all().order_by("-date")[0]
    try:
        policy = Policy.objects.get(pk=pk)
    except ObjectDoesNotExist:
        context = {'pk': pk,
                   'type': 'policy',
                   'policies': Policy.objects.all(),
                   'scenarios': scenarios,
                   'recent_pk': recent_pk,
                   }
        return render(request, '404.html', context)


    # price_effects = policy.df_for_display('prices')
    # techs_effects = policy.df_for_display('techs')
    techs_effects = policy.df_for_display()
    print('dont cache me')
    context = {'scenario': scenario,
               'scenarios': scenarios,
               'policies': Policy.objects.all(),
            #    'prices_effects': price_effects,
               'techs_effects': techs_effects,
               'policy': policy,
               'recent_pk': recent_pk,
               }
    return render(request, 'lcf/policy_detail.html', context)

def scenario_detail(request, pk=None):
    recent_pk = Scenario.objects.all().order_by("-date")[0].pk
    scenarios = Scenario.objects.all()
    if pk == None:
        pk = Scenario.objects.all().order_by("-date")[0].pk
    # scenario = get_object_or_404(Scenario.objects.prefetch_related('auctionyear_set__pot_set__technology_set', 'policies'), pk=pk)
    try:
        scenario = Scenario.objects.prefetch_related('auctionyear_set__pot_set__technology_set', 'policies').get(pk=pk) #new
    except ObjectDoesNotExist:
        context = {'pk': pk,
                   'type': 'scenario',
                   'policies': Policy.objects.all(),
                   'scenarios': scenarios,
                   'recent_pk': recent_pk,
                   }
        return render(request, '404.html', context)
    # print('instantiating a scenario object with prefetched attributes')
    # print(scenario.name)
    # print("[lease sss don't c a che me!")
    try:
        scenario.get_results()
        e = None
    except ScenarioError as e:
        context = {'scenario': scenario,
                   'policies': Policy.objects.all(),
                   'scenarios': scenarios,
                   'recent_pk': recent_pk,
                   'error_message': e,
                   }
        return render(request, 'lcf/scenario_error.html', context = context)
    else:
        chart = {}
        df = {}
        context = {'scenario': scenario,
                   'policies': Policy.objects.all(),
                   'scenarios': scenarios,
                   'recent_pk': recent_pk
                   }
        for column in ['awarded_cap', 'awarded_gen', 'cum_owed_v_wp', 'cum_owed_v_gas', 'cum_owed_v_absolute', 'cum_awarded_gen']:
            for num in [1,2]:
                pivot_table = getattr(scenario, 'pivot')(column, num)
                context["".join([column,str(num)])] = getattr(scenario, 'pivot_to_html')(pivot_table)

        for column in ["awarded_cap", "cum_awarded_gen"]:
            chart_data, options = scenario.df_to_chart_data(column)['chart_data'], scenario.df_to_chart_data(column)['options']
            data_source = SimpleDataSource(data=chart_data)
            context["".join([column,"_chart"])] = ColumnChart(data_source, options=options)


        print('rendering request')
        return render(request, 'lcf/scenario_detail.html', context)

def scenario_delete(request, pk):
    scenario = get_object_or_404(Scenario, pk=pk)
    scenario.delete()
    recent_pk = Scenario.objects.all().order_by("-date")[0].pk
    return redirect('scenario_detail', pk=recent_pk)

def scenario_delete_and_create_new(request, pk):
    scenario = get_object_or_404(Scenario, pk=pk)
    scenario.delete()
    return redirect('scenario_new')

def policy_delete(request, pk):
    policy = get_object_or_404(Policy, pk=pk)
    policy.delete()
    recent_pk = Scenario.objects.all().order_by("-date")[0].pk
    return redirect('scenario_detail', pk=recent_pk)

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

    writer.writerow(["............Inputs to model, before policies have been applied..........."])

    tech, prices, notes = scenario.inputs_download()
    writer.writerow(["Prices (£/MWh)"])
    writer.writerows(prices)
    writer.writerow([""])
    writer.writerow([""])
    writer.writerow(["Technology data"])
    writer.writerows(tech)
    writer.writerow([""])
    writer.writerow([""])
    writer.writerow(["Notes"])
    writer.writerows(notes)



    writer.writerow([""])
    writer.writerow([""])
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
    file = open('lcf/policy_template_su.csv')
    response = HttpResponse(file, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="policy_template_su.csv"'
    file.close()
    return response

def template(request):
    print("downloading template")
    file = open('lcf/template_with_sources.csv')
    response = HttpResponse(file, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="template_with_sources.csv"'
    file.close()
    return response
