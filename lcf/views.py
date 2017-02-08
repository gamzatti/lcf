from django.shortcuts import render, redirect, get_object_or_404
from django.forms import modelformset_factory
from .forms import ScenarioForm
from .models import Scenario, AuctionYear, AuctionYearTechnology
from django.http import HttpResponse

# Create your views here.
def scenario_new(request):
    AuctionYearTechnologyFormSet = modelformset_factory(AuctionYearTechnology, extra=0, fields='__all__')
    scenarios = Scenario.objects.all()
    #queryset = AuctionYearTechnology.objects.filter(year__scenario__name="2")
    queryset = AuctionYearTechnology.objects.filter(year__scenario__name="default")
    if request.method == "POST":
        formset = AuctionYearTechnologyFormSet(request.POST, queryset=queryset)
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
                AuctionYear.objects.create(year=y, scenario=scenario)
            q = AuctionYear.objects.filter(scenario=scenario)
            for form in formset:
                auctionyear = q.get(year=form.cleaned_data['year'].year)
                #auctionyear = q.get(year=form.instance.year) # don't know why this doesn't work
                AuctionYearTechnology.objects.create(year = auctionyear,
                                                    technology_name = form.cleaned_data['technology_name'],
                                                    pot = form.cleaned_data['pot'],
                                                    min_levelised_cost = form.cleaned_data['min_levelised_cost'],
                                                    max_levelised_cost = form.cleaned_data['max_levelised_cost'],
                                                    strike_price = form.cleaned_data['strike_price'],
                                                    load_factor = form.cleaned_data['load_factor'],
                                                    project_gen = form.cleaned_data['project_gen'],
                                                    max_deployment_cap = form.cleaned_data['max_deployment_cap'])
            return redirect('scenario_detail', pk=scenario.pk)
    else:
        #scenario_name_form = ScenarioNameForm()
        scenario_form = ScenarioForm()
        formset = AuctionYearTechnologyFormSet(queryset=queryset)

    return render(request, 'lcf/scenario_new.html', {'formset': formset, 'scenarios': scenarios, 'scenario_form': scenario_form})

def scenario_delete(request, pk):
    scenario = get_object_or_404(Scenario, pk=pk)
    scenario.delete()
    return redirect('scenario_new')

def scenario_detail(request, pk):
    scenario = get_object_or_404(Scenario,pk=pk)
    scenarios = Scenario.objects.all()
    return render(request, 'lcf/scenario_detail.html', {'scenario': scenario, 'scenarios': scenarios })
