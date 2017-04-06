from django.conf.urls import include, url
from django.conf import settings
from . import views

urlpatterns = [
    url('upload/', views.upload, name='upload'),
    url('template/', views.template, name='template'),
    url(r'^scenario/(?P<pk>\d+)/$', views.scenario_detail, name='scenario_detail'),
#    url(r'^scenario/(?P<pk>\d+)/new/$', views.scenario_new, name='scenario_new'),
#    url(r'^scenario/(?P<pk>\d+)/new2/$', views.scenario_new2, name='scenario_new2'),
    url(r'^scenario/(?P<pk>\d+)/delete/$', views.scenario_delete, name='scenario_delete'),
    url(r'^scenario/(?P<pk>\d+)/download/$', views.scenario_download, name='scenario_download'),
    url('', views.scenario_detail, name='scenario_detail'),

]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
