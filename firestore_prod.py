
import json
import os
import requests

access_token = os.popen('gcloud auth print-access-token').read().strip()

url = 'https://firestore.googleapis.com/v1/projects/agentes-ia-prod/databases/(default)/documents/tenants/viajes-bumeran'

headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json',
}

data = {
    'fields': {
        'phone_id': {
            'stringValue': '875276082327651'
        },
        'secrets': {
            'mapValue': {
                'fields': {
                    'meta_token': {
                        'stringValue': 'tenants/viajes-bumeran/META_TOKEN'
                    },
                    'verify_token': {
                        'stringValue': 'tenants/viajes-bumeran/VERIFY_TOKEN'
                    },
                    'meta_app_secret': {
                        'stringValue': 'tenants/viajes-bumeran/META_APP_SECRET'
                    }
                }
            }
        },
        'locale': {
            'stringValue': 'es'
        },
        'persona': {
            'stringValue': 'BUMI'
        },
        'templates': {
            'arrayValue': {
                'values': [
                    {
                        'stringValue': 'bienvenida_bumeran'
                    },
                    {
                        'stringValue': 'reapertura_bumeran'
                    },
                    {
                        'stringValue': 'pago_bumeran'
                    },
                    {
                        'stringValue': 'postventa_bumeran'
                    }
                ]
            }
        }
    }
}

response = requests.patch(url, headers=headers, data=json.dumps(data))

print(response.status_code)
print(response.text)
