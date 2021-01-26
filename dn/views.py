from django.http import HttpResponse, JsonResponse
from django.views.generic import TemplateView
import json
from SPARQLWrapper import SPARQLWrapper, JSON, POST, DIGEST, INSERT, BASIC
import requests
import time
import os
import urllib
import subprocess
from django.conf import settings
import sys
from django.http.response import StreamingHttpResponse
from django.core.files.storage import FileSystemStorage
from django.http import FileResponse
from django.views.decorators.csrf import csrf_exempt

graphdb = "http://172.17.0.4:7200/repositories/dn"
dataverse = "http://localhost:8085"
dataverse_ex = "http://localhost:8085" 
#dataverse = "http://melodi.irit.fr:8080"
#dataverse_ex = "http://localhost:8085" 
dv_key = "9cc13e11-6ac8-42bc-8dc5-28a0c4e622da"


def import_meta(request):
  ds_id = request.GET.get('id') 
  ts = round(time.time()*1000)
  resp = requests.get('https://www.data.gouv.fr/api/1/datasets/' + str(ds_id))
  ds = resp.json()  
  triples = []   
  prefixes = []
  prefixes.append("PREFIX dct: <http://purl.org/dc/terms/>")
  prefixes.append("PREFIX foaf: <http://xmlns.com/foaf/0.1/>")
  prefixes.append("PREFIX dcat: <http://www.w3.org/ns/dcat#>")
  prefixes.append("PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>")
  prefixes.append("PREFIX dn: <http://melodi.irit.fr/ontologies/dn/>") 
   
  ds_uri = "<http://melodi.irit.fr/resource/Dataset/dn_"+ str(ts) + ">"
  dis_uri = ds_uri.replace("Dataset","Distribution")
  triples.append("{} a dn:Dataset.".format(ds_uri))
  triples.append("{} dcat:landingPage \"{}\".".format(ds_uri, ds.get("page")))
  triples.append("{} dct:identifier \"{}\".".format(ds_uri, ds.get("id")))
  triples.append("{} dn:hasSubject <http://melodi.irit.fr/resource/Subject/99>.".format(ds_uri))
  triples.append("{} dct:title \"{}\".".format(ds_uri, ds.get("title")))
  triples.append("{} dct:description \"\"\"{}\"\"\".".format(ds_uri, ds.get("description")))
  triples.append("{} dcat:distribution {}.".format(ds_uri, dis_uri))
  triples.append("{} a dn:Distribution.".format(dis_uri))
  triples.append("{} dcat:accessURL \"{}\".".format(dis_uri, ds.get("resources")[0].get("url")))
  print( ds.get("resources")[0].get("filesize", 0))
  if ds.get("resources")[0].get("filesize"):
    triples.append("{} dcat:byteSize {}.".format(dis_uri, ds.get("resources")[0].get("filesize", 0))) 
  triples.append("{} dct:identidier \"{}\".".format(dis_uri, ds.get("resources")[0].get("id"))) 
  triples.append("{} dcat:mediaType \"{}\".".format(dis_uri, ds.get("resources")[0].get("mime")))
  triples.append("{} dct:license \"{}\".".format(ds_uri, ds.get("license")))
  triples.append("{} dct:issued \"{}\"^^xsd:dateTime.".format(ds_uri, ds.get("created_at")))    
  for kw in ds.get("tags"):
    triples.append("{} dcat:keyword \"{}\".".format(ds_uri, kw))

  
  insert_data("\n ".join(prefixes), "\n ".join(triples))
  return HttpResponse("ok")

   
  

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

    

