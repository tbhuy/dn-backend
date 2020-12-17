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

    path('api/onto', views.getOntologies, name='onto'),
    path('api/classes', views.getClasses, name='classes'),
    path('api/props', views.getDataProps, name='props'),
    #path('onto/load', views.load, name='index'),
    path('dataset', views.new_dataset, name='new_dataset'),
    path('api/agent', views.agent, name='agent'),
    path('api/pub', views.pub, name='pub'),
    path('api/work', views.work, name='work'),
    path('api/format', views.format, name='format'),
    path('api/operation', views.operation, name='operation'),
    path('api/download', views.download_file, name='download'),
    path('api/stat_subj', views.stat_subj, name='stat_subj'),
    path('api/list_recents', views.list_recents, name='list_recents'),
    path('api/loc', views.loc, name='loc'),    
    path('api/stat_key', views.stat_key, name='stat_key'),
    path('api/instance', views.instance, name='instance'),
    path('api/new_service', views.new_service, name='new_service'),
]
