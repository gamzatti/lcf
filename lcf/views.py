from django.shortcuts import render, redirect
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
        form.save()
    return redirect('scenario_new')
