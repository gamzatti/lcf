from django.shortcuts import render, redirect, get_object_or_404
from django.forms import modelformset_factory, formset_factory
from .forms import ScenarioForm, PricesForm, TechnologyStringForm
from .models import Scenario, AuctionYear, Pot, Technology
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
    if request.method == "POST":
        scenario_form = ScenarioForm(request.POST)
        prices_form = PricesForm(request.POST)
        string_formset = TechnologyStringFormSet(request.POST)

        if string_formset.is_valid() and scenario_form.is_valid() and prices_form.is_valid():
            scenario_new = scenario_form.save()
            wholesale_prices = [float(w) for w in list(filter(None, re.split("[, \-!?:\t]+",prices_form.cleaned_data['wholesale_prices'])))]
            gas_prices = [float(g) for g in list(filter(None, re.split("[, \-!?:\t]+",prices_form.cleaned_data['gas_prices'])))]

            for i, y in enumerate(range(2020,scenario_new.end_year+1)):
                a = AuctionYear.objects.create(year=y, scenario=scenario_new, gas_price=gas_prices[i], wholesale_price=wholesale_prices[i])
                for p in [p.name for p in scenario_original.auctionyear_set.all()[0].pot_set.all()]:
                #for p in ['E', 'M', 'SN']:
                    Pot.objects.create(auctionyear=a,name=p)
            q = Pot.objects.filter(auctionyear__scenario=scenario_new)

            for form in string_formset:
                fields = [f.name for f in Technology._meta.get_fields() if f.name not in ["pot", "id", "name"]]
                field_data = { field : [float(s) for s in list(filter(None, re.split("[, \-!?:\t]+",form.cleaned_data[field])))] for field in fields }
                for i, a in enumerate(AuctionYear.objects.filter(scenario=scenario_new)):
                    kwargs = { field : field_data[field][i] for field in field_data }
                    kwargs['name'] = form.cleaned_data['name']
                    kwargs['pot'] = q.filter(auctionyear=a).get(name=form.cleaned_data['pot'])
                    Technology.objects.create(**kwargs)
            return redirect('scenario_detail', pk=scenario_new.pk)

    scenario_form = ScenarioForm(instance=scenario_original)
    initial_prices = {'gas_prices': str([a.gas_price for a in scenario_original.auctionyear_set.all()]).strip('[]'), 'wholesale_prices': str([a.wholesale_price for a in scenario_original.auctionyear_set.all() ]).strip('[]')}
    prices_form = PricesForm(initial=initial_prices)
    names = scenario_original.initial_technologies()[0]
    initial_technologies = scenario_original.initial_technologies()[1]
    string_formset = TechnologyStringFormSet(initial=initial_technologies)
    context = {'scenario': scenario_original,
               'scenarios': scenarios,
               'scenario_form': scenario_form,
               'prices_form': prices_form,
               'string_formset': string_formset,
               'names': names}
    return render(request, 'lcf/scenario_new.html', context)



def scenario_delete(request, pk):
    scenario = get_object_or_404(Scenario, pk=pk)
    scenario.delete()
    return redirect('scenario_new', pk=196)


def scenario_detail(request, pk):
    scenario = get_object_or_404(Scenario,pk=pk)
    scenarios = Scenario.objects.all()

    accounting_cost_data = scenario.accounting_cost()['title']
    accounting_cost_data_source = SimpleDataSource(data=accounting_cost_data)
    accounting_cost_options = {'title': None, 'vAxis': {'title': '£bn'}}
    accounting_cost_chart = LineChart(accounting_cost_data_source, options=accounting_cost_options)
    accounting_cost_df = scenario.accounting_cost()['df']

    gen_by_tech_data = scenario.summary_gen_by_tech()['title']
    gen_by_tech_data_source = SimpleDataSource(data=gen_by_tech_data)
    gen_by_tech_options = {'vAxis': {'title': 'TWh'}, 'title': None}
    gen_by_tech_chart = ColumnChart(gen_by_tech_data_source, options=gen_by_tech_options)
    gen_by_tech_df = scenario.summary_gen_by_tech()['df']

    cap_by_tech_data = scenario.summary_cap_by_tech()['title']
    cap_by_tech_data_source = SimpleDataSource(data=cap_by_tech_data)
    cap_by_tech_options = {'vAxis': {'title': 'GW'}, 'title': None}
    cap_by_tech_chart = ColumnChart(cap_by_tech_data_source, options=cap_by_tech_options)
    cap_by_tech_df = scenario.summary_cap_by_tech()['df']

    context = {'scenario': scenario,
               'scenarios': scenarios,
               'accounting_cost_chart': accounting_cost_chart,
               'gen_by_tech_chart': gen_by_tech_chart,
               'cap_by_tech_chart': cap_by_tech_chart,
               'accounting_cost_df': accounting_cost_df,
               'cap_by_tech_df': cap_by_tech_df,
               'gen_by_tech_df': gen_by_tech_df }

    return render(request, 'lcf/scenario_detail.html', context)

def scenario_download(request,pk):
    scenario = get_object_or_404(Scenario,pk=pk)
    scenarios = Scenario.objects.all()

    accounting_cost_df = scenario.accounting_cost()['df']

    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="accounting_cost.csv"'

    writer = csv.writer(response)
    headers = ['']
    headers.extend(accounting_cost_df.columns)
    writer.writerow(headers)
    for i in range(len(accounting_cost_df.index)):
        row = [accounting_cost_df.index[i]]
        row.extend(accounting_cost_df.iloc[i])
        writer.writerow(row)

    return response
