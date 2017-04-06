from django import forms
from .models import Scenario, AuctionYear, Pot, Technology
from django.forms import Textarea


class ScenarioForm(forms.ModelForm):
    #all_excel_quirks = forms.BooleanField(required=False, label="Include/exclude all Excel quirks")
    WP_CHOICES = (("excel", "Excel version"),
                  ("new", "2017 Emissions data"),
                  ("other", "Other"),
                  )
    GAS_CHOICES = (("excel", "Excel version"),
                  ("other", "Other"),
                  )
    wholesale_prices = forms.ChoiceField(widget=forms.Select, choices=WP_CHOICES)
    wholesale_prices_other = forms.CharField(max_length=400, label="If other, please list", required=False)
    gas_prices = forms.ChoiceField(widget=forms.Select, choices=GAS_CHOICES)
    gas_prices_other = forms.CharField(max_length=400, label="If other, please list", required=False)

    class Meta:
        model = Scenario
        fields = ('name', 'description', 'budget', 'budget2', 'percent_emerging','excel_quirks', 'end_year1')
        widgets = {
          'description': Textarea(attrs={'rows':2, 'cols':20}),
        }

class PricesForm(forms.Form):
    wholesale_prices = forms.CharField(max_length=400)
    gas_prices = forms.CharField(max_length=400)

class UploadFileForm(forms.Form):
    #title = forms.CharField(max_length=200)
    file = forms.FileField()

# class TechnologyStringForm(forms.Form):
#     POT_CHOICES = (
#             ('E', 'Emerging'),
#             ('M', 'Mature'),
#             ('FIT', 'Feed-in-tariff'),
#             ('SN', 'Separate negotiations'),
#     )
#     name = forms.CharField(max_length=400)
#     included = forms.BooleanField(required=False)
#     pot = forms.ChoiceField(widget=forms.Select,
#         choices=POT_CHOICES)
#     min_levelised_cost = forms.CharField(max_length=400)
#     max_levelised_cost = forms.CharField(max_length=400)
#     max_deployment_cap = forms.CharField(max_length=400,required=False)
#     num_new_projects = forms.CharField(max_length=400,required=False)
#     load_factor = forms.CharField(max_length=400)
#     strike_price = forms.CharField(max_length=400)
#     project_gen = forms.CharField(max_length=400)
#     """def __init__(self, *args, **kwargs):
#         super(TechnologyStringForm, self).__init__(*args, **kwargs)
#         self.fields['name'].disabled = True
#         self.fields['pot'].disabled = True"""
