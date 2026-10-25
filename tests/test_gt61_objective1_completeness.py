"""GT-61 objective 1: an uploaded PDF must become searchable IN FULL.

Program issue #61, objective 1 — "your documents, fully in". This test
locks the property the owner's DevOps upload called into question: a
multi-page PDF uploaded through the real endpoint must be parsed,
chunked, persisted, and answerable from EVERY page, not just the first
one. It runs the full local chain (upload -> list -> query) with
deterministic test doubles, so it proves completeness without any live
service or API key.

Note on scope: this test proves completeness generally. The owner's
specific DevOps file ("1 page, 1 chunk" on the live site) is still
undiagnosed for lack of that file — see issue #61. Nothing here claims
that case is reproduced or explained.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from test_gt1_persistence import make_pdf_bytes
from test_gt2_retrieval import CitingGenerationProvider, TopicEmbeddingProvider

from groundtruth.api.app import (
    app,
    get_embedding_provider,
    get_generation_provider,
    get_session_factory,
)
from groundtruth.evidence.db import Base
from groundtruth.ingestion.pdf import PdfLoader, StructureAwareChunker

# Twelve pages; page 7 carries a combination of rare vocabulary words
# that no other page shares, so a question using those words must
# retrieve page 7 specifically (the topic provider is bag-of-words).
PAGE_LINES = [
    ["GroundTruth stores uploaded documents as evidence."],
    ["Each page of text becomes one or more chunks."],
    ["The second page talks about retrieval and citations."],
    ["Chunks keep the page number they came from."],
    ["The fifth page keeps a number for every chunk."],
    ["This page talks about how retrieval works."],
    ["The zebra eats a quantum banana smoothie recipe."],
    ["GroundTruth stores uploaded documents as evidence."],
    ["This page talks about the second number again."],
    ["Chunks become evidence when they are stored."],
    ["The eleventh page keeps talking about retrieval."],
    ["The last page stores documents as evidence."],
]
TWELVE_PAGE_PDF = make_pdf_bytes(PAGE_LINES)
TARGET_QUESTION = "What does the document say about the zebra quantum banana smoothie recipe?"


@pytest.fixture()
def client(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path}/gt61.db")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    app.dependency_overrides[get_session_factory] = lambda: factory
    app.dependency_overrides[get_embedding_provider] = lambda: TopicEmbeddingProvider()
    app.dependency_overrides[get_generation_provider] = lambda: CitingGenerationProvider()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_parser_and_chunker_cover_every_page():
    parsed = PdfLoader().load_bytes(TWELVE_PAGE_PDF, filename="field-guide.pdf")
    assert parsed.page_count == 12
    version = StructureAwareChunker().chunk(parsed, "doc:v1")
    pages_covered = {chunk.page_start for chunk in version.chunks}
    assert pages_covered == set(range(1, 13))
    assert len(version.chunks) == 12  # one short line per page -> one chunk each


def test_uploaded_document_lists_all_pages_and_chunks(client):
    response = client.post(
        "/api/v1/documents",
        files={"file": ("field-guide.pdf", TWELVE_PAGE_PDF, "application/pdf")},
    )
    assert response.status_code == 200
    assert response.json()["pages"] == 12
    listed = client.get("/api/v1/documents").json()
    assert len(listed) == 1
    assert listed[0]["pages"] == 12
    assert listed[0]["chunk_count"] == 12


def test_page_specific_question_gets_a_cited_answer_from_that_page(client):
    upload = client.post(
        "/api/v1/documents",
        files={"file": ("field-guide.pdf", TWELVE_PAGE_PDF, "application/pdf")},
    )
    assert upload.status_code == 200
    response = client.post("/api/v1/query", json={"question": TARGET_QUESTION})
    assert response.status_code == 200
    payload = response.json()
    assert payload["decision"] == "ANSWERED"
    assert payload["answer"] is not None
    cited_pages = {item["page_start"] for item in payload["citations"]}
    assert 7 in cited_pages
    # Every citation resolves to a chunk that was actually returned as
    # evidence, and every cited chunk carries its page.
    evidence_ids = {item["chunk_id"] for item in payload["evidence"]}
    for citation in payload["citations"]:
        assert citation["chunk_id"] in evidence_ids
        assert citation["page_start"] is not None
