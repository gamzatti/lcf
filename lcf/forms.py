from django import forms
from .models import Scenario, AuctionYear, Pot, Technology, Policy
from django.forms import Textarea
import re
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from .validators import validate_file_extension

class MultiPriceField(forms.CharField):
    def to_python(self, value):
        """Normalize data to a list of strings."""
        # Return an empty list if no input was given.
        if not value:
            return []
        delimters = "[, \-!?:\t]+"
        return list(filter(None, re.split(delimters,value)))

    def validate(self, value):
        """Check if value consists only of valid emails."""
        super(MultiPriceField, self).validate(value)
        if len(value) > 0 and len(value) != 11:
            raise ValidationError(
                # _('%(value)s does not have 11 values'),
                # params={'value': value},
                'Must have 11 values, separated by commas, spaces or tabs.'
                )
        for price in value:
            try:
                float(price)
            except ValueError:
                raise ValidationError(
                    _('%(price)s is not a valid number'),
                    params={'price': price},
                    )



class ScenarioForm(forms.ModelForm):
    #all_excel_quirks = forms.BooleanField(required=False, label="Include/exclude all Excel quirks")
    # WP_CHOICES = (("excel", "Excel version"),
    #               ("new", "2017 Emissions data"),
    #               ("other", "Other"),
    #               )
    # GAS_CHOICES = (("excel", "Excel version"),
    #               ("other", "Other"),
    #               )
    # wholesale_prices = forms.ChoiceField(widget=forms.Select(attrs={'class': "col-sm-5"}), choices=WP_CHOICES)
    # # wholesale_prices_other = forms.CharField(widget=forms.TextInput(attrs={'class': "col-sm-5"}), max_length=400, label="If other, please list", required=False)
    # wholesale_prices_other = MultiPriceField(widget=forms.TextInput(attrs={'class': "col-sm-5"}), max_length=400, label="If other, please list", required=False)
    #
    # gas_prices = forms.ChoiceField(widget=forms.Select(attrs={'class': "col-sm-5"}), choices=GAS_CHOICES)
    # # gas_prices_other = forms.CharField(widget=forms.TextInput(attrs={'class': "col-sm-5"}), max_length=400, label="If other, please list", required=False)
    # gas_prices_other = MultiPriceField(widget=forms.TextInput(attrs={'class': "col-sm-5"}), max_length=400, label="If other, please list", required=False)
    file = forms.FileField(label="Technology and prices data", validators=[validate_file_extension])

    class Meta:
        model = Scenario
        fields = ('name', 'description', 'budget', 'budget2', 'percent_emerging', 'excel_sp_error', 'excel_2020_gen_error', 'excel_nw_carry_error', 'excel_include_previous_unsuccessful_nuclear', 'excel_include_previous_unsuccessful_all','excel_external_clearing_price', 'excel_quirks', 'end_year1', 'subsidy_free_p2', 'policies')
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
          'excel_external_clearing_price': forms.CheckboxInput(attrs={'class': 'col-sm-5'}),
          'excel_quirks': forms.CheckboxInput(attrs={'class': "col-sm-5"}),
          'end_year1': forms.NumberInput(attrs={'class': "col-sm-5"}),
          'subsidy_free_p2': forms.CheckboxInput(attrs={'class': "col-sm-5"}),
          'policies': forms.CheckboxSelectMultiple()
        }
        help_texts = {
            'end_year1': 'Used for aggregation purposes. Default is 2025, after which the cost accumulation is reset.',
             'excel_include_previous_unsuccessful_all': 'Overrides maximum deployment limit. Incompatible with switching technologies on/off for individual years.',
             'excel_quirks': 'If selected, overrides individual quirk settings.',
             'subsidy_free_p2': 'Only projects cheaper than gas+carbon price are considered.'
        }

    def clean(self):
        cleaned_data = super(ScenarioForm, self).clean()
        wholesale_prices = cleaned_data.get('wholesale_prices')
        wholesale_prices_other = cleaned_data.get('wholesale_prices_other')
        gas_prices = cleaned_data.get('gas_prices')
        gas_prices_other = cleaned_data.get('gas_prices_other')
        if wholesale_prices != 'other' and wholesale_prices_other:
            raise forms.ValidationError(
                    "To specify new wholesale prices, first set the option to 'Other' above."
                )
        if wholesale_prices == 'other' and wholesale_prices_other == []:
            raise forms.ValidationError(
                    "If specifying 'Other' for wholesale prices, please input 11 valid numbers, separated by commas, spaces or tabs."
                )
        if gas_prices != 'other' and gas_prices_other:
            raise forms.ValidationError(
                    "To specify new gas prices, first set the option to 'Other' above."
                )
        if gas_prices == 'other' and gas_prices_other == []:
            raise forms.ValidationError(
                    "If specifying 'Other' for gas prices, please input 11 valid numbers, separated by commas, spaces or tabs."
                )



class PricesForm(forms.Form):
    wholesale_prices = forms.CharField(max_length=400)
    gas_prices = forms.CharField(max_length=400)


class PolicyForm(forms.ModelForm):
    file = forms.FileField(label="Cost changes", validators=[validate_file_extension])

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
        help_texts = {
        'method': 'Multiply means values in csv will be multiplied by existing tech data, subtract means they will be subtracted from it.'
        }
