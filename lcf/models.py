from django.db import models
from django.utils import timezone
import pandas as pd
import numpy as np
from pandas import DataFrame, Series

# Create your models here.

class Scenario(models.Model):
    name = models.CharField(max_length=200)
    date = models.DateTimeField(default=timezone.now)
    budget = models.DecimalField(default=3, max_digits=5, decimal_places=3)
    percent_emerging = models.DecimalField(default=0.6, max_digits=4, decimal_places=3)

    def __str__(self):
        return self.name


    def results(self):
        number = self.budget * 4
        return number / 7


class AuctionYear(models.Model):
    scenario = models.ForeignKey('lcf.scenario', default=48)#http://stackoverflow.com/questions/937954/how-do-you-specify-a-default-for-a-django-foreignkey-model-or-adminmodel-field
    year = models.IntegerField(default=2020)
    wholesale_price = models.IntegerField(default=50)



    def __str__(self):
        return str(self.year)

    def pot_budget(self):
        pot_budget = {2020: 196,
                    2021: 156,
                    2022: 260,
                    2023: 327,
                    2024: 245,
                    2025: 114,
                    2026: 66,
                    2027: 73,
                    2028: 94,
                    2029: 272,
                    2030: 366}
        return pot_budget[self.year]


    def find_projects(self):
        project_lists = []
        for t in self.auctionyeartechnology_set.filter(pot='E'):
            project_list = ProjectList(technology_code = t.technology_name,
                                year = t.year.year,
                                min_levelised_cost = t.min_levelised_cost,
                                max_levelised_cost = t.max_levelised_cost,
                                strike_price = t.strike_price,
                                load_factor = t.load_factor,
                                project_gen = t.project_size,
                                max_deployment_cap = t.max_deployment)
            project_lists.append(project_list)
        return project_lists

    def run_auction(self):
        cost = 0
        gen = 0
        combined_tech_affordable_projects = Series(name='Combined tech affordable projects')
        project_lists = self.find_projects()
        for project_list in project_lists:
            cfd_unit_cost = project_list.strike_price - self.wholesale_price
            for ind in project_list.affordable_projects().index:
                if cost + cfd_unit_cost * project_list.project_gen < self.pot_budget():
                    combined_tech_affordable_projects[ind] = project_list.affordable_projects()[ind]
                    cost += cfd_unit_cost * project_list.project_gen
                    gen += project_list.project_gen
                else:
                    break
        return {'cost': cost, 'gen': gen}

    def auction_cost(self):
        return round(self.run_auction()['cost'],2)

    def auction_gen(self):
        return round(self.run_auction()['gen'],2)


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
    project_size = models.FloatField(default=100)
    max_deployment = models.FloatField(default=100)

    def __str__(self):
        return str((self.year,self.technology_name))

    """def project_list(self):
        return ProjectList(technology_code = self.technology_name,
                            year = self.year.year,
                            min_levelised_cost = self.min_levelised_cost,
                            max_levelised_cost = self.max_levelised_cost,
                            strike_price = self.strike_price,
                            load_factor = self.load_factor,
                            project_gen = self.project_size,
                            max_deployment_cap = self.max_deployment)"""


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

class ProjectList:
    def __init__(self,**kwargs):
        self.technology_code = kwargs['technology_code']
        self.year = kwargs['year']
        self.min_levelised_cost = kwargs['min_levelised_cost']
        self.max_levelised_cost = kwargs['max_levelised_cost']
        self.strike_price = kwargs['strike_price']
        self.load_factor = kwargs['load_factor']
        self.project_gen = kwargs['project_gen'] / 1000
        self.project_cap = cap(self.project_gen,self.load_factor)
        self.max_deployment_cap = kwargs['max_deployment_cap']
        self.max_deployment_gen = gen(self.max_deployment_cap,self.load_factor)
        self.num_projects = self.max_deployment_gen / self.project_gen
        self.years_supported = 2031 - self.year

    def deployable_projects(self):
        dep = Series(np.linspace(self.min_levelised_cost,self.max_levelised_cost,self.num_projects+2)[1:-1],name="Deployable Projects") # could change to a normal distribution
        dep.index = [ self.technology_code + str(i + 1) for i in range(len(dep)) ]
        return dep

    def affordable_projects(self):
        aff = Series(self.deployable_projects()[self.deployable_projects() <= self.strike_price],name="Affordable Projects")
        return aff

    def unaffordable_projects(self):
        un = Series(self.deployable_projects()[self.deployable_projects() > self.strike_price],name="Unaffordable Projects")
        return un

    def __str__(self):
        return str(self.affordable_projects())
