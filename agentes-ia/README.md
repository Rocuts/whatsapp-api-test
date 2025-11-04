# Agentes de IA

This repository contains the source code for the Agentes de IA platform.

## Services

- **whatsapp-webhook**: Handles incoming WhatsApp messages.
- **llm-orchestrator**: Orchestrates the interaction with the LLM.
- **dispatcher**: Dispatches outgoing WhatsApp messages.

## LLM model (Gemini)

- El modelo productivo es **Gemini 1.5 Pro**, configurado vía el secreto `GEMINI_MODEL`.
- Los endpoints de Vertex AI se consumen desde `llm-orchestrator` usando `google-cloud-aiplatform`.
- Para actualizar la versión del modelo, rota el secreto y redeploya los servicios dependientes.

## Entrenamiento y RAG

- La carpeta `rag-training/` concentra documentación y datasets para generar embeddings y alimentar el RAG.
- Coloca los documentos fuente en `rag-training/documents/` y los artefactos en `rag-training/artifacts/`.
- Sigue las instrucciones en `rag-training/README.md` para orquestar la ingesta y refresco de conocimiento.

## Lista de proveedores

- `agentes-ia/whatsapp-webhook/data/providers_blacklist.json` almacena los números de WhatsApp identificados como proveedores.
- El webhook consulta esta lista antes de invocar al LLM; si el número está presente, se descarta la interacción automática.
- Cuando un contacto se declara proveedor, el webhook actualiza la lista para futuras conversaciones.
