"""Issue #65: document-scoped querying.

Live failure (2026-10-25, program #61 live test): unscoped retrieval
across a shared library let a 360-chunk document's many similar chunks
crowd the top-10, so a 12-chunk document's unique chunk never made the
evidence set — and a document named in the question was ignored. A
specific question about stored page-7 content then declined via
citation verification.

These tests reproduce that shape deterministically: document A has 30
near-identical chunks sharing the question's vocabulary; document B
has 7 pages with one unique chunk on page 7. Scoped to B, the answer
must come from B's page-7 chunk, cited with its page. Scope-clear
restores unscoped behaviour, and an unknown scope fails loudly
instead of silently searching the whole library.

Note: issue #67 changed the unscoped outcome — per-document caps now
guarantee B's unique chunk a place in the evidence set, so the old
"unscoped is crowded out" expectation no longer holds. That fixed
behaviour is locked in by test_gt67_per_doc_caps.py, not here.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from test_gt1_persistence import make_pdf_bytes
from test_gt2_retrieval import CitingGenerationProvider

import groundtruth.api
from groundtruth.api.app import (
    app,
    get_embedding_provider,
    get_generation_provider,
    get_session_factory,
)
from groundtruth.evidence.db import Base

# Bag-of-words vocabulary for the deterministic test double. The
# question shares "survey"/"code" with every A chunk, but only B's
# page-7 chunk carries "annex" — the live shape, where the unique
# chunk loses to many similar ones.
VOCAB = [
    "survey",
    "code",
    "annex",
    "record",
    "page",
    "seven",
    "zebra",
    "observatory",
    "filed",
    "section",
]

# 30 near-identical chunks: each scores higher than B's unique chunk
# on both lexical count (4 vs 3) and dense cosine (~0.696 vs ~0.655),
# so unscoped fusion fills the top-10 with A alone.
A_LINE = "survey code survey code record page seven"
A_PDF = make_pdf_bytes([[A_LINE] for _ in range(30)])

FILLER = "Zebra observatory notes filed under section one."
B_PAGES = [[FILLER] for _ in range(6)] + [
    # No leading "The": "the" is itself a lexical term, and with it
    # this chunk would tie A's lexical score (4) and sneak into the
    # fused top-10 on the tie-break — the crowding must be total.
    ["Zorath Observatory annex survey code REC-PG-07, filed under section seven."]
]
B_PDF = make_pdf_bytes(B_PAGES)

QUESTION = "What is the annex survey code?"
TOPICLESS = "What do the documents say about?"


class CrowdingEmbeddingProvider:
    """Deterministic bag-of-words double over VOCAB."""

    provider_name = "fake-provider"
    model_name = "fake-crowding-v1"

    def embed(self, texts):
        vectors = []
        for text in texts:
            tokens = re.findall(r"[\w-]+", text.lower())
            vectors.append([float(tokens.count(word)) for word in VOCAB])
        return vectors


@pytest.fixture()
def client(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path}/gt65.db")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    app.dependency_overrides[get_session_factory] = lambda: factory
    app.dependency_overrides[get_embedding_provider] = lambda: CrowdingEmbeddingProvider()
    app.dependency_overrides[get_generation_provider] = lambda: CitingGenerationProvider()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _upload(client, filename, pdf_bytes):
    response = client.post(
        "/api/v1/documents",
        files={"file": (filename, pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200, response.text
    return response.json()


def _library(client):
    """Upload the crowding library; return (A id, B id, B title)."""
    _upload(client, "large_test.pdf", A_PDF)
    _upload(client, "gt_objectives_test.pdf", B_PDF)
    listed = client.get("/api/v1/documents").json()
    assert len(listed) == 2
    by_filename = {doc["filename"]: doc for doc in listed}
    a_doc = by_filename["large_test.pdf"]
    b_doc = by_filename["gt_objectives_test.pdf"]
    assert a_doc["chunk_count"] == 30
    assert b_doc["pages"] == 7
    return a_doc["document_id"], b_doc["document_id"], b_doc["title"]


def _ask(client, question, document_id=None):
    payload = {"question": question}
    if document_id is not None:
        payload["document_id"] = document_id
    return client.post("/api/v1/query", json=payload)


def test_scoped_query_returns_the_scoped_documents_chunk_cited_with_page(client):
    """Scoped to B, the same question must be answered from B's
    page-7 chunk, cited with its page — the live acceptance case."""
    _a_id, b_id, _title = _library(client)
    response = _ask(client, QUESTION, document_id=b_id)
    assert response.status_code == 200
    payload = response.json()
    assert payload["decision"] == "ANSWERED"
    assert payload["evidence"], "scoped query must return evidence"
    assert {item["document_id"] for item in payload["evidence"]} == {b_id}
    cited_pages = {item["page_start"] for item in payload["citations"]}
    assert 7 in cited_pages
    assert any("REC-PG-07" in item["snippet"] for item in payload["evidence"])
    evidence_ids = {item["chunk_id"] for item in payload["evidence"]}
    for citation in payload["citations"]:
        assert citation["chunk_id"] in evidence_ids
        assert citation["page_start"] == 7


def test_clearing_the_scope_restores_unscoped_behaviour(client):
    """Scope, then clear: the cleared question matches a fresh
    unscoped question exactly (chunk for chunk). Scoping must be
    per-question state, not a sticky server side. The unscoped result
    itself is no longer "all A" — issue #67 caps per document, so
    B's unique chunk is in it; that fixed shape is asserted in
    test_gt67_per_doc_caps.py."""
    _a_id, b_id, _title = _library(client)
    scoped = _ask(client, QUESTION, document_id=b_id)
    assert scoped.json()["decision"] == "ANSWERED"
    assert {item["document_id"] for item in scoped.json()["evidence"]} == {b_id}
    unscoped = _ask(client, QUESTION)
    fresh = _ask(client, QUESTION)
    assert unscoped.json()["decision"] == "ANSWERED"
    assert [item["chunk_id"] for item in unscoped.json()["evidence"]] == [
        item["chunk_id"] for item in fresh.json()["evidence"]
    ]


def test_scoped_query_against_an_unknown_document_fails_loudly(client):
    """An unknown scope must 404 — never silently fall back to
    library-wide search and answer from a document not asked about."""
    _a_id, _b_id, _title = _library(client)
    response = _ask(client, QUESTION, document_id="no-such-document")
    assert response.status_code == 404
    assert "Unknown document" in response.json()["detail"]


def test_scoped_topicless_question_gets_scoped_guidance_only(client):
    """A scoped topic-less question gets guidance about the scoped
    document only — not the whole library, and not a bare decline."""
    _a_id, b_id, b_title = _library(client)
    response = _ask(client, TOPICLESS, document_id=b_id)
    assert response.status_code == 200
    payload = response.json()
    assert payload["decision"] == "GUIDANCE"
    assert payload["guidance"]["documents"] == [b_title]


def test_scope_ui_markers_exist_in_page_script_and_styles():
    """Structural UI test (same pattern as the other UI tests): the
    scope bar + clear control exist in the page, the script keeps scope
    state, sends it with the question, and renders the scoped name via
    textContent only."""
    static_dir = Path(groundtruth.api.__file__).parent / "static"
    html = (static_dir / "index.html").read_text(encoding="utf-8")
    js = (static_dir / "app.js").read_text(encoding="utf-8")
    css = (static_dir / "style.css").read_text(encoding="utf-8")
    for element_id in ("query-scope", "query-scope-text", "clear-scope"):
        assert f'id="{element_id}"' in html, element_id
    assert "Click a document in the library to scope questions to it." in html
    assert "let scopedDocument = null" in js
    assert "function setScope(doc)" in js
    assert "function clearScope()" in js
    assert "if (scopedDocument) queryBody.document_id = scopedDocument.document_id;" in js
    assert 'text.textContent = "Searching only: " + scopedDocument.name;' in js
    assert ".query-scope {" in css
    assert ".doc-card {" in css and "cursor: pointer" in css
