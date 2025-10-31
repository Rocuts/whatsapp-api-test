
from fastapi import FastAPI
import requests
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

@app.post("/send")
def send(request: dict):
    tenant = request.get("tenant")
    phone_number = request.get("phone_number")
    message = request.get("message")
    message_type = request.get("message_type", "text")

    # Get secrets from Secret Manager
    # ...

    if message_type == "text":
        send_text(phone_number, message)
    elif message_type == "template":
        send_template(phone_number, message)

    logger.info("Outgoing message", extra={
        "json_fields": {
            "app": "agentes-ia",
            "env": "dev",
            "tenant": tenant,
            "metric": "outgoing_messages_total",
        }
    })

    return {"status": "success"}

def send_text(phone_number, message):
    # Send text message using Meta Graph API
    pass

def send_template(phone_number, message):
    # Send template message using Meta Graph API
    pass
