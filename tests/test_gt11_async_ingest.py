"""GT-11: async ingestion for large documents.

Production symptom (after GT-10): a 360-chunk upload still failed live,
now with Google's free-tier quota — 100 embedded ITEMS per minute,
counted per item, not per batch call — so a multi-minute paced run is
required, which no synchronous request survives on Render's free edge.

The contract (issue #49):
* <=100 chunks: synchronous, exactly as before (200, same payload).
* >100 chunks: the endpoint parses + chunks + duplicate-checks
  synchronously, then returns 202 with a job record and ingests in a
  background task paced at <=100 items per 60s window, with bounded
  429 retries. The documents list and retrieval exclude documents whose
  jobs have not succeeded; terminal failure deletes the partial
  document and marks the job failed.

Test notes: FastAPI BackgroundTasks run sync callables in a worker
thread, so the test engines are created with ``check_same_thread=False``
(SQLite file databases would otherwise refuse a pooled connection
checked out on a different thread). Pacing is neutralised in
endpoint tests by monkeypatching ``jobs.pacer_from_env`` to an
unlimited pacer — the pacer itself is unit-tested separately with a
fake clock.
"""

from __future__ import annotations

import importlib
import re
import time
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from test_gt1_persistence import TWO_PAGE_PDF, make_pdf_bytes, upload

from groundtruth.domain.models import Document

# NB: `import groundtruth.api.app as ...` binds the FastAPI object, not
# the module, because the package __init__ re-exports `app`; go through
# sys.modules via import_module to get the real module object.
app_module = importlib.import_module("groundtruth.api.app")
from groundtruth.api.app import (
    app,
    get_embedding_provider,
    get_generation_provider,
    get_session_factory,
)
from groundtruth.evidence import jobs
from groundtruth.evidence.db import (
    Base,
    ChunkEmbeddingRow,
    ChunkRow,
    DocumentRow,
    DocumentVersionRow,
    IngestionJobRow,
)
from groundtruth.evidence.embeddings import EmbeddingError
from groundtruth.evidence.pacing import QuotaPacer, pacer_from_env
from groundtruth.ingestion.pdf import PdfLoader, StructureAwareChunker

BIG_PDF = make_pdf_bytes(
    [
        [f"Async ingestion evidence line {n} of 250." for n in range(start, start + 50)]
        for start in range(1, 251, 50)
    ]
)


class ConstantEmbeddingProvider:
    """Vectors identical for every text, so dense cosine is 1.0 and the
    retrieval gate always passes — queries in these tests assert
    visibility, not ranking."""

    provider_name = "fake-provider"
    model_name = "fake-constant-v1"

    def __init__(self) -> None:
        self.calls = 0
        self.batch_sizes: list[int] = []

    def embed(self, texts):
        self.calls += 1
        self.batch_sizes.append(len(texts))
        return [[1.0] * 8 for _ in texts]


class CitingGenerationProvider:
    """Answers citing the first evidence block in the prompt."""

    provider_name = "fake-provider"
    model_name = "fake-generation-v1"

    def generate(self, prompt: str) -> str:
        chunk_id = re.search(r'<evidence id="([^"]+)"', prompt).group(1)
        return f"Grounded answer citing the evidence [{chunk_id}]."