@csrf_exempt
def  upload_distribution(request):  
    file_uploaded = request.FILES.get('file_uploaded')
    pid = request.POST.get('pid')
    uri = request.POST.get('uri')
    file_id = request.POST.get('id')
    file_format = request.POST.get('format')
    r = requests.post(dataverse + "/api/datasets/:persistentId/add?persistentId="+pid, files={'file': file_uploaded}, data={"description":"Initial file"}, headers={ 'X-Dataverse-key': dv_key})
    
      #{"status":"OK","data":{"files":[{"description":"","label":"dcat.csv","restricted":false,"version":1,"datasetVersionId":13,"dataFile":{"id":22,"persistentId":"","pidURL":"","filename":"dcat.csv","contentType":"text/csv","filesize":10887,"description":"","storageIdentifier":"local://175e1e0e2b5-68f3d93a8f1d","rootDataFileId":-1,"md5":"60e5abb7a8c9207456490df444659211","checksum":{"type":"MD5","value":"60e5abb7a8c9207456490df444659211"},"creationDate":"2020-11-19"}}]}}
   
    if r.status_code == 200 or r.status_code == 201:  
        prefixes = []
        prefixes.append("PREFIX dct: <http://purl.org/dc/terms/>")
        prefixes.append("PREFIX foaf: <http://xmlns.com/foaf/0.1/>")
        prefixes.append("PREFIX dcat: <http://www.w3.org/ns/dcat#>")
        prefixes.append("PREFIX bibo: <http://purl.org/ontology/bibo/>")
        prefixes.append("PREFIX dn: <http://melodi.irit.fr/ontologies/dn/>")
        triples = []        
        rs = json.loads(r.text).get("data").get("files")[0].get("dataFile")
        dis = "<http://melodi.irit.fr/resource/Distribution/{}-{}>".format( file_id, rs.get("id"))
        triples.append("{} dcat:distribution {}.".format(uri, dis))
        triples.append("{} a dcat:Distribution.".format(dis))
        triples.append("{} dcat:byteSize {}.".format(dis, rs.get("filesize")))
        triples.append("{} dcat:downloadURL \"{}/api/access/datafile/{}\".".format(dis, dataverse_ex, rs.get("id")))
        triples.append("{} dcat:mediaType \"{}\".".format(dis, rs.get("contentType")))
        triples.append("{} dct:description \"{}\".".format(dis, rs.get("filename")))    
        triples.append("{} dct:issued \"{}\"^^xsd:date.".format(dis, rs.get("creationDate")))   
        triples.append("{} dn:hasFormat <{}>.".format(dis, file_format))  
   
        print(triples)
        insert_data("\n ".join(prefixes), "\n ".join(triples))
        return HttpResponse("ok")
    else:
        return HttpResponse("failed")     


 
def insert_data(prefixes, triples): 
    sparql = SPARQLWrapper(graphdb)
    sparql.setReturnFormat(JSON)
    sparql = SPARQLWrapper(graphdb +"/statements")
    sparql.setHTTPAuth(DIGEST)
    sparql.setCredentials("admin", "melodi")
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

def work(request):
  python_path = sys.executable
  time.sleep(1)
  ts = round(time.time())
  files_path = os.path.join(settings.BASE_DIR, 'public',  'static', 'scripts')
  input_file = "" if request.GET.get('in', '') == "" else os.path.join(files_path, request.GET.get('in', ''))
  print("input file: " + input_file)
  uri = request.GET.get('uri', '')
  print("service: " + uri)
  q = """
  PREFIX dn: <http://melodi.irit.fr/ontologies/dn/>
  select ?url ?output where {{ 
	<{}> dn:accessURL ?url.
  OPTIONAL
  {{
  <{}> dn:hasOutputFormat ?of.
  ?of rdfs:label ?output.
  }}
  }}""".format(uri, uri)
  #print(q)
  results = query(q)  
  
  url = results["results"]["bindings"][0]["url"]["value"]
  print("url: " + url)
  out_format = "" if not results["results"]["bindings"][0].get("output") else ("." + results["results"]["bindings"][0]["output"]["value"])
  params = "" if request.GET.get('params') == "None" else request.GET.get('params')
  output_file = os.path.join(files_path,  str(ts) + out_format)
  print("output file:" + output_file)
  call = ["python3", url]
  if input_file != "": 
    call.append(input_file)
  if params != "":
    call.extend(params.split(" "))
  call.append(output_file)
  print(params)
  try:  
    subprocess.call(call)
    return JsonResponse({'rs':{'rs':'OK','file': str(ts) + out_format}}, safe=False)
  except subprocess.CalledProcessError as e:
    print(e.returncode)
    print(e.cmd)
    print(e.output)
    return JsonResponse({'rs':{'rs':'Error','file': 'None'}}, safe=False)

  
def download(request, path):
    file_path = os.path.join(BASE_DIR, 'static')
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    raise Http404

