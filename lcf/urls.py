from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^scenario/(?P<pk>\d+)/$', views.scenario_detail, name='scenario_detail'),
    url(r'^scenario/(?P<pk>\d+)/new/$', views.scenario_new, name='scenario_new'),
#    url(r'^scenario/(?P<pk>\d+)/new2/$', views.scenario_new2, name='scenario_new2'),
    url(r'^scenario/(?P<pk>\d+)/delete/$', views.scenario_delete, name='scenario_delete'),
]
