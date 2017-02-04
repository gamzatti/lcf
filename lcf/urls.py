from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.scenario_new, name='scenario_new'),
    url(r'^scenario_save/$', views.scenario_save, name='scenario_save'),
]
