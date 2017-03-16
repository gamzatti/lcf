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

    #@lru_cache(maxsize=None)
    def budget(self):
        if self._budget:
            return self._budget
        else:
            self._budget = self.starting_budget + self.previous_year_unspent() - self.awarded_from_negotiation() - self.awarded_from_fit()
            return self._budget


    #@lru_cache(maxsize=None)
    def awarded(self):
        awarded = 0
        for pot in self.active_pots().order_by("name"):
            awarded += pot.cost()
        return awarded

    def awarded_from_negotiation(self):
        if self.active_pots().filter(name="SN").exists():
            return self.active_pots().get(name="SN").cost()
        else:
            return 0

    def awarded_from_fit(self):
        if self.active_pots().filter(name="FIT").exists():
            return self.active_pots().get(name="FIT").cost()
        else:
            return 0


    def awarded_from_auction(self):
        awarded = 0
        for pot in self.active_pots().all():
            if pot.name == "E" or pot.name == "M":
                awarded += pot.cost()
        return awarded

    def awarded_gen(self):
        awarded_gen = 0
        for pot in self.active_pots().all():
            #print(pot.name, 'awarded', self.year, pot.gen())
            awarded_gen += pot.gen()
        return awarded_gen

    #@lru_cache(maxsize=None)
    def unspent(self):
        if self._unspent:
            return self._unspent
        else:
            self._unspent = self.budget() - self.awarded_from_auction() + self.awarded_from_fit()
            return self._unspent


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

    def previous_years(self):
        if self.year == 2020:
            return None
        else:
            return self.scenario.auctionyear_set.filter(year__range=(self.scenario.start_year,self.year-1)).order_by('year')

    def years(self):
        if self.year == 2020:
            return self
        else:
            return self.scenario.auctionyear_set.filter(year__range=(self.scenario.start_year,self.year)).order_by('year')


    def paid(self):
        if self.year == 2020:
            return self.owed(self)
        else:
            return sum([self.owed(year) for year in self.years()])

    def paid_v_gas(self):
        if self.year == 2020:
            return self.owed_v_gas(self)
        else:
            return sum([self.owed_v_gas(year) for year in self.years()])

    def innovation_premium(self):
        return self.paid_v_gas() - self.nw_paid()


    def owed(self, previous_year):
        owed = {}
        for pot in previous_year.active_pots().all():
            owed[pot.name] = 0
            data = pot.summary_for_future()
            for t in pot.tech_set().all():
                gen = data['gen'][t.name]
                strike_price = data['strike_price'][t.name]
                if self.scenario.excel_wp_error == True:
                    #next 5 lines account for Angela's error
                    if (pot.name == "E") or (pot.name == "SN"):
                        try:
                            strike_price = self.active_pots().get(name=pot.name).tech_set().get(name=t.name).strike_price
                        except:
                            break
                difference = strike_price - self.wholesale_price
                if pot.name == "FIT":
                    difference = strike_price
                tech_owed = gen * difference
                owed[pot.name] += tech_owed
                #print(self.year, previous_year.year, t.name, tech_owed)
        owed = sum(owed.values())
        return owed

    def nw_paid(self):
        if self.year == 2020:
            return self.nw_owed(self)
        else:
            return sum([self.nw_owed(year) for year in self.years()])

    def nw_owed(self,previous_year):
        pot = previous_year.active_pots().get(name="FIT")
        data = pot.summary_for_future()
        t = Technology.objects.get(name="NW", pot=pot)
        gen = data['gen'][t.name]
        difference = data['strike_price'][t.name]
        owed = gen * difference
        return owed


    def owed_v_gas(self, previous_year):
        owed = {}
        for pot in previous_year.active_pots().all():
            owed[pot.name] = 0
            data = pot.summary_for_future()
            for t in pot.tech_set().all():
                gen = data['gen'][t.name]
                strike_price = data['strike_price'][t.name]
                if self.scenario.excel_wp_error == True:
                    #next 5 lines account for Angela's error
                    if (pot.name == "E") or (pot.name == "SN"):
                        try:
                            strike_price = self.active_pots().get(name=pot.name).tech_set().get(name=t.name).strike_price
                        except:
                            break
                difference = strike_price - self.gas_price
                if pot.name == "FIT":
                    difference = strike_price
                tech_owed = gen * difference
                owed[pot.name] += tech_owed
                #print(self.year, previous_year.year, t.name, tech_owed)
        owed = sum(owed.values())
        return owed

    @lru_cache(maxsize=None)
    def active_pots(self):
        active_names = [ pot.name for pot in self.pot_set.all() if pot.tech_set().count() > 0 ]
        return self.pot_set.filter(name__in=active_names)
