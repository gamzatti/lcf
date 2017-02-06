from django.shortcuts import render, redirect, get_object_or_404
from django.forms import modelformset_factory
from .forms import ScenarioNameForm
from .models import Scenario, AuctionYear, AuctionYearTechnology

# Create your views here.
def scenario_new(request):
    AuctionYearTechnologyFormSet = modelformset_factory(AuctionYearTechnology, extra=0, fields='__all__')
    afields = AuctionYearTechnology._meta.get_fields()
    scenarios = Scenario.objects.all()
#    queryset = AuctionYearTechnology.objects.filter(year__year__gte=2020)
    queryset = AuctionYearTechnology.objects.all()
    if request.method == "POST":
        formset = AuctionYearTechnologyFormSet(request.POST, queryset=queryset)
        scenario_name_form = ScenarioNameForm(request.POST)
        if formset.is_valid() and scenario_name_form.is_valid():
            scenario_name = scenario_name_form.cleaned_data['name']
            scenario = Scenario.objects.create(name=scenario_name)
            for form in formset:
                auctionyeartechnology = form.save(commit=False)
                auctionyear = AuctionYear.objects.create(year=auctionyeartechnology.year.year, scenario=scenario)
                auctionyeartechnology.year = auctionyear
                form.save()

        return redirect('scenario_detail', pk=scenario.pk)
    else:
        scenario_name_form = ScenarioNameForm()
        formset = AuctionYearTechnologyFormSet(queryset=queryset)

    return render(request, 'lcf/scenario_new.html', {'formset': formset, 'scenarios': scenarios, 'scenario_name_form': scenario_name_form, 'afields': afields })


def scenario_detail(request, pk):
    scenario = get_object_or_404(Scenario,pk=pk)
    scenarios = Scenario.objects.all()
    return render(request, 'lcf/scenario_detail.html', {'scenario': scenario, 'scenarios': scenarios})
