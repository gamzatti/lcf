from django.shortcuts import render, redirect, get_object_or_404
from .forms import ScenarioForm
from .models import Scenario

# Create your views here.
def scenario_new(request):
    form = ScenarioForm()
    scenarios = Scenario.objects.all()
    return render(request, 'lcf/scenario_new.html', {'form': form, 'scenarios': scenarios })

def scenario_save(request):
    form = ScenarioForm(request.POST)
    if form.is_valid():
        scenario = form.save()
    return redirect('scenario_detail', pk=scenario.pk)

def scenario_detail(request, pk):
    scenario = get_object_or_404(Scenario,pk=pk)
    scenarios = Scenario.objects.all()
    return render(request, 'lcf/scenario_detail.html', {'scenario': scenario, 'scenarios': scenarios})
