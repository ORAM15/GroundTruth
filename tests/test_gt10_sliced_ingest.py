"""GT-10: large-document ingestion is sliced into bounded commits.

Production symptom (after GT-9): a 46-page / 966-chunk PDF still failed
with a detail-less 502 — Render's edge gave up on a request that embedded
everything and then wrote ~37 MB of embedding parameters in ONE
transaction — and nothing was stored.

The upload path now embeds + commits at most ``store.INGEST_SLICE_SIZE``
chunks per slice (``persist_document_sliced``):

* a 250-chunk upload succeeds and the store holds every chunk + embedding;
* the provider is called once per slice with bounded batch sizes;
* if a later slice fails, the partially stored document is deleted — the
  store keeps no trace of it — and the original error surfaces (502);
* duplicate uploads still short-circuit before any embedding call.

Chunking note: the generated PDF below has one text line per chunk in the
ingestion pipeline (same behaviour the GT-1 fixtures rely on), so 5 pages
of 50 lines produce exactly 250 chunks.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from test_gt1_persistence import TWO_PAGE_PDF, FakeEmbeddingProvider, make_pdf_bytes, upload

from groundtruth.api.app import app, get_embedding_provider, get_session_factory
from groundtruth.evidence import store
from groundtruth.evidence.db import (
    Base,
    ChunkEmbeddingRow,
    ChunkRow,
    DocumentRow,
    DocumentVersionRow,
)
from groundtruth.evidence.embeddings import EmbeddingError

BIG_PDF = make_pdf_bytes(
    [
        [f"Sliced ingestion evidence line {n} of 250." for n in range(start, start + 50)]
        for start in range(1, 251, 50)
    ]
)


class RecordingProvider(FakeEmbeddingProvider):
    """Fake provider that also records the size of every embed batch."""

    def __init__(self) -> None:
        super().__init__()
        self.batch_sizes: list[int] = []

    def embed(self, texts):
        self.batch_sizes.append(len(texts))
        return super().embed(texts)


class FailOnCallProvider(FakeEmbeddingProvider):
    """Fake provider that raises EmbeddingError on the Nth embed call
    (1-based). ``probe`` runs just before the failure is raised, letting a
    test observe what earlier slices have already committed."""

    def __init__(self, fail_on_call: int, probe=None) -> None:
        super().__init__()
        self.fail_on_call = fail_on_call
        self.probe = probe
        self.probe_results: list[int] = []

    def embed(self, texts):
        if self.calls == self.fail_on_call - 1:
            self.calls += 1
            if self.probe is not None:
                self.probe_results.append(self.probe())
            raise EmbeddingError("injected embedding failure (GT-10 test)")
        return super().embed(texts)


def _wire(tmp_path, provider, db_name: str):
    engine = create_engine(f"sqlite:///{tmp_path}/{db_name}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    app.dependency_overrides[get_session_factory] = lambda: factory
    app.dependency_overrides[get_embedding_provider] = lambda: provider
    return factory


@pytest.fixture()
def client(tmp_path):
    fake = RecordingProvider()
    factory = _wire(tmp_path, fake, "gt10.db")
    with TestClient(app) as test_client:
        yield test_client, fake, factory
    app.dependency_overrides.clear()


@pytest.fixture()
def failing_client(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path}/gt10-fail.db")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)

    def committed_chunk_count() -> int:
        session = factory()
        try:
            return session.query(ChunkRow).count()
        finally:
            session.close()

    fake = FailOnCallProvider(fail_on_call=2, probe=committed_chunk_count)
    app.dependency_overrides[get_session_factory] = lambda: factory
    app.dependency_overrides[get_embedding_provider] = lambda: fake
    with TestClient(app) as test_client:
        yield test_client, fake, factory
    app.dependency_overrides.clear()


def all_row_counts(factory):
    session = factory()
    try:
        return {
            "documents": session.query(DocumentRow).count(),
            "versions": session.query(DocumentVersionRow).count(),
            "chunks": session.query(ChunkRow).count(),
            "embeddings": session.query(ChunkEmbeddingRow).count(),
        }
    finally:
        session.close()


# --------------------------------------------------------------------------
# Multi-slice ingest
# --------------------------------------------------------------------------


def test_multi_slice_upload_commits_every_chunk_and_embedding(client):
    test_client, fake, factory = client
    response = upload(test_client, BIG_PDF, filename="big.pdf")
    assert response.status_code == 200
    body = response.json()
    # Response payload shape is unchanged from the pre-slicing flow.
    assert set(body) == {
        "status",
        "document_id",
        "version_id",
        "filename",
        "pages",
        "chunks",
        "duplicate",
    }
    assert body["status"] == "stored"
    assert body["duplicate"] is False
    assert body["filename"] == "big.pdf"
    assert body["pages"] == 5
    assert body["chunks"] == 250

    # The provider saw one call per slice, each within the slice bound.
    assert store.INGEST_SLICE_SIZE == 100
    assert fake.batch_sizes == [100, 100, 50]
    assert fake.calls == 3

    assert all_row_counts(factory) == {
        "documents": 1,
        "versions": 1,
        "chunks": 250,
        "embeddings": 250,
    }
    session = factory()
    try:
        chunk_ids = {row.id for row in session.query(ChunkRow).all()}
        embeddings = session.query(ChunkEmbeddingRow).all()
        # Every embedding resolves to a stored chunk, and vice versa.
        assert {row.chunk_id for row in embeddings} == chunk_ids
        ordinals = sorted(row.ordinal for row in session.query(ChunkRow).all())
        assert ordinals == list(range(1, 251))
    finally:
        session.close()


# --------------------------------------------------------------------------
# Failure in a later slice: no partial document survives
# --------------------------------------------------------------------------


def test_failed_slice_leaves_no_partial_document(failing_client):
    test_client, fake, factory = failing_client
    response = upload(test_client, BIG_PDF, filename="big.pdf")
    # The original embedding error surfaces exactly as before: 502 + detail.
    assert response.status_code == 502
    assert "injected embedding failure" in response.json()["detail"]
    assert fake.calls == 2
    # The probe proves slice 1 had genuinely COMMITTED its 100 chunks
    # before slice 2 failed — so the empty store below is the cleanup's
    # doing, not a transaction that never landed.
    assert fake.probe_results == [100]
    assert all_row_counts(factory) == {
        "documents": 0,
        "versions": 0,
        "chunks": 0,
        "embeddings": 0,
    }


# --------------------------------------------------------------------------
# Duplicates still short-circuit before any embedding call
# --------------------------------------------------------------------------


def test_duplicate_upload_makes_no_additional_embedding_calls(client):
    test_client, fake, factory = client
    first = upload(test_client, BIG_PDF, filename="big.pdf")
    assert first.status_code == 200
    counts_after_first = all_row_counts(factory)
    calls_after_first = fake.calls
    batches_after_first = list(fake.batch_sizes)

    second = upload(test_client, BIG_PDF, filename="big-again.pdf")
    assert second.status_code == 200
    body = second.json()
    assert body["duplicate"] is True
    assert body["document_id"] == first.json()["document_id"]
    assert body["version_id"] == first.json()["version_id"]
    assert body["chunks"] == first.json()["chunks"] == 250
    assert fake.calls == calls_after_first
    assert fake.batch_sizes == batches_after_first
    assert all_row_counts(factory) == counts_after_first


# --------------------------------------------------------------------------
# delete_document: the cleanup primitive itself
# --------------------------------------------------------------------------


def test_delete_document_removes_everything_and_is_idempotent(client):
    test_client, _fake, factory = client
    response = upload(test_client, TWO_PAGE_PDF)
    assert response.status_code == 200
    document_id = response.json()["document_id"]
    assert all_row_counts(factory) == {
        "documents": 1,
        "versions": 1,
        "chunks": 4,
        "embeddings": 4,
    }

    store.delete_document(factory, document_id)
    assert all_row_counts(factory) == {
        "documents": 0,
        "versions": 0,
        "chunks": 0,
        "embeddings": 0,
    }
    # Deleting a missing document is a no-op, not an error.
    store.delete_document(factory, document_id)
    assert all_row_counts(factory)["documents"] == 0
