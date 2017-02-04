from django.contrib import admin

# Register your models here.
from .models import Scenario, AuctionYearSet, AuctionYear, TechnologyYearData, Project
admin.site.register(Scenario)
admin.site.register(AuctionYearSet)
admin.site.register(AuctionYear)
admin.site.register(TechnologyYearData)
admin.site.register(Project)
