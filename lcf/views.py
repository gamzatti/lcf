from django.shortcuts import render, redirect, get_object_or_404
from django.forms import modelformset_factory, formset_factory
from .forms import ScenarioForm, PricesForm, TechnologyStringForm, UploadFileForm
from .models import Scenario, AuctionYear, Pot, Technology
import time
from .helpers import handle_uploaded_file
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
        upload_form = UploadFileForm(request.POST, request.FILES)
        scenario_form = ScenarioForm(request.POST)

        if upload_form.is_valid() and scenario_form.is_valid():
            s = scenario_form.save()
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
            for i, y in enumerate(range(2020,scenario.end_year2+1)):
                a = AuctionYear.objects.create(year=y, scenario=s, gas_price=gas_prices[i], wholesale_price=wholesale_prices[i])
                for p in ['E', 'M', 'SN', 'FIT']:
                    Pot.objects.create(auctionyear=a,name=p)
            #s = Scenario.objects.all().prefetch_related('auctionyear_set__pot_set__technology_set').get(pk=s.pk)

            file = request.FILES['file']
            handle_uploaded_file(file,s)
            recent_pk = Scenario.objects.all().order_by("-date")[0].pk
            return redirect('scenario_detail', pk=recent_pk)
        else:
            print(form.errors)
    else:
        print("GETTING ")
        scenario_form = ScenarioForm()
        upload_form = UploadFileForm()
    context = {'scenario': scenario,
               'scenarios': scenarios,
               'scenario_form': scenario_form,
               'recent_pk': recent_pk,
               'upload_form' : upload_form,
               }
    return render(request, 'lcf/upload.html', context)

def scenario_delete(request, pk):
    scenario = get_object_or_404(Scenario, pk=pk)
    scenario.delete()
    recent_pk = Scenario.objects.all().order_by("-date")[0].pk
    return redirect('scenario_detail', pk=recent_pk)

from django.views.decorators.cache import never_cache

