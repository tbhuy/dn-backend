from django.http import HttpResponse, JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
from dn import utils
import time
import requests
import urllib3

def import_meta(request):
  sites = utils.read_sites()
  ds_id = request.GET.get('id') 
  ds_site = ""
  ds_type = ""
  for site in sites:
    if site.get("name") == request.GET.get('site'):
      ds_site = site.get("api") 
      ds_type = site.get("type") 
      


  ts = round(time.time()*1000)
  requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = 'ALL:@SECLEVEL=1'
  resp = requests.get(ds_site + str(ds_id))
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
  triples.append("{} dn:hasSubject <http://melodi.irit.fr/resource/Subject/99>.".format(ds_uri))  
  triples.append("{} dcat:distribution {}.".format(ds_uri, dis_uri))
  triples.append("{} a dn:Distribution.".format(dis_uri))

  if("dataverse" not in ds_type):
    triples.append("{} dcat:landingPage \"{}\".".format(ds_uri, ds.get("page")))
    triples.append("{} dct:identifier \"{}\".".format(ds_uri, ds.get("id")))
    triples.append("{} dct:issued \"{}\"^^xsd:dateTime.".format(ds_uri, ds.get("created_at")))  
    triples.append("{} dct:license \"{}\".".format(ds_uri, ds.get("license")))   
    triples.append("{} dct:title \"{}\".".format(ds_uri, ds.get("title")))
    triples.append("{} dct:description \"\"\"{}\"\"\".".format(ds_uri, ds.get("description")))
    for kw in ds.get("tags"):
      triples.append("{} dcat:keyword \"{}\".".format(ds_uri, kw))

    triples.append("{} dcat:downloadURL \"{}\".".format(dis_uri, ds.get("resources")[0].get("url")))
    triples.append("{} dct:identidier \"{}\".".format(dis_uri, ds.get("resources")[0].get("id")))
    if ds.get("resources")[0].get("filesize"):
      triples.append("{} dcat:byteSize {}.".format(dis_uri, ds.get("resources")[0].get("filesize", 0))) 
    triples.append("{} dcat:mediaType \"{}\".".format(dis_uri, ds.get("resources")[0].get("mime"))) 

  else:
    ds = ds.get("data")
    print(ds.get("latestVersion").get("metadataBlocks"))
    triples.append("{} dcat:landingPage \"{}\".".format(ds_uri, ds.get("persistentUrl")))
    triples.append("{} dct:identifier \"{}\".".format(ds_uri, ds.get("identifier")))
    triples.append("{} dct:issued \"{}\"^^xsd:dateTime.".format(ds_uri, ds.get("publicationDate")))
    triples.append("{} dct:license \"{}\".".format(ds_uri, ds.get("latestVersion").get("license"))) 
    for att in ds.get("latestVersion").get("metadataBlocks").get("citation").get("fields"):
      if att.get("typeName") =="title":
        triples.append("{} dct:title \"{}\".".format(ds_uri, att.get("value")))  
      if att.get("typeName") == "dsDescription":
        for desc in att.get("value"):
          triples.append("{} dct:description \"\"\"{}\"\"\".".format(ds_uri, desc.get("dsDescriptionValue").get("value")))
      if att.get("typeName") == "keyword":
        for kw in att.get("value"):
          triples.append("{} dcat:keyword \"{}\".".format(ds_uri, kw.get("keywordValue").get("value")))    

    triples.append("{} dcat:downloadURL \"{}\".".format(dis_uri, "https://" + request.GET.get('site') + "/api/access/datafile/" + str(ds.get("latestVersion").get("files")[0].get("dataFile").get("id"))))
    triples.append("{} dcat:byteSize {}.".format(dis_uri,ds.get("latestVersion").get("files")[0].get("dataFile").get("filesize")))
    triples.append("{} dcat:mediaType \"{}\".".format(dis_uri, ds.get("latestVersion").get("files")[0].get("dataFile").get("originalFileFormat")))

  utils.insert_data("\n ".join(prefixes), "\n ".join(triples))
  return HttpResponse("ok")

   

def get_data_props(request):
  classes = []
  results = utils.query(""" PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
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
    results = utils.query(""" PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
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
    results = utils.query(""" PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
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
    utils.insert_data("","\n ".join(triples))  
    return JsonResponse({'result':'ok'} , safe=False)