def _wire(tmp_path, provider, db_name: str):
    engine = create_engine(
        f"sqlite:///{tmp_path}/{db_name}", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    app.dependency_overrides[get_session_factory] = lambda: factory
    app.dependency_overrides[get_embedding_provider] = lambda: provider
    app.dependency_overrides[get_generation_provider] = lambda: CitingGenerationProvider()
    return factory


@pytest.fixture()
def client(tmp_path):
    fake = ConstantEmbeddingProvider()
    factory = _wire(tmp_path, fake, "gt11.db")
    with TestClient(app) as test_client:
        yield test_client, fake, factory
    app.dependency_overrides.clear()


def _unlimited_pacer(monkeypatch) -> None:
    """Neutralise quota pacing for endpoint tests (the pacer itself is
    unit-tested below with a fake clock)."""
    monkeypatch.setattr(
        jobs,
        "pacer_from_env",
        lambda: QuotaPacer(max_items_per_window=10**9, window_seconds=60.0),
    )


def _wait_for_job(test_client, document_id: str, timeout: float = 20.0) -> dict:
    """Poll the status endpoint until the job reaches a terminal state."""
    deadline = time.monotonic() + timeout
    while True:
        response = test_client.get(f"/api/v1/documents/{document_id}/ingestion")
        assert response.status_code == 200, response.text
        body = response.json()
        if body["status"] in ("succeeded", "failed"):
            return body
        assert time.monotonic() < deadline, f"job stuck: {body}"
        time.sleep(0.1)


def _row_counts(factory) -> dict:
    session = factory()
    try:
        return {
            "documents": session.query(DocumentRow).count(),
            "versions": session.query(DocumentVersionRow).count(),
            "chunks": session.query(ChunkRow).count(),
            "embeddings": session.query(ChunkEmbeddingRow).count(),
            "jobs": session.query(IngestionJobRow).count(),
        }
    finally:
        session.close()


def _ask(test_client, question: str) -> dict:
    response = test_client.post("/api/v1/query", json={"question": question})
    assert response.status_code == 200, response.text
    return response.json()


# --------------------------------------------------------------------------
# Small documents stay synchronous
# --------------------------------------------------------------------------


def test_small_doc_stays_synchronous(client):
    test_client, _fake, _factory = client
    response = upload(test_client, TWO_PAGE_PDF)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "stored"
    assert body["duplicate"] is False
    assert set(body) == {
        "status",
        "document_id",
        "version_id",
        "filename",
        "pages",
        "chunks",
        "duplicate",
    }

    listed = test_client.get("/api/v1/documents").json()
    assert len(listed) == 1
    assert listed[0]["document_id"] == body["document_id"]

    # Synchronous ingests create no job row: the status endpoint 404s.
    status = test_client.get(f"/api/v1/documents/{body['document_id']}/ingestion")
    assert status.status_code == 404


# --------------------------------------------------------------------------
# Large documents: 202 + background completion through the real path
# --------------------------------------------------------------------------


def test_large_doc_returns_202_and_completes(client, monkeypatch):
    test_client, fake, _factory = client
    _unlimited_pacer(monkeypatch)

    response = upload(test_client, BIG_PDF, filename="big.pdf")
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "processing"
    assert set(body) == {"status", "document_id", "version_id", "filename", "pages", "chunks"}
    assert body["pages"] == 5
    assert body["chunks"] == 250

    job = _wait_for_job(test_client, body["document_id"])
    assert job["status"] == "succeeded"
    assert job["chunks_done"] == 250
    assert job["chunks_total"] == 250
    assert fake.batch_sizes == [100, 100, 50]

    listed = test_client.get("/api/v1/documents").json()
    assert len(listed) == 1
    assert listed[0]["chunk_count"] == 250

    answer = _ask(test_client, "What does async ingestion evidence line 42 say?")
    assert answer["decision"] == "ANSWERED"
    assert answer["citations"]


# --------------------------------------------------------------------------
# Processing state is observable; retrieval excludes partial documents
# --------------------------------------------------------------------------


def test_processing_doc_hidden_until_job_completes(client, monkeypatch):
    test_client, _fake, _factory = client
    _unlimited_pacer(monkeypatch)

    captured: dict = {}

    def capture(background_tasks, fn, *args, **kwargs):
        captured["fn"] = fn
        captured["args"] = args
        captured["kwargs"] = kwargs

    monkeypatch.setattr(app_module, "schedule_ingestion", capture)

    response = upload(test_client, BIG_PDF, filename="big.pdf")
    assert response.status_code == 202
    document_id = response.json()["document_id"]
    assert captured["fn"] is jobs.run_ingestion_job

    status = test_client.get(f"/api/v1/documents/{document_id}/ingestion").json()
    assert status["status"] == "processing"
    assert status["chunks_done"] == 0
    assert status["chunks_total"] == 250

    # The processing document is listed nowhere and answered from nowhere.
    assert test_client.get("/api/v1/documents").json() == []
    answer = _ask(test_client, "What does async ingestion evidence line 42 say?")
    assert answer["decision"] == "ABSTAIN"

    # Run the captured worker directly: the job completes and the
    # document becomes visible and answerable.
    captured["fn"](*captured["args"], **captured["kwargs"])
    status = test_client.get(f"/api/v1/documents/{document_id}/ingestion").json()
    assert status["status"] == "succeeded"
    assert status["chunks_done"] == 250
    listed = test_client.get("/api/v1/documents").json()
    assert len(listed) == 1
    assert listed[0]["chunk_count"] == 250
    answer = _ask(test_client, "What does async ingestion evidence line 42 say?")
    assert answer["decision"] == "ANSWERED"
    assert answer["citations"]


# --------------------------------------------------------------------------
# 429 retry, then success (direct worker invocation)
# --------------------------------------------------------------------------


class Flaky429Provider:
    """Fails the first embed call with a 429, then behaves."""

    provider_name = "fake-provider"
    model_name = "fake-flaky-v1"

    def __init__(self) -> None:
        self.calls = 0

    def embed(self, texts):
        self.calls += 1
        if self.calls == 1:
            raise EmbeddingError(
                "Gemini embedding request failed with HTTP 429: quota",
                status_code=429,
                retry_after=0,
            )
        return [[1.0] * 8 for _ in texts]


def _document_and_version():
    parsed = PdfLoader().load_bytes(BIG_PDF, filename="big.pdf")
    version = StructureAwareChunker().chunk(parsed, "flaky:v1")
    document = Document(
        document_id="flaky-doc",
        title="big",
        source_type="pdf",
        source_uri="big.pdf",
        created_at=datetime.now(UTC),
        metadata={"filename": "big.pdf", "pages": 5},
        versions=(version,),
    )
    return document, version


def test_429_retry_then_success(tmp_path):
    factory = _wire(tmp_path, Flaky429Provider(), "gt11-429.db")
    try:
        _test_429_retry_then_success(factory)
    finally:
        app.dependency_overrides.clear()


def _test_429_retry_then_success(factory):
    document, version = _document_and_version()
    jobs.create_ingestion_job(
        factory,
        document_id=document.document_id,
        version_id=version.version_id,
        filename="big.pdf",
        chunks_total=len(version.chunks),
    )
    # The fake clock advances on sleep (a fixed clock would make the
    # slice-3 window wait loop forever, appending sleeps unboundedly).
    now = [0.0]
    sleeps: list[float] = []

    def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)
        now[0] += seconds

    pacer = QuotaPacer(
        max_items_per_window=100,
        window_seconds=60.0,
        sleep_fn=fake_sleep,
        clock_fn=lambda: now[0],
    )
    provider = Flaky429Provider()
    jobs.run_ingestion_job(
        factory,
        provider,
        document,
        version,
        model_provider="fake-provider",
        model_name="fake-flaky-v1",
        pacer=pacer,
    )
    # First slice retried once (429, then success); the other two slices
    # embedded once each.
    assert provider.calls == 4
    # The 429 had retry_after=0, so the pacer waited out the window
    # (first 60s); slice 3 then needed a fresh window (second 60s).
    assert sleeps == [60.0, 60.0]
    job = jobs.get_ingestion_job(factory, document.document_id)
    assert job is not None and job.status == "succeeded"
    assert job.chunks_done == 250
    counts = _row_counts(factory)
    assert counts["chunks"] == 250
    assert counts["embeddings"] == 250


