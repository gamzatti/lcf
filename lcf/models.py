from django.db import models
from django.utils import timezone
import pandas as pd
import numpy as np
from pandas import DataFrame, Series
from functools import lru_cache


class Scenario(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True, verbose_name="Description (optional)")
    date = models.DateTimeField(default=timezone.now)
    budget = models.FloatField(default=3.3, verbose_name="Budget (£bn)")
    percent_emerging = models.FloatField(default=0.6)
    rank_by_levelised_cost = models.BooleanField(default=True)

    def __str__(self):
        return self.name


    @lru_cache(maxsize=None)
    def cost(self):
        cost = 0
        for a in self.auctionyear_set.all():
            for p in a.pot_set.all():
                cost += p.cost()
        return round(cost,3)

    @lru_cache(maxsize=None)
    def cost_2020(self):
        cost = 0
        for a in self.auctionyear_set.filter(year__lte=2020):
            for p in a.pot_set.all():
                cost += p.cost()
        return round(cost,3)


    @lru_cache(maxsize=None)
    def cost_lcf2(self):
        cost = 0
        for a in self.auctionyear_set.filter(year__range=(2021,2025)):
            for p in a.pot_set.all():
                cost += p.cost()
        return round(cost,3)


    @lru_cache(maxsize=None)
    def cost_lcf3(self):
        cost = 0
        for a in self.auctionyear_set.filter(year__range=(2026,2030)):
            for p in a.pot_set.all():
                cost += p.cost()
        return round(cost,3)



    @lru_cache(maxsize=None)
    def gen(self):
        gen = 0
        for a in self.auctionyear_set.all():
            for p in a.pot_set.all():
                gen += p.gen()
        return round(gen,3)

class AuctionYear(models.Model):
    scenario = models.ForeignKey('lcf.scenario', default=1)#http://stackoverflow.com/questions/937954/how-do-you-specify-a-default-for-a-django-foreignkey-model-or-adminmodel-field
    year = models.IntegerField(default=2020)
    wholesale_price = models.IntegerField(default=53)

    def __str__(self):
        return str(self.year)

    @lru_cache(maxsize=None)
    def budget(self):
        return round(self.starting_budget() + self.previous_year_unspent(),3)

    @lru_cache(maxsize=None)
    def starting_budget(self):
        if self.year == 2020:
            yearly_budget = 481.29
        else:
            yearly_budget = self.scenario.budget / 5 * 1000
        return yearly_budget

    @lru_cache(maxsize=None)
    def cost(self):
        combined = 0
        for pot in self.pot_set.all():
            combined += pot.cost()
        return combined

    @lru_cache(maxsize=None)
    def unspent(self):
        return self.budget() - self.cost()

    @lru_cache(maxsize=None)
    def previous_year_unspent(self):
        if self.year == 2020 or self.year == 2021:
            previous_year_unspent = 0
        else:
            previous_year = self.scenario.auctionyear_set.all().get(year=self.year-1)
            previous_year_unspent = previous_year.unspent()
        return previous_year_unspent


class Pot(models.Model):
    POT_CHOICES = (
            ('E', 'Emerging'),
            ('M', 'Mature'),
            ('NW', 'Negawatts'),
            ('SN', 'Separate negotiations'),
    )
    auctionyear = models.ForeignKey('lcf.auctionyear', default=232)
    name = models.CharField(max_length=1, choices=POT_CHOICES, default='E')

    def __str__(self):
        return str((self.auctionyear, self.name))

    @lru_cache(maxsize=None)
    def budget(self):
        return round((self.auctionyear.budget() * self.percent()),3)

    @lru_cache(maxsize=None)
    def percent(self):
        if self.name == "E":
            return self.auctionyear.scenario.percent_emerging
        if self.name == "M":
            return 1 - self.auctionyear.scenario.percent_emerging
        else:
            return 0

    """Attempt at new calculations that use clearing price.
    @lru_cache(maxsize=None)
    def run_auction(self):
        projects = self.concat_projects()
        spent = 0
        gen = 0
        for i in projects[projects.affordable == True].index:
            if spent + projects.cfd_payout[i] < self.budget():
                projects['funded'][i] = True
                #change the clearing price to the next lowest levelised_cost for the technology
                tech_subset = projects[technology==projects.technology[i]]
                tech_subset['clearing_price'] = tech_subset['clearing_price'][i+1]
                projects['cfd_unit_cost'] = projects.clearing_price - self.auctionyear.wholesale_price # not accurate - all projects get paid out the highest LCOE, not the strike price
                projects['cfd_payout'] = projects.cfd_unit_cost * projects.gen
                spent += projects[projects.funded == True]['cfd_payout'][i]
                gen += projects[projects.funded == True]['gen'][i]
            else:
                break
        return {'cost': spent, 'gen': gen, 'projects': projects}


    def concat_projects(self):
        if self.technology_set.count() == 0:
            projects = DataFrame(columns=['levelised_cost', 'gen', 'technology', 'strike_price', 'clearing_price', 'affordable', 'funded', 'cfd_unit_cost', 'cfd_payout', 'cum_cost', 'cum_gen'])
        else:
            projects = pd.concat([t.projects() for t in self.technology_set.all()])
            projects['affordable'] = projects.levelised_cost <= projects.strike_price
            projects['funded'] = False
            if self.auctionyear.scenario.rank_by_levelised_cost == True:
                projects = projects.sort_values('levelised_cost')
            else:
                projects = projects.sort_values('cfd_payout')
        return projects"""

    @lru_cache(maxsize=None)
    def run_auction(self):
        projects = self.concat_projects()
        spent = 0
        gen = 0
        for i in projects[projects.affordable == True].index:
            if spent + projects.cfd_payout[i] < self.budget():
                projects['funded'][i] = True
                spent += projects[projects.funded == True]['cfd_payout'][i]
                gen += projects[projects.funded == True]['gen'][i]
            else:
                break
        return {'cost': spent, 'gen': gen, 'projects': projects}


    def concat_projects(self):
        if self.technology_set.count() == 0:
            projects = DataFrame(columns=['levelised_cost', 'gen', 'technology', 'strike_price', 'clearing_price', 'affordable', 'funded', 'cfd_unit_cost', 'cfd_payout', 'cum_cost', 'cum_gen'])
        else:
            projects = pd.concat([t.projects() for t in self.technology_set.all()])
            projects['affordable'] = projects.levelised_cost <= projects.strike_price
            projects['cfd_unit_cost'] = projects.strike_price - self.auctionyear.wholesale_price # not accurate - all projects get paid out the highest LCOE, not the strike price
            projects['cfd_payout'] = projects.cfd_unit_cost * projects.gen
            projects['funded'] = False
            if self.auctionyear.scenario.rank_by_levelised_cost == True:
                projects = projects.sort_values('levelised_cost')
            else:
                projects = projects.sort_values('cfd_payout')
        return projects


    @lru_cache(maxsize=None)
    def cost(self):
        return round(self.run_auction()['cost'],3)

    @lru_cache(maxsize=None)
    def unspent(self):
        return round(self.budget() - self.cost(),3)

    @lru_cache(maxsize=None)
    def gen(self):
        return round(self.run_auction()['gen'],3)

    @lru_cache(maxsize=None)
    def funded_projects(self):
        df = self.run_auction()['projects']
        return df[df.funded == True]







