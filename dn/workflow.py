from django.http import HttpResponse, JsonResponse
import json
import requests
import time
import os
import subprocess
from django.conf import settings
import sys
from django.core.files.storage import FileSystemStorage
from django.views.decorators.csrf import csrf_exempt
from dn import utils

def execute_workflow(request):
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
  results = utils.query(q)  
  
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

 
def get_services(request):  
  results = utils.query("""
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
    utils.insert_data("\n ".join(prefixes), "\n ".join(triples))  
    return JsonResponse({'result':'ok'} , safe=False)