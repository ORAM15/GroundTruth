"""GT-8: production upload 500 — FK violation on chunk_embeddings insert.

Root cause (from the production Render traceback): ``persist_document``
added Document -> Version -> Chunks -> Embeddings and issued a single
``commit()``. ``ChunkEmbeddingRow`` has an FK to ``chunks.id`` but no ORM
relationship to ``ChunkRow``, so the unit of work had no dependency
information to order the cross-table inserts, and Postgres — which enforces
FKs — rejected embeddings flushed before their chunks.

Local tests never caught this because SQLite does not enforce foreign keys
unless ``PRAGMA foreign_keys=ON`` is set per connection.

These tests pin both halves of the fix:

* ``create_session_factory`` turns FK enforcement ON for SQLite engines, so
  local behaviour matches Postgres.
* ``persist_document`` inserts deterministically (flush document+version,
  flush chunks, then embeddings), so a persist with embeddings succeeds
  under enforcement and every stored embedding resolves to a stored chunk.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from test_gt1_persistence import TWO_PAGE_PDF, FakeEmbeddingProvider

from groundtruth.api.app import app, get_embedding_provider, get_session_factory
from groundtruth.domain.models import Document
from groundtruth.evidence import store
from groundtruth.evidence.db import ChunkEmbeddingRow, ChunkRow, create_session_factory
from groundtruth.ingestion.pdf import PdfLoader, StructureAwareChunker


@pytest.fixture()
def production_factory(tmp_path):
    """A session factory built exactly the way production builds it —
    ``create_session_factory`` on a SQLite URL (FK enforcement now on)."""
    factory, engine = create_session_factory(f"sqlite:///{tmp_path}/gt8.db")
    yield factory, engine
    engine.dispose()


def build_document_and_version():
    parsed = PdfLoader().load_bytes(TWO_PAGE_PDF, filename="notes.pdf")
    document_id = parsed.content_hash[:32]
    version = StructureAwareChunker().chunk(parsed, f"{document_id}:v1")
    document = Document(
        document_id=document_id,
        title=parsed.title,
        source_type="pdf",
        source_uri=parsed.source_uri,
        created_at=datetime(2026, 10, 23, tzinfo=UTC),
        versions=(version,),
    )
    return document, version


# --------------------------------------------------------------------------
# FK enforcement is actually active on factory-created SQLite connections
# --------------------------------------------------------------------------


def test_sqlite_factory_connections_report_foreign_keys_on(production_factory):
    _, engine = production_factory
    with engine.connect() as connection:
        assert connection.execute(text("PRAGMA foreign_keys")).scalar_one() == 1


def test_orphan_embedding_insert_is_rejected(production_factory):
    """An embedding pointing at a chunk that does not exist must fail with
    an IntegrityError — proof the pragma is enforced, not just reported."""
    factory, _ = production_factory
    session = factory()
    try:
        session.add(
            ChunkEmbeddingRow(
                chunk_id="chunk-that-does-not-exist",
                model_provider="fake-provider",
                model_name="fake-embedding-v1",
                representation_version="REP-01",
                dimensions=2,
                vector=[0.1, 0.2],
            )
        )
        with pytest.raises(IntegrityError):
            session.commit()
    finally:
        session.rollback()
        session.close()


# --------------------------------------------------------------------------
# End-to-end persist with embeddings under FK enforcement
# --------------------------------------------------------------------------


def test_persist_document_with_embeddings_resolves_every_chunk_id(production_factory):
    factory, _ = production_factory
    document, version = build_document_and_version()
    vectors = FakeEmbeddingProvider().embed([chunk.text for chunk in version.chunks])

    stored = store.persist_document(
        factory,
        document,
        version,
        embeddings=vectors,
        model_provider="fake-provider",
        model_name="fake-embedding-v1",
    )
    assert stored.duplicate is False
    assert stored.chunk_count == len(version.chunks) > 0

    session = factory()
    try:
        embeddings = session.query(ChunkEmbeddingRow).all()
        assert len(embeddings) == len(version.chunks)
        # Every embedding's chunk_id resolves to a stored chunk (inner join
        # keeps exactly the resolvable ones)...
        joined = (
            session.query(ChunkEmbeddingRow)
            .join(ChunkRow, ChunkRow.id == ChunkEmbeddingRow.chunk_id)
            .count()
        )
        assert joined == len(embeddings)
        # ...and the resolvable set is exactly the chunked ids.
        assert {row.chunk_id for row in embeddings} == {
            chunk.chunk_id for chunk in version.chunks
        }
    finally:
        session.close()

    # The duplicate path (pre-check + no writes) still behaves as before.
    again = store.persist_document(
        factory,
        document,
        version,
        embeddings=vectors,
        model_provider="fake-provider",
        model_name="fake-embedding-v1",
    )
    assert again.duplicate is True
    assert again.chunk_count == stored.chunk_count


def test_upload_end_to_end_against_production_factory(production_factory):
    """The exact production failure path: HTTP upload -> parse -> chunk ->
    embed -> persist, with the session factory production actually uses."""
    factory, _ = production_factory
    app.dependency_overrides[get_session_factory] = lambda: factory
    app.dependency_overrides[get_embedding_provider] = lambda: FakeEmbeddingProvider()
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/documents",
                files={"file": ("notes.pdf", TWO_PAGE_PDF, "application/pdf")},
            )
            assert response.status_code == 200
            body = response.json()
            assert body["status"] == "stored"
            assert body["duplicate"] is False
            assert body["chunks"] > 0
            listing = client.get("/api/v1/documents")
            assert listing.status_code == 200
            assert len(listing.json()) == 1
    finally:
        app.dependency_overrides.clear()
