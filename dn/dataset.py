import json
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from dn import utils

@csrf_exempt
# upload a distribution (a file), given the PID of the dataset (returned by Dataverse) 
def  upload_distribution(request):  
    file_uploaded = request.FILES.get('file_uploaded')
    pid = request.POST.get('pid')
    uri = request.POST.get('uri')
    file_id = request.POST.get('id')
    file_format = request.POST.get('format')
    #send the file to Dataverse and get its ID in return
    r = requests.post(dataverse + "/api/datasets/:persistentId/add?persistentId="+pid, files={'file': file_uploaded}, data={"description":"Initial file"}, headers={ 'X-Dataverse-key': dv_key})
    
      #{"status":"OK","data":{"files":[{"description":"","label":"dcat.csv","restricted":false,"version":1,"datasetVersionId":13,"dataFile":{"id":22,"persistentId":"","pidURL":"","filename":"dcat.csv","contentType":"text/csv","filesize":10887,"description":"","storageIdentifier":"local://175e1e0e2b5-68f3d93a8f1d","rootDataFileId":-1,"md5":"60e5abb7a8c9207456490df444659211","checksum":{"type":"MD5","value":"60e5abb7a8c9207456490df444659211"},"creationDate":"2020-11-19"}}]}}
    # if OK compose the triple describing the file (a distribution)
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
        utils.insert_data("\n ".join(prefixes), "\n ".join(triples))
        return HttpResponse("ok")
    else:
        return HttpResponse("failed")     

