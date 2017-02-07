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
        return number / 7


class AuctionYear(models.Model):
    scenario = models.ForeignKey('lcf.scenario', default=48)#http://stackoverflow.com/questions/937954/how-do-you-specify-a-default-for-a-django-foreignkey-model-or-adminmodel-field
    year = models.IntegerField(default=2020)
    wholesale_price = models.IntegerField(default=50)

    def __str__(self):
        return str(self.year)


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


class Project(models.Model):
    auction_year_technology = models.ForeignKey('lcf.AuctionYearTechnology', blank=True, null=True)
    levelised_cost = models.FloatField(default=100)
    affordable = models.BooleanField(default=False)
    successful = models.BooleanField(default=False)

    def __str__(self):
        return str((self.auction_year_technology.year, self.auction_year_technology.technology_name, str(self.levelised_cost), self.affordable, self.successful))