def get_services(request):  
  results = query("""
  PREFIX dn: <http://melodi.irit.fr/ontologies/dn/>
  select ?uri ?name ?desc ?input ?output ?operation where {{ 
	?uri a dn:Service.
  ?uri dn:description ?desc.
  ?uri dn:name ?name.
  ?uri dn:hasInputFormat ?if.
  ?if rdfs:label ?input.
  ?uri dn:hasOutputFormat ?of.
  ?of rdfs:label ?output.
  ?uri dn:performsOperation ?op.
  ?op rdfs:label ?operation.
  }}""".format())  
  json = []
  rec = {}
  for result in results["results"]["bindings"]:
    rec = {}
    for label in results["head"]["vars"]:
      rec[label] = result[label]["value"]
    json.append(rec)
   
  return JsonResponse({'rs':json}, safe=False) 


def get_distributions(request):  
  results = query("""PREFIX dn: <http://melodi.irit.fr/ontologies/dn/>
  PREFIX dcat: <http://www.w3.org/ns/dcat#>
   PREFIX dct: <http://purl.org/dc/terms/>
  select ?uri ?format ?download ?size where {{ 
  <{}> dcat:distribution ?uri.  
	?uri dn:hasFormat ?fm.
  ?uri dcat:byteSize ?size.
  ?uri dcat:downloadURL ?download.
  ?fm rdfs:label ?format.
  }}""".format(request.GET.get('uri')))  
  json = []
  for result in results["results"]["bindings"]:
    json.append({'uri':result["uri"]["value"], 'label':result["uri"]["value"][result["uri"]["value"].rindex('/')+1:] + ", format " + result["format"]["value"] + ", size " + result["size"]["value"] + " bytes", 'download': result["download"]["value"], 'size':result["size"]["value"], 'format':result["format"]["value"]})   
  return JsonResponse({'rs':json}, safe=False)

def get_distribution(request):  
  results = query("""PREFIX dn: <http://melodi.irit.fr/ontologies/dn/>
  PREFIX dcat: <http://www.w3.org/ns/dcat#>
   PREFIX dct: <http://purl.org/dc/terms/>
  select ?format ?download ?size ?title where {{ 
	<{}> dn:hasFormat ?fm.
  <{}> dcat:byteSize ?size.
  ?ds dcat:distribution <{}>.
  ?ds dct:title ?title.
  <{}> dcat:downloadURL ?download.
  ?fm rdfs:label ?format.
  }}""".format(request.GET.get('uri'), request.GET.get('uri'), request.GET.get('uri'),request.GET.get('uri')))  
  json = []
  for result in results["results"]["bindings"]:
    json.append({'size':result["size"]["value"], 'title':result["title"]["value"], 'format':result["format"]["value"], 'download': result["download"]["value"]})   
  return JsonResponse({'rs':json}, safe=False)


def get_claim(request):  
  results = query("""
  PREFIX mp:  <http://purl.org/mp/>
  PREFIX owl: <http://www.w3.org/2002/07/owl#>
  PREFIX dct: <http://purl.org/dc/terms/>
  select ?uri ?statement  where {{
	?uri a mp:Claim.
  ?uri mp:statement ?statement.
  ?uri mp:supports ?ref.
  ?ref owl:sameAs {}.
  }}
  """.format(request.GET.get('uri', ''))) 

  json = []
  for result in results["results"]["bindings"]:
    json.append({'uri':result["uri"]["value"], 'statement': result["statement"]["value"]})   
  return JsonResponse({'rs':json}, safe=False)

def get_claims(request):  
  results = query("""
  PREFIX mp:  <http://purl.org/mp/>
  PREFIX owl: <http://www.w3.org/2002/07/owl#>
  PREFIX dct: <http://purl.org/dc/terms/>
  select ?uri ?statement ?title where {
	?uri a mp:Claim.
  ?uri mp:statement ?statement.
  ?uri mp:supports ?ref.
  ?ref owl:sameAs ?pub.
  ?pub dct:title ?title.
  }
  """)  
  json = []
  for result in results["results"]["bindings"]:
    json.append({'uri':result["uri"]["value"], 'statement': result["statement"]["value"], 'publication': result["title"]["value"]})   
  return JsonResponse({'rs':json}, safe=False)