@never_cache
def scenario_detail(request, pk=None):
    # if pk == None:
    #     scenario = Scenario.objects.all().order_by("-date")[0]
    # else:
    #scenario = get_object_or_404(Scenario,pk=pk)
    #print("without prefetching")
    scenario = Scenario.objects.prefetch_related('auctionyear_set__pot_set__technology_set').get(id=pk)
    print('instantiating a scenario object with prefetched attributes')
    print(scenario.name)
    print("[lease sss don't cache me!")
    scenario.get_results()

    recent_pk = Scenario.objects.all().order_by("-date")[0].pk
    scenarios = Scenario.objects.all()
    chart = {}
    df = {}
    context = {'scenario': scenario,
               'scenarios': scenarios,
               'recent_pk': recent_pk
               }
    # meth_list_long = ["cumulative_costs","cum_awarded_gen_by_pot","awarded_cost_by_tech","gen_by_tech","cap_by_tech"]
    # meth_list = ["cumulative_costs","cum_awarded_gen_by_pot","gen_by_tech", 'cap_by_tech']
    # t1 = time.time() * 1000

    context['tech_gen_pivot'] = scenario.pivot_to_html(scenario.tech_pivot_table(1,'awarded_gen', 'Generation awarded each year LCF 1'))
    context['tech_gen_pivot2'] = scenario.pivot_to_html(scenario.tech_pivot_table(2,'awarded_gen', 'Generation awarded each year LCF 2'))
    context['tech_cum_owed_v_wp_pivot'] = scenario.pivot_to_html(scenario.tech_pivot_table(1,'cum_owed_v_wp','Accounting cost LCF 1'))
    context['tech_cum_owed_v_wp_pivot2'] = scenario.pivot_to_html(scenario.tech_pivot_table(2,'cum_owed_v_wp','Accounting cost LCF 2'))
    context['tech_cum_owed_v_gas_pivot'] = scenario.pivot_to_html(scenario.tech_pivot_table(1,'cum_owed_v_gas', 'Cost v gas LCF 1'))
    context['tech_cum_owed_v_gas_pivot2'] = scenario.pivot_to_html(scenario.tech_pivot_table(2,'cum_owed_v_gas', 'Cost v gas LCF 2'))
    context['tech_cum_owed_v_absolute_pivot'] = scenario.pivot_to_html(scenario.tech_pivot_table(1,'cum_owed_v_absolute', 'Absolute cost LCF 1'))
    context['tech_cum_owed_v_absolute_pivot2'] = scenario.pivot_to_html(scenario.tech_pivot_table(2,'cum_owed_v_absolute', 'Absolute cost LCF 2'))
    context['tech_cum_awarded_gen_pivot'] = scenario.pivot_to_html(scenario.tech_pivot_table(1,'cum_awarded_gen', 'Cumulative new generation LCF 1'))
    context['tech_cum_awarded_gen_pivot2'] = scenario.pivot_to_html(scenario.tech_pivot_table(2,'cum_awarded_gen', 'Cumulative new generation LCF 2'))
    # context['pot_cum_owed_v_wp_pivot'] = scenario.pivot_to_html(scenario.pot_pivot_table(1,'cum_owed_v_wp'))
    # context['pot_cum_awarded_gen_pivot'] = scenario.pivot_to_html(scenario.pot_pivot_table(1,'cum_awarded_gen_result'))

    # for meth in meth_list:
    #     chart[meth] = {}
    #     df[meth] = {}
    #     for period_num in [1,2]:
    #         results = scenario.get_or_make_chart_data(meth,period_num)
    #         data = results['data']
    #         data_source = SimpleDataSource(data=data)
    #         options = results['options']
    #         if meth == "cumulative_costs" or meth == "cum_awarded_gen_by_pot":
    #             chart[meth][period_num] = LineChart(data_source, options=options, height=400, width="100%")
    #         else:
    #             chart[meth][period_num] = ColumnChart(data_source, options=options, height=400, width="100%")
    #         df[meth][period_num] = results['df'].to_html(classes="table table-striped table-condensed") # slowest line; consider saving in db
    #         context["".join([meth,"_chart",str(period_num)])] = chart[meth][period_num]
    #         context["".join([meth,"_df",str(period_num)])] = df[meth][period_num]
    # t2 = time.time() * 1000
    # print(t2-t1,t1-t0)
    #print(connection.queries)
    #for query in connection.queries:
    #    print('\n',query)
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
    #qs_techs = Technology.objects.filter(pot__auctionyear__in = auctionyears)
    #df_techs = read_frame(qs_techs, fieldnames=['pot__auctionyear__year','pot__name','name','awarded_gen', 'awarded_cost', 'cum_awarded_gen', 'cum_owed_v_gas', 'cum_owed_v_wp', 'cum_owed_v_absolute'])
    df_techs = scenario.get_results()
    tech_data = df_techs.values.tolist()
    tech_col_names = list(df_techs.columns)

    # df_pots = read_frame(qs_pots, fieldnames=['auctionyear__year','name','cum_awarded_gen_result', 'cum_owed_v_wp', 'cum_owed_v_gas'])
    # qs_pots = Pot.objects.filter(auctionyear__in = auctionyears)
    # pot_data = df_pots.values.tolist()
    # pot_col_names = list(df_pots.columns)

    writer.writerow([scenario.name])
    writer.writerow(['Budget', scenario.budget])
    writer.writerow(['Percent in emerging pot', scenario.percent_emerging])

    writer.writerow([""])
    # writer.writerow(["Summary tables"])

    # df_list = [
    #            ('Cumulative costs (£bn) (2021-2025)', scenario.cumulative_costs(1)['df']),
    #            ('Cumulative costs (£bn) (2026-2030)', scenario.cumulative_costs(2)['df']),
    #            ('Cumulative generation (TWh) (2021-2025)', scenario.cum_awarded_gen_by_pot(1)['df']),
    #            ('Cumulative generation (TWh) (2026-2030)', scenario.cum_awarded_gen_by_pot(2)['df']),
    #            ('Cost of new generation awarded (£m) (2021-2025)', scenario.awarded_cost_by_tech(1)['df']),
    #            ('Cost of new generation awarded (£m) (2026-2030)', scenario.awarded_cost_by_tech(2)['df']),
    #            ('Generation (TWh) (2021-2025)', scenario.gen_by_tech(1)['df']),
    #            ('Generation (TWh) (2026-2030)', scenario.gen_by_tech(2)['df']),
    #            ('Capacity (GW) (2021-2025)', scenario.cap_by_tech(1)['df']),
    #            ('Capacity (GW) (2026-2030)', scenario.cap_by_tech(2)['df']),
    #            ]

    # for df_pair in df_list:
    #     title = [df_pair[0]]
    #     writer.writerow(title)
    #     headers = ['']
    #     headers.extend(df_pair[1].columns)
    #     writer.writerow(headers)
    #     for i in range(len(df_pair[1].index)):
    #         row = [df_pair[1].index[i]]
    #         row.extend(df_pair[1].iloc[i])
    #         writer.writerow(row)
        # writer.writerow([])

    writer.writerow([""])
    writer.writerow(["Inputs"])

    inputs = [
               ('Prices (£/MWh)', scenario.prices_input()),
               ('Technology data', scenario.techs_input()),
               ]

    for df_pair in inputs:
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

    writer.writerow([''])
    writer.writerow(['Raw output'])
    writer.writerow(['Technology'])
    writer.writerow(tech_col_names)
    writer.writerows(tech_data)
    # writer.writerow([""])
    # writer.writerow(["Pot"])
    # writer.writerow(pot_col_names)
    # writer.writerows(pot_data)


    return response

def template(request):
    print("downloading template")
    file = open('lcf/template.csv')
    response = HttpResponse(file, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="template.csv"'

    return response
