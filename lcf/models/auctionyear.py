from django.db import models
from django.utils import timezone
import pandas as pd
import numpy as np
from pandas import DataFrame, Series
from functools import lru_cache
import datetime
import time

from .pot import Pot
from .technology import Technology

class AuctionYear(models.Model):
    scenario = models.ForeignKey('lcf.scenario', default=1)#http://stackoverflow.com/questions/937954/how-do-you-specify-a-default-for-a-django-foreignkey-model-or-adminmodel-field
    year = models.IntegerField(default=2020)
    wholesale_price = models.FloatField(default=53)
    gas_price = models.FloatField(default=85)
    budget_result = models.FloatField(blank=True, null=True)
    # cum_owed_v_wp = models.FloatField(blank=True, null=True)
    # cum_owed_v_gas = models.FloatField(blank=True, null=True)
    # cum_owed_v_absolute = models.FloatField(blank=True, null=True)


    def __str__(self):
        return str(self.year)

    def __init__(self, *args, **kwargs):
        super(AuctionYear, self).__init__(*args, **kwargs)
        #self._budget = None
        self._unspent = None
        self._previous_year_unspent = None


    #budget methods
    def starting_budget(self):
        if self.year == 2020:
            return 481.29

        elif self.period_num() == 2 and self.scenario.budget2 != None:
            period_length = self.scenario.end_year2 - self.scenario.start_year2 + 1
            return self.scenario.budget2 / period_length * 1000
        else:
            period_length = self.scenario.end_year1 - self.scenario.start_year1 + 1
            return self.scenario.budget / period_length * 1000



    #@lru_cache(maxsize=128)
    def budget(self):
        if self.budget_result:
            res = self.budget_result
            return res
        else:
            sb = self.starting_budget() #slower than necessary but not that big a deal
            pyu = self.previous_year_unspent()
            afsn = self.awarded_from("SN")
            affit = self.awarded_from("FIT")
            self.budget_result = sb + pyu - afsn - affit
            res = self.budget_result
            self.save()

        return res

    #@lru_cache(maxsize=128)
    def unspent(self):
        if self._unspent:
            return self._unspent
        else:
            nw_carry = 0
            if self.scenario.excel_nw_carry_error == True or self.scenario.excel_quirks == True:
                nw_carry =  self.awarded_from("FIT")
            self._unspent = self.budget() - self.awarded_from("auction") + nw_carry
            return self._unspent

    #@lru_cache(maxsize=128)
    def previous_year(self):
        if self.year == 2020:
            return None
        return self.scenario.auctionyear_set.get(year=self.year-1)

    #@lru_cache(maxsize=128)
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
    #
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

    #@lru_cache(maxsize=128)
    # def cum_years(self):
    #     if self.year == 2020:
    #         return [self]
    #     else:
    #         start_year = self.scenario.start_year1 if self.year <= self.scenario.end_year1 else self.scenario.start_year2
    #         return self.scenario.auctionyear_set.filter(year__range=(start_year,self.year)).order_by('year')

    #@lru_cache(maxsize=128)
    def active_pots(self):
        active_names = [ pot.name for pot in self.pot_set.all() if pot.tech_set().count() > 0 ]
        return self.pot_set.filter(name__in=active_names).order_by("name")

    #
    #summary methods
    #@lru_cache(maxsize=128)
    def awarded_from(self,pot):
        if pot == "FIT" or pot == "SN":
            if self.active_pots().filter(name=pot).exists():
                p = Pot.objects.get(name=pot,auctionyear=self)
                res = p.awarded_cost()
                return res
            else:
                return 0
        elif pot == "auction":
            res = sum([pot.awarded_cost() for pot in self.active_pots() if pot.name == "E" or pot.name == "M"])
            return res
        elif pot == "total":
            res = sum([self.awarded_from("FIT"),self.awarded_from("SN"),self.awarded_from("auction")])
            return res
    #
    #
    #
    #
    # #@lru_cache(maxsize=128)
    # def awarded_gen(self):
    #     return sum(pot.awarded_gen() for pot in self.active_pots().all())
    #
    #
    # @lru_cache(maxsize=128)
    # def owed_v(self, comparison, previous_year):
    #     return sum([pot.owed_v(comparison, previous_year.active_pots().get(name=pot.name)) for pot in self.active_pots() ])
    #
    # #@lru_cache(maxsize=128)
    # def nw_owed(self,previous_year):
    #     if self.active_pots().filter(name="FIT").exists():
    #         # pot = self.active_pots().get(name="FIT")
    #         # previous_fpot = previous_year.active_pots().get(name="FIT")
    #         # return pot.owed_v("absolute", previous_fpot)
    #         pot = Pot.objects.get(auctionyear=self,name="FIT")
    #         previous_pot = Pot.objects.get(auctionyear = previous_year, name="FIT")
    #         return pot.owed_v("absolute",previous_pot)
    #     else:
    #         return 0
    #
    #
    # #accumulating methods
    # #@lru_cache(maxsize=128)
    # def cum_awarded_gen(self):
    #     return sum([pot.cum_awarded_gen() for pot in self.active_pots()])
    #
    # @lru_cache(maxsize=128)
    # def cum_owed_v(self, comparison):
    #     if self.year == 2020:
    #         return self.owed_v(comparison, self)
    #     else:
    #         return sum([pot.cum_owed_v(comparison) for pot in self.active_pots()])
    #
    # #@lru_cache(maxsize=128)
    # def innovation_premium(self):
    #     return self.cum_owed_v("gas") - self.cum_nw_owed()
    #
    # def cum_nw_owed(self):
    #     if self.year == 2020:
    #         return self.nw_owed(self)
    #     else:
    #         return self.active_pots().get(name="FIT").cum_owed_v("absolute")