def test_embed_with_retry_bounds_and_backoff():
    sleeps: list[float] = []

    def always_429(texts):
        raise EmbeddingError("quota", status_code=429, retry_after=7)

    pacer = QuotaPacer(sleep_fn=sleeps.append, clock_fn=lambda: 0.0)
    with pytest.raises(EmbeddingError, match="quota"):
        jobs.embed_with_retry(always_429, ["a"], pacer, max_retries=5)
    # 1 initial attempt + 5 retries = 6 calls; each 429 sleeps retry_after.
    assert sleeps == [7.0, 7.0, 7.0, 7.0, 7.0]

    def not_rate_limited(texts):
        raise EmbeddingError("bad request", status_code=400)

    sleeps.clear()
    with pytest.raises(EmbeddingError, match="bad request"):
        jobs.embed_with_retry(not_rate_limited, ["a"], pacer, max_retries=5)
    assert sleeps == []  # non-429 errors are never retried


def test_pacer_windows_with_fake_clock():
    # The fake clock must advance when sleep is called — otherwise a
    # window wait would loop forever (this test once OOM-killed a run).
    now = [0.0]
    sleeps: list[float] = []

    def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)
        now[0] += seconds

    pacer = QuotaPacer(
        max_items_per_window=100,
        window_seconds=60.0,
        sleep_fn=fake_sleep,
        clock_fn=lambda: now[0],
    )
    pacer.acquire(60)
    assert sleeps == []
    pacer.acquire(60)  # 120 > 100: waits out the window, then fits
    assert sleeps == [60.0]
    assert now[0] == 60.0
    pacer.acquire(60)  # window used again: waits out the new window
    assert sleeps == [60.0, 60.0]
    # An oversized request gets a fresh window to itself, not a deadlock.
    pacer.acquire(150)
    assert sleeps == [60.0, 60.0, 60.0]


