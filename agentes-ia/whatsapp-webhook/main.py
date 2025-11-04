from fastapi import FastAPI, Request, HTTPException, Response
from pathlib import Path
from typing import Any, List, Tuple
import hashlib
import hmac
import json
from google.cloud import firestore, secretmanager
import google.cloud.logging
import logging


# -------------------------------------------------------------------
# 🚀 CONFIGURACIÓN INICIAL
# -------------------------------------------------------------------
app = FastAPI()

# Configurar cliente de Google Cloud Logging (para registrar eventos en la nube)
client = google.cloud.logging.Client()
client.setup_logging()

# Crear logger
log_name = "agentes-ia-log"
logger = logging.getLogger(log_name)

# Directorio base de datos y configuración local
DATA_DIR = Path(__file__).resolve().parent / "data"
PROVIDERS_FILE = DATA_DIR / "providers_blacklist.json"
PROMPT_FILE = DATA_DIR / "prompt_master.txt"  # Prompt maestro de personalidad del bot

# Mensajes predefinidos (no técnicos, claros para los usuarios)
WELCOME_PROMPT = "¡Hola! Soy BUMI de Viajes Bumeran 🌎. ¿Nos visitas como proveedor o como cliente?"
CLIENT_ACK = "Perfecto 😊 gracias por confirmarlo. Compártenos tu consulta y un asesor te apoyará."


# -------------------------------------------------------------------
# 🧩 FUNCIONES DE UTILIDAD
# -------------------------------------------------------------------

def load_providers() -> set[str]:
    """
    Carga la lista de números de teléfono que son proveedores desde un archivo JSON local.
    Estos números serán ignorados por el bot (serán atendidos por un humano).
    """
    if not PROVIDERS_FILE.exists():
        return set()

    try:
        with PROVIDERS_FILE.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        logger.error("El archivo de proveedores no es un JSON válido: %s", exc)
        return set()

    providers = data.get("providers", [])
    if not isinstance(providers, list):
        logger.warning("Formato inesperado en el archivo de proveedores.")
        return set()

    return {str(provider) for provider in providers}