class Technology(models.Model):
    TECHNOLOGY_CHOICES = (
            ('OFW', 'Offshore wind'),
            ('ONW', 'Onshore wind'),
            ('NU', 'Nuclear'),
            ('TL', 'Tidal lagoon'),
            ('TS', 'Tidal stream'),
            ('WA', 'Wave'),
            ('PVLS', 'Solar PV'),
    )
    name = models.CharField(max_length=4, choices=TECHNOLOGY_CHOICES, default='OFW')
    pot = models.ForeignKey('lcf.pot', default='E')
    min_levelised_cost = models.FloatField(default=100)
    max_levelised_cost = models.FloatField(default=100)
    strike_price = models.FloatField(default=100)
    load_factor = models.FloatField(default=0.5)
    project_gen = models.FloatField(default=100)
    max_deployment_cap = models.FloatField(default=100)

    def __str__(self):
        return str((self.pot.auctionyear,self.pot.name,self.name))

    @lru_cache(maxsize=None)
    def project_gen_correct(self):
        return self.project_gen / 1000

    @lru_cache(maxsize=None)
    def project_cap(self):
        return cap(self.project_gen_correct(),self.load_factor)

    @lru_cache(maxsize=None)
    def max_deployment_gen(self):
        return gen(self.max_deployment_cap,self.load_factor)

    @lru_cache(maxsize=None)
    def num_projects(self):
        return self.max_deployment_gen() / self.project_gen_correct()

    @lru_cache(maxsize=None)
    def years_supported(self):
        return 2031 - self.pot.auctionyear

    @lru_cache(maxsize=None)
    def projects(self):
        dep = Series(np.linspace(self.min_levelised_cost,self.max_levelised_cost,self.num_projects()+2)[1:-1],name="levelised_cost")
        gen = Series(np.repeat(self.project_gen_correct(),len(dep)),name='gen')
        projects = pd.concat([dep,gen], axis=1)
        projects.index = [ self.name + str(i + 1) for i in range(len(dep)) ]
        projects['technology'] = self.name
        projects['strike_price'] = self.strike_price
        projects['clearing_price'] = projects.levelised_cost.min()
        projects['affordable'] = False
        #projects['affordable'] = projects.levelised_cost <= projects.strike_price
        projects['funded'] = False
        return projects



class StoredProject(models.Model):
    technology = models.ForeignKey('lcf.Technology', blank=True, null=True)
    levelised_cost = models.FloatField(default=100)
    affordable = models.BooleanField(default=False)
    successful = models.BooleanField(default=False)

    def __str__(self):
        return str((self.technology.pot.auctionyear, self.technology.name, str(self.levelised_cost), self.affordable, self.successful))


@lru_cache(maxsize=None)
def load_factor(cap_gw,gen_twh):
    return gen_twh / (cap_gw * 8.760)

@lru_cache(maxsize=None)
def cap(gen_twh,load_factor):
    return gen_twh / (load_factor * 8.760)

@lru_cache(maxsize=None)
def gen(cap_gw,load_factor):
    return cap_gw * load_factor * 8.760
