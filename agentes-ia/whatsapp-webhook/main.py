
from fastapi import FastAPI, Request, HTTPException, Response
from pathlib import Path
from typing import Any, List, Tuple
import hashlib
import hmac
import json
from google.cloud import firestore
from google.cloud import secretmanager
import google.cloud.logging
import logging

app = FastAPI()

# Instantiates a client
client = google.cloud.logging.Client()

# Retrieves a Cloud Logging handler; you can log standard Python
# logging messages to Cloud Logging
client.setup_logging()

# The name of the log to write to
log_name = "agentes-ia-log"
# The logger object
logger = logging.getLogger(log_name)

DATA_DIR = Path(__file__).resolve().parent / "data"
PROVIDERS_FILE = DATA_DIR / "providers_blacklist.json"
WELCOME_PROMPT = (
    "¡Hola! Soy BUMI de Viajes Bumeran. ¿Nos visitas como proveedor o como cliente?"
)
CLIENT_ACK = (
    "Perfecto, gracias por confirmarlo. Compártenos tu consulta y un asesor te apoyará."
)

def load_providers() -> set[str]:
    if not PROVIDERS_FILE.exists():
        return set()

    try:
        with PROVIDERS_FILE.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        logger.error("Providers blacklist is not valid JSON: %s", exc)
        return set()

    providers = data.get("providers", [])
    if not isinstance(providers, list):
        logger.warning("Providers blacklist has unexpected format. Resetting.")
        return set()

    return {str(provider) for provider in providers}


def save_providers(providers: set[str]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with PROVIDERS_FILE.open("w", encoding="utf-8") as handle:
        json.dump({"providers": sorted(providers)}, handle, ensure_ascii=False, indent=2)


def extract_messages(payload: dict[str, Any]) -> List[Tuple[str, str]]:
    results: List[Tuple[str, str]] = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for message in value.get("messages", []):
                sender = message.get("from", "")
                text = extract_message_text(message)
                results.append((sender, text))
    return results


def extract_message_text(message: dict[str, Any]) -> str:
    message_type = message.get("type", "")
    if message_type == "text":
        return message.get("text", {}).get("body", "")

    if message_type == "interactive":
        interactive = message.get("interactive", {})
        if interactive.get("type") == "button_reply":
            return interactive.get("button_reply", {}).get("title", "")
        if interactive.get("type") == "list_reply":
            return interactive.get("list_reply", {}).get("title", "")

    return ""


def is_provider_intent(text: str) -> bool:
    normalized = text.lower()
    return any(keyword in normalized for keyword in ("proveedor", "proveedora", "supplier"))


def is_client_intent(text: str) -> bool:
    normalized = text.lower()
    return any(keyword in normalized for keyword in ("cliente", "client"))


@app.get("/api/webhook/{tenant}")
def verify_webhook(tenant: str, request: Request):
    # Your verify token. Should be a random string.
    db = firestore.Client()
    tenant_ref = db.collection("tenants").document(tenant)
    tenant_doc = tenant_ref.get()

    if not tenant_doc.exists:
        raise HTTPException(status_code=404, detail="Tenant not found")

    secrets_client = secretmanager.SecretManagerServiceClient()
    verify_token_name = f"projects/agentes-ia-dev/secrets/{tenant_doc.to_dict()['secrets']['verify_token']}/versions/latest"
    response = secrets_client.access_secret_version(request={"name": verify_token_name})
    verify_token = response.payload.data.decode("UTF-8")

    # Parse params from the webhook verification request
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    # Check if a token and mode were sent
    if mode and token:
        # Check the mode and token sent are correct
        if mode == "subscribe" and token == verify_token:
            # Respond with 200 OK and challenge token from the request
            logging.info("WEBHOOK_VERIFIED")
            return Response(content=challenge, status_code=200)
        else:
            # Responds with '403 Forbidden' if verify tokens do not match
            raise HTTPException(status_code=403, detail="Forbidden")
    else:
        # Responds with '404 Not Found' if verify tokens do not match
        raise HTTPException(status_code=404, detail="Not Found")

@app.post("/api/webhook/{tenant}")
async def webhook(tenant: str, request: Request):
    db = firestore.Client()
    tenant_ref = db.collection("tenants").document(tenant)
    tenant_doc = tenant_ref.get()

    if not tenant_doc.exists:
        raise HTTPException(status_code=404, detail="Tenant not found")

    secrets_client = secretmanager.SecretManagerServiceClient()
    meta_app_secret_name = f"projects/agentes-ia-dev/secrets/{tenant_doc.to_dict()['secrets']['meta_app_secret']}/versions/latest"
    response = secrets_client.access_secret_version(request={"name": meta_app_secret_name})
    meta_app_secret = response.payload.data.decode("UTF-8")

    # Get the request body and signature
    body = await request.body()
    signature = request.headers.get("x-hub-signature-256")

    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")

    # Validate the signature
    if not validate_signature(body, signature, meta_app_secret):
        raise HTTPException(status_code=401, detail="Invalid signature")

    body = json.loads(body)

    providers = load_providers()
    providers_updated = False
    actions: List[dict[str, Any]] = []

    for sender, message_text in extract_messages(body):
        if not sender:
            logger.warning("Skipping message without sender information.")
            continue

        if sender in providers:
            logger.info(
                "Ignoring message from provider",
                extra={
                    "json_fields": {
                        "app": "agentes-ia",
                        "env": "dev",
                        "tenant": tenant,
                        "metric": "incoming_messages_total",
                        "category": "provider",
                        "sender": sender,
                    }
                },
            )
            continue

        if is_provider_intent(message_text):
            providers.add(sender)
            providers_updated = True
            logger.info(
                "Provider added to blacklist",
                extra={
                    "json_fields": {
                        "app": "agentes-ia",
                        "env": "dev",
                        "tenant": tenant,
                        "metric": "providers_total",
                        "sender": sender,
                    }
                },
            )
            continue

        if is_client_intent(message_text):
            actions.append(
                {
                    "to": sender,
                    "type": "text",
                    "message": CLIENT_ACK,
                    "next": "delegate_to_llm",
                }
            )
            continue

        actions.append(
            {
                "to": sender,
                "type": "text",
                "message": WELCOME_PROMPT,
                "next": "await_intent",
            }
        )

    if providers_updated:
        save_providers(providers)

    logger.info(
        "Incoming message",
        extra={
            "json_fields": {
                "app": "agentes-ia",
                "env": "dev",
                "tenant": tenant,
                "metric": "incoming_messages_total",
                "actions_generated": len(actions),
            }
        },
    )

    return {"status": "success", "actions": actions}

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

def validate_signature(body, signature, secret):
    # Create a new HMAC SHA256 hash
    h = hmac.new(secret.encode(), body, hashlib.sha256)
    expected_signature = "sha256=" + h.hexdigest()

    # Compare the signatures
    return hmac.compare_digest(expected_signature, signature)
