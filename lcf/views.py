from django.shortcuts import render, redirect, get_object_or_404
from django.forms import modelformset_factory, formset_factory
from .forms import ScenarioForm, PricesForm, TechnologyStringForm, UploadFileForm
from .models import Scenario, AuctionYear, Pot, Technology
import time
from .helpers import handle_uploaded_file

from django.http import HttpResponse
import pandas as pd
import numpy as np
from pandas import DataFrame, Series
import re
import csv
from graphos.sources.simple import SimpleDataSource
from graphos.renderers.gchart import LineChart, ColumnChart

def scenario_new(request,pk):
    scenarios = Scenario.objects.all()
    scenario_original = get_object_or_404(Scenario, pk=pk)
    queryset = Technology.objects.filter(pot__auctionyear__scenario=scenario_original)
    techs = Technology.objects.filter(pot__auctionyear=scenario_original.auctionyear_set.all()[0])
    num_techs = techs.count()
    TechnologyStringFormSet = formset_factory(TechnologyStringForm, extra=0, max_num=10)
    recent_pk = Scenario.objects.all().order_by("-date")[0].pk

    if request.method == "POST":
        scenario_form = ScenarioForm(request.POST)
        prices_form = PricesForm(request.POST)
        string_formset = TechnologyStringFormSet(request.POST)

        if string_formset.is_valid() and scenario_form.is_valid() and prices_form.is_valid():
            scenario_new = scenario_form.save()
            wholesale_prices = [float(w) for w in list(filter(None, re.split("[, \-!?:\t]+",prices_form.cleaned_data['wholesale_prices'])))]
            gas_prices = [float(g) for g in list(filter(None, re.split("[, \-!?:\t]+",prices_form.cleaned_data['gas_prices'])))]
            for i, y in enumerate(range(2020,scenario_new.end_year2+1)):
                a = AuctionYear.objects.create(year=y, scenario=scenario_new, gas_price=gas_prices[i], wholesale_price=wholesale_prices[i])
                for p in [p.name for p in scenario_original.auctionyear_set.all()[0].pot_set.all()]:
                #for p in ['E', 'M', 'SN', 'FIT']:
                    Pot.objects.create(auctionyear=a,name=p)
            q = Pot.objects.filter(auctionyear__scenario=scenario_new)

            for form in string_formset:
                fields = [f.name for f in Technology._meta.get_fields() if f.name not in ["pot", "id", "name", "included", "awarded_gen", "awarded_cost"]]
                field_data = { field : [float(s) for s in list(filter(None, re.split("[, \-!?:\t]+",form.cleaned_data[field])))] for field in fields  }
                for i, a in enumerate(AuctionYear.objects.filter(scenario=scenario_new)):
                    kwargs = { field : field_data[field][i] if field_data[field] != [] else None for field in field_data }
                    kwargs['name'] = form.cleaned_data['name']
                    kwargs['included'] = form.cleaned_data['included']
                    kwargs['pot'] = q.filter(auctionyear=a).get(name=form.cleaned_data['pot'])
                    Technology.objects.create_technology(**kwargs)
            return redirect('scenario_detail', pk=scenario_new.pk)
        else:
            print(string_formset.errors)
            print(scenario_form.errors)
            print(prices_form.errors)
    print('rendering scenario form')
    scenario_form = ScenarioForm(instance=scenario_original)
    print('finding initial prices')
    initial_prices = {'gas_prices': str([a.gas_price for a in scenario_original.auctionyear_set.all()]).strip('[]'), 'wholesale_prices': str([a.wholesale_price for a in scenario_original.auctionyear_set.all() ]).strip('[]')}
    print('rendering pries form')
    prices_form = PricesForm(initial=initial_prices)
    print('finding technology data')
    names = scenario_original.technology_form_helper()[0]
    print('rendering technology form')
    technology_form_helper = scenario_original.technology_form_helper()[1]
    string_formset = TechnologyStringFormSet(initial=technology_form_helper)
    print('assembling context')
    context = {'scenario': scenario_original,
               'scenarios': scenarios,
               'scenario_form': scenario_form,
               'prices_form': prices_form,
               'string_formset': string_formset,
               'names': names,
               'recent_pk': recent_pk}
    return render(request, 'lcf/scenario_new.html', context)


