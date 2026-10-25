"""GT-53: a ``processing`` ingestion job left behind by a dead process
(instance spin-down or restart mid-job) must recover instead of
staying stuck forever.

The worker is in-process, so a ``processing`` row found at startup
belongs to a worker that will never report again. Startup recovery
marks it failed (with an interruption error) and removes its partial
document rows, so a re-upload takes the existing failed-job path and
schedules a fresh worker — never a silent 202 with no worker behind
it. The partial-row cleanup is load-bearing: without it a re-upload's
first slice collides with the leftovers and ``persist_document_sliced``
mistakes the partial document for a concurrent winner's complete one,
marking the job succeeded with only some slices stored.

Quota pacer behaviour and the synchronous small-document path are
untouched by this change.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from test_gt1_persistence import TWO_PAGE_PDF, upload
from test_gt11_async_ingest import (
    BIG_PDF,
    ConstantEmbeddingProvider,
    _row_counts,
    _unlimited_pacer,
    _wait_for_job,
    _wire,
)

# NB: same sys.modules note as test_gt11_async_ingest — import the real
# module object, not the FastAPI object re-exported by the package.
app_module = importlib.import_module("groundtruth.api.app")
from groundtruth.api.app import (
    app,
    get_embedding_provider,
    get_generation_provider,
    get_session_factory,
)
from groundtruth.evidence import jobs
from groundtruth.evidence.db import Base
from groundtruth.ingestion.pdf import PdfLoader, StructureAwareChunker


@pytest.fixture()
def client(tmp_path):
    fake = ConstantEmbeddingProvider()
    factory = _wire(tmp_path, fake, "gt53.db")
    with TestClient(app) as test_client:
        yield test_client, fake, factory
    app.dependency_overrides.clear()


class SimulatedProcessDeath(BaseException):
    """Stands in for the process dying mid-job: unlike ``Exception`` it
    is caught by neither the sliced persist's cleanup nor the worker's
    failure handler, so partial rows remain and the job stays
    ``processing`` — exactly the interrupted state recovery must fix."""


class KillerEmbeddingProvider:
    """Embeds the first slice, then dies mid-job like a killed process."""

    provider_name = "fake-provider"
    model_name = "fake-killer-v1"

    def __init__(self) -> None:
        self.calls = 0

    def embed(self, texts):
        self.calls += 1
        if self.calls > 1:
            raise SimulatedProcessDeath("process died during slice 2")
        return [[1.0] * 8 for _ in texts]


def _capture_schedule(monkeypatch):
    captured: dict = {}

    def capture(background_tasks, fn, *args, **kwargs):
        captured["fn"] = fn
        captured["args"] = args
        captured["kwargs"] = kwargs

    monkeypatch.setattr(app_module, "schedule_ingestion", capture)
    return captured


# --------------------------------------------------------------------------
# Recovery itself: unit level
# --------------------------------------------------------------------------


def test_recovery_fails_stale_processing_jobs_and_leaves_others_alone(tmp_path):
    factory = _wire(tmp_path, ConstantEmbeddingProvider(), "gt53-unit.db")
    try:
        jobs.create_ingestion_job(
            factory,
            document_id="stale-doc",
            version_id="stale-doc:v1",
            filename="stale.pdf",
            chunks_total=250,
        )
        jobs.create_ingestion_job(
            factory,
            document_id="done-doc",
            version_id="done-doc:v1",
            filename="done.pdf",
            chunks_total=10,
        )
        jobs.update_ingestion_job(factory, "done-doc", status="succeeded", chunks_done=10)

        assert jobs.recover_stale_processing_jobs(factory) == 1
        stale = jobs.get_ingestion_job(factory, "stale-doc")
        assert stale is not None and stale.status == "failed"
        assert stale.error is not None
        assert stale.error.startswith(jobs.INTERRUPTED_ERROR_PREFIX)
        done = jobs.get_ingestion_job(factory, "done-doc")
        assert done is not None and done.status == "succeeded"

        # Idempotent: a second run finds nothing to do.
        assert jobs.recover_stale_processing_jobs(factory) == 0
    finally:
        app.dependency_overrides.clear()


# --------------------------------------------------------------------------
# Re-upload after recovery: small document (the issue's acceptance test)
# --------------------------------------------------------------------------


def test_reupload_after_recovery_succeeds_for_small_document(client):
    test_client, _fake, factory = client
    parsed = PdfLoader().load_bytes(TWO_PAGE_PDF, filename="notes.pdf")
    document_id = parsed.content_hash[:32]
    chunk_count = len(
        StructureAwareChunker().chunk(parsed, f"{document_id}:v1").chunks
    )

    # A stale processing row for this content (e.g. left by a restart).
    jobs.create_ingestion_job(
        factory,
        document_id=document_id,
        version_id=f"{document_id}:v1",
        filename="notes.pdf",
        chunks_total=chunk_count,
    )
    assert jobs.recover_stale_processing_jobs(factory) == 1
    assert jobs.get_ingestion_job(factory, document_id).status == "failed"

    # The re-upload takes the failed-job path: reset, synchronous
    # persist (small document), job marked succeeded, document listed.
    response = upload(test_client, TWO_PAGE_PDF)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "stored"
    assert body["chunks"] == chunk_count
    assert jobs.get_ingestion_job(factory, document_id).status == "succeeded"
    listed = test_client.get("/api/v1/documents").json()
    assert len(listed) == 1
    assert listed[0]["document_id"] == document_id
    assert listed[0]["chunk_count"] == chunk_count


# --------------------------------------------------------------------------
# Re-upload after recovery: large document with partial rows
# --------------------------------------------------------------------------


def test_interrupted_large_job_recovers_and_reuploads_complete(client, monkeypatch):
    test_client, _fake, factory = client
    _unlimited_pacer(monkeypatch)
    captured = _capture_schedule(monkeypatch)
    # The killer provider is live from the first upload: slice 0
    # commits, then the "process" dies during slice 1.
    app.dependency_overrides[get_embedding_provider] = lambda: KillerEmbeddingProvider()

    response = upload(test_client, BIG_PDF, filename="big.pdf")
    assert response.status_code == 202
    document_id = response.json()["document_id"]

    with pytest.raises(SimulatedProcessDeath):
        captured["fn"](*captured["args"], **captured["kwargs"])
    status = test_client.get(f"/api/v1/documents/{document_id}/ingestion").json()
    assert status["status"] == "processing"
    counts = _row_counts(factory)
    assert counts["chunks"] == 100  # slice 0 committed, then death
    assert counts["embeddings"] == 100
    assert test_client.get("/api/v1/documents").json() == []

    # Startup recovery: partial rows removed, job failed/retryable.
    assert jobs.recover_stale_processing_jobs(factory) == 1
    status = test_client.get(f"/api/v1/documents/{document_id}/ingestion").json()
    assert status["status"] == "failed"
    assert status["error"].startswith(jobs.INTERRUPTED_ERROR_PREFIX)
    counts = _row_counts(factory)
    assert counts["documents"] == 0
    assert counts["chunks"] == 0
    assert counts["embeddings"] == 0
    assert counts["jobs"] == 1  # the failed job row is kept, by design

    # Re-upload with a healthy provider: a fresh worker ingests the
    # FULL document — not the partial 100 chunks a naive retry would
    # have mistaken for a complete duplicate.
    app.dependency_overrides[get_embedding_provider] = lambda: ConstantEmbeddingProvider()
    response = upload(test_client, BIG_PDF, filename="big.pdf")
    assert response.status_code == 202
    captured["fn"](*captured["args"], **captured["kwargs"])
    job = _wait_for_job(test_client, document_id)
    assert job["status"] == "succeeded"
    assert job["chunks_done"] == 250
    listed = test_client.get("/api/v1/documents").json()
    assert len(listed) == 1
    assert listed[0]["chunk_count"] == 250


# --------------------------------------------------------------------------
# Lifespan wiring: recovery runs on app startup
# --------------------------------------------------------------------------


def test_lifespan_recovers_stale_jobs_on_startup(tmp_path, monkeypatch):
    factory = _wire(tmp_path, ConstantEmbeddingProvider(), "gt53-lifespan.db")
    try:
        jobs.create_ingestion_job(
            factory,
            document_id="stale-doc",
            version_id="stale-doc:v1",
            filename="stale.pdf",
            chunks_total=250,
        )
        # The lifespan resolves the module global at call time, so
        # pointing it at the test factory exercises the real path.
        monkeypatch.setattr(app_module, "get_session_factory", lambda: factory)
        with TestClient(app):
            pass
        job = jobs.get_ingestion_job(factory, "stale-doc")
        assert job is not None and job.status == "failed"
        assert job.error.startswith(jobs.INTERRUPTED_ERROR_PREFIX)
    finally:
        app.dependency_overrides.clear()


# --------------------------------------------------------------------------
# UI: an interrupted job says so and points at the retry (structural)
# --------------------------------------------------------------------------


def test_ui_shows_interrupted_retry_message():
    js = (Path(app_module.__file__).parent / "static" / "app.js").read_text()
    assert "Ingestion was interrupted" in js
    assert "upload the document again to retry" in js