# get all available datasets
def get_datasets (request):
  results = utils.query("""  PREFIX dc: <http://purl.org/dc/elements/1.1/>
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

# get the most recent (six) datasets
def list_recents(request):
  results = utils.query("""  PREFIX dc: <http://purl.org/dc/elements/1.1/>
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

#get the location (X,Y) of all datasets
#used to visualize them on the map 
def get_loc(request):
    results = utils.query("""  PREFIX dct: <http://purl.org/dc/terms/>
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


#get the keywords of all datasets
#used to display the word cloud
def get_stat_key(request):
    results = utils.query("""PREFIX dn: <http://melodi.irit.fr/ontologies/dn/>
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

#get the subject of all datasets
#used to display diagram
def get_stat_subj(request):
    results = utils.query("""select ?name (count (?name) as ?total) where { 
	?ds <http://melodi.irit.fr/ontologies/dn/hasSubject> ?subj .
    ?subj <http://melodi.irit.fr/ontologies/dn/name> ?name.    
    } group by ?name 
    """)
    json = []
    for result in results["results"]["bindings"]:
        json.append({'name':result["name"]["value"], 'total': result["total"]["value"]})
   
    return JsonResponse({'rs':json}, safe=False) 

#get all operations/functions
def get_operations(request):
    results = utils.query("""PREFIX owl: <http://www.w3.org/2002/07/owl#>
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

# Get information of a dataset
# used to display dataset metadata in Normal view mode    
def show_dataset(request):
  uri = "<" + request.GET.get("uri")  + ">"
 
  results = utils.query("""PREFIX dc: <http://purl.org/dc/elements/1.1/>
  PREFIX dct: <http://purl.org/dc/terms/>
  PREFIX dcat: <http://www.w3.org/ns/dcat#>
  PREFIX dn: <http://melodi.irit.fr/ontologies/dn/>
  PREFIX locn: <http://www.w3.org/ns/locn#>
  PREFIX geo: <http://www.opengis.net/ont/geosparql#>
  select distinct ?dn ?title ?description ?issued ?subject ?note ?geom ?identifier ?page where {{ 
	  {} a  dn:Dataset.
    {} dct:issued ?issued.
    {} dct:identifier ?identifier.
    {} dcat:landingPage ?page.
    {} dct:title ?title.
    {} dct:description ?description.
    {} dn:hasSubject ?subj.
  OPTIONAL{{ {} dn:note ?note.}}
  OPTIONAL{{ {}  dct:spatial ?sp.
          ?sp locn:geometry ?geom.}}
    
    ?subj dn:name ?subject.}}""".format(uri, uri, uri, uri, uri, uri, uri, uri, uri))
  

  result = results["results"]["bindings"][0]
  json = {'title':result["title"]["value"], 'description': result["description"]["value"], 'issued': result["issued"]["value"], 'identifier': result["identifier"]["value"], 'page': result["page"]["value"], 'subject': result["subject"]["value"]}
  if result.get("note"):
    json["note"] = result["note"]["value"]
  if result.get("geom"):
    json["geom"] = result["geom"]["value"]

  results = utils.query("""PREFIX dc: <http://purl.org/dc/elements/1.1/>
  PREFIX dct: <http://purl.org/dc/terms/>
  PREFIX foaf: <http://xmlns.com/foaf/0.1/>
  PREFIX dcat: <http://www.w3.org/ns/dcat#>
  PREFIX dn: <http://melodi.irit.fr/ontologies/dn/>
  select distinct ?creator ?creator_name where {{ 
	  {} a  dn:Dataset.
    {} dct:creator ?creator.
    ?creator foaf:name ?creator_name.}}""".format(uri, uri))


  json2 = []
  for result in results["results"]["bindings"]:
    json2.append({'uri':result["creator"]["value"], 'name': result["creator_name"]["value"]})
  json["creators"] = json2


  results = utils.query("""PREFIX dc: <http://purl.org/dc/elements/1.1/>
  PREFIX dct: <http://purl.org/dc/terms/>
  PREFIX foaf: <http://xmlns.com/foaf/0.1/>
  PREFIX dcat: <http://www.w3.org/ns/dcat#>
  PREFIX dn: <http://melodi.irit.fr/ontologies/dn/>
  select distinct ?publisher ?publisher_name where {{ 
	  {} a  dn:Dataset.
    {} dct:publisher ?publisher.
    ?publisher foaf:name ?publisher_name.}}""".format(uri, uri))


  json21 = []
  for result in results["results"]["bindings"]:
    json21.append({'uri':result["publisher"]["value"], 'name': result["publisher_name"]["value"]})
  json["publishers"] = json21



  results = utils.query("""PREFIX dc: <http://purl.org/dc/elements/1.1/>
  PREFIX dct: <http://purl.org/dc/terms/>
  PREFIX foaf: <http://xmlns.com/foaf/0.1/>
  PREFIX dcat: <http://www.w3.org/ns/dcat#>
  PREFIX dn: <http://melodi.irit.fr/ontologies/dn/>
  select distinct ?depositor ?depositor where {{ 
	  {} a  dn:Dataset.
    {} dn:depositor ?depositor.
    ?depositor foaf:name ?depositor.}}""".format(uri, uri))


  json22 = []
  for result in results["results"]["bindings"]:
    json22.append({'uri':result["depositor"]["value"], 'name': result["depositor_name"]["value"]})
  json["depositors"] = json22


  results = utils.query("""PREFIX dc: <http://purl.org/dc/elements/1.1/>
  PREFIX dct: <http://purl.org/dc/terms/>
  PREFIX foaf: <http://xmlns.com/foaf/0.1/>
  PREFIX dcat: <http://www.w3.org/ns/dcat#>
  PREFIX dn: <http://melodi.irit.fr/ontologies/dn/>
  select distinct ?keyword where {{ 
	  {} a  dn:Dataset.
    {} dcat:keyword ?keyword.}}""".format(uri, uri))

  json3 = []
  for result in results["results"]["bindings"]:
    json3.append({'keyword':result["keyword"]["value"]})
  json["keywords"] = json3


  results = utils.query("""PREFIX dc: <http://purl.org/dc/elements/1.1/>
  PREFIX dct: <http://purl.org/dc/terms/>
  PREFIX foaf: <http://xmlns.com/foaf/0.1/>
  PREFIX dcat: <http://www.w3.org/ns/dcat#>
  PREFIX dn: <http://melodi.irit.fr/ontologies/dn/>
  select ?article ?title ?issued ?identifier where {{ 
	  {} a  dn:Dataset.
    {} dn:presentedIn ?article.
    ?article dct:title ?title.
    ?article dct:issued ?issued.
    ?article dct:identifier ?identifier.}}
    """.format(uri, uri))

  json4 = []
  for result in results["results"]["bindings"]:
    json4.append({'uri':result["article"]["value"], 'DOI': result["identifier"]["value"],  'title': result["title"]["value"], 'issued': result["issued"]["value"]})   
 
  json["publication"] = json4

  results = utils.query("""PREFIX dc: <http://purl.org/dc/elements/1.1/>
  PREFIX dct: <http://purl.org/dc/terms/>
  PREFIX foaf: <http://xmlns.com/foaf/0.1/>
  PREFIX dcat: <http://www.w3.org/ns/dcat#>
  PREFIX dn: <http://melodi.irit.fr/ontologies/dn/>
  select ?dist ?size ?downloadURL ?mediaType ?format where {{ 
	  {} a  dn:Dataset.
    {} dcat:distribution ?dist.  
    ?dist dcat:downloadURL ?downloadURL.  
    OPTIONAL{{   
    ?dist dcat:byteSize ?size.
    ?dist dcat:mediaType ?mediaType. 
    ?dist dn:hasFormat ?fo.
    ?fo rdfs:label ?format.}}
    }}
    """.format(uri, uri))
  json5 = []

  for result in results["results"]["bindings"]:
    json51 = {'uri':result["dist"]["value"], 'downloadURL': result["downloadURL"]["value"]}
    if result.get("format"):
      json51["format"] = result["format"]["value"]
    else:
      json51["format"] = "Unknown"
    if result.get("size"):
      json51["size"] = result["size"]["value"]
    else:
      json51["size"] = "Unknown"  
    if result.get("mediaType"):
      json51["mediaType"] = result["mediaType"]["value"]
    else:
      json51["mediaType"] = "Unknown"
    json5.append(json51)


  results = utils.query("""PREFIX dc: <http://purl.org/dc/elements/1.1/>
  PREFIX dct: <http://purl.org/dc/terms/>
  PREFIX foaf: <http://xmlns.com/foaf/0.1/>
  PREFIX dcat: <http://www.w3.org/ns/dcat#>
  PREFIX dn: <http://melodi.irit.fr/ontologies/dn/>
  PREFIX prov-o: <http://www.w3.org/ns/prov#>
  select ?agent ?agent_name ?atTime ?source ?site where {{ 
	  {} a  dn:Dataset.  
    {} prov-o:wasDerivedFrom  ?source.
    {} prov-o:wasGeneratedBy ?act.
    ?act prov-o:atTime ?atTime.
    ?act dn:harvestSource ?site.
    ?act prov-o:wasAssociatedWith ?agent.
    ?agent foaf:name ?agent_name.}}
    """.format(uri, uri, uri))

  json6 = {}
  if len(results["results"]["bindings"])>0:
    result = results["results"]["bindings"][0]
    json6 = {'agent':result["agent"]["value"], 'agentName': result["agent_name"]["value"],  'atTime': result["atTime"]["value"], 'source': result["source"]["value"], 'site': result["site"]["value"]} 
 
  json["provo"] = json6  
 
  json["dists"] = json5


  return JsonResponse({'rs':json}, safe=False)  

# Get a dataset based on its title or a keyword
def get_dataset(request):
  if request.GET.get("search") == "title":
    filter = 'FILTER regex(str(?title), "' + request.GET.get('value')+ '", "i")'
  elif request.GET.get("search") == "keyword":
    filter = 'FILTER regex(str(?keyword), "' + request.GET.get('value')+ '" , "i")'

  results = utils.query("""PREFIX dc: <http://purl.org/dc/elements/1.1/>
  PREFIX dct: <http://purl.org/dc/terms/>
  PREFIX dcat: <http://www.w3.org/ns/dcat#>
  PREFIX dn: <http://melodi.irit.fr/ontologies/dn/>
  select distinct ?dn ?title ?description ?issued ?subject where {{ 
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

#Get all distributions of a dataset
def get_distributions(request):  
  results = utils.query("""PREFIX dn: <http://melodi.irit.fr/ontologies/dn/>
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

#Get information of a distribution
def get_distribution(request):  
  results = utils.query("""PREFIX dn: <http://melodi.irit.fr/ontologies/dn/>
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

# create a new dataset based on the form data sent by the frontend
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
    #insert the dataset metadata into Dataverse
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
    if r.status_code == 200 or r.status_code == 201: #if OK, get the returned DOI/ID and insert the triples into the triplestore
      rs = json.loads(r.text).get("data").get("persistentId")    
      triples.append("{} dct:identifier \"{}\".".format(data.get('uri'), rs))
      triples.append("{} dcat:landingPage \"{}/dataset.xhtml?persistentId={}\".".format(data.get('uri'), dataverse_ex, rs))
      utils.insert_data("\n ".join(prefixes), "\n ".join(triples))
    else:
      rs = "failed"
    return JsonResponse({'doi':rs, 'page': dataverse_ex + '/dataset.xhtml?persistentId=' + rs} , safe=False)