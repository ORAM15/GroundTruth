"""GT-2: /query must run hybrid retrieval over stored chunks and abstain
honestly when the semantic evidence is weak.

End-to-end through TestClient on SQLite: a synthetic PDF is uploaded via
the real GT-1 endpoint with a deterministic topic provider, then queried.

The fake provider is a bag-of-words over a fixed vocabulary, so cosine
similarity is fully deterministic: a question using the document's words
scores ~1.0 against its chunk, a question about other topics scores 0.0.
The word "quixotic" is a marker that maps any text containing it to a
vector orthogonal to every document chunk — used to prove that strong
*lexical* overlap cannot override a failing *dense* score.
"""

from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from test_gt1_persistence import TWO_PAGE_PDF

from groundtruth.api.app import app, get_embedding_provider, get_session_factory
from groundtruth.evidence.db import Base

VOCAB = [
    "groundtruth",
    "stores",
    "uploaded",
    "documents",
    "evidence",
    "page",
    "text",
    "becomes",
    "chunks",
    "retrieval",
    "citations",
    "keep",
    "number",
    "second",
    "talks",
    "banana",
    "smoothie",
    "recipe",
    "quantum",
    "zebra",
]


class TopicEmbeddingProvider:
    """Deterministic test double: bag-of-words vectors over VOCAB, plus
    one extra orthogonal dimension used by the "quixotic" marker."""

    provider_name = "fake-provider"
    model_name = "fake-topic-v1"

    def embed(self, texts):
        vectors = []
        for text in texts:
            lowered = text.lower()
            if "quixotic" in lowered:
                vectors.append([0.0] * len(VOCAB) + [1.0])
                continue
            tokens = re.findall(r"[\w-]+", lowered)
            vectors.append([float(tokens.count(word)) for word in VOCAB] + [0.0])
        return vectors


@pytest.fixture()
def client(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path}/gt2.db")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    fake = TopicEmbeddingProvider()
    app.dependency_overrides[get_session_factory] = lambda: factory
    app.dependency_overrides[get_embedding_provider] = lambda: fake
    with TestClient(app) as test_client:
        yield test_client, fake, factory
    app.dependency_overrides.clear()


def upload(client) -> dict:
    response = client.post(
        "/api/v1/documents",
        files={"file": ("notes.pdf", TWO_PAGE_PDF, "application/pdf")},
    )
    assert response.status_code == 200
    return response.json()


def ask(client, question: str):
    return client.post("/api/v1/query", json={"question": question})


# (a) A question near the stored chunks finds evidence.
def test_query_finds_evidence_with_right_chunk_and_page(client):
    test_client, _, _ = client
    stored = upload(test_client)
    response = ask(test_client, "How does GroundTruth stores uploaded documents as evidence?")
    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == "EVIDENCE_FOUND"
    assert body["evidence"], "expected at least one evidence item"
    top = body["evidence"][0]
    assert top["document_id"] == stored["document_id"]
    assert top["filename"] == "notes.pdf"
    assert top["title"] == "notes"
    assert top["page_start"] == 1
    assert top["page_end"] == 1
    assert top["snippet"].startswith("GroundTruth stores uploaded documents")
    assert top["chunk_id"].endswith(":chunk:1")
    assert top["method"] == "hybrid"
    assert top["dense_score"] == pytest.approx(1.0)
    assert top["dense_rank"] == 1
    assert top["score"] > 0


# (b) An unrelated question abstains, with no evidence attached.
def test_query_unrelated_question_abstains(client):
    test_client, _, _ = client
    upload(test_client)
    response = ask(test_client, "What is the recipe for a quantum banana smoothie?")
    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == "ABSTAIN"
    assert body["evidence"] == []


# Lexical overlap must NOT override a failing dense score: this question
# repeats document words (strong lexical match) but its embedding is
# orthogonal to every chunk, so the honest answer is ABSTAIN.
def test_lexical_match_cannot_override_dense_gate(client):
    test_client, _, _ = client
    upload(test_client)
    response = ask(test_client, "evidence chunks page quixotic")
    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == "ABSTAIN"
    assert body["evidence"] == []


# (c) Nothing stored yet -> abstain.
def test_query_with_empty_store_abstains(client):
    test_client, _, _ = client
    response = ask(test_client, "How does GroundTruth stores uploaded documents as evidence?")
    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == "ABSTAIN"
    assert body["evidence"] == []
    assert "empty" in body["message"]


# (d) The threshold is tunable via GT_MIN_EVIDENCE_SCORE. This question's
# best dense score is ~0.913: it passes the 0.35 default but must abstain
# when the operator raises the threshold to 0.95.
def test_threshold_env_override_is_respected(client, monkeypatch):
    test_client, _, _ = client
    upload(test_client)
    question = "GroundTruth stores uploaded documents evidence retrieval"
    passing = ask(test_client, question)
    assert passing.json()["decision"] == "EVIDENCE_FOUND"

    monkeypatch.setenv("GT_MIN_EVIDENCE_SCORE", "0.95")
    blocked = ask(test_client, question)
    assert blocked.status_code == 200
    assert blocked.json()["decision"] == "ABSTAIN"
    assert blocked.json()["evidence"] == []


# DB configured but embeddings not configured -> loud 503, not a fake answer.
def test_query_without_embedding_provider_is_503(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path}/gt2-noprovider.db")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    app.dependency_overrides[get_session_factory] = lambda: factory
    app.dependency_overrides[get_embedding_provider] = lambda: None
    try:
        with TestClient(app) as test_client:
            response = test_client.post(
                "/api/v1/query", json={"question": "GroundTruth stores documents?"}
            )
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 503
    assert "GEMINI_API_KEY" in response.json()["detail"]
