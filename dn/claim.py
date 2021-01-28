import json
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from dn import utils

def get_claim(request):  
  results = utils.query("""
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
  results = utils.query("""
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
 
  utils.insert_data("\n ".join(prefixes), "\n ".join(triples))  
  return JsonResponse({'result':'ok'} , safe=False)
