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


#refactor this in a sec
    def awarded_gen(self):
        return sum(pot.awarded_gen() for pot in self.active_pots().all())
        awarded_gen = 0
        for pot in self.active_pots().all():
            awarded_gen += pot.awarded_gen()
        return awarded_gen


    def cum_awarded_gen(self):
        extra2020 = 0
        if self.scenario.excel_2020_gen_error:
            pots2020 = self.scenario.auctionyear_set.get(year=2020).active_pots().exclude(name="FIT")
            extra2020 = sum([pot.awarded_gen() for pot in pots2020])
        return sum([year.awarded_gen() for year in self.years()]) + extra2020



    def years(self):
        if self.year == 2020:
            return [self]
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
            pot.run_auction()
            for t in pot.tech_set().all():
                gen = t.awarded_gen
                strike_price = t.strike_price
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
        owed = sum(owed.values())
        return owed

    def nw_paid(self):
        if self.year == 2020:
            return self.nw_owed(self)
        else:
            return sum([self.nw_owed(year) for year in self.years()])

    def nw_owed(self,previous_year):
        if self.active_pots().filter(name="FIT").exists():
            pot = self.active_pots().get(name="FIT")
            previous_pot = previous_year.active_pots().get(name="FIT")
            return pot.nw_owed(previous_pot)
        else:
            return 0


    """def nw_owed_old(self,previous_year):
        if self.active_pots().filter(name="FIT").exists():
            pot = previous_year.active_pots().get(name="FIT")
            pot.run_auction()
            t = Technology.objects.get(name="NW", pot=pot)
            gen = t.awarded_gen
            difference = t.strike_price
            owed = gen * difference
            return owed
        else:
            return 0"""


    def owed_v_gas(self, previous_year):
        owed = {}
        for pot in previous_year.active_pots().all():
            owed[pot.name] = 0
            for t in pot.tech_set().all():
                gen = t.awarded_gen
                strike_price = t.strike_price
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
        owed = sum(owed.values())
        return owed

    @lru_cache(maxsize=None)
    def active_pots(self):
        active_names = [ pot.name for pot in self.pot_set.all() if pot.tech_set().count() > 0 ]
        return self.pot_set.filter(name__in=active_names)
