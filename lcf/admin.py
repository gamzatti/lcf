from django.contrib import admin

# Register your models here.
from .models import Scenario, AuctionYear, AuctionYearTechnology, Project
admin.site.register(Scenario)
admin.site.register(AuctionYear)
admin.site.register(AuctionYearTechnology)
admin.site.register(Project)