@csrf_exempt
def new_claim(request):
  data = json.loads(request.body)
  prefixes = []
  prefixes.append("PREFIX mp:  <http://purl.org/mp/>")
  prefixes.append("PREFIX bibo: <http://purl.org/ontology/bibo/>")
  prefixes.append("PREFIX owl: <http://www.w3.org/2002/07/owl#>")
  triples = []
  uri = data.get('uri').replace("Document", "Reference")
  id = uri[uri.rindex("/")+1:-1]
  triples.append("{} a mp:Reference.".format(uri)) 
  triples.append("{} owl:sameAs {}.".format(uri,  data.get('uri'))) 
  for st in data.get("statements"):
    triples.append("<http:melodi.irit.fr/resource/Claim/{}> a mp:Claim.".format(id+str(st["id"])))
    triples.append("<http:melodi.irit.fr/resource/Claim/{}> mp:supports {}.".format(id+str(st["id"]), uri))
    triples.append("<http:melodi.irit.fr/resource/Claim/{}> mp:statement \"{}\".".format(id+str(st["id"]), st["value"]))
 
  insert_data("\n ".join(prefixes), "\n ".join(triples))  
  return JsonResponse({'result':'ok'} , safe=False)



@csrf_exempt
def new_pub(request):
  data = json.loads(request.body)
  prefixes = []
  prefixes.append("PREFIX dct: <http://purl.org/dc/terms/>")
  prefixes.append("PREFIX bibo: <http://purl.org/ontology/bibo/>")
  triples = []
  uri = data.get('uri')
  triples.append("{} a bibo:Document.".format(uri)) 
  triples.append("{} dct:title \"{}\".".format(uri, data.get("title"))) 
  triples.append("{} dct:issued \"{}\"^^xsd:date.".format(uri, data.get("issued"))) 
  triples.append("{} dct:identifier \"{}\".".format(uri, data.get("doi")))  
  for author in data.get("authors"):
    triples.append("{} dct:creator {}.".format(uri, author.get("uri")))
  
  insert_data("\n ".join(prefixes), "\n ".join(triples))  
  return JsonResponse({'result':'ok'} , safe=False)

def get_pubs_doi(request):  
  results = query("""
  PREFIX bibo: <http://purl.org/ontology/bibo/>
  PREFIX dct: <http://purl.org/dc/terms/>
  select ?uri ?title ?doi ?date where {{
	?uri a bibo:Document.
  ?uri dct:identifier ?doi.
  ?uri dct:title ?title.
  ?uri dct:issued ?date.
  FILTER regex((str(?doi)), "{}", "i") }}""".format(request.GET.get('doi', ''))) 
 
  json = []
  for result in results["results"]["bindings"]:
    json.append({'uri':result["uri"]["value"], 'DOI': result["doi"]["value"],  'title': result["title"]["value"], 'date': result["date"]["value"]})   
  return JsonResponse({'rs':json}, safe=False)

def get_pubs(request):  
  results = query("""
       PREFIX bibo: <http://purl.org/ontology/bibo/>
  PREFIX dct: <http://purl.org/dc/terms/>
  select ?uri ?doi ?title where {
	?uri a bibo:Document.
  ?uri dct:title ?title.
  ?uri dct:identifier ?doi.
  }
  """)  
  json = []
  for result in results["results"]["bindings"]:
    json.append({'uri':result["uri"]["value"], 'title': result["title"]["value"], 'DOI': result["doi"]["value"]})   
  return JsonResponse({'rs':json}, safe=False)

def get_pubs_title(request):  
  results = query("""
       PREFIX bibo: <http://purl.org/ontology/bibo/>
  PREFIX dct: <http://purl.org/dc/terms/>
  select ?uri ?title ?doi where {{ 
	?uri a bibo:Document.
  ?uri dct:title ?title.
  ?uri dct:identifier ?doi.
  FILTER regex(lcase(str(?title)), "{}", "i") }}""".format(request.GET.get('title', '')))  
  json = []
  for result in results["results"]["bindings"]:
    json.append({'uri':result["uri"]["value"], 'title': result["title"]["value"], 'doi': result["doi"]["value"]})   
  return JsonResponse({'rs':json}, safe=False)

