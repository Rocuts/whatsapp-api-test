
import json
import os
import requests

access_token = os.popen('gcloud auth print-access-token').read().strip()

url = 'https://monitoring.googleapis.com/v3/projects/agentes-ia-prod/uptimeCheckConfigs'

headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json',
}

with open('/home/contacto/uptime_check_prod.json', 'r') as f:
    data = json.load(f)

response = requests.post(url, headers=headers, data=json.dumps(data))

print(response.status_code)
print(response.text)