def save_providers(providers: set[str]) -> None:
    """
    Guarda la lista actualizada de proveedores en el archivo JSON.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with PROVIDERS_FILE.open("w", encoding="utf-8") as handle:
        json.dump({"providers": sorted(providers)}, handle, ensure_ascii=False, indent=2)


def load_master_prompt() -> str:
    """
    Carga el prompt maestro desde un archivo de texto plano.
    Este prompt define la 'personalidad' y conocimiento base del bot.
    """
    if not PROMPT_FILE.exists():
        logger.warning("Archivo de prompt maestro no encontrado. Usando texto vacío.")
        return ""
    return PROMPT_FILE.read_text(encoding="utf-8").strip()


def extract_messages(payload: dict[str, Any]) -> List[Tuple[str, str]]:
    """
    Extrae el número del remitente y el texto de cada mensaje recibido en el payload.
    """
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
    """
    Extrae el texto de distintos tipos de mensajes de WhatsApp (texto, botones, listas).
    """
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
    """
    Determina si el mensaje recibido tiene intención de proveedor.
    """
    normalized = text.lower()
    return any(keyword in normalized for keyword in ("proveedor", "proveedora", "supplier"))


def is_client_intent(text: str) -> bool:
    """
    Determina si el mensaje recibido tiene intención de cliente.
    """
    normalized = text.lower()
    return any(keyword in normalized for keyword in ("cliente", "client"))


def validate_signature(body, signature, secret):
    """
    Valida la firma de seguridad de Meta usando HMAC-SHA256.
    """
    h = hmac.new(secret.encode(), body, hashlib.sha256)
    expected_signature = "sha256=" + h.hexdigest()
    return hmac.compare_digest(expected_signature, signature)


# -------------------------------------------------------------------
# 🔐 ENDPOINT DE VERIFICACIÓN DEL WEBHOOK (GET)
# -------------------------------------------------------------------

@app.get("/api/webhook/{tenant}")
def verify_webhook(tenant: str, request: Request):
    """
    Endpoint para verificar la conexión del webhook con Meta.
    Se usa cuando se configura la URL del webhook en el panel de Meta.
    """
    db = firestore.Client()
    tenant_ref = db.collection("tenants").document(tenant)
    tenant_doc = tenant_ref.get()

    if not tenant_doc.exists:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    secrets_client = secretmanager.SecretManagerServiceClient()
    verify_token_name = (
        f"projects/agentes-ia-dev/secrets/{tenant_doc.to_dict()['secrets']['verify_token']}/versions/latest"
    )
    response = secrets_client.access_secret_version(request={"name": verify_token_name})
    verify_token = response.payload.data.decode("UTF-8")

    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == verify_token:
            logging.info("WEBHOOK_VERIFIED")
            return Response(content=challenge, status_code=200)
        else:
            raise HTTPException(status_code=403, detail="Token inválido")
    raise HTTPException(status_code=404, detail="Solicitud incorrecta")


# -------------------------------------------------------------------
# 💬 ENDPOINT PRINCIPAL DE MENSAJES (POST)
# -------------------------------------------------------------------

@app.post("/api/webhook/{tenant}")
async def webhook(tenant: str, request: Request):
    """
    Endpoint principal que recibe los mensajes de los usuarios desde Meta.
    """
    db = firestore.Client()
    tenant_ref = db.collection("tenants").document(tenant)
    tenant_doc = tenant_ref.get()

    if not tenant_doc.exists:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")

    # Recuperar secretos seguros desde Secret Manager
    secrets_client = secretmanager.SecretManagerServiceClient()
    meta_app_secret_name = (
        f"projects/agentes-ia-dev/secrets/{tenant_doc.to_dict()['secrets']['meta_app_secret']}/versions/latest"
    )
    response = secrets_client.access_secret_version(request={"name": meta_app_secret_name})
    meta_app_secret = response.payload.data.decode("UTF-8")

    # Validar firma del mensaje
    body = await request.body()
    signature = request.headers.get("x-hub-signature-256")

    if not signature:
        raise HTTPException(status_code=400, detail="Falta la firma de seguridad")

    if not validate_signature(body, signature, meta_app_secret):
        raise HTTPException(status_code=401, detail="Firma inválida")

    body = json.loads(body)

    # Cargar datos base
    providers = load_providers()
    master_prompt = load_master_prompt()
    providers_updated = False
    actions: List[dict[str, Any]] = []

    # Procesar mensajes recibidos
    for sender, message_text in extract_messages(body):
        if not sender:
            logger.warning("Mensaje sin número de remitente, se omite.")
            continue

        # Ignorar mensajes de proveedores conocidos
        if sender in providers:
            logger.info(f"Mensaje ignorado de proveedor: {sender}")
            continue

        # Si se identifica como proveedor, agregar a la lista
        if is_provider_intent(message_text):
            providers.add(sender)
            providers_updated = True
            logger.info(f"Nuevo proveedor detectado y agregado: {sender}")
            continue

        # Si es cliente, generar respuesta de confirmación
        if is_client_intent(message_text):
            actions.append({
                "to": sender,
                "type": "text",
                "message": CLIENT_ACK,
                "next": "delegate_to_llm",
                "context": master_prompt
            })
            continue

        # Si no hay intención detectada, enviar saludo inicial
        actions.append({
            "to": sender,
            "type": "text",
            "message": WELCOME_PROMPT,
            "next": "await_intent",
            "context": master_prompt
        })

    if providers_updated:
        save_providers(providers)

    logger.info(f"Mensajes procesados correctamente. Acciones: {len(actions)}")

    return {"status": "success", "actions": actions}


# -------------------------------------------------------------------
# ❤️ ENDPOINT DE SALUD (para monitoreo)
# -------------------------------------------------------------------

@app.get("/healthz")
def healthz():
    """
    Permite verificar que el servicio está funcionando correctamente.
    """
    return {"status": "ok"}