def get_datasets (request):
  results = query("""  PREFIX dc: <http://purl.org/dc/elements/1.1/>
  PREFIX dct: <http://purl.org/dc/terms/>
  PREFIX dn: <http://melodi.irit.fr/ontologies/dn/>
  select * where { 
	?dn a  dn:Dataset.
    ?dn dct:issued ?date.
    ?dn dct:title ?title.
    ?dn dct:description ?desc.
    ?dn dn:hasSubject ?subj.
    ?subj dn:name ?subj_name.
  } order by DESC(?date)   
    """)
  
  json = []
  for result in results["results"]["bindings"]:
    json.append({'uri':result["dn"]["value"], 'title':result["title"]["value"], 'description': result["desc"]["value"], 'issued': result["date"]["value"], 'subject': result["subj_name"]["value"]})
  return JsonResponse({'rs':json}, safe=False) 

def list_recents(request):
  results = query("""  PREFIX dc: <http://purl.org/dc/elements/1.1/>
  PREFIX dct: <http://purl.org/dc/terms/>
  PREFIX dn: <http://melodi.irit.fr/ontologies/dn/>
  select * where { 
	?dn a  dn:Dataset.
    ?dn dct:issued ?date.
    ?dn dct:title ?title.
    ?dn dct:description ?desc.
    ?dn dn:hasSubject ?subj.
    ?subj dn:name ?subj_name.
  } order by DESC(?date)
    limit 6
    """)
  
  json = []
  for result in results["results"]["bindings"]:
    json.append({'uri':result["dn"]["value"], 'title':result["title"]["value"], 'description': result["desc"]["value"], 'issued': result["date"]["value"], 'subject': result["subj_name"]["value"]})
  return JsonResponse({'rs':json}, safe=False) 

def get_loc(request):
    results = query("""  PREFIX dct: <http://purl.org/dc/terms/>
PREFIX dn: <http://melodi.irit.fr/ontologies/dn/>
select ?dn ?title ?geom where { 
	?dn a <http://melodi.irit.fr/ontologies/dn/Dataset>.    
    ?dn dct:spatial ?loc.
    ?dn dct:title ?title.
    ?loc <http://www.w3.org/ns/locn#geometry> ?geom.        
} 
    """)
    json = []
    for result in results["results"]["bindings"]:
        json.append({'uri':result["dn"]["value"], 'geom': result["geom"]["value"], 'title': result["title"]["value"]})
   
    return JsonResponse({'rs':json}, safe=False) 

def get_stat_key(request):
    results = query("""PREFIX dn: <http://melodi.irit.fr/ontologies/dn/>
PREFIX dcat: <http://www.w3.org/ns/dcat#>
select ?keyword (count(?keyword) as ?total) where { 
	?dn a <http://melodi.irit.fr/ontologies/dn/Dataset>.    
    ?dn dcat:keyword ?keyword. 
          
} 
group by ?keyword""")
  
    json = []
    for result in results["results"]["bindings"]:
        json.append({'keyword':result["keyword"]["value"], 'total': result["total"]["value"]})
   
    return JsonResponse({'rs':json}, safe=False) 

def get_stat_subj(request):
    results = query("""select ?name (count (?name) as ?total) where { 
	?ds <http://melodi.irit.fr/ontologies/dn/hasSubject> ?subj .
    ?subj <http://melodi.irit.fr/ontologies/dn/name> ?name.    
    } group by ?name 
    """)
    json = []
    for result in results["results"]["bindings"]:
        json.append({'name':result["name"]["value"], 'total': result["total"]["value"]})
   
    return JsonResponse({'rs':json}, safe=False) 

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

def get_dataset(request):
  if request.GET.get("search") == "title":
    filter = 'FILTER regex(str(?title), "' + request.GET.get('value')+ '", "i")'
  elif request.GET.get("search") == "keyword":
    filter = 'FILTER regex(str(?keyword), "' + request.GET.get('value')+ '" , "i")'

  results = query("""PREFIX dc: <http://purl.org/dc/elements/1.1/>
  PREFIX dct: <http://purl.org/dc/terms/>
  PREFIX dcat: <http://www.w3.org/ns/dcat#>
  PREFIX dn: <http://melodi.irit.fr/ontologies/dn/>
  select ?dn ?title ?description ?issued ?subject where {{ 
	?dn a  dn:Dataset.
    ?dn dct:issued ?issued.
    ?dn dct:title ?title.
    ?dn dct:description ?description.
    ?dn dn:hasSubject ?subj.
    ?subj dn:name ?subject.
    ?dn dcat:keyword ?keyword.
    {}
    }}
    """.format(filter))
  
  json = []
  for result in results["results"]["bindings"]:
    json.append({'uri':result["dn"]["value"], 'title':result["title"]["value"], 'description': result["description"]["value"], 'issued': result["issued"]["value"], 'subject': result["subject"]["value"]})
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

