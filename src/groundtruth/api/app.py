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
from groundtruth.generation import (
    EvidencePassage,
    GeminiGenerationProvider,
    GenerationError,
    GenerationProvider,
    build_grounded_prompt,
    verify_citations,
)
from groundtruth.ingestion.pdf import PdfLoader, StructureAwareChunker
from groundtruth.retrieval import service as retrieval_service

app = FastAPI(title="GroundTruth", version="0.1.0")

MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB upload limit for the MVP.


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=20_000)
    top_k: int = Field(default=10, ge=1, le=100)


class EvidenceItem(BaseModel):
    chunk_id: str
    document_id: str
    title: str | None = None
    filename: str | None = None
    page_start: int | None = None
    page_end: int | None = None
    score: float  # Fused hybrid (RRF) score of the returned ranking.
    dense_score: float | None = None  # Raw dense cosine similarity for this chunk.
    lexical_rank: int | None = None
    dense_rank: int | None = None
    method: str
    snippet: str


class QueryResponse(BaseModel):
    decision: str
    message: str
    evidence: list[EvidenceItem] = Field(default_factory=list)
    answer: str | None = None
    citations: list[EvidenceItem] = Field(default_factory=list)


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


def get_generation_provider() -> GenerationProvider | None:
    """FastAPI dependency: the configured generation provider, or ``None``
    when no provider is configured (currently: ``GEMINI_API_KEY`` unset).
    Tests override this dependency with a deterministic fake provider."""
    if not os.getenv("GEMINI_API_KEY"):
        return None
    return GeminiGenerationProvider()


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
GenerationProviderDep = Annotated[GenerationProvider | None, Depends(get_generation_provider)]


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


SNIPPET_CHARS = 300


@app.post("/api/v1/query", response_model=QueryResponse)
def query(
    request: QueryRequest,
    session_factory: SessionFactoryDep,
    embedding_provider: EmbeddingProviderDep,
    generation_provider: GenerationProviderDep,
) -> QueryResponse:
    # Trust behavior: until an evidence store is configured, never fabricate an answer.
    if session_factory is None:
        return QueryResponse(
            decision="ABSTAIN",
            message="No authorized evidence store is configured; GroundTruth will not fabricate an answer.",
        )
    if embedding_provider is None:
        raise HTTPException(
            status_code=503,
            detail="Embeddings are not configured: GEMINI_API_KEY is not set.",
        )
    try:
        outcome = retrieval_service.search(
            session_factory,
            embedding_provider,
            request.question,
            top_k=request.top_k,
        )
    except EmbeddingError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    # The generation provider is only consulted past this gate: every
    # abstention path above returns without calling it.
    if not outcome.sufficient:
        return QueryResponse(decision="ABSTAIN", message=outcome.reason)
    if generation_provider is None:
        raise HTTPException(
            status_code=503,
            detail="Answer generation is not configured: GEMINI_API_KEY is not set.",
        )
    evidence = [
        EvidenceItem(
            chunk_id=hit.result.chunk.chunk_id,
            document_id=hit.document_id,
            title=hit.title,
            filename=hit.filename,
            page_start=hit.result.chunk.page_start,
            page_end=hit.result.chunk.page_end,
            score=hit.result.score,
            dense_score=hit.dense_score,
            lexical_rank=hit.result.lexical_rank,
            dense_rank=hit.result.dense_rank,
            method=hit.result.method,
            snippet=hit.result.chunk.text[:SNIPPET_CHARS],
        )
        for hit in outcome.hits
    ]
    # The prompt is built from the chunks' FULL text — the EvidenceItem
    # snippet is a display truncation and would ground answers in fragments.
    prompt = build_grounded_prompt(
        request.question,
        [
            EvidencePassage(chunk_id=hit.result.chunk.chunk_id, text=hit.result.chunk.text)
            for hit in outcome.hits
        ],
    )
    try:
        answer = generation_provider.generate(prompt)
    except GenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    # Trust gate: an answer is returned only if every citation it makes
    # resolves to a chunk that was actually retrieved. Unverifiable text is
    # never returned as an answer; the query abstains instead.
    verification = verify_citations(answer, {item.chunk_id for item in evidence})
    if not verification.ok:
        return QueryResponse(
            decision="ABSTAIN",
            message=(
                f"Generated answer failed citation verification ({verification.reason}); "
                "abstaining rather than returning an unverifiable answer."
            ),
        )
    by_chunk_id = {item.chunk_id: item for item in evidence}
    citations = [by_chunk_id[chunk_id] for chunk_id in verification.cited_ids]
    return QueryResponse(
        decision="ANSWERED",
        message=(
            f"Answered from {len(citations)} cited source(s); every citation "
            "was verified against the retrieved evidence."
        ),
        evidence=evidence,
        answer=answer,
        citations=citations,
    )
