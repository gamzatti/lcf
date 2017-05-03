from django.db import models
from django.utils import timezone
import pandas as pd
import numpy as np
from pandas import DataFrame, Series
from functools import lru_cache
import datetime
import time
import lcf.dataframe_helpers as dfh

from .auctionyear import AuctionYear
from .pot import Pot
from .technology import Technology

class Policy(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    date = models.DateTimeField(default=timezone.now)
    METHOD_CHOICES = [('MU', 'multiply'), ('SU', 'subtract')]
    method = models.CharField(max_length=2, choices=METHOD_CHOICES, default='MU')
    effects = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name

    @lru_cache(maxsize=1024)
    def df(self, subset=None):
        if subset == "prices":
            columns = dfh.prices_policy_keys
        elif subset == "techs":
            columns = dfh.tech_policy_keys
        else:
            columns = dfh.policy_keys
        df = pd.read_json(self.effects).reindex(columns=columns)
        return df


    def df_for_display(self,subset):
        effects = self.df(subset)
        if subset == 'techs':
            effects.columns = dfh.tech_policy_columns
            effects = effects.dropna(axis=1,how="all")
            effects = effects.set_index(dfh.tech_policy_index['titles'])
            effects = effects.dropna(axis=0,how="all")
        elif subset == 'prices':
            effects = self.df('prices')
            effects = effects.dropna(axis=1,how="all")
            effects = effects.set_index(dfh.prices_policy_index)
            effects = effects.dropna(axis=0,how="all")
            effects = effects.unstack(0)
            effects.columns = dfh.prices_policy_columns
        effects = effects.style.format("{:.0%}").render()
        effects = effects.replace('<table id=', '<table class="table table-striped table-condensed" id=')
        return effects


    def df_for_download(self):
        effects = self.df()
        effects = effects.dropna(axis=1,how="all")
        return effects
