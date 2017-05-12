from django.conf.urls import include, url
from django.conf import settings
from django.views.generic import TemplateView
from django.conf.urls import handler404
from . import views

urlpatterns = [
    url('scenario/new/', views.scenario_new, name='scenario_new'),
    url('scenario/new', views.scenario_new, name='scenario_new'),
    url('policy/new/', views.policy_new, name='policy_new'),
    url('policy/new', views.policy_new, name='policy_new'),
    url(r'^policy/(?P<pk>\d+)/$', views.policy_detail, name='policy_detail'),
    url(r'^policy/(?P<pk>\d+)$', views.policy_detail, name='policy_detail'),
    url(r'^policy/(?P<pk>\d+)/delete/$', views.policy_delete, name='policy_delete'),
    url(r'^policy/(?P<pk>\d+)/delete$', views.policy_delete, name='policy_delete'),
    url('policy/template/', views.policy_template, name='policy_template'),
    url('policy/template', views.policy_template, name='policy_template'),
    url('template/', views.template, name='template'),
    url('template', views.template, name='template'),
    url(r'^scenario/(?P<pk>\d+)/$', views.scenario_detail, name='scenario_detail'),
    url(r'^scenario/(?P<pk>\d+)$', views.scenario_detail, name='scenario_detail'),
    url(r'^scenario/(?P<pk>\d+)/delete/$', views.scenario_delete, name='scenario_delete'),
    url(r'^scenario/(?P<pk>\d+)/delete$', views.scenario_delete, name='scenario_delete'),
    url(r'^scenario/(?P<pk>\d+)/delete/new/$', views.scenario_delete_and_create_new, name='scenario_delete_and_create_new'),
    url(r'^scenario/(?P<pk>\d+)/delete/new$', views.scenario_delete_and_create_new, name='scenario_delete_and_create_new'),
    url(r'^scenario/(?P<pk>\d+)/download/$', views.scenario_download, name='scenario_download'),
    url(r'^scenario/(?P<pk>\d+)/download$', views.scenario_download, name='scenario_download'),
    url('glossary/', views.glossary, name='glossary'),
    url('glossary', views.glossary, name='glossary'),
    url(r'', views.scenario_detail, name='scenario_detail'),
]
# handler404 = 'views.error404'

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns
