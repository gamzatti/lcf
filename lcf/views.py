from django.shortcuts import render, redirect, get_object_or_404
from django.forms import modelformset_factory, formset_factory
from .forms import ScenarioForm, PricesForm, TechnologyStringForm
from .models import Scenario, AuctionYear, Pot, Technology
from django.http import HttpResponse
import pandas as pd
import numpy as np
import re
# Create your views here.
#old version
"""def scenario_new_existing_version(request,pk):
    scenarios = Scenario.objects.all()
    scenario_original = get_object_or_404(Scenario, pk=pk)
    queryset = Technology.objects.filter(pot__auctionyear__scenario=scenario_original)
    TechnologyFormSet = modelformset_factory(Technology, extra=0, fields="__all__")
    if request.method == "POST":
        scenario_form = ScenarioForm(request.POST)
        prices_form = PricesForm(request.POST)
        formset = TechnologyFormSet(request.POST, queryset=queryset)
        if formset.is_valid() and scenario_form.is_valid() and prices_form.is_valid():
            scenario_new = scenario_form.save()
            gas_prices = [float(g) for g in list(filter(None, re.split("[, \-!?:\t]+",prices_form.cleaned_data['gas_prices'])))]
            wholesale_prices = [float(g) for g in list(filter(None, re.split("[, \-!?:\t]+",prices_form.cleaned_data['wholesale_prices'])))]

            for i, y in enumerate(range(2020,2023)):
                a = AuctionYear.objects.create(year=y, scenario=scenario_new, gas_price=gas_prices[i], wholesale_price=wholesale_prices[i])
                for p in ['E','M','SN','NW']:
                    Pot.objects.create(auctionyear=a,name=p)
            q = Pot.objects.filter(auctionyear__scenario=scenario_new)
            for form in formset:
                pot = q.filter(auctionyear__year=form.cleaned_data['pot'].auctionyear.year).get(name=form.cleaned_data['pot'].name)
                Technology.objects.create(pot = pot,
                                        name = form.cleaned_data['name'],
                                        min_levelised_cost = form.cleaned_data['min_levelised_cost'],
                                        max_levelised_cost = form.cleaned_data['max_levelised_cost'],
                                        strike_price = form.cleaned_data['strike_price'],
                                        load_factor = form.cleaned_data['load_factor'],
                                        project_gen = form.cleaned_data['project_gen'],
                                        max_deployment_cap = form.cleaned_data['max_deployment_cap'])


            return redirect('scenario_detail', pk=scenario_new.pk)
    scenario_form = ScenarioForm(instance=scenario_original)
    initial_prices = {'gas_prices': str([a.gas_price for a in scenario_original.auctionyear_set.all()]).strip('[]'), 'wholesale_prices': str([a.wholesale_price for a in scenario_original.auctionyear_set.all() ]).strip('[]')}
    prices_form = PricesForm(initial=initial_prices)
    formset = TechnologyFormSet(queryset=queryset)
    return render(request, 'lcf/scenario_new.html', {'scenario': scenario_original, 'scenarios': scenarios, 'scenario_form': scenario_form, 'formset': formset, 'prices_form': prices_form })"""