# --------------------------------------------------------------------------
# Terminal failure: no partial document, job failed
# --------------------------------------------------------------------------


class AlwaysFailingProvider:
    provider_name = "fake-provider"
    model_name = "fake-failing-v1"

    def embed(self, texts):
        raise EmbeddingError("injected terminal failure (GT-11 test)")


def test_terminal_failure_leaves_no_partial_document(client, monkeypatch):
    test_client, _fake, factory = client
    _unlimited_pacer(monkeypatch)

    captured: dict = {}

    def capture(background_tasks, fn, *args, **kwargs):
        captured["fn"] = fn
        captured["args"] = args
        captured["kwargs"] = kwargs

    monkeypatch.setattr(app_module, "schedule_ingestion", capture)
    app.dependency_overrides[get_embedding_provider] = lambda: AlwaysFailingProvider()

    response = upload(test_client, BIG_PDF, filename="big.pdf")
    assert response.status_code == 202
    document_id = response.json()["document_id"]

    # The worker records the failure in the job row and does not
    # re-raise (the job row is the durable error record).
    captured["fn"](*captured["args"], **captured["kwargs"])

    status = test_client.get(f"/api/v1/documents/{document_id}/ingestion").json()
    assert status["status"] == "failed"
    assert "injected terminal failure" in (status["error"] or "")
    assert test_client.get("/api/v1/documents").json() == []
    counts = _row_counts(factory)
    assert counts["documents"] == 0
    assert counts["versions"] == 0
    assert counts["chunks"] == 0
    assert counts["embeddings"] == 0
    assert counts["jobs"] == 1  # the failed job row is kept, by design


# --------------------------------------------------------------------------
# UI: 202 handling + polling (structural)
# --------------------------------------------------------------------------


def test_ui_handles_202_and_polls_ingestion_status():
    js = (Path(app_module.__file__).parent / "static" / "app.js").read_text()
    assert "/ingestion" in js
    assert "setInterval" in js
    assert "202" in js
    assert "processing" in js


def test_pacer_from_env_defaults_and_overrides(monkeypatch):
    monkeypatch.delenv("GT_EMBED_RATE_WINDOW_SECONDS", raising=False)
    monkeypatch.delenv("GT_EMBED_RATE_MAX_ITEMS", raising=False)
    pacer = pacer_from_env()
    assert pacer._window == 60.0
    assert pacer._max_items == 100
    monkeypatch.setenv("GT_EMBED_RATE_WINDOW_SECONDS", "0.5")
    monkeypatch.setenv("GT_EMBED_RATE_MAX_ITEMS", "10")
    pacer = pacer_from_env()
    assert pacer._window == 0.5
    assert pacer._max_items == 10
    monkeypatch.setenv("GT_EMBED_RATE_WINDOW_SECONDS", "not-a-number")
    pacer = pacer_from_env()
    assert pacer._window == 60.0
