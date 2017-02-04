from django.db import models
from django.utils import timezone

# Create your models here.
class Scenario(models.Model):
    name = models.CharField(max_length=200)
    date = models.DateTimeField(default=timezone.now)
    generalinputset = models.ForeignKey('lcf.generalinputset', blank=True, null=True)

    def __str__(self):
        return self.name

    def results(self):
        number = self.generalinputset.budget * 4
        return number

class GeneralInputSet(models.Model):
    budget = models.DecimalField(default=3, max_digits=5, decimal_places=3)
    percent_emerging = models.DecimalField(default=0.6, max_digits=4, decimal_places=3)

    def __str__(self):
        return str({'budget': str(self.budget), 'percent_emerging': str(self.percent_emerging)})
