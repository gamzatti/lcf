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

    def get_foo(self):
        try:
            self.foo
        except AttributeError:
            self.foo = 5+17
        return self.foo

    def bar(self):
        pass

    def __str__(self):
        return self.name

    def cost(self):
        cost = 0
        for a in self.auctionyear_set.all():
            for p in a.pot_set.all():
                cost += p.cost()
        return round(cost,3)

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


    def budget(self):
        if self.year == 2020:
            yearly_budget = 481.29
            previous_year_leftover = 0
        else:
            yearly_budget = self.scenario.budget / 5 * 1000
            previous_year = self.scenario.auctionyear_set.all().get(year=self.year-1)
            previous_year_leftover = previous_year.leftover()
        yearly_budget += previous_year_leftover
        return yearly_budget


    def leftover(self):
        #nb this is combined pots
        l = {2019: 0, 2020: 0, 2021: 349.07, 2022: 524.76 , 2023: 1048.10, 2024: 1616.12, 2025: 2200.54, 2026: 2145.85, 2027: 2093.53, 2028: 2028.08, 2029: 1958.61, 2030: 1889.38}
        return l[self.year]

    def combined_manual_leftover(self):
        combined = 0
        for pot in self.pot_set.all():
            combined += pot.manual_leftover()
        return combined



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


    def budget(self):
        return self.auctionyear.budget() * self.percent()

    def percent(self):
        if self.name == "E":
            return self.auctionyear.scenario.percent_emerging
        if self.name == "M":
            return 1 - self.auctionyear.scenario.percent_emerging
        else:
            return 0


    def manual_leftover(self):
        #single pot leftover
        return self.budget() - self.cost()

    def combined_leftover(self):
        AuctionYear.objects.filter(scenario=self.auctionyear.scenario)

    def run_auction(self):
        cost = 0
        gen = 0
        combined_tech_affordable_projects = Series(name='Combined tech affordable projects')
        project_lists = self.technology_set.all()
        for project_list in project_lists:
            cfd_unit_cost = project_list.strike_price - self.auctionyear.wholesale_price
            for ind in project_list.affordable_projects().index:
                if cost + cfd_unit_cost * project_list.project_gen_correct() < self.budget():
                    combined_tech_affordable_projects[ind] = project_list.affordable_projects()[ind]
                    cost += cfd_unit_cost * project_list.project_gen_correct()
                    gen += project_list.project_gen_correct()
                else:
                    break
        return {'cost': cost, 'gen': gen, 'combined_tech_affordable_projects': combined_tech_affordable_projects}

    def cost(self):
        return round(self.run_auction()['cost'],3)

    def gen(self):
        return round(self.run_auction()['gen'],3)

    def combined_tech_affordable_projects(self):
        return self.run_auction()['combined_tech_affordable_projects']







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

    def project_gen_correct(self):
        return self.project_gen / 1000

    def project_cap(self):
        return cap(self.project_gen_correct(),self.load_factor)

    def max_deployment_gen(self):
        return gen(self.max_deployment_cap,self.load_factor)

    def num_projects(self):
        return self.max_deployment_gen() / self.project_gen_correct()

    def years_supported(self):
        return 2031 - self.pot.auctionyear

    def deployable_projects(self):
        dep = Series(np.linspace(self.min_levelised_cost,self.max_levelised_cost,self.num_projects()+2)[1:-1],name="Deployable Projects") # could change to a normal distribution
        dep.index = [ self.name + str(i + 1) for i in range(len(dep)) ]
        return dep

    def affordable_projects(self):
        aff = Series(self.deployable_projects()[self.deployable_projects() <= self.strike_price],name="Affordable Projects")
        return aff

    def unaffordable_projects(self):
        un = Series(self.deployable_projects()[self.deployable_projects() > self.strike_price],name="Unaffordable Projects")
        return un


class StoredProject(models.Model):
    technology = models.ForeignKey('lcf.Technology', blank=True, null=True)
    levelised_cost = models.FloatField(default=100)
    affordable = models.BooleanField(default=False)
    successful = models.BooleanField(default=False)

    def __str__(self):
        return str((self.technology.pot.auctionyear, self.technology.name, str(self.levelised_cost), self.affordable, self.successful))


def load_factor(cap_gw,gen_twh):
    return gen_twh / (cap_gw * 8.760)

def cap(gen_twh,load_factor):
    return gen_twh / (load_factor * 8.760)

def gen(cap_gw,load_factor):
    return cap_gw * load_factor * 8.760
