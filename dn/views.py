from django.http import HttpResponse, JsonResponse
from django.views.generic import TemplateView
import json
from SPARQLWrapper import SPARQLWrapper, JSON, POST, DIGEST, INSERT, BASIC
import requests
import time
import os
import subprocess
from django.conf import settings
import sys
from django.http.response import StreamingHttpResponse
from django.core.files.storage import FileSystemStorage
from django.http import FileResponse
from django.views.decorators.csrf import csrf_exempt

url = "http://172.17.0.4:7200/repositories/dn"

def query(str):
    sparql = SPARQLWrapper(url)
    sparql.setReturnFormat(JSON)
    sparql.setQuery(str)        
    results = sparql.query().convert()
    return results

def download_file(request):
    file_name = request.GET.get('fn')
    file_path = os.path.join(settings.BASE_DIR, 'public',  'static', 'scripts')
    fs = FileSystemStorage(file_path)
    response = FileResponse(fs.open(file_name, 'rb'), content_type='application/force-download')
    response['Content-Disposition'] = 'attachment; filename="'+ file_name+ '"'
    return response

def  upload_distribution(request):  
    file_uploaded = request.FILES.get('file_uploaded')
    pid = request.data.get('pid')
    uri = request.data.get('uri')
    id = request.data.get('id')
    r = requests.post("http://localhost:8085/api/datasets/:persistentId/add?persistentId="+pid, files={'file': file_uploaded}, data={"description":"Initial file"}, headers={ 'X-Dataverse-key': '9cc13e11-6ac8-42bc-8dc5-28a0c4e622da'})
    
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
        dis = "<http://melodi.irit.fr/resource/Distribution/{}-{}>".format( id, rs.get("id"))
        triples.append("{} dcat:distribution {}.".format(uri, dis))
        triples.append("{} a dcat:Distribution.".format(dis))
        triples.append("{} dcat:byteSize {}.".format(dis, rs.get("filesize")))
        triples.append("{} dcat:downloadURL \"http://localhost:8085/api/access/datafile/{}\".".format(dis, rs.get("id")))
        triples.append("{} dcat:mediaType \"{}\".".format(dis, rs.get("contentType")))
        triples.append("{} dct:description \"{}\".".format(dis, rs.get("filename")))
        triples.append("{} dct:issued \"{}\"^^xsd:date.".format(dis, rs.get("creationDate")))        
        #print(triples)
        insertData("\n ".join(prefixes), "\n ".join(triples))
        return Response("ok")
    else:
        return Response("failed")     

def createDataset(datajson):    
    #curl -H "X-Dataverse-key:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" -X POST "https://demo.dataverse.org/api/dataverses/root/datasets" --upload-file "dataset-finch1.json"
    headers = {
    'X-Dataverse-key': '9cc13e11-6ac8-42bc-8dc5-28a0c4e622da'  
    }
    #print(datajson)
    r = requests.post("http://localhost:8085/api/dataverses/root/datasets", data=datajson, headers=headers)
    if r.status_code == 200 or r.status_code == 201:
        return json.loads(r.text).get("data").get("persistentId")
    else:
        return "failed"
 
def insertData(prefixes, triples):
    url = "http://172.17.0.4:7200/repositories/dn"
    sparql = SPARQLWrapper(url)
    sparql.setReturnFormat(JSON)
    sparql = SPARQLWrapper(url+"/statements")
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
    sparql.setQuery(query)
    results = sparql.query()
    return results.response.read()