def get_agents(request):
    results = query(""" PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        SELECT ?uri ?name ?email 
        WHERE {{
           ?uri a foaf:Agent.
           ?uri foaf:name ?name.     
        OPTIONAL
          {{
            ?uri foaf:email ?email.
          }}
        }}""")        
  
    json = []
    for result in results["results"]["bindings"]:
        ins ={'uri':result["uri"]["value"], 'name': result["name"]["value"]}
        
        if result.get("email"):
            ins['email'] = result["email"]["value"]
        else:
            ins['email'] = '-'   
        json.append(ins)
    return JsonResponse({'rs':json}, safe=False)

def get_agent(request):
    results = query(""" PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        SELECT ?uri ?name ?email 
        WHERE {{
           ?uri a foaf:Agent.
           ?uri foaf:name ?name. 
           FILTER regex(str(?name), "{}",  "i") .
          OPTIONAL
          {{
            ?uri foaf:email ?email.
          }}
        }}""".format(request.GET.get('name', '')))
        
  
    json = []
    for result in results["results"]["bindings"]:
        ins ={'uri':result["uri"]["value"], 'name': result["name"]["value"]}
        
        if result.get("email"):
            ins['email'] = result["email"]["value"]
        else:
            ins['email'] = '-'   
        json.append(ins)
    return JsonResponse({'rs':json}, safe=False)

