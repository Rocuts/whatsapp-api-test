
from fastapi import FastAPI
from google.cloud import aiplatform
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

@app.post("/nlu/generate")
def generate(request: dict):
    tenant = request.get("tenant")
    model = request.get("model")
    prompt = request.get("prompt")

    aiplatform.init(project="agentes-ia-dev", location="us-central1")
    model = aiplatform.gapic.Model(model_name=model)

    response = model.predict(instances=[prompt])

    logger.info("LLM tokens", extra={
        "json_fields": {
            "app": "agentes-ia",
            "env": "dev",
            "tenant": tenant,
            "model": model,
            "metric": "llm_tokens_total",
            "tokens": response.usage_metadata.total_token_count
        }
    })

    return {"response": response.predictions[0].content}
