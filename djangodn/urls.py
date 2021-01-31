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
from dn import agent, claim, dataset, publication, workflow, utils, meta

urlpatterns = [
    path('api/show-dataset', dataset.show_dataset, name='show-dataset'),
    path('api/import-meta', meta.import_meta, name='import-meta'),
    path('api/new-meta', meta.new_meta, name='new-meta'),
    path('api/onto', utils.get_ontologies, name='ontologies'),
    path('api/datasets', dataset.get_datasets, name='datasets'),
    path('api/dataset', dataset.get_dataset, name='dataset'),
    path('api/classes', utils.get_classes, name='classes'),
    path('api/props', meta.get_data_props, name='props'),
    path('api/claims', claim.get_claims, name='claims'),
    path('api/claim', claim.get_claim, name='claim'),
    path('api/new-dataset', dataset.new_dataset, name='new_dataset'),
    path('api/agent', agent.get_agent, name='agent'),
    path('api/agents', agent.get_agents, name='agents'),
    path('api/pub', publication.get_pubs_doi, name='pub'),
    path('api/pub-title', publication.get_pubs_title, name='pub-title'),
    path('api/publications', publication.get_pubs, name='pubs'),
    path('api/work', workflow.execute_workflow, name='work'),
    path('api/formats', utils.get_formats, name='format'),
    path('api/operations', utils.get_operations, name='operation'),
    path('api/download', utils.download_file, name='download'),
    path('api/stat-subj', dataset.get_stat_subj, name='stat-subj'),
    path('api/list-recents', dataset.list_recents, name='list-recents'),
    path('api/loc', dataset.get_loc, name='loc'),    
    path('api/stat-key', dataset.get_stat_key, name='stat_key'),
    path('api/instance', utils.get_instance, name='instance'),
    path('api/new-service', workflow.new_service, name='new-service'),
    path('api/new-pub', publication.new_pub, name='new-service'),
    path('api/new-agent', agent.new_agent, name='new-agent'),
    path('api/new-claim', claim.new_claim, name='new-claim'),
    path('api/query', utils.query_KB, name='query'),
    path('api/service', workflow.get_services, name='service'),
    path('api/services', workflow.get_services, name='services'),
    path('api/distribution', dataset.get_distribution, name='distribution'),
    path('api/distributions', dataset.get_distributions, name='distributions'),
    path('api/new-distribution', dataset.upload_distribution, name='new-distribution'),
    path('api/preview', utils.view_file, name='preview'),
    path('api/sites', utils.get_sites, name='sites'),
]
