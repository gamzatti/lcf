from django.db import models
from django.utils import timezone

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
        return number


class AuctionYear(models.Model):
    inputset = models.ForeignKey('lcf.scenario', blank=True, null=True)
    year = models.IntegerField(default=2020)

    def __str__(self):
        return str(self.year)


class AuctionYearTechnology(models.Model):
    year = models.ForeignKey('lcf.auctionyear', blank=True, null=True)
    technology_name = models.CharField(max_length=200)
    strike_price = models.DecimalField(default=100, max_digits=5, decimal_places=2)
    min_levelised_cost = models.DecimalField(default=100, max_digits=5, decimal_places=2)
    max_levelised_cost = models.DecimalField(default=100, max_digits=5, decimal_places=2)
    project_size = models.DecimalField(default=100, max_digits=5, decimal_places=2)
    max_deployment = models.DecimalField(default=100, max_digits=5, decimal_places=2)

    def __str__(self):
        return str((self.year,self.technology_name))


class Project(models.Model):
    auction_year_technology = models.ForeignKey('lcf.AuctionYearTechnology', blank=True, null=True)
    levelised_cost = models.DecimalField(default=100, max_digits=5, decimal_places=2)
    affordable = models.BooleanField(default=False)
    successful = models.BooleanField(default=False)

    def __str__(self):
        return str((self.auction_year_technology.year, self.auction_year_technology.technology_name, str(self.levelised_cost), self.affordable, self.successful))
