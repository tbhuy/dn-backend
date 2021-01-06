import requests
import sys
import os

headers = {"X-Dataverse-key":"9cc13e11-6ac8-42bc-8dc5-28a0c4e622da"}
#"X-Dataverse-key:$API_TOKEN"
r = requests.get(sys.argv[1],headers=headers)
open(sys.argv[2], 'wb').write(r.content)
#os.system('wget -d --header="X-Dataverse-key: 9cc13e11-6ac8-42bc-8dc5-28a0c4e622da" ' + sys.argv[1] + ' -O ' + sys.argv[2])

