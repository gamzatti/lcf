from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.scenario_new, name='scenario_new'),
    url(r'^scenario/(?P<pk>\d+)/$', views.scenario_detail, name='scenario_detail'),
    url(r'^scenario/(?P<pk>\d+)/delete/$', views.scenario_delete, name='scenario_delete'),
]
