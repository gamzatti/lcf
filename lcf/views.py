from django.shortcuts import render, redirect, get_object_or_404
from django.forms import modelformset_factory
from .forms import ScenarioForm
from .models import Scenario, AuctionYear, Pot, Technology
from django.http import HttpResponse
import pandas as pd
import numpy as np

# Create your views here.
def scenario_new2(request,pk):
    TechnologyFormSet = modelformset_factory(Technology, extra=0, fields="__all__")
    scenarios = Scenario.objects.all()
    scenario_original = get_object_or_404(Scenario, pk=pk)
    #queryset = Technology.objects.filter(pot__auctionyear__scenario__name="default")
    #queryset = Technology.objects.filter(pot__auctionyear__scenario=scenario_original)
    if request.method == "POST":

        formset = TechnologyFormSet(request.POST, queryset=queryset)
        scenario_form = ScenarioForm(request.POST)
        if formset.is_valid() and scenario_form.is_valid():
            scenario_new = scenario_form.save()
            for y in range(2020,2031):
                a = AuctionYear.objects.create(year=y, scenario=scenario_new2)
                for p in ['E','M','SN','NW']:
                    Pot.objects.create(auctionyear=a,name=p)
            q = Pot.objects.filter(auctionyear__scenario=scenario_new2)
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
    else:
        scenario_form = ScenarioForm()
        #formset = TechnologyFormSet(queryset=queryset)
        formset = "foo"

    return render(request, 'lcf/scenario_new2.html', {'scenario_original': scenario_original, 'formset': formset, 'scenarios': scenarios, 'scenario_form': scenario_form })

def scenario_new(request,pk):
    scenarios = Scenario.objects.all()
    scenario_original = get_object_or_404(Scenario, pk=pk)
    queryset = Technology.objects.filter(pot__auctionyear__scenario=scenario_original)
    #print(queryset)
    TechnologyFormSet = modelformset_factory(Technology, extra=0, fields="__all__")

    if request.method == "POST":
        scenario_form = ScenarioForm(request.POST)
        formset = TechnologyFormSet(request.POST, queryset=queryset)
        if scenario_form.is_valid():
            scenario_new = scenario_form.save()
            return redirect('scenario_detail', pk=scenario_new.pk)
        else:
            scenario_form = ScenarioForm(instance=scenario_original)
            formset = TechnologyFormSet(queryset=queryset)
            return render(request, 'lcf/scenario_new.html', {'scenario': scenario_original, 'scenarios': scenarios, 'scenario_form': scenario_form, 'formset': formset })
    else:
        scenario_form = ScenarioForm(instance=scenario_original)
        formset = TechnologyFormSet(queryset=queryset)
        return render(request, 'lcf/scenario_new.html', {'scenario': scenario_original, 'scenarios': scenarios, 'scenario_form': scenario_form, 'formset': formset })


def scenario_delete(request, pk):
    scenario = get_object_or_404(Scenario, pk=pk)
    scenario.delete()
    return redirect('scenario_new', pk=1)


def scenario_detail(request, pk):
    scenario = get_object_or_404(Scenario,pk=pk)
    scenarios = Scenario.objects.all()
    return render(request, 'lcf/scenario_detail.html', {'scenario': scenario, 'scenarios': scenarios})
