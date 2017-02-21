from django.contrib import admin

# Register your models here.
from .models import Scenario, AuctionYear, Pot, Technology
admin.site.register(Scenario)
admin.site.register(AuctionYear)
admin.site.register(Pot)
admin.site.register(Technology)
