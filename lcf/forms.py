from django import forms
from .models import Scenario, AuctionYear, Pot, Technology
from django.forms import Textarea

class ScenarioForm(forms.ModelForm):

    class Meta:
        model = Scenario
        fields = ('name', 'description', 'budget', 'percent_emerging','end_year',)
        widgets = {
          'description': Textarea(attrs={'rows':2, 'cols':20}),
        }

class PricesForm(forms.Form):
    wholesale_prices = forms.CharField(max_length=200)
    gas_prices = forms.CharField(max_length=200)

class TechnologyStringForm(forms.Form):
    name = forms.CharField(max_length=200)
    min_levelised_costs = forms.CharField(max_length=200)
    max_levelised_costs = forms.CharField(max_length=200)
    #strike_prices = forms.CharField(max_length=200)
    #load_factors = forms.CharField(max_length=200)
    #project_gens = forms.CharField(max_length=200)
    #max_deployment_caps = forms.CharField(max_length=200)
