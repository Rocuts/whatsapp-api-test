"""
Plantilla para el pipeline de ingestión de documentos y generación de embeddings.

Completa este script con la lógica necesaria para:
1. Leer documentos desde `rag-training/documents/`.
2. Normalizar y dividir el texto en fragmentos.
3. Invocar el modelo Gemini 1.5 Pro para obtener embeddings.
4. Guardar los artefactos resultantes en `rag-training/artifacts/`.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Iterable

DOCUMENTS_DIR = Path(__file__).resolve().parents[1] / "documents"
ARTIFACTS_DIR = Path(__file__).resolve().parents[1] / "artifacts"
EMBEDDINGS_FILE = ARTIFACTS_DIR / "embeddings.jsonl"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rag-training")


def load_documents() -> Iterable[Path]:
    """Yield all supported document paths."""
    for path in sorted(DOCUMENTS_DIR.glob("**/*")):
        if path.is_dir():
            continue
        if path.suffix.lower() not in {".txt", ".md"}:
            continue
        yield path


def create_embeddings() -> None:
    """
    Stub principal para generar embeddings.

    Sustituye el contenido de esta función con:
    - Normalización de texto.
    - Generación de embeddings vía Vertex AI (Gemini).
    - Persistencia de resultados en JSONLines.
    """
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Ingestión iniciada.")

    with EMBEDDINGS_FILE.open("w", encoding="utf-8") as handle:
        for document in load_documents():
            payload = {
                "source": str(document.relative_to(DOCUMENTS_DIR)),
                "embedding": [],
                "metadata": {},
            }
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
            logger.info("Documento registrado: %s", document.name)

    logger.info("Ingestión finalizada. Artefactos en %s", EMBEDDINGS_FILE)


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera embeddings para el RAG.")
    parser.parse_args()
    create_embeddings()


if __name__ == "__main__":
    main()
