from django.shortcuts import render, redirect, get_object_or_404
from django.forms import modelformset_factory
from .forms import ScenarioForm
from .models import Scenario, AuctionYear, Pot, Technology
from django.http import HttpResponse
import pandas as pd
import numpy as np

# Create your views here.
def scenario_new(request):
    TechnologyFormSet = modelformset_factory(Technology, extra=0, exclude=['cum_project_gen_incorrect'])
    scenarios = Scenario.objects.all()
    #queryset = Technology.objects.filter(year__scenario__name="2")
    queryset = Technology.objects.filter(pot__auctionyear__scenario__name="default")
    if request.method == "POST":
        formset = TechnologyFormSet(request.POST, queryset=queryset)
        #scenario_name_form = ScenarioNameForm(request.POST)
        scenario_form = ScenarioForm(request.POST)
        #if formset.is_valid() and scenario_name_form.is_valid():
        if formset.is_valid() and scenario_form.is_valid():
            #scenario_name = scenario_name_form.cleaned_data['name']
            #scenario_budget = scenario_name_form.cleaned_data['budget']
            #scenario_percent_emerging = scenario_name_form.cleaned_data['percent_emerging']
            #scenario = Scenario.objects.create(name=scenario_name, budget=scenario_budget, percent_emerging=scenario_percent_emerging)
            scenario = scenario_form.save()
            for y in range(2020,2031):
                a = AuctionYear.objects.create(year=y, scenario=scenario)
                for p in ['E','M','SN','NW']:
                    Pot.objects.create(auctionyear=a,name=p)
            q = Pot.objects.filter(auctionyear__scenario=scenario)
            cum_project_gen_incorrect = {'OFW': 0, 'NU': 0, 'TL':0, 'TS':0, 'WA': 0, 'ONW': 0, 'PVLS': 0}
            for form in formset:
                pot = q.filter(auctionyear__year=form.cleaned_data['pot'].auctionyear.year).get(name=form.cleaned_data['pot'].name)
                cum_project_gen_incorrect[form.cleaned_data['name']] += form.cleaned_data['project_gen_incorrect']
                Technology.objects.create(pot = pot,
                                        name = form.cleaned_data['name'],
                                        min_levelised_cost = form.cleaned_data['min_levelised_cost'],
                                        max_levelised_cost = form.cleaned_data['max_levelised_cost'],
                                        strike_price = form.cleaned_data['strike_price'],
                                        load_factor = form.cleaned_data['load_factor'],
                                        project_gen_incorrect = form.cleaned_data['project_gen_incorrect'],
                                        max_deployment_cap = form.cleaned_data['max_deployment_cap'],
                                        cum_project_gen_incorrect = cum_project_gen_incorrect[form.cleaned_data['name']])
            return redirect('scenario_detail', pk=scenario.pk)
    else:
        #scenario_name_form = ScenarioNameForm()
        scenario_form = ScenarioForm()
        formset = TechnologyFormSet(queryset=queryset)

    return render(request, 'lcf/scenario_new.html', {'formset': formset, 'scenarios': scenarios, 'scenario_form': scenario_form})

def scenario_delete(request, pk):
    scenario = get_object_or_404(Scenario, pk=pk)
    scenario.delete()
    return redirect('scenario_new')

def scenario_detail(request, pk):
    scenario = get_object_or_404(Scenario,pk=pk)
    scenarios = Scenario.objects.all()
    return render(request, 'lcf/scenario_detail.html', {'scenario': scenario, 'scenarios': scenarios})
