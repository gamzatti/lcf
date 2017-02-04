from django.contrib import admin

# Register your models here.
from .models import Scenario, GeneralInputSet
admin.site.register(Scenario)
admin.site.register(GeneralInputSet)