#version that actually works
"""def scenario_new(request,pk):
    scenarios = Scenario.objects.all()
    scenario_original = get_object_or_404(Scenario, pk=pk)
    queryset = Technology.objects.filter(pot__auctionyear__scenario=scenario_original)
    first_auctionyear = scenario_original.auctionyear_set.all()[0]
    techs = Technology.objects.filter(pot__auctionyear=first_auctionyear)
    num_techs = techs.count()
    TechnologyStringFormSet = formset_factory(TechnologyStringForm, extra=0, max_num=num_techs)
    if request.method == "POST":
        scenario_form = ScenarioForm(request.POST)
        prices_form = PricesForm(request.POST)
        string_formset = TechnologyStringFormSet(request.POST)
        if string_formset.is_valid() and scenario_form.is_valid() and prices_form.is_valid():
            scenario_new = scenario_form.save()
            gas_prices = [float(g) for g in list(filter(None, re.split("[, \-!?:\t]+",prices_form.cleaned_data['gas_prices'])))]
            wholesale_prices = [float(g) for g in list(filter(None, re.split("[, \-!?:\t]+",prices_form.cleaned_data['wholesale_prices'])))]

            for i, y in enumerate(range(2020,2023)):
                a = AuctionYear.objects.create(year=y, scenario=scenario_new, gas_price=gas_prices[i], wholesale_price=wholesale_prices[i])
                for p in ['E','M','SN','NW']:
                    Pot.objects.create(auctionyear=a,name=p)
            q = Pot.objects.filter(auctionyear__scenario=scenario_new)
            #for form in formset:
            #    pot = q.filter(auctionyear__year=form.cleaned_data['pot'].auctionyear.year).get(name=form.cleaned_data['pot'].name)
            #    Technology.objects.create(pot = pot,
            #                            name = form.cleaned_data['name'],
            #                            min_levelised_cost = form.cleaned_data['min_levelised_cost'],
            #                            max_levelised_cost = form.cleaned_data['max_levelised_cost'],
            #                            strike_price = form.cleaned_data['strike_price'],
            #                            load_factor = form.cleaned_data['load_factor'],
            #                            project_gen = form.cleaned_data['project_gen'],
            #                            max_deployment_cap = form.cleaned_data['max_deployment_cap'])


            return redirect('scenario_detail', pk=scenario_new.pk)
    #version that actually works!!
    scenario_form = ScenarioForm(instance=scenario_original)
    initial_prices = {'gas_prices': str([a.gas_price for a in scenario_original.auctionyear_set.all()]).strip('[]'), 'wholesale_prices': str([a.wholesale_price for a in scenario_original.auctionyear_set.all() ]).strip('[]')}
    prices_form = PricesForm(initial=initial_prices)

    t_names = [t.name for t in techs]
    t_max_levelised_costs = ["wave maxes", "ofw maxes", "onw maxes"]

    ofw_objects = Technology.objects.filter(name="OFW", pot__auctionyear__scenario=scenario_original)

    #ofw_min_levelised_costs = str([ofw_objects.get(pot__auctionyear=a).min_levelised_cost for a in scenario_original.auctionyear_set.all()]).strip('[]')

    fields = {}

    fields['ofw'] = {}
    fields['ofw']['min_levelised_costs'] = []
    fields['ofw']['max_levelised_costs'] = []
    for a in scenario_original.auctionyear_set.all():
        fields['ofw']['min_levelised_costs'].append(ofw_objects.get(pot__auctionyear=a).min_levelised_cost)
        fields['ofw']['max_levelised_costs'].append(ofw_objects.get(pot__auctionyear=a).max_levelised_cost)
    fields['ofw']['min_levelised_costs'] = str(fields['ofw']['min_levelised_costs']).strip('[]')
    fields['ofw']['max_levelised_costs'] = str(fields['ofw']['max_levelised_costs']).strip('[]')

    t_min_levelised_costs = ["wave mins", fields['ofw']['min_levelised_costs'], "onw mins"]
    t_max_levelised_costs = ["wave maxes", fields['ofw']['max_levelised_costs'], "onw maxes"]


    #initial_min_levelised_costs = [ str([t.min_levelised_cost for t in a for a in scenario_original.auctionyear_set.all()]).strip('[]') ]
    initial_technologies = []
    for i in range(len(techs)):
        line = {'name': t_names[i], 'min_levelised_costs': t_min_levelised_costs[i], 'max_levelised_costs': t_max_levelised_costs[i]}
        initial_technologies.append(line)
    string_formset = TechnologyStringFormSet(initial=initial_technologies)
    return render(request, 'lcf/scenario_new.html', {'scenario': scenario_original, 'scenarios': scenarios, 'scenario_form': scenario_form, 'prices_form': prices_form, 'string_formset': string_formset})"""




