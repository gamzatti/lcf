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
