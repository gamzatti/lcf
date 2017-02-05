from django.shortcuts import render, redirect, get_object_or_404
from .forms import ScenarioForm, BigForm
from .models import Scenario

# Create your views here.
def scenario_new(request):
    scenarios = Scenario.objects.all()
    if request.method == "POST":
        form = BigForm(request.POST)
        if form.is_valid():
            scenario = form.save()
        return redirect('scenario_detail', pk=scenario.pk)
    else:
        form = BigForm()
    return render(request, 'lcf/scenario_new.html', {'form': form, 'scenarios': scenarios })


def scenario_detail(request, pk):
    scenario = get_object_or_404(Scenario,pk=pk)
    scenarios = Scenario.objects.all()
    return render(request, 'lcf/scenario_detail.html', {'scenario': scenario, 'scenarios': scenarios})