#Will be replaced by SPARQL queries
def work(request):
  python_path = sys.executable
  ts = round(time.time())
  files_path = os.path.join(settings.BASE_DIR, 'public',  'static', 'scripts')
  input_file = os.path.join(files_path, request.GET.get('in', ''))
  print(input_file)
  uri = request.GET.get('uri', '')
  print(uri)
  if uri == "http://melodi.irit.fr/resource/Service/0":
    return JsonResponse({'rs':{'rs':'ok','file':'synop.202011.csv'}}, safe=False)
  elif uri == "http://melodi.irit.fr/resource/Service/1":      
      try:
        output_file = os.path.join(files_path,  str(ts) + 'rc.csv')
        subprocess.call(['python3', os.path.join(files_path,  'csv_remove_col.py'), input_file, '3', output_file ])
        return JsonResponse({'rs':{'rs':'ok','file': str(ts) + 'rc.csv'}}, safe=False)
      except subprocess.CalledProcessError as e:
        print(e.returncode)
        print(e.cmd)
        print(e.output)
        return JsonResponse({'rs':{'rs':'error','file': '.csv'}}, safe=False)
  elif uri == "http://melodi.irit.fr/resource/Service/2":
      
      try:
        output_file = os.path.join(files_path,  str(ts) + 'm.csv')
     
        subprocess.call(['python3', os.path.join(files_path, 'csv_mean.py'),   input_file , output_file])
        return JsonResponse({'rs':{'rs':'ok','file': str(ts) + 'm.csv'}}, safe=False)
      except subprocess.CalledProcessError as e:
        print(e.returncode)
        print(e.cmd)
        print(e.output)
        return JsonResponse({'rs':{'rs':'ok','file': str(ts) + '.csv'}}, safe=False)
  
  elif uri == "http://melodi.irit.fr/resource/Service/3":
      
      try:
        output_file = os.path.join(files_path,  str(ts) + 'p.png')
      
        subprocess.call(['python3', os.path.join(files_path, 'csv_plot.py'),  input_file , output_file])
        return JsonResponse({'rs':{'rs':'ok','file': str(ts) + 'p.png'}}, safe=False)
      except subprocess.CalledProcessError as e:
        print(e.returncode)
        print(e.cmd)
        print(e.output)
        return JsonResponse({'rs':{'rs':'ok','file': str(ts) + '.csv'}}, safe=False)
  
  elif uri == "http://melodi.irit.fr/resource/Service/4":
      
      try:
        output_file = os.path.join(files_path,  str(ts) + 'f.csv')
     
        subprocess.call(['python3', os.path.join(files_path, 'csv_filter.py'),  input_file , '07005', output_file])
        return JsonResponse({'rs':{'rs':'ok','file': str(ts) + 'f.csv'}}, safe=False)
      except subprocess.CalledProcessError as e:
        print(e.returncode)
        print(e.cmd)
        print(e.output)
        return JsonResponse({'rs':{'rs':'ok','file': str(ts) + '.csv'}}, safe=False)
  
  else:
      return JsonResponse({'rs':{'rs':'error','file':''}}, safe=False)
  
def download(request, path):
    file_path = os.path.join(BASE_DIR, 'static')
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    raise Http404

def pub(request):  
  results = query("""
       PREFIX bibo: <http://purl.org/ontology/bibo/>
  PREFIX dct: <http://purl.org/dc/terms/>
  select ?uri ?title where {{ 
	?uri a bibo:Document.
  ?uri dct:title ?title.
  FILTER regex(lcase(str(?title)), "{}") }}""".format(request.GET.get('title', '')))  
  json = []
  for result in results["results"]["bindings"]:
    json.append({'uri':result["uri"]["value"], 'title': result["title"]["value"]})   
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

def loc(request):
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

def stat_key(request):
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

def stat_subj(request):
    results = query("""select ?name (count (?name) as ?total) where { 
	?ds <http://melodi.irit.fr/ontologies/dn/hasSubject> ?subj .
    ?subj <http://melodi.irit.fr/ontologies/dn/name> ?name.    
    } group by ?name 
    """)
    json = []
    for result in results["results"]["bindings"]:
        json.append({'name':result["name"]["value"], 'total': result["total"]["value"]})
   
    return JsonResponse({'rs':json}, safe=False) 

def operation(request):
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


def instance(request):
    results = query("""PREFIX owl: <http://www.w3.org/2002/07/owl#>
  PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
  select ?pre ?prop ?label {{
    <{}> ?pre ?prop. 
    ?pre rdfs:label ?label.
    }}""".format(request.GET.get('uri', '')))
  
    json = []
    for result in results["results"]["bindings"]:
        json.append({'property':result["label"]["value"] + " (" + result["pre"]["value"] + ") ", 'value': result["prop"]["value"]})
   
    return JsonResponse({'rs':json}, safe=False)  



def format(request):
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

