# RAG training pipeline

## Objetivo

Centralizar la documentación y datos necesarios para generar embeddings y alimentar el RAG del bot de Viajes Bumeran.

## Estructura

- `documents/`: fuentes originales (PDF, Markdown, CSV, etc.).
- `artifacts/`: resultados de procesamiento (embeddings, índices, metadatos).
- `scripts/`: notebooks o scripts auxiliares para la ingesta y refresco.

## Flujo sugerido

1. **Ingesta**  
   Normaliza los documentos en `documents/` (UTF-8, formato limpio).  
   Usa `scripts/ingest.py` (plantilla) para generar embeddings con Gemini 1.5 Pro y guarda la salida en `artifacts/`.

2. **Validación**  
   Documenta en esta carpeta las métricas de evaluación (recall, latencia, etc.).

3. **Deploy**  
   Publica los artefactos validados en el almacenamiento elegido (por ejemplo, Vertex Matching Engine o Firestore) y actualiza las referencias en `llm-orchestrator`.

## Próximos pasos

- Completar `scripts/ingest.py` con la lógica de extracción y chunking.
- Configurar pruebas automáticas que validen la coherencia de los embeddings antes de publicarlos.
