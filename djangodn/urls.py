"""djangodn URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from dn import views

urlpatterns = [

    path('api/onto', views.get_ontologies, name='ontologies'),
    path('api/datasets', views.get_datasets, name='datasets'),
    path('api/classes', views.get_classes, name='classes'),
    path('api/props', views.get_data_props, name='props'),
    path('api/claims', views.get_claims, name='claims'),
    path('api/new_dataset', views.new_dataset, name='new_dataset'),
    path('api/agent', views.get_agent, name='agent'),
    path('api/agents', views.get_agents, name='agents'),
    path('api/pub', views.pub, name='pub'),
    path('api/publications', views.pubs, name='pubs'),
    path('api/work', views.work, name='work'),
    path('api/format', views.get_formats, name='format'),
    path('api/operation', views.get_operations, name='operation'),
    path('api/download', views.download_file, name='download'),
    path('api/stat_subj', views.get_stat_subj, name='stat_subj'),
    path('api/list_recents', views.list_recents, name='list_recents'),
    path('api/loc', views.loc, name='loc'),    
    path('api/stat_key', views.get_stat_key, name='stat_key'),
    path('api/instance', views.get_instance, name='instance'),
    path('api/new_service', views.new_service, name='new_service'),
    path('api/datasets', views.get_datasets, name='get_datasets'),
    path('api/query', views.query_KB, name='query'),
    path('api/service', views.get_services, name='service'),
    path('api/services', views.get_services, name='services'),
    path('api/distribution', views.get_distribution, name='distribution'),
    path('api/new_distribution', views.upload_distribution, name='new_distribution'),
]
