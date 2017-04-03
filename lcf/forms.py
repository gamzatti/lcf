from django import forms
from .models import Scenario, AuctionYear, Pot, Technology
from django.forms import Textarea


class ScenarioForm(forms.ModelForm):
    all_excel_quirks = forms.BooleanField(required=False, label="Include/exclude all Excel quirks")

    class Meta:
        model = Scenario
        fields = ('name', 'description', 'budget', 'budget2', 'percent_emerging','start_year1','end_year1','excel_2020_gen_error', 'excel_sp_error','excel_nw_carry_error', 'tidal_levelised_cost_distribution')
        widgets = {
          'description': Textarea(attrs={'rows':2, 'cols':20}),
        }

class PricesForm(forms.Form):
    wholesale_prices = forms.CharField(max_length=400)
    gas_prices = forms.CharField(max_length=400)

class UploadFileForm(forms.Form):
    title = forms.CharField(max_length=200)
    file = forms.FileField()

class TechnologyStringForm(forms.Form):
    POT_CHOICES = (
            ('E', 'Emerging'),
            ('M', 'Mature'),
            ('FIT', 'Feed-in-tariff'),
            ('SN', 'Separate negotiations'),
    )
    name = forms.CharField(max_length=400)
    included = forms.BooleanField(required=False)
    pot = forms.ChoiceField(widget=forms.Select,
        choices=POT_CHOICES)
    min_levelised_cost = forms.CharField(max_length=400)
    max_levelised_cost = forms.CharField(max_length=400)
    max_deployment_cap = forms.CharField(max_length=400,required=False)
    num_new_projects = forms.CharField(max_length=400,required=False)
    load_factor = forms.CharField(max_length=400)
    strike_price = forms.CharField(max_length=400)
    project_gen = forms.CharField(max_length=400)
    """def __init__(self, *args, **kwargs):
        super(TechnologyStringForm, self).__init__(*args, **kwargs)
        self.fields['name'].disabled = True
        self.fields['pot'].disabled = True"""
