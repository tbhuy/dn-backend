from django.http import HttpResponse, JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
from dn import utils

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
  
  utils.insert_data("\n ".join(prefixes), "\n ".join(triples))  
  return JsonResponse({'result':'ok'} , safe=False)

def get_pubs_doi(request):  
  results = utils.query("""
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
  results = utils.query("""
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
  results = utils.query("""
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