from django.db import models
from django.utils import timezone
import pandas as pd
import numpy as np
from pandas import DataFrame, Series
from functools import lru_cache
import datetime
import time

from .auctionyear import AuctionYear
from .pot import Pot
from .technology import Technology

class Policy(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    date = models.DateTimeField(default=timezone.now)
    effects = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name

    def df(self):
        print(pd.read_json(self.effects))
        columns = ["tech_name", "listed_year", "min_levelised_cost_change", "max_levelised_cost_change", "strike_price_change", "load_factor_change", "max_deployment_cap_change", "num_new_projects_change", "project_gen_change"]
        return pd.read_json(self.effects).reindex(columns=columns)

    def df_for_display(self):
        effects = pd.read_json(self.effects)
        columns = ["tech_name", "listed_year", "min_levelised_cost_change", "max_levelised_cost_change", "strike_price_change", "load_factor_change", "max_deployment_cap_change", "num_new_projects_change", "project_gen_change"]
        effects = effects.reindex(columns=columns)
        effects = effects.dropna(axis=1,how="all")
        effects = effects.set_index(['tech_name','listed_year'])
        effects = effects.style.format("{:.0%}").render()
        effects = effects.replace('<table id=', '<table class="table table-striped table-condensed" id=')
        return effects

    def df_for_download(self):
        effects = pd.read_json(self.effects)
        columns = ["tech_name", "listed_year", "min_levelised_cost_change", "max_levelised_cost_change", "strike_price_change", "load_factor_change", "max_deployment_cap_change", "num_new_projects_change", "project_gen_change"]
        effects = effects.reindex(columns=columns)
        effects = effects.dropna(axis=1,how="all")
        return effects
