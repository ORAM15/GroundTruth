"""GT-61 objectives 2, 3, 5 audit: receipts, honest no's, no silent failures.

Program issue #61. These tests LOCK behaviour that already exists (no
production change in this PR) — they are the audit trail proving
objectives 2, 3 and 5 hold on the current code:

- Obj 2: every citation names the document and page it came from.
- Obj 3: every abstention path speaks in plain words, with no internal
  chunk ids leaking into user-facing text.
- Obj 5: failures surface loudly — a failed ingestion job reports its
  error through the status endpoint, an unknown job 404s instead of
  pretending, and an embedding failure during upload returns 502 with
  detail rather than a silent success.
"""

from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from test_gt1_persistence import TWO_PAGE_PDF
from test_gt2_retrieval import CitingGenerationProvider, TopicEmbeddingProvider

from groundtruth.api.app import (
    app,
    get_embedding_provider,
    get_generation_provider,
    get_session_factory,
)
from groundtruth.evidence import jobs
from groundtruth.evidence.db import Base
from groundtruth.evidence.embeddings import EmbeddingError

HEX_ID = re.compile(r"\b[0-9a-f]{32}\b")
RELEVANT_QUESTION = "How does GroundTruth stores uploaded documents as evidence?"
UNRELATED_QUESTION = "quixotic banana smoothie recipe"


class FailingEmbeddingProvider:
    """Test double whose embed always fails loudly."""

    provider_name = "fake-failing"
    model_name = "fake-failing-v1"

    def embed(self, texts):
        raise EmbeddingError("embedding provider unavailable (test)")


@pytest.fixture()
def client(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path}/gt61audit.db")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    app.dependency_overrides[get_session_factory] = lambda: factory
    app.dependency_overrides[get_embedding_provider] = lambda: TopicEmbeddingProvider()
    app.dependency_overrides[get_generation_provider] = lambda: CitingGenerationProvider()
    with TestClient(app) as test_client:
        yield test_client, factory
    app.dependency_overrides.clear()


def _upload(client, payload=TWO_PAGE_PDF, filename="notes.pdf"):
    response = client.post(
        "/api/v1/documents",
        files={"file": (filename, payload, "application/pdf")},
    )
    assert response.status_code == 200
    return response.json()


def test_citations_name_document_and_page(client):
    test_client, _factory = client
    _upload(test_client)
    listed = test_client.get("/api/v1/documents").json()
    assert len(listed) == 1
    response = test_client.post("/api/v1/query", json={"question": RELEVANT_QUESTION})
    assert response.status_code == 200
    payload = response.json()
    assert payload["decision"] == "ANSWERED"
    assert payload["citations"], "an answer must carry at least one receipt"
    evidence_by_id = {item["chunk_id"]: item for item in payload["evidence"]}
    for citation in payload["citations"]:
        assert citation["document_id"] == listed[0]["document_id"]
        assert citation["filename"] == "notes.pdf"
        assert citation["page_start"] in (1, 2)
        # The citation resolves to returned evidence with the same page.
        assert citation["chunk_id"] in evidence_by_id
        assert evidence_by_id[citation["chunk_id"]]["page_start"] == citation["page_start"]


def test_empty_store_decline_is_plain_words(client):
    test_client, _factory = client
    response = test_client.post("/api/v1/query", json={"question": RELEVANT_QUESTION})
    assert response.status_code == 200
    payload = response.json()
    assert payload["decision"] == "ABSTAIN"
    assert payload["answer"] is None
    assert payload["message"]
    assert not HEX_ID.search(payload["message"])
    assert "document" in payload["message"].lower()


def test_weak_evidence_decline_has_no_internal_ids(client):
    test_client, _factory = client
    _upload(test_client)
    response = test_client.post("/api/v1/query", json={"question": UNRELATED_QUESTION})
    assert response.status_code == 200
    payload = response.json()
    assert payload["decision"] == "ABSTAIN"
    assert payload["answer"] is None
    assert not HEX_ID.search(payload["message"])


def test_failed_job_surfaces_error_and_unknown_job_404s(client):
    test_client, factory = client
    jobs.create_ingestion_job(
        factory, document_id="doc-failed", version_id="doc-failed:v1",
        filename="failed.pdf", chunks_total=10,
    )
    jobs.update_ingestion_job(
        factory, "doc-failed", status="failed",
        error="embedding quota exhausted (test)",
    )
    response = test_client.get("/api/v1/documents/doc-failed/ingestion")
    assert response.status_code == 200
    assert response.json()["status"] == "failed"
    assert "quota exhausted" in response.json()["error"]
    assert test_client.get("/api/v1/documents/no-such-doc/ingestion").status_code == 404


def test_embedding_failure_during_upload_is_reported_not_silent(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path}/gt61fail.db")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    app.dependency_overrides[get_session_factory] = lambda: factory
    app.dependency_overrides[get_embedding_provider] = lambda: FailingEmbeddingProvider()
    try:
        with TestClient(app) as test_client:
            response = test_client.post(
                "/api/v1/documents",
                files={"file": ("notes.pdf", TWO_PAGE_PDF, "application/pdf")},
            )
            assert response.status_code == 502
            assert "embedding provider unavailable" in response.json()["detail"]
            assert test_client.get("/api/v1/documents").json() == []
    finally:
        app.dependency_overrides.clear()