#new version with dataframes
def scenario_new(request,pk):
    scenarios = Scenario.objects.all()
    scenario_original = get_object_or_404(Scenario, pk=pk)
    queryset = Technology.objects.filter(pot__auctionyear__scenario=scenario_original)

    techs = Technology.objects.filter(pot__auctionyear=scenario_original.auctionyear_set.all()[0])
    num_techs = techs.count()
    TechnologyStringFormSet = formset_factory(TechnologyStringForm, extra=0, max_num=num_techs)
    if request.method == "POST":
        scenario_form = ScenarioForm(request.POST)
        prices_form = PricesForm(request.POST)
        string_formset = TechnologyStringFormSet(request.POST)

        if string_formset.is_valid() and scenario_form.is_valid() and prices_form.is_valid():
            scenario_new = scenario_form.save()
            wholesale_prices = [float(w) for w in list(filter(None, re.split("[, \-!?:\t]+",prices_form.cleaned_data['wholesale_prices'])))]
            gas_prices = [float(g) for g in list(filter(None, re.split("[, \-!?:\t]+",prices_form.cleaned_data['gas_prices'])))]

            for i, y in enumerate(range(2020,2023)):
                a = AuctionYear.objects.create(year=y, scenario=scenario_new, gas_price=gas_prices[i], wholesale_price=wholesale_prices[i])

                for p in [p.name for p in scenario_original.auctionyear_set.all()[0].pot_set.all()]:
                    Pot.objects.create(auctionyear=a,name=p)
            q = Pot.objects.filter(auctionyear__scenario=scenario_new)
            for form in string_formset:
                name = form.cleaned_data['name']
                form_pot_name = form.cleaned_data['pot']
                strike_price = [float(s) for s in list(filter(None, re.split("[, \-!?:\t]+",form.cleaned_data['strike_price'])))]
                min_levelised_cost = [float(s) for s in list(filter(None, re.split("[, \-!?:\t]+",form.cleaned_data['min_levelised_cost'])))]
                max_levelised_cost = [float(s) for s in list(filter(None, re.split("[, \-!?:\t]+",form.cleaned_data['max_levelised_cost'])))]
                load_factor = [float(s) for s in list(filter(None, re.split("[, \-!?:\t]+",form.cleaned_data['load_factor'])))]
                project_gen = [float(s) for s in list(filter(None, re.split("[, \-!?:\t]+",form.cleaned_data['project_gen'])))]
                max_deployment_cap = [float(s) for s in list(filter(None, re.split("[, \-!?:\t]+",form.cleaned_data['max_deployment_cap'])))]

                for i, a in enumerate(AuctionYear.objects.filter(scenario=scenario_new)):
                    right_pot = q.filter(auctionyear=a).get(name=form_pot_name)
                    Technology.objects.create(name=name,
                                            pot=right_pot,
                                            min_levelised_cost = min_levelised_cost[i],
                                            max_levelised_cost = max_levelised_cost[i],
                                            strike_price = strike_price[i],
                                            load_factor = load_factor[i],
                                            project_gen = project_gen[i],
                                            max_deployment_cap = max_deployment_cap[i])
            #for form in formset:
            #    pot = q.filter(auctionyear__year=form.cleaned_data['pot'].auctionyear.year).get(name=form.cleaned_data['pot'].name)
            #    Technology.objects.create(pot = pot,
            #                            name = form.cleaned_data['name'],
            #                            min_levelised_cost = form.cleaned_data['min_levelised_cost'],
            #                            max_levelised_cost = form.cleaned_data['max_levelised_cost'],
            #                            strike_price = form.cleaned_data['strike_price'],
            #                            load_factor = form.cleaned_data['load_factor'],
            #                            project_gen = form.cleaned_data['project_gen'],
            #                            max_deployment_cap = form.cleaned_data['max_deployment_cap'])


            return redirect('scenario_detail', pk=scenario_new.pk)
    scenario_form = ScenarioForm(instance=scenario_original)

    initial_prices = {'gas_prices': str([a.gas_price for a in scenario_original.auctionyear_set.all()]).strip('[]'), 'wholesale_prices': str([a.wholesale_price for a in scenario_original.auctionyear_set.all() ]).strip('[]')}
    prices_form = PricesForm(initial=initial_prices)

    names = scenario_original.initial_technologies()[0]
    initial_technologies = scenario_original.initial_technologies()[1]
    string_formset = TechnologyStringFormSet(initial=initial_technologies)

    return render(request, 'lcf/scenario_new.html', {'scenario': scenario_original, 'scenarios': scenarios, 'scenario_form': scenario_form, 'prices_form': prices_form, 'string_formset': string_formset, 'names': names})



def scenario_delete(request, pk):
    scenario = get_object_or_404(Scenario, pk=pk)
    scenario.delete()
    return redirect('scenario_new', pk=119)


def scenario_detail(request, pk):
    scenario = get_object_or_404(Scenario,pk=pk)
    scenarios = Scenario.objects.all()
    return render(request, 'lcf/scenario_detail.html', {'scenario': scenario, 'scenarios': scenarios})
