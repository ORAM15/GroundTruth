"""GT-1: document upload must persist (parse, chunk, embed, store).

Covers the upload->persist round-trip, idempotent duplicate uploads, the
error paths (415/400/413/422/503), the Gemini provider's HTTP shape via
httpx MockTransport, and — only when TEST_DATABASE_URL points at a real
Postgres — embedding-row persistence through the production session factory.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from hashlib import sha256

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from groundtruth.api.app import (
    MAX_UPLOAD_BYTES,
    app,
    get_embedding_provider,
    get_session_factory,
)
from groundtruth.domain.models import Document
from groundtruth.evidence import store
from groundtruth.evidence.db import (
    Base,
    ChunkEmbeddingRow,
    ChunkRow,
    DocumentRow,
    DocumentVersionRow,
    create_session_factory,
)
from groundtruth.evidence.embeddings import EmbeddingError, GeminiEmbeddingProvider
from groundtruth.ingestion.pdf import PdfLoader, StructureAwareChunker

# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def make_pdf_bytes(pages: list[list[str]]) -> bytes:
    """Build a minimal multi-page PDF (Helvetica, one Tj per line) that
    pypdf can extract text from, without needing a PDF-writing dependency."""

    def escape(text: str) -> str:
        return text.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")

    objects: list[bytes] = []
    page_obj_numbers: list[int] = []
    content_obj_numbers: list[int] = []
    next_number = 3  # 1 = catalog, 2 = pages tree
    for lines in pages:
        page_obj_numbers.append(next_number)
        content_obj_numbers.append(next_number + 1)
        next_number += 2
    font_number = next_number

    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    kids_ref = " ".join(f"{n} 0 R" for n in page_obj_numbers)
    objects.append(f"<< /Type /Pages /Kids [{kids_ref}] /Count {len(pages)} >>".encode())
    for lines, page_no, content_no in zip(
        pages, page_obj_numbers, content_obj_numbers, strict=True
    ):
        objects.append(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                f"/Contents {content_no} 0 R /Resources << /Font << /F1 {font_number} 0 R >> >> >>"
            ).encode()
        )
        stream_lines = ["BT", "/F1 12 Tf", "14 TL", "72 720 Td"]
        for index, line in enumerate(lines):
            if index:
                stream_lines.append("T*")
            stream_lines.append(f"({escape(line)}) Tj")
        stream_lines.append("ET")
        stream = "\n".join(stream_lines).encode()
        objects.append(
            b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream"
        )
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    out = bytearray(b"%PDF-1.4\n")
    offsets: list[int] = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
    xref_start = len(out)
    size = len(objects) + 1
    out += f"xref\n0 {size}\n".encode()
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {size} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF\n".encode()
    return bytes(out)


class FakeEmbeddingProvider:
    """Deterministic test double: vectors derived from the text hash.
    Lives in tests only — never shipped as a production fallback."""

    provider_name = "fake-provider"
    model_name = "fake-embedding-v1"

    def __init__(self) -> None:
        self.calls = 0

    def embed(self, texts):
        self.calls += 1
        vectors = []
        for text in texts:
            digest = sha256(text.encode("utf-8")).digest()
            vectors.append([byte / 255.0 for byte in digest[:8]])
        return vectors


TWO_PAGE_PDF = make_pdf_bytes(
    [
        [
            "GroundTruth stores uploaded documents as evidence.",
            "Each page of text becomes one or more chunks.",
        ],
        [
            "This second page talks about retrieval and citations.",
            "Chunks keep the page number they came from.",
        ],
    ]
)


@pytest.fixture()
def sqlite_factory(tmp_path):
    """Session factory on a throwaway SQLite DB with only the
    documents/document_versions/chunks tables (no pgvector table)."""
    engine = create_engine(f"sqlite:///{tmp_path}/gt1.db")
    Base.metadata.create_all(
        engine,
        tables=[
            DocumentRow.__table__,
            DocumentVersionRow.__table__,
            ChunkRow.__table__,
        ],
    )
    return sessionmaker(bind=engine)


@pytest.fixture()
def client(tmp_path):
    """Full-stack client: fake embedding provider + a session factory on a
    throwaway SQLite DB with the complete schema. The endpoint writes
    embedding rows, so this fixture needs chunk_embeddings too; SQLAlchemy's
    create_all handles the pgvector Vector column on SQLite with the pinned
    pgvector/SQLAlchemy versions (verified locally), while the gated
    Postgres test below stays the authoritative embedding-persistence check.
    The subset-tables path is covered separately by the store-level test."""
    engine = create_engine(f"sqlite:///{tmp_path}/gt1-full.db")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    fake = FakeEmbeddingProvider()
    app.dependency_overrides[get_session_factory] = lambda: factory
    app.dependency_overrides[get_embedding_provider] = lambda: fake
    with TestClient(app) as test_client:
        yield test_client, fake, factory
    app.dependency_overrides.clear()


def row_counts(factory):
    session = factory()
    try:
        return (
            session.query(DocumentRow).count(),
            session.query(DocumentVersionRow).count(),
            session.query(ChunkRow).count(),
        )
    finally:
        session.close()


def upload(client, payload: bytes, filename: str = "notes.pdf", content_type: str = "application/pdf"):
    return client.post(
        "/api/v1/documents",
        files={"file": (filename, payload, content_type)},
    )


# --------------------------------------------------------------------------
# PdfLoader.load_bytes
# --------------------------------------------------------------------------


def test_load_bytes_matches_load_from_disk(tmp_path):
    path = tmp_path / "notes.pdf"
    path.write_bytes(TWO_PAGE_PDF)
    from_disk = PdfLoader().load(path)
    from_bytes = PdfLoader().load_bytes(TWO_PAGE_PDF, filename="notes.pdf")
    assert from_bytes.content_hash == from_disk.content_hash
    assert from_bytes.blocks == from_disk.blocks
    assert from_bytes.title == "notes"
    assert from_bytes.page_count == 2


# --------------------------------------------------------------------------
# Upload -> persist round-trip
# --------------------------------------------------------------------------


def test_upload_persists_chunks_with_pages_and_ordinals(client):
    test_client, fake, factory = client
    response = upload(test_client, TWO_PAGE_PDF)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "stored"
    assert body["duplicate"] is False
    assert body["pages"] == 2
    assert body["filename"] == "notes.pdf"
    assert fake.calls == 1

    session = factory()
    try:
        version = session.query(DocumentVersionRow).one()
        assert version.id == body["version_id"]
        assert version.document_id == body["document_id"]
        document = session.query(DocumentRow).one()
        assert document.id == body["document_id"]
        assert document.title == "notes"
        chunks = session.query(ChunkRow).order_by(ChunkRow.ordinal).all()
        assert len(chunks) == body["chunks"] == 4
        assert [c.ordinal for c in chunks] == [1, 2, 3, 4]
        assert [c.page_start for c in chunks] == [1, 1, 2, 2]
        assert [c.page_end for c in chunks] == [1, 1, 2, 2]
        assert chunks[0].text.startswith("GroundTruth stores uploaded documents")
        assert chunks[2].text.startswith("This second page talks about retrieval")
        assert all(c.document_version_id == version.id for c in chunks)
        embeddings = session.query(ChunkEmbeddingRow).all()
        assert len(embeddings) == len(chunks)
        assert {row.chunk_id for row in embeddings} == {c.id for c in chunks}
        assert all(row.model_name == "fake-embedding-v1" for row in embeddings)
        assert all(row.model_provider == "fake-provider" for row in embeddings)
        assert all(row.dimensions == 8 for row in embeddings)
    finally:
        session.close()


def test_duplicate_upload_returns_flag_and_writes_nothing(client):
    test_client, fake, factory = client
    first = upload(test_client, TWO_PAGE_PDF)
    assert first.status_code == 200
    counts_after_first = row_counts(factory)
    calls_after_first = fake.calls

    second = upload(test_client, TWO_PAGE_PDF, filename="same-content-different-name.pdf")
    assert second.status_code == 200
    body = second.json()
    assert body["duplicate"] is True
    assert body["document_id"] == first.json()["document_id"]
    assert body["version_id"] == first.json()["version_id"]
    assert body["chunks"] == first.json()["chunks"]
    assert row_counts(factory) == counts_after_first
    # A duplicate must not pay for another embedding call.
    assert fake.calls == calls_after_first


def test_store_persist_without_embeddings_on_subset_tables(sqlite_factory):
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
    stored = store.persist_document(sqlite_factory, document, version)
    assert stored.duplicate is False
    assert stored.chunk_count == 4
    again = store.persist_document(sqlite_factory, document, version)
    assert again.duplicate is True
    assert row_counts(sqlite_factory) == (1, 1, 4)


# --------------------------------------------------------------------------
# Error paths
# --------------------------------------------------------------------------


def test_upload_rejects_non_pdf_content_type(client):
    test_client, _, _ = client
    response = upload(test_client, b"hello", filename="note.txt", content_type="text/plain")
    assert response.status_code == 415


def test_upload_rejects_empty_payload(client):
    test_client, _, _ = client
    response = upload(test_client, b"")
    assert response.status_code == 400


def test_upload_rejects_corrupt_pdf(client):
    test_client, _, _ = client
    response = upload(test_client, b"this is not a pdf at all")
    assert response.status_code == 422


def test_upload_rejects_oversized_pdf(client):
    test_client, _, _ = client
    payload = b"%PDF-1.4\n" + b"0" * MAX_UPLOAD_BYTES
    response = upload(test_client, payload)
    assert response.status_code == 413


def test_upload_without_database_url_is_503(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with TestClient(app) as bare_client:
        response = upload(bare_client, TWO_PAGE_PDF)
    assert response.status_code == 503
    assert "DATABASE_URL" in response.json()["detail"]


# --------------------------------------------------------------------------
# Gemini provider (httpx MockTransport — no network, no key needed)
# --------------------------------------------------------------------------


def test_gemini_provider_request_and_response_shape():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["api_key_header"] = request.headers.get("x-goog-api-key")
        seen["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={"embeddings": [{"values": [0.1, 0.2]}, {"values": [0.3, 0.4]}]},
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = GeminiEmbeddingProvider(api_key="test-key", client=client)
    vectors = provider.embed(["first text", "second text"])
    assert vectors == [[0.1, 0.2], [0.3, 0.4]]
    assert seen["url"].endswith("/models/gemini-embedding-001:batchEmbedContents")
    assert seen["api_key_header"] == "test-key"
    requests = seen["body"]["requests"]
    assert len(requests) == 2
    assert requests[0]["model"] == "models/gemini-embedding-001"
    assert requests[0]["content"]["parts"][0]["text"] == "first text"
    assert requests[1]["content"]["parts"][0]["text"] == "second text"


def test_gemini_provider_requires_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(EmbeddingError, match="GEMINI_API_KEY"):
        GeminiEmbeddingProvider()


def test_gemini_provider_http_error_raises_embedding_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": {"message": "boom"}})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = GeminiEmbeddingProvider(api_key="test-key", client=client)
    with pytest.raises(EmbeddingError):
        provider.embed(["anything"])


def test_gemini_provider_empty_input_short_circuits():
    provider = GeminiEmbeddingProvider(
        api_key="test-key",
        client=httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(500))),
    )
    assert provider.embed([]) == []


# --------------------------------------------------------------------------
# Embedding persistence against a real Postgres (gated)
# --------------------------------------------------------------------------


@pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason=(
        "TEST_DATABASE_URL is not set. Embedding rows use the pgvector Vector "
        "column, whose real behaviour is only meaningful against Postgres; "
        "the SQLite suites above cover chunk persistence on the subset of "
        "tables that do not need pgvector."
    ),
)
def test_embedding_rows_persist_on_postgres():
    """End-to-end embedding persistence via the production session factory.

    Runs only when TEST_DATABASE_URL points at a Postgres database with the
    pgvector extension available (e.g. a Neon dev branch)."""
    factory, engine = create_session_factory(os.environ["TEST_DATABASE_URL"])
    try:
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
        vectors = [[0.01 * i] * 8 for i in range(len(version.chunks))]
        stored = store.persist_document(
            factory,
            document,
            version,
            embeddings=vectors,
            model_provider="test",
            model_name="test-model",
        )
        session = factory()
        try:
            rows = session.query(ChunkEmbeddingRow).all()
            by_chunk = {row.chunk_id: row for row in rows}
            assert len(rows) == len(version.chunks)
            for chunk, vector in zip(version.chunks, vectors, strict=True):
                row = by_chunk[chunk.chunk_id]
                assert row.dimensions == 8
                assert row.model_name == "test-model"
                assert list(row.vector) == pytest.approx(vector)
            assert stored.chunk_count == len(version.chunks)
        finally:
            session.close()
    finally:
        # Leave the test database as we found it.
        session = factory()
        try:
            session.query(ChunkEmbeddingRow).delete()
            session.query(ChunkRow).delete()
            session.query(DocumentVersionRow).delete()
            session.query(DocumentRow).delete()
            session.commit()
        finally:
            session.close()
        engine.dispose()
