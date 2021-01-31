from django.http import HttpResponse, JsonResponse
from SPARQLWrapper import SPARQLWrapper, JSON, POST, DIGEST, INSERT, BASIC
import requests
import os
from django.views.decorators.csrf import csrf_exempt
import json
from django.conf import settings

#graphdb = "#GRAPHDB#"
dataverse = "#DATAVERSE#"
dataverse_ex = "#DATAVERSEEX#" 
dv_key = "#DATAVERSEKEY#"
graphdb_user = "#GRAPHDBUSER#"
graphdb_pwd = "#GRAPHDBPWD#"

graphdb = "http://172.17.0.4:7200/repositories/dn"
#dataverse = "http://localhost:8085"
#dataverse_ex = "http://localhost:8085" 
#dataverse = "http://melodi.irit.fr:8080"
#dataverse_ex = "http://localhost:8085" 
#dv_key = "9cc13e11-6ac8-42bc-8dc5-28a0c4e622da"


def read_sites():
  files_path = os.path.join(settings.BASE_DIR, 'public',  'static', 'sites.json') 
  json_file = open(files_path)   
  json_data = json.load(json_file)
  json_file.close()
  return json_data

def get_sites(request):
  return JsonResponse(read_sites(), safe=False) 

def query(str):
    sparql = SPARQLWrapper(graphdb)
    sparql.setReturnFormat(JSON)
    sparql.setQuery(str)        
    results = sparql.query().convert()
    return results

@csrf_exempt
def query_KB(request):
   
    results = query(request.GET.get('query'))
    json = []
    rec = {}
    for result in results["results"]["bindings"]:
      rec = {}
      for label in results["head"]["vars"]:
        rec[label] = result[label]["value"]
      json.append(rec)
   
    return JsonResponse({'rs':json}, safe=False) 


def download_file(request):
    file_name = request.GET.get('fn')
    file_path = os.path.join(settings.BASE_DIR, 'public',  'static', 'scripts')
    fs = FileSystemStorage(file_path)
    response = FileResponse(fs.open(file_name, 'rb'), content_type='application/force-download')
    response['Content-Disposition'] = 'attachment; filename="'+ file_name+ '"'
    return response

def view_file(request):
    file_name = request.GET.get('fn')
    file_path = os.path.join(settings.BASE_DIR, 'public',  'static', 'scripts', file_name)
    myfile = open(file_path, "r")
    myline = myfile.readline()
    data = ""
    line = 1
    while myline and line <=10:
      data = data +  myline
      myline = myfile.readline()
      line = line +1
    myfile.close()  

    return HttpResponse(data)

def insert_data(prefixes, triples): 
    sparql = SPARQLWrapper(graphdb)
    sparql.setReturnFormat(JSON)
    sparql = SPARQLWrapper(graphdb +"/statements")
    sparql.setHTTPAuth(DIGEST)
    sparql.setCredentials(graphdb_user, graphdb_pwd)
    sparql.setMethod(POST)
    sparql.setHTTPAuth(BASIC)
    query = """{}
    INSERT DATA
        {{ 
            {} 
        }}
        """.format(prefixes, triples)  
    print(query)    
    sparql.setQuery(query)
    results = sparql.query()
    print(results.response.read())
    return results.response.read()

def get_operations(request):
    results = query("""PREFIX owl: <http://www.w3.org/2002/07/owl#>
  PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
  select ?uri ?label where {
    ?uri a owl:Class. 
    filter(regex(str(?uri), "edamontology.org/operation")).
    ?uri rdfs:label ?label.
    }
    order by strlen(str(?label))  
    """)
  
    json = []
    for result in results["results"]["bindings"]:
        json.append({'id':result["uri"]["value"], 'name': result["label"]["value"]})
   
    return JsonResponse({'rs':json}, safe=False)


def get_formats(request):
    results = query("""PREFIX owl: <http://www.w3.org/2002/07/owl#>
  PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
  select ?uri ?label where {
    ?uri a owl:Class. 
    filter(regex(str(?uri), "edamontology.org/format")).
    ?uri rdfs:label ?label.
    }
    order by strlen(str(?label))  
    """)

    json = []
    for result in results["results"]["bindings"]:
        json.append({'id':result["uri"]["value"], 'name': result["label"]["value"]})
   
    return JsonResponse({'rs':json}, safe=False)

def get_instance(request):
    results = query("""PREFIX owl: <http://www.w3.org/2002/07/owl#>
  PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
  select ?pre ?prop ?label {{
    <{}> ?pre ?prop. 
    ?pre rdfs:label ?label.
    FILTER (lang(?label)= "en" || lang(?label)="")

    }}""".format(request.GET.get('uri', '')))
  
    json = []
    for result in results["results"]["bindings"]:
        json.append({'property':result["label"]["value"] + " (" + result["pre"]["value"] + ") ", 'value': result["prop"]["value"]})
   
    return JsonResponse({'rs':json}, safe=False)
    
def get_classes(request):
  results = query(""" PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
        SELECT ?uri ?label ?comment ?onto
        WHERE {{
           <{}> a ?uri.

           ?uri rdfs:label ?label.
           FILTER (lang(?label)= "en" || lang(?label)="") 
        OPTIONAL
           {{
           ?uri rdfs:comment ?comment.
           FILTER (lang(?comment)= "en" || lang(?comment)="")
           }}
        ?uri rdfs:isDefinedBy ?onto.
        }}""".format(request.GET.get('uri')))
        
  json = []
  for result in results["results"]["bindings"]:
    cls = {'uri':result["uri"]["value"], 'onto':result["onto"]["value"]}
    if result.get("label"):
      cls['label'] = result["label"]["value"]
    else:
      cls['label'] = ''
    if result.get("comment"):
      cls["comment"] = result["comment"]["value"]
    else:
      cls["comment"] = '-'
    json.append(cls)

  json.append({'uri': 'http://purl.org/dc/terms/Thing' , 'onto':'http://purl.org/dc/terms/', 'label':'Thing', 'comment':'A blank class'})
  json.append({'uri':'http://www.w3.org/2000/01/rdf-schema#Resource', 'onto':'http://www.w3.org/2000/01/rdf-schema#', 'label':'Resource', 'comment':'The class resource, everything'})
  json.append({'uri':' http://www.w3.org/2002/07/owl#Thing', 'onto':' http://www.w3.org/2002/07/owl#', 'label':'Thing', 'comment':'The class of OWL individuals'})
  return JsonResponse({'rs':json}, safe=False)

def get_ontologies(request):
    results = query(""" PREFIX dc: <http://purl.org/dc/terms/>
        SELECT ?uri ?title ?description 
        WHERE {
           ?uri rdf:type owl:Ontology .
           ?uri dc:title ?title . 
        OPTIONAL{
           ?uri dc:description ?description.
           }
        }
        ORDER BY ?title
        """)    
    json = []
    for result in results["results"]["bindings"]:
        on = {'uri':result["uri"]["value"], 'title':result["title"]["value"]}
        if result.get("description"):
            on['description'] = result["description"]["value"]
        else:
            on['description'] = '-'    
        json.append(on)
    return JsonResponse({'rs':json}, safe=False)