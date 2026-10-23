from __future__ import annotations

import os
from datetime import UTC, datetime
from functools import lru_cache
from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException, UploadFile
from pydantic import BaseModel, Field

from groundtruth.domain.models import Document
from groundtruth.evidence import store
from groundtruth.evidence.db import create_session_factory
from groundtruth.evidence.embeddings import (
    PROVIDER_NAME,
    EmbeddingError,
    EmbeddingProvider,
    GeminiEmbeddingProvider,
)
from groundtruth.ingestion.pdf import PdfLoader, StructureAwareChunker

app = FastAPI(title="GroundTruth", version="0.1.0")

MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB upload limit for the MVP.


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=20_000)
    top_k: int = Field(default=10, ge=1, le=100)


class QueryResponse(BaseModel):
    decision: str
    message: str


@lru_cache(maxsize=4)
def _session_factory_for(database_url: str):
    return create_session_factory(database_url)[0]


def get_session_factory():
    """FastAPI dependency: the evidence-store session factory, or ``None``
    when ``DATABASE_URL`` is not configured. Tests override this dependency
    with a factory bound to a throwaway database."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return None
    return _session_factory_for(database_url)


def get_embedding_provider() -> EmbeddingProvider | None:
    """FastAPI dependency: the configured embedding provider, or ``None``
    when no provider is configured (currently: ``GEMINI_API_KEY`` unset).
    Tests override this dependency with a deterministic fake provider."""
    if not os.getenv("GEMINI_API_KEY"):
        return None
    return GeminiEmbeddingProvider()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, str]:
    if not os.getenv("DATABASE_URL"):
        raise HTTPException(status_code=503, detail="Evidence store is not configured.")
    return {"status": "ready"}


SessionFactoryDep = Annotated[Any, Depends(get_session_factory)]
EmbeddingProviderDep = Annotated[EmbeddingProvider | None, Depends(get_embedding_provider)]


@app.post("/api/v1/documents")
async def ingest_document(
    file: UploadFile,
    session_factory: SessionFactoryDep,
    embedding_provider: EmbeddingProviderDep,
):
    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(status_code=415, detail="Only PDF uploads are supported in the MVP.")
    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Uploaded document is empty.")
    if len(payload) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Uploaded document exceeds the 25 MB limit.")
    if session_factory is None:
        raise HTTPException(
            status_code=503,
            detail="Document persistence is not configured: DATABASE_URL is not set.",
        )
    if embedding_provider is None:
        raise HTTPException(
            status_code=503,
            detail="Embeddings are not configured: GEMINI_API_KEY is not set.",
        )

    filename = file.filename or "document.pdf"
    try:
        parsed = PdfLoader().load_bytes(payload, filename=filename)
    except Exception as exc:  # pypdf raises PdfReadError and friends on bad input.
        raise HTTPException(status_code=422, detail=f"Could not parse PDF: {exc}") from exc

    # Ids are content-addressed so re-uploading identical bytes is idempotent.
    document_id = parsed.content_hash[:32]
    version_id = f"{document_id}:v1"
    version = StructureAwareChunker().chunk(parsed, version_id)
    if not version.chunks:
        raise HTTPException(
            status_code=422,
            detail="No extractable text found in the PDF; nothing to store.",
        )

    document = Document(
        document_id=document_id,
        title=parsed.title,
        source_type="pdf",
        source_uri=parsed.source_uri,
        created_at=datetime.now(UTC),
        metadata={"filename": filename, "pages": parsed.page_count},
        versions=(version,),
    )
    already = store.find_stored_version(session_factory, parsed.content_hash)
    if already is not None:
        return {
            "status": "stored",
            "document_id": already.document_id,
            "version_id": already.version_id,
            "filename": filename,
            "pages": parsed.page_count,
            "chunks": already.chunk_count,
            "duplicate": True,
        }
    try:
        vectors = embedding_provider.embed([chunk.text for chunk in version.chunks])
    except EmbeddingError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    stored = store.persist_document(
        session_factory,
        document,
        version,
        embeddings=vectors,
        model_provider=getattr(embedding_provider, "provider_name", PROVIDER_NAME),
        model_name=embedding_provider.model_name,
    )
    return {
        "status": "stored",
        "document_id": stored.document_id,
        "version_id": stored.version_id,
        "filename": filename,
        "pages": parsed.page_count,
        "chunks": stored.chunk_count,
        "duplicate": stored.duplicate,
    }


@app.post("/api/v1/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    # Trust behavior: until an evidence store is configured, never fabricate an answer.
    return QueryResponse(
        decision="ABSTAIN",
        message="No authorized evidence store is configured; GroundTruth will not fabricate an answer.",
    )
