from django import forms
from .models import Scenario, AuctionYear, Pot, Technology, Policy
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
    wholesale_prices = forms.ChoiceField(widget=forms.Select(attrs={'class': "col-sm-5"}), choices=WP_CHOICES)
    wholesale_prices_other = forms.CharField(widget=forms.TextInput(attrs={'class': "col-sm-5"}), max_length=400, label="If other, please list", required=False)
    gas_prices = forms.ChoiceField(widget=forms.Select(attrs={'class': "col-sm-5"}), choices=GAS_CHOICES)
    gas_prices_other = forms.CharField(widget=forms.TextInput(attrs={'class': "col-sm-5"}), max_length=400, label="If other, please list", required=False)
    file = forms.FileField(label="Technology data")

    class Meta:
        model = Scenario
        fields = ('name', 'description', 'budget', 'budget2', 'percent_emerging', 'excel_sp_error', 'excel_2020_gen_error', 'excel_nw_carry_error', 'excel_include_previous_unsuccessful_nuclear', 'excel_include_previous_unsuccessful_all', 'excel_quirks', 'end_year1', 'subsidy_free_p2', 'policies')
        widgets = {
          'name': forms.TextInput(attrs={'class': "col-sm-5"}),
          'description': Textarea(attrs={'rows':2, 'cols':40, 'class': "col-sm-5"}),
          'budget': forms.NumberInput(attrs={'class': "col-sm-5", 'step': 0.1}),
          'budget2': forms.NumberInput(attrs={'class': "col-sm-5", 'step': 0.1}),
          'percent_emerging': forms.NumberInput(attrs={'class': "col-sm-5", 'step': 0.1}),
          'excel_sp_error': forms.CheckboxInput(attrs={'class': "col-sm-5"}),
          'excel_2020_gen_error': forms.CheckboxInput(attrs={'class': "col-sm-5"}),
          'excel_nw_carry_error': forms.CheckboxInput(attrs={'class': "col-sm-5"}),
          'excel_include_previous_unsuccessful_all': forms.CheckboxInput(attrs={'class': "col-sm-5"}),
          'excel_include_previous_unsuccessful_nuclear': forms.CheckboxInput(attrs={'class': "col-sm-5"}),
          'excel_quirks': forms.CheckboxInput(attrs={'class': "col-sm-5"}),
          'end_year1': forms.NumberInput(attrs={'class': "col-sm-5"}),
          'subsidy_free_p2': forms.CheckboxInput(attrs={'class': "col-sm-5"}),
          'policies': forms.CheckboxSelectMultiple()
        }

class PricesForm(forms.Form):
    wholesale_prices = forms.CharField(max_length=400)
    gas_prices = forms.CharField(max_length=400)


class PolicyForm(forms.ModelForm):
    file = forms.FileField(label="Cost changes")

    class Meta:
        model = Policy
        fields = ('name',
                  'description',
                  'method',
        )
        widgets = {
          'name': forms.TextInput(attrs={'class': "col-sm-5"}),
          'description': Textarea(attrs={'rows':2, 'cols':40, 'class': "col-sm-5"}),
          'method': forms.RadioSelect(attrs={'class': "col-sm-5"}),
        }
