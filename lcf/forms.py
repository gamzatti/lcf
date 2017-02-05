from django import forms
from .models import Scenario

class ScenarioForm(forms.ModelForm):

    class Meta:
        model = Scenario
        fields = ('name','budget', 'percent_emerging',)

class BigForm(forms.Form):
    starting_scenario = Scenario.objects.get(pk=21)
    scenario_name = forms.CharField(label="Scenario name", max_length=200)
    for y in starting_scenario.auctionyear_set.all():
        for t in y.auctionyeartechnology_set.all():
            technology_name = str(t.technology_name)
            technology_name = forms.CharField(label=technology_name, max_length=200)