def upload(request):
    scenarios = Scenario.objects.all()
    recent_pk = Scenario.objects.all().order_by("-date")[0].pk
    scenario = Scenario.objects.all().order_by("-date")[0]
    if request.method == "POST":
        print("posting")
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            handle_uploaded_file(request.FILES['file'])

            return redirect('scenario_detail', pk=recent_pk)
        else:
            print(form.errors)
    else:
        print("GETTING ")
        form = UploadFileForm()
    context = {'scenario': scenario,
               'scenarios': scenarios,
               'recent_pk': recent_pk,
               'form' : form,
               }
    return render(request, 'lcf/upload.html', context)

def scenario_delete(request, pk):
    scenario = get_object_or_404(Scenario, pk=pk)
    scenario.delete()
    recent_pk = Scenario.objects.all().order_by("-date")[0].pk
    return redirect('scenario_detail', pk=recent_pk)


def scenario_detail(request, pk=None):
    t0 = time.time() * 1000
    if pk == None:
        scenario = Scenario.objects.all().order_by("-date")[0]
    else:
        scenario = get_object_or_404(Scenario,pk=pk)
    for p in Pot.objects.filter(auctionyear__scenario=scenario):
        p.run_auction()

    recent_pk = Scenario.objects.all().order_by("-date")[0].pk
    scenarios = Scenario.objects.all()
    chart = {}
    df = {}
    context = {'scenario': scenario,
               'scenarios': scenarios,
               'recent_pk': recent_pk
               }
    meth_list_long = ["cumulative_costs","cum_awarded_gen_by_pot","awarded_cost_by_tech","gen_by_tech","cap_by_tech"]
    meth_list = ["cumulative_costs","cum_awarded_gen_by_pot","gen_by_tech"]
    t1 = time.time() * 1000
    for meth in meth_list:
        chart[meth] = {}
        df[meth] = {}
        for period_num in [1,2]:
            results = scenario.get_or_make_chart_data(meth,period_num)
            data =results['data']
            data_source = SimpleDataSource(data=data)
            options = results['options']
            if meth == "cumulative_costs" or meth == "cum_awarded_gen_by_pot":
                chart[meth][period_num] = LineChart(data_source, options=options, height=400, width="100%")
            else:
                chart[meth][period_num] = ColumnChart(data_source, options=options, height=400, width="100%")
            df[meth][period_num] = results['df'].to_html(classes="table table-striped table-condensed") # slowest line; consider saving in db
            context["".join([meth,"_chart",str(period_num)])] = chart[meth][period_num]
            context["".join([meth,"_df",str(period_num)])] = df[meth][period_num]
    t2 = time.time() * 1000
    print(t2-t1,t1-t0)
    return render(request, 'lcf/scenario_detail.html', context)

def scenario_download(request,pk):
    print("downloading")
    scenario = get_object_or_404(Scenario,pk=pk)
    scenarios = Scenario.objects.all()

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="data.csv"'

    writer = csv.writer(response)
    df_list = [
               ('Cumulative costs (£bn) (2021-2025)', scenario.cumulative_costs(1)['df']),
               ('Cumulative costs (£bn) (2026-2030)', scenario.cumulative_costs(2)['df']),
               ('Cumulative generation (TWh) (2021-2025)', scenario.cum_awarded_gen_by_pot(1)['df']),
               ('Cumulative generation (TWh) (2026-2030)', scenario.cum_awarded_gen_by_pot(2)['df']),
               ('Cost of new generation awarded (£m) (2021-2025)', scenario.awarded_cost_by_tech(1)['df']),
               ('Cost of new generation awarded (£m) (2026-2030)', scenario.awarded_cost_by_tech(2)['df']),
               ('Generation (TWh) (2021-2025)', scenario.gen_by_tech(1)['df']),
               ('Generation (TWh) (2026-2030)', scenario.gen_by_tech(2)['df']),
               ('Capacity (GW) (2021-2025)', scenario.cap_by_tech(1)['df']),
               ('Capacity (GW) (2026-2030)', scenario.cap_by_tech(2)['df']),
               ('Inputs - Prices (£/MWh)', scenario.prices_input()),
               ('Inputs - Technology data', scenario.techs_input()),
               ]

    writer.writerow([scenario.name])
    writer.writerow(['Budget', scenario.budget])
    writer.writerow(['Percent in emerging pot', scenario.percent_emerging])
    writer.writerow([''])

    for df_pair in df_list:
        title = [df_pair[0]]
        writer.writerow(title)
        headers = ['']
        headers.extend(df_pair[1].columns)
        writer.writerow(headers)
        for i in range(len(df_pair[1].index)):
            row = [df_pair[1].index[i]]
            row.extend(df_pair[1].iloc[i])
            writer.writerow(row)
        writer.writerow([])

    return response
