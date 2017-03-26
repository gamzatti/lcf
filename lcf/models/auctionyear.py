from django.db import models
from django.utils import timezone
import pandas as pd
import numpy as np
from pandas import DataFrame, Series
from functools import lru_cache
import datetime


from .pot import Pot
from .technology import Technology

class AuctionYear(models.Model):
    scenario = models.ForeignKey('lcf.scenario', default=1)#http://stackoverflow.com/questions/937954/how-do-you-specify-a-default-for-a-django-foreignkey-model-or-adminmodel-field
    year = models.IntegerField(default=2020)
    wholesale_price = models.FloatField(default=53)
    gas_price = models.FloatField(default=85)


    def __str__(self):
        return str(self.year)

    def __init__(self, *args, **kwargs):
        super(AuctionYear, self).__init__(*args, **kwargs)
        self.starting_budget = 481.29 if self.year == 2020 else self.scenario.budget / 5 * 1000
        self._budget = None
        self._unspent = None
        self._previous_year_unspent = None

    #budget methods
    #@lru_cache(maxsize=None)
    def budget(self):
        if self._budget:
            return self._budget
        else:
            self._budget = self.starting_budget + self.previous_year_unspent() - self.awarded_from("SN") - self.awarded_from("FIT")
            return self._budget

    #@lru_cache(maxsize=None)
    def unspent(self):
        if self._unspent:
            return self._unspent
        else:
            nw_carry = 0
            if self.scenario.excel_nw_carry_error:
                nw_carry =  self.awarded_from("FIT")
            self._unspent = self.budget() - self.awarded_from("auction") + nw_carry
            return self._unspent

    #@lru_cache(maxsize=None)
    def previous_year(self):
        if self.year == 2020:
            return None
        return self.scenario.auctionyear_set.get(year=self.year-1)

    #@lru_cache(maxsize=None)
    def previous_year_unspent(self):
        if self._previous_year_unspent:
            return self._previous_year_unspent
        elif self.year == 2020 or self.year == 2021:
            return 0
        else:
            previous_year = self.previous_year()
            self._previous_year_unspent = previous_year.unspent()
            return previous_year.unspent()



    #helper methods

    def period(self):
        return self.period_calc()['years']

    def period_num(self):
        return self.period_calc()['num']

    def period_calc(self):
        if self.year == 2020:
            num = 0
            years = [self]
        else:
            if self in self.scenario.period(1):
                num = 1
                years = self.scenario.period(1)
            elif self in self.scenario.period(2):
                num = 2
                years = self.scenario.period(2)
        return {'num': num, 'years': years}

    #@lru_cache(maxsize=None)
    def cum_years(self):
        if self.year == 2020:
            return [self]
        else:
            start_year = self.scenario.start_year1 if self.year <= self.scenario.end_year1 else self.scenario.start_year2
            return self.scenario.auctionyear_set.filter(year__range=(start_year,self.year)).order_by('year')

    #@lru_cache(maxsize=None)
    def active_pots(self):
        active_names = [ pot.name for pot in self.pot_set.all() if pot.tech_set().count() > 0 ]
        return self.pot_set.filter(name__in=active_names)


    #summary methods
    #@lru_cache(maxsize=None)
    def awarded_from(self,pot):
        if pot == "FIT" or pot == "SN":
            if self.active_pots().filter(name=pot).exists():
                return self.active_pots().get(name=pot).awarded_cost()
            else:
                return 0
        elif pot == "auction":
            return sum([pot.awarded_cost() for pot in self.active_pots() if pot.name == "E" or pot.name == "M"])
        elif pot == "total":
            return sum([self.awarded_from("FIT"),self.awarded_from("SN"),self.awarded_from("auction")])

    #@lru_cache(maxsize=None)
    def awarded_gen(self):
        return sum(pot.awarded_gen() for pot in self.active_pots().all())


    #@lru_cache(maxsize=None)
    def owed_v(self, comparison, previous_year):
        return sum([pot.owed_v(comparison, previous_year.active_pots().get(name=pot.name)) for pot in self.active_pots() ])

    #@lru_cache(maxsize=None)
    def nw_owed(self,previous_year):
        if self.active_pots().filter(name="FIT").exists():
            pot = self.active_pots().get(name="FIT")
            previous_fpot = previous_year.active_pots().get(name="FIT")
            return pot.owed_v("absolute", previous_fpot)
        else:
            return 0


    #accumulating methods
    #@lru_cache(maxsize=None)
    def cum_awarded_gen(self):
        return sum([pot.cum_awarded_gen() for pot in self.active_pots()])

    #@lru_cache(maxsize=None)
    def cum_owed_v(self, comparison):
        if self.year == 2020:
            return self.owed_v(comparison, self)
        else:
            return sum([pot.cum_owed_v(comparison) for pot in self.active_pots()])

    #@lru_cache(maxsize=None)
    def innovation_premium(self):
        return self.cum_owed_v("gas") - self.nw_cum_owed()

    def nw_cum_owed(self):
        if self.year == 2020:
            return self.nw_owed(self)
        else:
            return self.active_pots().get(name="FIT").nw_cum_owed()
