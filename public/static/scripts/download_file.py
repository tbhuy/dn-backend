import requests
import sys

headers = {"X-Dataverse-key":"9cc13e11-6ac8-42bc-8dc5-28a0c4e622da"}
"X-Dataverse-key:$API_TOKEN"
r = requests.get(sys.argv[1],headers=headers)
open(sys.argv[2], 'wb').write(r.content)
