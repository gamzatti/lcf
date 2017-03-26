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
                #for p in ['E', 'M', 'SN', 'FIT']:
                    Pot.objects.create(auctionyear=a,name=p)
            q = Pot.objects.filter(auctionyear__scenario=scenario_new)

            for form in string_formset:
                fields = [f.name for f in Technology._meta.get_fields() if f.name not in ["pot", "id", "name", "included", "awarded_gen", "awarded_cost"]]
                field_data = { field : [float(s) for s in list(filter(None, re.split("[, \-!?:\t]+",form.cleaned_data[field])))] for field in fields }
                for i, a in enumerate(AuctionYear.objects.filter(scenario=scenario_new)):
                    kwargs = { field : field_data[field][i] for field in field_data }
                    kwargs['name'] = form.cleaned_data['name']
                    kwargs['included'] = form.cleaned_data['included']
                    kwargs['pot'] = q.filter(auctionyear=a).get(name=form.cleaned_data['pot'])
                    Technology.objects.create(**kwargs)
            return redirect('scenario_detail', pk=scenario_new.pk)

    scenario_form = ScenarioForm(instance=scenario_original)
    initial_prices = {'gas_prices': str([round(a.gas_price,2) for a in scenario_original.auctionyear_set.all()]).strip('[]'), 'wholesale_prices': str([round(a.wholesale_price,5) for a in scenario_original.auctionyear_set.all() ]).strip('[]')}
    prices_form = PricesForm(initial=initial_prices)
    names = scenario_original.technology_form_helper()[0]
    technology_form_helper = scenario_original.technology_form_helper()[1]
    string_formset = TechnologyStringFormSet(initial=technology_form_helper)
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
    return redirect('scenario_detail', pk=245)


def scenario_detail(request, pk=None):
    if pk == None:
        scenario = Scenario.objects.all().order_by("-date")[0]
    else:
        scenario = get_object_or_404(Scenario,pk=pk)
    scenarios = Scenario.objects.all()
    chart = {}
    df = {}
    for meth in ["accounting_cost","cum_awarded_gen_by_pot","awarded_cost_by_tech","gen_by_tech","cap_by_tech"]:
        results = scenario.get_or_make_chart_data(meth,2)
        data =results['data']
        data_source = SimpleDataSource(data=data)
        options = results['options']
        if meth == "accounting_cost" or meth == "cum_awarded_gen_by_pot":
            chart[meth] = LineChart(data_source, options=options, height=400, width="100%")
        else:
            chart[meth] = ColumnChart(data_source, options=options, height=400, width="100%")
        df[meth] = results['df'].to_html(classes="table table-striped table-condensed")

    context = {'scenario': scenario,
               'scenarios': scenarios,
               'accounting_cost_chart': chart["accounting_cost"],
               'accounting_cost_df': df["accounting_cost"],
               'cum_awarded_gen_by_pot_chart': chart["cum_awarded_gen_by_pot"],
               'cum_awarded_gen_by_pot_df': df["cum_awarded_gen_by_pot"],
               'awarded_cost_by_tech_chart': chart["awarded_cost_by_tech"],
               'awarded_cost_by_tech_df': df["awarded_cost_by_tech"],
               'gen_by_tech_chart': chart["gen_by_tech"],
               'gen_by_tech_df': df["gen_by_tech"],
               'cap_by_tech_chart': chart["cap_by_tech"],
               'cap_by_tech_df': df["cap_by_tech"],
               }

    return render(request, 'lcf/scenario_detail.html', context)

def scenario_download(request,pk):
    print("downloading")
    scenario = get_object_or_404(Scenario,pk=pk)
    scenarios = Scenario.objects.all()

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="data.csv"'

    writer = csv.writer(response)
    df_list = [
               ('Accounting cost (£bn)', scenario.accounting_cost()['df']),
               ('Cumulative generation (TWh)', scenario.cum_awarded_gen_by_pot()['df']),
               #('Cost of new generation awarded (£m)', scenario.awarded_cost_by_tech()['df']),
               #('Generation (TWh)', scenario.gen_by_tech()['df']),
               #('Capacity (GW)', scenario.cap_by_tech()['df']),
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