def agent(request):
    results = query(""" PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        SELECT ?uri ?name ?email 
        WHERE {{
           ?uri a foaf:Agent.
           ?uri foaf:name ?name. 
           FILTER regex(str(?name), "{}") .
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

def getDataProps(request):
    results = query(""" PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
        SELECT ?uri ?label ?comment ?domain ?range ?domainLabel
        WHERE {
        
           ?uri rdfs:label ?label.
           FILTER (lang(?label)= "en" || lang(?label)="") 
        OPTIONAL
           {
           ?uri rdfs:comment ?comment.
           FILTER (lang(?comment)= "en" || lang(?comment)="")
           }
        ?uri rdfs:domain ?domain.
        ?domain rdfs:label ?domainLabel.
        ?uri rdfs:range ?range.
        } order by ?label""")      
    json = []
    for result in results["results"]["bindings"]:
        cls = {'uri':result["uri"]["value"], 'domain':result["domain"]["value"], 'range':result["range"]["value"], 'domainLabel':result["domainLabel"]["value"]}
        if result.get("label"):
            cls['label'] = result["label"]["value"]
        else:
            cls['label'] = '-'
        if result.get("comment"):
            cls["comment"] = result["comment"]["value"]
        else:
            cls["comment"] = '-'
        json.append(cls)


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
        cls = {'uri':result["uri"]["value"], 'domain':'http://purl.org/dc/terms/Thing', 'range':result["range"]["value"], 'domainLabel':'Thing'}
        if result.get("label"):
            cls['label'] = result["label"]["value"]
        else:
            cls['label'] = '-'
        if result.get("comment"):
            cls["comment"] = result["comment"]["value"]
        else:
            cls["comment"] = '-'

        json.append(cls)
    return JsonResponse({'rs':json}, safe=False)

def getClasses(request):
  results = query(""" PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
        SELECT ?uri ?label ?comment ?onto
        WHERE {
           ?uri rdf:type owl:Class .
           ?uri rdfs:label ?label.
           FILTER (lang(?label)= "en" || lang(?label)="") 
        OPTIONAL
           {
           ?uri rdfs:comment ?comment.
           FILTER (lang(?comment)= "en" || lang(?comment)="")
           }
        ?uri rdfs:isDefinedBy ?onto.
        } order by ?label""")
        
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
  return JsonResponse({'rs':json}, safe=False)

def getOntologies(request):
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
    triples.append("{} dn:description \"{}\".".format(uri, request.POST.get('description')))
    triples.append("{} dn:hasOperation <{}>.".format(uri,  operation))
    triples.append("{} dn:hasInputFormat <{}>.".format(uri,  input_format))
    triples.append("{} dn:hasOutputFormat <{}>.".format(uri,  output_format))
    triples.append("{} dn:hasSubject <http://melodi.irit.fr/resource/Subject/{}>.".format(uri,  subject))
    
    
    print("\n ".join(triples))

    #insertData("\n ".join(prefixes), "\n ".join(triples))
    

    return JsonResponse({'result':{}} , safe=False)


def new_dataset(request):  
    data = json.loads(request.body)
    prefixes = []
    prefixes.append("PREFIX dct: <http://purl.org/dc/terms/>")
    prefixes.append("PREFIX foaf: <http://xmlns.com/foaf/0.1/>")
    prefixes.append("PREFIX dcat: <http://www.w3.org/ns/dcat#>")
    prefixes.append("PREFIX bibo: <http://purl.org/ontology/bibo/>")
    prefixes.append("PREFIX dn: <http://melodi.irit.fr/ontologies/dn/>")
    triples = []    
    triples.append("{} a dn:Dataset.".format(data.get('uri')))
    triples.append("{} dct:title \"{}\".".format(data.get('uri'), data.get("title")))
    triples.append("{} dct:description \"{}\".".format(data.get('uri'),  data.get("description")))
    triples.append("{} dcat:keyword \"{}\".".format(data.get('uri'),  data.get("keywords")))
    triples.append("{} dct:issued \"{}\"^^xsd:date.".format(data.get('uri'), data.get("issuedDate")))
    triples.append("{} dn:note \"{}\".".format(data.get('uri'),  data.get("note")))
    
    for creator in data.get('creators'):
        triples.append("{} dct:creator {}.".format(data.get('uri'), creator.get("uri")))
        triples.append("{} a foaf:Agent.".format(creator.get('uri'))) 
        triples.append("{} foaf:name \"{}\".".format(creator.get('uri'), creator.get("name"))) 
        triples.append("{} foaf:email \"{}\".".format(creator.get('uri'), creator.get("email")))
    
    for publisher in data.get('publishers'):
        triples.append("{} dct:publisher {}.".format(data.get('uri'), publisher.get("uri")))
        triples.append("{} a foaf:Agent.".format(publisher.get('uri'))) 
        triples.append("{} foaf:name \"{}\".".format(publisher.get('uri'), publisher.get("name"))) 
        triples.append("{} foaf:email \"{}\".".format(publisher.get('uri'), publisher.get("email")))

    depositors = []
    for depositor in data.get('depositors'):        
        triples.append("{} dn:depositor {}.".format(data.get('uri'), depositor.get("uri")))
        triples.append("{} a foaf:Agent.".format(depositor.get('uri'))) 
        triples.append("{} foaf:name \"{}\".".format(depositor.get('uri'), depositor.get("name"))) 
        triples.append("{} foaf:email \"{}\".".format(depositor.get('uri'), depositor.get("email")))

    for pub in data.get('pubs'):
        triples.append("{} dn:usedIn {}.".format(data.get('uri'), pub.get("uri")))
        triples.append("{} a bibo:Document.".format(pub.get('uri'))) 
        triples.append("{} dct:title \"{}\".".format(pub.get('uri'), pub.get("title"))) 
        triples.append("{} dct:issued \"{}\"^^xsd:date.".format(pub.get('uri'), pub.get("issuedDate")))
        for author in pub.get("authors"):
            triples.append("{} dct:creator {}.".format(pub.get('uri'), author.get("uri")))
            triples.append("{} a foaf:Agent.".format(author.get('uri'))) 
            triples.append("{} foaf:name \"{}\".".format(author.get('uri'), author.get("name"))) 
            triples.append("{} foaf:email \"{}\".".format(author.get('uri'), author.get("email")))

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

    rs = createDataset(str)
    triples.append("{} dct:identifier \"{}\".".format(data.get('uri'), rs))
    triples.append("{} dcat:landingPage \"http://localhost:8085/dataset.xhtml?persistentId={}\".".format(data.get('uri'), rs))
    insertData("\n ".join(prefixes), "\n ".join(triples))
    return JsonResponse({'result':rs} , safe=False)

def getClasses(request):      
    results = query(""" SELECT DISTINCT ?uri ?label ?comment
    WHERE
         { 
              ?uri  rdf:type   owl:Class . 
                   ?uri    rdfs:label  ?label .
                   FILTER (lang(?label) = "" || lang(?label) = "en" )
               OPTIONAL {  
                   ?uri    rdfs:comment  ?comment .
                   FILTER (lang(?comment) = "" || lang(?comment) = "en" )
               } 
         } 
         ORDER BY ASC(?label)""")
     
    json = []
    for result in results["results"]["bindings"]:
        on = {'uri':result["uri"]["value"], 'label':result["label"]["value"]}
        if result.get("description"):
            on['comment'] = result["comment"]["value"]
        else:
            on['comment'] = '-'    
        json.append(on)
       
    return JsonResponse({'result':json} , safe=False)
 
def getProperties(request):
    results = query("""SELECT DISTINCT ?uri ?label ?comment ?domain ?domain_label ?range 
    WHERE 
         { 
              ?uri  rdf:type     owl:DatatypeProperty    .
              ?uri  rdfs:domain     ?domain    . 
              ?domain  rdfs:label     ?domain_label    . 
              ?uri  rdfs:range     ?range    .               
               OPTIONAL {  
                   ?uri    rdfs:label  ?label .
                   FILTER (lang(?label) = "" || lang(?label) = "en") 
               } 
               OPTIONAL {  
                   ?uri  rdfs:comment   ?comment .
                  FILTER (lang(?comment) = "" || lang(?comment) = "en" ) 
               } 
         } 
    ORDER BY ASC(?label) """)
    json = []
    for result in results["results"]["bindings"]:        
        on = {'uri':result["uri"]["value"], 'label':result["label"]["value"], 'domain':result["domain"]["value"], 'domain_label':result["domain_label"]["value"], 'range':result["range"]["value"] }
        if result.get("comment"):
            on['comment'] = result["comment"]["value"]
        else:
            on['comment'] = '-'
        if result.get("label"):
            on['label'] = result["label"]["value"]
        else:
            on['label'] = '-'    
        json.append(on)
    return JsonResponse({'result':json} , safe=False)

