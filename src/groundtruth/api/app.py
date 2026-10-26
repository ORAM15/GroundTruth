from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from groundtruth.domain.models import Document
from groundtruth.evidence import jobs, store
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
from groundtruth.generation.guidance import (
    guidance_examples,
    guidance_message,
    is_topicless_question,
)
from groundtruth.ingestion.pdf import PdfLoader, StructureAwareChunker
from groundtruth.retrieval import service as retrieval_service

@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Startup recovery for stale ingestion jobs (issue #53).

    The ingestion worker is in-process, so a ``processing`` job cannot
    survive a restart by definition — yet before this handler such a
    row stayed ``processing`` forever, and a re-upload returned 202
    with no worker behind it. Recovering at startup restores the
    invariant every later request relies on: a ``processing`` job
    either has a live worker in this process or does not exist.
    Recovery is deliberately never fatal: if the store is unreachable
    at boot, the app still starts and the next restart retries.
    (``get_session_factory`` is defined below but resolved at call
    time, when the module is fully loaded.)
    """
    try:
        session_factory = get_session_factory()
        if session_factory is not None:
            recovered = jobs.recover_stale_processing_jobs(session_factory)
            if recovered:
                logging.getLogger(__name__).info(
                    "Recovered %d stale ingestion job(s)", recovered
                )
    except Exception:
        logging.getLogger(__name__).exception(
            "Stale ingestion-job recovery failed at startup"
        )
    yield


app = FastAPI(title="GroundTruth", version="0.1.0", lifespan=lifespan)

logger = logging.getLogger(__name__)

MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB upload limit for the MVP.

STATIC_DIR = Path(__file__).parent / "static"


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=20_000)
    top_k: int = Field(default=10, ge=1, le=100)
    # Issue #65: optional scope — when set, retrieval considers ONLY
    # this document's chunks. Unset means library-wide, exactly as
    # before. An unknown id is rejected (404) before any other path.
    document_id: str | None = None


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


class GuidanceInfo(BaseModel):
    """Topic-less question guidance (GT-61 objective 4): stored document
    titles and example-question templates derived from those titles
    only. Carries no summary content and no citations by design."""

    documents: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)


class CoverageItem(BaseModel):
    """Issue #67: one document's contribution to an answer's evidence
    set — the document id, its display title, and how many of the
    returned evidence chunks came from it. Computed server-side from
    the returned hits, so the UI strip cannot drift from the evidence
    the answer was actually grounded in."""

    document_id: str
    title: str | None = None
    chunk_count: int


class QueryResponse(BaseModel):
    decision: str
    message: str
    evidence: list[EvidenceItem] = Field(default_factory=list)
    answer: str | None = None
    citations: list[EvidenceItem] = Field(default_factory=list)
    guidance: GuidanceInfo | None = None
    coverage: list[CoverageItem] = Field(default_factory=list)


class DocumentListItem(BaseModel):
    document_id: str
    title: str
    filename: str | None = None
    pages: int | None = None
    chunk_count: int
    created_at: datetime | None = None


class IngestionJobResponse(BaseModel):
    document_id: str
    version_id: str
    filename: str | None = None
    status: str
    chunks_done: int
    chunks_total: int
    error: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


def schedule_ingestion(background_tasks: BackgroundTasks, fn, *args, **kwargs) -> None:
    """Schedule a background task, indirection point for tests.

    Production delegates to FastAPI's BackgroundTasks; tests override
    this function to capture the scheduled callable without running it,
    so the ``processing`` state is observable deterministically.
    """
    background_tasks.add_task(fn, *args, **kwargs)


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


@app.get("/")
def index() -> FileResponse:
    """The one-page UI. A single static page; all data comes from the
    JSON API below, and the page renders document-derived text only via
    textContent (documents are untrusted input)."""
    return FileResponse(STATIC_DIR / "index.html", media_type="text/html")


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

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/api/v1/documents", response_model=list[DocumentListItem])
def list_documents(session_factory: SessionFactoryDep) -> list[DocumentListItem]:
    if session_factory is None:
        raise HTTPException(
            status_code=503,
            detail="Document store is not configured: DATABASE_URL is not set.",
        )
    return [
        DocumentListItem(
            document_id=summary.document_id,
            title=summary.title,
            filename=summary.filename,
            pages=summary.pages,
            chunk_count=summary.chunk_count,
            created_at=summary.created_at,
        )
        for summary in store.list_documents(session_factory)
    ]


@app.post("/api/v1/documents")
async def ingest_document(
    file: UploadFile,
    background_tasks: BackgroundTasks,
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
    # A job row, when one exists, is the authority on this content's
    # state — it is checked BEFORE the version rows, because a
    # partially ingested document already has version rows committed
    # (slice 0) and must not be reported as a stored duplicate.
    job = jobs.get_ingestion_job(session_factory, document_id)
    if job is not None and job.status == "processing":
        return JSONResponse(
            status_code=202,
            content={
                "status": "processing",
                "document_id": document_id,
                "version_id": version_id,
                "filename": filename,
                "pages": parsed.page_count,
                "chunks": len(version.chunks),
            },
        )
    # A failed job's partial document was deleted by its worker, so the
    # content is ingestible again — but the duplicate check below must
    # be skipped for it (there are no rows to find, and the job row
    # itself is the record of this content).
    skip_duplicate_check = job is not None and job.status == "failed"
    if skip_duplicate_check:
        jobs.reset_ingestion_job(session_factory, document_id)
        job = None
    if not skip_duplicate_check:
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
    # Small documents (one slice) stay synchronous, exactly as before:
    # same endpoint behaviour, same 200 payload. Large documents go
    # async (GT-11): the free-tier quota (~100 embedded items/minute)
    # makes their embedding take minutes, which no synchronous request
    # survives on Render's free edge — so the endpoint records a job,
    # returns 202, and the worker paces the slices in the background.
    model_provider = getattr(embedding_provider, "provider_name", PROVIDER_NAME)
    model_name = embedding_provider.model_name
    if len(version.chunks) <= store.INGEST_SLICE_SIZE:
        try:
            stored = store.persist_document_sliced(
                session_factory,
                document,
                version,
                embed_slice=embedding_provider.embed,
                model_provider=model_provider,
                model_name=model_name,
            )
        except EmbeddingError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        # Defensive, and a no-op when no job row exists: a failed job
        # was reset above and the content fit in one slice after all,
        # so the document is complete and the job must not stay
        # "processing" and hide it.
        jobs.update_ingestion_job(
            session_factory,
            document_id,
            status="succeeded",
            chunks_done=stored.chunk_count,
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
    jobs.create_ingestion_job(
        session_factory,
        document_id=document_id,
        version_id=version_id,
        filename=filename,
        chunks_total=len(version.chunks),
    )
    schedule_ingestion(
        background_tasks,
        jobs.run_ingestion_job,
        session_factory,
        embedding_provider,
        document,
        version,
        model_provider=model_provider,
        model_name=model_name,
    )
    return JSONResponse(
        status_code=202,
        content={
            "status": "processing",
            "document_id": document_id,
            "version_id": version_id,
            "filename": filename,
            "pages": parsed.page_count,
            "chunks": len(version.chunks),
        },
    )


@app.get(
    "/api/v1/documents/{document_id}/ingestion",
    response_model=IngestionJobResponse,
)
def ingestion_status(document_id: str, session_factory: SessionFactoryDep):
    """Report a background ingestion job, or 404 when the document has
    no job row (synchronous ingests never create one)."""
    if session_factory is None:
        raise HTTPException(
            status_code=503,
            detail="Document store is not configured: DATABASE_URL is not set.",
        )
    job = jobs.get_ingestion_job(session_factory, document_id)
    if job is None:
        raise HTTPException(
            status_code=404, detail="No ingestion job for this document."
        )
    return IngestionJobResponse(
        document_id=job.document_id,
        version_id=job.version_id,
        filename=job.filename,
        status=job.status,
        chunks_done=job.chunks_done,
        chunks_total=job.chunks_total,
        error=job.error,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


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
    # Issue #65: an unknown scope fails loudly before any other path
    # runs — including guidance — so no path can silently answer from
    # a document the user did not scope to.
    if request.document_id is not None and not store.document_exists(
        session_factory, request.document_id
    ):
        raise HTTPException(
            status_code=404,
            detail=(
                f"Unknown document id: {request.document_id}; no scoped "
                "search was performed."
            ),
        )
    # GT-61 objective 4: a topic-less question has nothing to ground an
    # answer in, so it gets guidance instead of a bare decline — but
    # only when something is actually stored (an empty library still
    # takes the normal path and its honest empty-store abstention).
    # Guidance needs no embedding or generation provider, so it is
    # answered before either is consulted. A scoped question gets
    # guidance about the scoped document only; a scoped document still
    # processing is not listed, so it falls through to the normal path
    # and its scoped "still being ingested" abstention.
    if is_topicless_question(request.question):
        stored = store.list_documents(session_factory)
        if request.document_id is not None:
            stored = [doc for doc in stored if doc.document_id == request.document_id]
        if stored:
            titles = [doc.title for doc in stored]
            return QueryResponse(
                decision="GUIDANCE",
                message=guidance_message(len(titles)),
                guidance=GuidanceInfo(documents=titles, examples=guidance_examples(titles)),
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
            document_id=request.document_id,
        )
    except retrieval_service.UnknownDocumentError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
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
        # GT-51: the detailed reason names internal chunk ids — it is
        # developer detail, so it goes to the server log only. The
        # user-facing message must be a clean sentence with no ids.
        logger.warning("Citation verification failed: %s", verification.reason)
        return QueryResponse(
            decision="ABSTAIN",
            message=(
                "The draft answer could not be verified against the "
                "retrieved evidence (citation verification failed), so it "
                "was withheld rather than shown unverified."
            ),
        )
    by_chunk_id = {item.chunk_id: item for item in evidence}
    citations = [by_chunk_id[chunk_id] for chunk_id in verification.cited_ids]
    # Issue #67: the coverage strip travels with the answer — per
    # document chunk counts over the returned evidence set.
    coverage = [
        CoverageItem(
            document_id=entry.document_id,
            title=entry.title,
            chunk_count=entry.chunk_count,
        )
        for entry in outcome.coverage
    ]
    return QueryResponse(
        decision="ANSWERED",
        message=(
            f"Answered from {len(citations)} cited source(s); every citation "
            "was verified against the retrieved evidence."
        ),
        evidence=evidence,
        answer=answer,
        citations=citations,
        coverage=coverage,
    )
