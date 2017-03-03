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
    load_factor = forms.CharField(max_length=200)
    min_levelised_cost = forms.CharField(max_length=200)
    max_levelised_cost = forms.CharField(max_length=200)
    strike_price = forms.CharField(max_length=200)
    name = forms.CharField(max_length=200)
    project_gen = forms.CharField(max_length=200)
    max_deployment_cap = forms.CharField(max_length=200)

    def __init__(self, *args, **kwargs):
        super(TechnologyStringForm, self).__init__(*args, **kwargs)
        self.fields['name'].disabled = True
