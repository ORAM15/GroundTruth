"""Issue #67: per-document retrieval caps + coverage strip.

Live failure (2026-10-25, program #61 live test): unscoped retrieval
ran one RRF top-10 over the whole library, so a 360-chunk document's
many similar chunks crowded a 12-chunk document's unique chunk out of
the evidence set — the page-7 question was declined or answered from
the wrong document. Document-scoped querying (#65) fixed only the
scoped path.

The fix: an unscoped query retrieves per document first (at most 3
chunks each), then merges by fused score into the final evidence set
of at most top_k hits. These tests reuse the #65 crowding library
(30 near-identical A chunks vs B's single unique page-7 chunk) and
assert the fixed shape: B's chunk is in the evidence set, no document
contributes more than 3 chunks, and the API reports per-document
contribution counts that match the evidence set exactly. The scoped
path is unchanged, and a single-document library caps at 3 chunks —
no filler is added past the per-document rankings.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from test_gt2_retrieval import CitingGenerationProvider
from test_gt65_document_scoped_query import (
    B_PDF,
    QUESTION,
    CrowdingEmbeddingProvider,
    _ask,
    _library,
    _upload,
)

import groundtruth.api
from groundtruth.api.app import (
    app,
    get_embedding_provider,
    get_generation_provider,
    get_session_factory,
)
from groundtruth.evidence.db import Base


@pytest.fixture()
def client(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path}/gt67.db")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    app.dependency_overrides[get_session_factory] = lambda: factory
    app.dependency_overrides[get_embedding_provider] = lambda: CrowdingEmbeddingProvider()
    app.dependency_overrides[get_generation_provider] = lambda: CitingGenerationProvider()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _counts(payload):
    counts = {}
    for item in payload["evidence"]:
        counts[item["document_id"]] = counts.get(item["document_id"], 0) + 1
    return counts


def test_unscoped_search_returns_the_small_documents_unique_chunk(client):
    """The regression: unscoped, B's unique page-7 chunk must be in
    the evidence set, and no document may contribute more than the
    per-document cap of 3. Before #67 this evidence set was all A."""
    a_id, b_id, _title = _library(client)
    response = _ask(client, QUESTION)
    assert response.status_code == 200
    payload = response.json()
    assert payload["decision"] == "ANSWERED"
    assert {item["document_id"] for item in payload["evidence"]} == {a_id, b_id}
    assert any("REC-PG-07" in item["snippet"] for item in payload["evidence"])
    counts = _counts(payload)
    assert counts[a_id] == 3, "A must be capped at 3 chunks"
    # B's per-document top-3 is its unique chunk plus two dense-only
    # fillers (the hybrid ranks every chunk); the cap binds at 3, and
    # the unique chunk — the one that used to be crowded out — is in.
    assert counts[b_id] == 3, "B must be capped at 3 chunks"
    assert len(payload["evidence"]) == 6


def test_coverage_counts_match_the_evidence_set(client):
    """The API's coverage strip must report exactly what the evidence
    set contains — per-document chunk counts, with titles matching
    the library listing, ordered by count descending."""
    a_id, b_id, _title = _library(client)
    payload = _ask(client, QUESTION).json()
    listed = {doc["document_id"]: doc["title"] for doc in client.get("/api/v1/documents").json()}
    coverage = payload["coverage"]
    assert {(entry["document_id"], entry["chunk_count"]) for entry in coverage} == {
        (a_id, 3),
        (b_id, 3),
    }
    assert all(entry["title"] == listed[entry["document_id"]] for entry in coverage)
    assert [entry["chunk_count"] for entry in coverage] == sorted(
        (entry["chunk_count"] for entry in coverage), reverse=True
    )


def test_scoped_search_is_unchanged_by_the_caps(client):
    """Scoping bypasses the per-document merge entirely: scoped to B,
    every evidence item comes from B, and coverage reports B alone
    with the full scoped evidence count."""
    _a_id, b_id, _title = _library(client)
    payload = _ask(client, QUESTION, document_id=b_id).json()
    assert payload["decision"] == "ANSWERED"
    assert {item["document_id"] for item in payload["evidence"]} == {b_id}
    assert len(payload["coverage"]) == 1
    assert payload["coverage"][0]["document_id"] == b_id
    assert payload["coverage"][0]["chunk_count"] == len(payload["evidence"])


def test_single_document_library_caps_at_three_chunks(client):
    """With one document stored, the final set is at most the
    per-document cap — no filler chunks are added past it — and the
    document's best chunk is still present."""
    _upload(client, "gt_objectives_test.pdf", B_PDF)
    payload = _ask(client, QUESTION).json()
    assert payload["decision"] == "ANSWERED"
    assert len(payload["evidence"]) == 3
    assert any("REC-PG-07" in item["snippet"] for item in payload["evidence"])
    assert len(payload["coverage"]) == 1
    assert payload["coverage"][0]["chunk_count"] == 3


def test_coverage_strip_markers_exist_in_page_script_and_styles():
    """Structural UI test (same pattern as the other UI tests): the
    strip renderer builds one textContent line from the server's
    coverage list, the ANSWERED branch appends it under the answer,
    and the style exists."""
    static_dir = Path(groundtruth.api.__file__).parent / "static"
    js = (static_dir / "app.js").read_text(encoding="utf-8")
    css = (static_dir / "style.css").read_text(encoding="utf-8")
    assert "function renderCoverageStrip(coverage)" in js
    assert "renderCoverageStrip(payload.coverage || [])" in js
    assert '"coverage-strip"' in js
    assert "Evidence from " in js
    assert ".coverage-strip {" in css
