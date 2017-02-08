from django.db import models
from django.utils import timezone
import pandas as pd
import numpy as np
from pandas import DataFrame, Series

# Create your models here.

class Scenario(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    date = models.DateTimeField(default=timezone.now)
    budget = models.FloatField(default=3.3)
    percent_emerging = models.FloatField(default=0.6)

    def __str__(self):
        return self.name


    def results(self):
        auction_tally = {'cost': 0, 'gen': 0}
        for auctionyear in self.auctionyear_set.all():
            auction_results = auctionyear.run_auction('E')
            auction_tally['cost'] += auction_results['cost']
            auction_tally['gen'] += auction_results['gen']
        return auction_tally

    def cost(self):
        return round(self.results()['cost'],3)

    def gen(self):
        return round(self.results()['gen'],3)

class AuctionYear(models.Model):
    scenario = models.ForeignKey('lcf.scenario', default=1)#http://stackoverflow.com/questions/937954/how-do-you-specify-a-default-for-a-django-foreignkey-model-or-adminmodel-field
    year = models.IntegerField(default=2020)
    wholesale_price = models.IntegerField(default=53)

    def __str__(self):
        return str(self.year)


    def budget_calc(self, pot):
        yearly_budget = self.scenario.budget / 5 * 1000
        if self.year == 2020:
            yearly_budget = 481.29
        previous_year_unspent = {2020: 0, 2021: 0, 2022: 349.07, 2023: 524.76 , 2024: 1048.10, 2025: 1616.12, 2026: 2200.54, 2027: 2145.85, 2028: 2093.53, 2029: 2028.08, 2030: 1958.61}
        yearly_budget += previous_year_unspent[self.year]
        budget_e = yearly_budget * self.scenario.percent_emerging
        budget_m = yearly_budget - budget_e
        if pot == "E":
            return budget_e
        if pot == "M":
            return budget_m



    def pot_budget_e(self):
        return self.budget_calc("E")

    def pot_budget_m(self):
        return self.budget_calc("M")


    def run_auction(self,pot):
        cost = 0
        gen = 0
        combined_tech_affordable_projects = Series(name='Combined tech affordable projects')
        project_lists = self.auctionyeartechnology_set.filter(pot=pot)
        for project_list in project_lists:
            cfd_unit_cost = project_list.strike_price - self.wholesale_price
            for ind in project_list.affordable_projects().index:
                if cost + cfd_unit_cost * project_list.project_gen_correct() < self.budget_calc(pot):
                    combined_tech_affordable_projects[ind] = project_list.affordable_projects()[ind]
                    cost += cfd_unit_cost * project_list.project_gen_correct()
                    gen += project_list.project_gen_correct()
                else:
                    break
        return {'cost': cost, 'gen': gen, 'combined_tech_affordable_projects': combined_tech_affordable_projects}

    def cost_e(self):
        return round(self.run_auction('E')['cost'],3)

    def gen_e(self):
        return round(self.run_auction('E')['gen'],3)

    def combined_tech_affordable_projects_e(self):
        return self.run_auction('E')['combined_tech_affordable_projects']


class AuctionYearTechnology(models.Model):
    POT_CHOICES = (
            ('E', 'Emerging'),
            ('M', 'Mature'),
    )
    TECHNOLOGY_CHOICES = (
            ('OFW', 'Offshore wind'),
            ('ONW', 'Onshore wind'),
            ('NU', 'Nuclear'),
            ('TL', 'Tidal lagoon'),
            ('TS', 'Tidal stream'),
            ('WA', 'Wave'),
            ('PVLS', 'Solar PV'),
    )
    year = models.ForeignKey('lcf.auctionyear', default=232)
    technology_name = models.CharField(max_length=4, choices=TECHNOLOGY_CHOICES, default='OFW')
    pot = models.CharField(max_length=1, choices=POT_CHOICES, default='E')
    min_levelised_cost = models.FloatField(default=100)
    max_levelised_cost = models.FloatField(default=100)
    strike_price = models.FloatField(default=100)
    load_factor = models.FloatField(default=0.5)
    project_gen = models.FloatField(default=100)
    max_deployment_cap = models.FloatField(default=100)

    def __str__(self):
        return str((self.year,self.technology_name))

    def project_gen_correct(self):
        return self.project_gen / 1000

    def project_cap(self):
        return cap(self.project_gen_correct(),self.load_factor)

    def max_deployment_gen(self):
        return gen(self.max_deployment_cap,self.load_factor)

    def num_projects(self):
        return self.max_deployment_gen() / self.project_gen_correct()

    def years_supported(self):
        return 2031 - self.year

    def deployable_projects(self):
        dep = Series(np.linspace(self.min_levelised_cost,self.max_levelised_cost,self.num_projects()+2)[1:-1],name="Deployable Projects") # could change to a normal distribution
        dep.index = [ self.technology_name + str(i + 1) for i in range(len(dep)) ]
        return dep

    def affordable_projects(self):
        aff = Series(self.deployable_projects()[self.deployable_projects() <= self.strike_price],name="Affordable Projects")
        return aff

    def unaffordable_projects(self):
        un = Series(self.deployable_projects()[self.deployable_projects() > self.strike_price],name="Unaffordable Projects")
        return un


class StoredProject(models.Model):
    auction_year_technology = models.ForeignKey('lcf.AuctionYearTechnology', blank=True, null=True)
    levelised_cost = models.FloatField(default=100)
    affordable = models.BooleanField(default=False)
    successful = models.BooleanField(default=False)

    def __str__(self):
        return str((self.auction_year_technology.year, self.auction_year_technology.technology_name, str(self.levelised_cost), self.affordable, self.successful))


def load_factor(cap_gw,gen_twh):
    return gen_twh / (cap_gw * 8.760)

def cap(gen_twh,load_factor):
    return gen_twh / (load_factor * 8.760)

def gen(cap_gw,load_factor):
    return cap_gw * load_factor * 8.760
