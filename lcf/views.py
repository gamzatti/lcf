from django.shortcuts import render, redirect, get_object_or_404
from django.forms import modelformset_factory
from .forms import ScenarioNameForm
from .models import Scenario, AuctionYear, AuctionYearTechnology

# Create your views here.
def scenario_new(request):
    AuctionYearTechnologyFormSet = modelformset_factory(AuctionYearTechnology, extra=0, fields="__all__")
    scenarios = Scenario.objects.all()
    if request.method == "POST":
        formset = AuctionYearTechnologyFormSet(request.POST)
        scenario_name_form = ScenarioNameForm(request.POST)
        if formset.is_valid() and scenario_name_form.is_valid():
            scenario_name = scenario_name_form.cleaned_data['name']
            scenario = Scenario.objects.create(name=scenario_name)
            for form in formset:
                year = form.cleaned_data['year']
                technology_name = form.cleaned_data['technology_name']
                strike_price = form.cleaned_data['strike_price']
                min_levelised_cost = form.cleaned_data['min_levelised_cost']
                auctionyear = AuctionYear.objects.create(year=year.year, scenario=scenario)
                AuctionYearTechnology.objects.create(year=auctionyear, technology_name=technology_name, strike_price = strike_price, min_levelised_cost=min_levelised_cost)

        return redirect('scenario_detail', pk=scenario.pk)
    else:
        scenario_name_form = ScenarioNameForm()
        formset = AuctionYearTechnologyFormSet()

    return render(request, 'lcf/scenario_new.html', {'formset': formset, 'scenarios': scenarios, 'scenario_name_form': scenario_name_form })


def scenario_detail(request, pk):
    scenario = get_object_or_404(Scenario,pk=pk)
    scenarios = Scenario.objects.all()
    return render(request, 'lcf/scenario_detail.html', {'scenario': scenario, 'scenarios': scenarios})
