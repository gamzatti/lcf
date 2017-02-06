from django import forms
from .models import Scenario, AuctionYear, AuctionYearTechnology

class ScenarioForm(forms.ModelForm):

    class Meta:
        model = Scenario
        fields = ('name','budget', 'percent_emerging',)

class ScenarioNameForm(forms.Form):
    name = forms.CharField(max_length=200)

'''class AuctionYearTechnologyForm(forms.Form):
    year = forms.ModelChoiceField(queryset = AuctionYear.objects.all())
    technology_name = forms.ModelChoiceField(queryset = AuctionYearTechnology.objects.all())
    strike_price = forms.IntegerField()
    min_levelised_cost = forms.IntegerField()

class BigForm(forms.Form):
    starting_scenario = Scenario.objects.get(pk=21)
    scenario_name = forms.CharField(label="Scenario name", max_length=200)
    for y in starting_scenario.auctionyear_set.all():
        z = str(y.year)
        z = forms.CharField(label=z, max_length=200)
        for t in y.auctionyeartechnology_set.all():
            technology_name = str(t.technology_name)
            technology_name = forms.CharField(label=technology_name, max_length=200)
'''
