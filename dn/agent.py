from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from dn import utils
import json

#Get all agents
def get_agents(request):
    results = utils.query(""" PREFIX foaf: <http://xmlns.com/foaf/0.1/>
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

#Get an agent by his/her name
def get_agent(request):
    results = utils.query(""" PREFIX foaf: <http://xmlns.com/foaf/0.1/>
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

#Create a new agent
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
    utils.insert_data("\n ".join(prefixes), "\n ".join(triples))  
    return JsonResponse({'result':'ok'} , safe=False)
