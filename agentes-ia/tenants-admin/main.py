
from fastapi import FastAPI, HTTPException
from google.cloud import firestore
from google.cloud import secretmanager

app = FastAPI()

@app.post("/tenants")
def create_tenant(request: dict):
    tenant_key = request.get("tenant_key")
    meta_token = request.get("meta_token")
    phone_id = request.get("phone_id")
    verify_token = request.get("verify_token")
    meta_app_secret = request.get("meta_app_secret")
    tenant_default_lang = request.get("tenant_default_lang")
    tenant_persona_name = request.get("tenant_persona_name")
    tenant_templates = request.get("tenant_templates")

    # Create secrets
    secrets_client = secretmanager.SecretManagerServiceClient()
    project_id = "agentes-ia-dev"

    for secret_id, secret_value in [("META_TOKEN", meta_token), ("PHONE_ID", phone_id), ("VERIFY_TOKEN", verify_token), ("META_APP_SECRET", meta_app_secret)]:
        secret_name = f"projects/{project_id}/secrets/tenants/{tenant_key}/{secret_id}"
        secrets_client.create_secret(
            request={
                "parent": f"projects/{project_id}",
                "secret_id": f"tenants-{tenant_key}-{secret_id}",
                "secret": {"replication": {"automatic": {}}},
            }
        )
        secrets_client.add_secret_version(
            request={"parent": secret_name, "payload": {"data": secret_value.encode()}}
        )

    # Create Firestore document
    db = firestore.Client()
    tenant_ref = db.collection("tenants").document(tenant_key)
    tenant_ref.set({
        "phone_id": phone_id,
        "secrets": {
            "meta_token": f"tenants/{tenant_key}/META_TOKEN",
            "verify_token": f"tenants/{tenant_key}/VERIFY_TOKEN",
            "meta_app_secret": f"tenants/{tenant_key}/META_APP_SECRET"
        },
        "locale": tenant_default_lang,
        "persona": tenant_persona_name,
        "templates": tenant_templates
    })

    webhook_url = f"https://whatsapp-webhook-878958463385.us-central1.run.app/api/webhook/{tenant_key}"

    return {"webhook_url": webhook_url}
