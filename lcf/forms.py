from django import forms
from .models import Scenario, AuctionYear, Pot, Technology
from django.forms import Textarea

class ScenarioForm(forms.ModelForm):

    class Meta:
        model = Scenario
        fields = ('name', 'description', 'budget', 'percent_emerging','set_strike_price',)
        widgets = {
          'description': Textarea(attrs={'rows':2, 'cols':20}),
        }