def get_data_props(request):
  classes = []
  results = query(""" PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
        SELECT distinct ?uri ?label ?comment ?onto
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
    classes.append(cls)

 
  classes.append({'uri':'http://www.w3.org/2000/01/rdf-schema#Resource', 'onto':'http://www.w3.org/2000/01/rdf-schema#', 'label':'Resource', 'comment':'The class resource, everything'})
  classes.append({'uri':'http://www.w3.org/2002/07/owl#Thing', 'onto':' http://www.w3.org/2002/07/owl#', 'label':'Thing', 'comment':'The class of OWL individuals'})
  
  for clss in classes:

    json = []
    results = query(""" PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
        SELECT distinct ?uri ?label ?comment ?range 
        WHERE {{
           ?uri rdfs:domain <{}>.               
           ?uri rdfs:label ?label.
           FILTER (lang(?label)= "en" || lang(?label)="") 
        OPTIONAL
           {{
           ?uri rdfs:comment ?comment.
           FILTER (lang(?comment)= "en" || lang(?comment)="")
           }}
        ?uri rdfs:range ?range.
        }} order by ?label""".format(clss["uri"]))  
    
    for result in results["results"]["bindings"]:
        cls = {'uri':result["uri"]["value"], 'range':result["range"]["value"]}
        if result.get("label"):
            cls['label'] = result["label"]["value"]
        else:
            cls['label'] = '-'
        if result.get("comment"):
            cls["comment"] = result["comment"]["value"]
        else:
            cls["comment"] = '-'
        json.append(cls)

    clss["props"] = json
    
 

    #load props for dcterms
    json = []
    results = query(""" PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
        SELECT ?uri ?label ?comment  ?range
        WHERE {      
           ?uri rdfs:label ?label.
           FILTER (lang(?label)= "en" || lang(?label)="") 
        OPTIONAL
           {
           ?uri rdfs:comment ?comment.
           FILTER (lang(?comment)= "en" || lang(?comment)="")
           }
        ?uri rdfs:isDefinedBy <http://purl.org/dc/terms/>.
        ?uri rdfs:range ?range.
   
        } order by ?label""")
      #FILTER(?range = <http://www.w3.org/2000/01/rdf-schema#Literal>)      
  
    for result in results["results"]["bindings"]:
        cls = {'uri':result["uri"]["value"], 'range':result["range"]["value"]}
        if result.get("label"):
            cls['label'] = result["label"]["value"]
        else:
            cls['label'] = '-'
        if result.get("comment"):
            cls["comment"] = result["comment"]["value"]
        else:
            cls["comment"] = '-'
        json.append(cls)

  json.append({'uri':'http://www.w3.org/1999/02/22-rdf-syntax-ns#type','label':'type', 'comment':'The subject is an instance of a class', 'range':'rdfs:Class'})

  classes.append({'uri': 'http://purl.org/dc/terms/Thing' , 'onto':'http://purl.org/dc/terms/', 'label':'Thing', 'comment':'A blank class', 'props':json})
        
  return JsonResponse({'rs':classes}, safe=False)

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


@csrf_exempt
def new_meta(request):  
    data = json.loads(request.body)
    uri = data.get('uri')
    triples = []    
    for meta in data.get("meta"):
      if "literal" in meta.get("range").lower():
        triples.append("<{}> <{}> {}.".format(uri, meta.get("uri"), meta.get("value")))
      else:
        triples.append("<{}> <{}> <{}>.".format(uri, meta.get("uri"), meta.get("value")))
    insert_data("","\n ".join(triples))  
    return JsonResponse({'result':'ok'} , safe=False)


@csrf_exempt
def new_agent(request):  
    data = json.loads(request.body)
    uri = data.get('uri')
    prefixes = []
    prefixes.append("PREFIX foaf: <http://xmlns.com/foaf/0.1/>")
    triples = []    
    triples.append("{} a foaf:Agent.".format(uri))
    triples.append("{} foaf:name \"{}\".".format(uri, data.get('name')))
    if data.get('email') != "":
      triples.append("{} foaf:email \"{}\".".format(uri, data.get('email'))) 
    insert_data("\n ".join(prefixes), "\n ".join(triples))  
    return JsonResponse({'result':'ok'} , safe=False)


@csrf_exempt
def new_service(request):  
    file_uploaded = request.FILES.get('file_uploaded')
    operation = request.POST.get('operation')
    input_format = request.POST.get('inputFormat')
    output_format = request.POST.get('outputFormat')
    uri = request.POST.get('uri')
    subject = request.POST.get('subject')
    myfile = request.FILES['file_uploaded']
    fs = FileSystemStorage()
    files_path = os.path.join(settings.BASE_DIR, 'public',  'static', 'scripts', myfile.name)
    filename = fs.save(files_path, myfile)
    print(fs.url(filename))
    prefixes = []
    prefixes.append("PREFIX dn: <http://melodi.irit.fr/ontologies/dn/>")
    triples = []    
    triples.append("{} a dn:Service.".format(uri))
    triples.append("{} dn:name \"{}\".".format(uri, request.POST.get('name')))
    triples.append("{} dn:accessURL \"{}\".".format(uri, fs.url(filename)))
    triples.append("{} dn:description \"{}\".".format(uri, request.POST.get('desc')))
    triples.append("{} dn:performsOperation <{}>.".format(uri,  operation))
    triples.append("{} dn:hasInputFormat <{}>.".format(uri,  input_format))
    triples.append("{} dn:hasOutputFormat <{}>.".format(uri,  output_format))
    triples.append("{} dn:hasSubject <http://melodi.irit.fr/resource/Subject/{}>.".format(uri,  subject))
    
    
    print("\n ".join(triples))
    insert_data("\n ".join(prefixes), "\n ".join(triples))  
    return JsonResponse({'result':'ok'} , safe=False)

@csrf_exempt
def new_dataset(request):  
    data = json.loads(request.body)
    prefixes = []
    prefixes.append("PREFIX dct: <http://purl.org/dc/terms/>")
    prefixes.append("PREFIX foaf: <http://xmlns.com/foaf/0.1/>")
    prefixes.append("PREFIX dcat: <http://www.w3.org/ns/dcat#>")
    prefixes.append("PREFIX bibo: <http://purl.org/ontology/bibo/>")
    prefixes.append("PREFIX dn: <http://melodi.irit.fr/ontologies/dn/>")
    prefixes.append("PREFIX geo: <http://www.opengis.net/ont/geosparql#>")
    prefixes.append("PREFIX locn: <http://www.w3.org/ns/locn#>")
    
    triples = []    
    triples.append("{} a dn:Dataset.".format(data.get('uri')))
    triples.append("{} dct:title \"{}\".".format(data.get('uri'), data.get("title")))
    triples.append("{} dct:description \"{}\".".format(data.get('uri'),  data.get("description")))
    triples.append("{} dcat:keyword \"{}\".".format(data.get('uri'),  data.get("keywords")))
    triples.append("{} dct:issued \"{}\"^^xsd:date.".format(data.get('uri'), data.get("issuedDate")))
    triples.append("{} dn:note \"{}\".".format(data.get('uri'),  data.get("note")))
    
    if data.get("loc","") != "":
      triples.append("{} dct:spatial {}.".format(data.get('uri'), data.get('uri').replace("Dataset","Loc")))
      triples.append("{} locn:geometry \"{}\"^^geo:wktLiteral.".format(data.get('uri').replace("Dataset","Loc"),  data.get("loc")))

    
    for creator in data.get('creators'):
        triples.append("{} dct:creator {}.".format(data.get('uri'), creator.get("uri")))
    
    for publisher in data.get('publishers'):
        triples.append("{} dct:publisher {}.".format(data.get('uri'), publisher.get("uri")))

    for depositor in data.get('depositors'):        
        triples.append("{} dn:depositor {}.".format(data.get('uri'), depositor.get("uri")))

    for pub in data.get('pubs'):
        triples.append("{} dn:presentedIn {}.".format(data.get('uri'), pub.get("uri")))


    #print("\n ".join(triples))
    sub = ["", "Arts and Humanities", "Astronomy and Astrophysics", "Business and Management","Chemistry", "Computer and Information Science","Earth and Environmental Sciences", "Engineering","Law","Mathematical Sciences","Medicine, Health and Life Sciences", "Physics", "Social Sciences", "Other"]
    triples.append("{} dn:hasSubject <http://melodi.irit.fr/resource/Subject/{}>.".format(data.get('uri'), data.get("subject")))
    
    str = """{{
  "datasetVersion": {{
    "metadataBlocks": {{
      "citation": {{
        "fields": [
          {{
            "value": "{}",
            "typeClass": "primitive",
            "multiple": false,
            "typeName": "title"
          }},
          {{
            "value": [
              {{
                "authorName": {{
                  "value": "{}",
                  "typeClass": "primitive",
                  "multiple": false,
                  "typeName": "authorName"
                }}
              }}
            ],
            "typeClass": "compound",
            "multiple": true,
            "typeName": "author"
          }},
          {{
            "value": [ 
                {{ "datasetContactEmail" : {{
                    "typeClass": "primitive",
                    "multiple": false,
                    "typeName": "datasetContactEmail",
                    "value" : "{}"
                }},
                "datasetContactName" : {{
                    "typeClass": "primitive",
                    "multiple": false,
                    "typeName": "datasetContactName",
                    "value": "{}"
                }}
            }}],
            "typeClass": "compound",
            "multiple": true,
            "typeName": "datasetContact"
          }},
          {{
            "value": [ {{
               "dsDescriptionValue":{{
                "value":   "{}",
                "multiple":false,
               "typeClass": "primitive",
               "typeName": "dsDescriptionValue"
            }}}}],
            "typeClass": "compound",
            "multiple": true,
            "typeName": "dsDescription"
          }},
          {{
            "value": [
              "{}"
            ],
            "typeClass": "controlledVocabulary",
            "multiple": true,
            "typeName": "subject"
          }}
        ],
        "displayName": "Citation Metadata"
      }}
    }}
  }}                                                                                                                                                                                                                                                            
}}""".format(data.get("title"), data.get("creators")[0].get("name"), data.get("publishers")[0].get("email"), data.get("publishers")[0].get("name"), data.get("description"), sub[int(data.get("subject"))])

    rs = ""
    #curl -H "X-Dataverse-key:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" -X POST "https://demo.dataverse.org/api/dataverses/root/datasets" --upload-file "dataset-finch1.json"
    headers = {
    'X-Dataverse-key': dv_key 
    }
    #print(datajson)
    r = requests.post(dataverse + "/api/dataverses/root/datasets", data=str, headers=headers)
    print(str)
    print(r.content)
    print(r.status_code)
    if r.status_code == 200 or r.status_code == 201:
      rs = json.loads(r.text).get("data").get("persistentId")
    else:
      rs = "failed"

    triples.append("{} dct:identifier \"{}\".".format(data.get('uri'), rs))
    triples.append("{} dcat:landingPage \"{}/dataset.xhtml?persistentId={}\".".format(data.get('uri'), dataverse_ex, rs))
    insert_data("\n ".join(prefixes), "\n ".join(triples))
    return JsonResponse({'doi':rs, 'page': dataverse_ex + '/dataset.xhtml?persistentId=' + rs} , safe=False)