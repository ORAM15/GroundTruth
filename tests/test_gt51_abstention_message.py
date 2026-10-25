"""GT-51: a citation-verification abstention must not leak internal
chunk ids into user-facing text.

The detailed reason (which names the offending chunk ids) is still
produced by ``verify_citations`` and is now logged server-side only;
the API response carries a clean sentence. These tests pin both halves:
the response contains no chunk id, and the detailed reason still
exists one layer down for debugging.
"""

from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from test_gt1_persistence import TWO_PAGE_PDF
from test_gt2_retrieval import TopicEmbeddingProvider
from test_gt3_generation import FakeGenerationProvider, ask, upload

from groundtruth.api.app import (
    app,
    get_embedding_provider,
    get_generation_provider,
    get_session_factory,
)
from groundtruth.evidence.db import Base
from groundtruth.generation import verify_citations


@pytest.fixture()
def client(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path}/gt51.db")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    generation = FakeGenerationProvider()
    app.dependency_overrides[get_session_factory] = lambda: factory
    app.dependency_overrides[get_embedding_provider] = lambda: TopicEmbeddingProvider()
    app.dependency_overrides[get_generation_provider] = lambda: generation
    with TestClient(app) as test_client:
        yield test_client, generation
    app.dependency_overrides.clear()

CHUNK_ID_PATTERN = re.compile(r"[0-9a-f]{32}:v1:chunk:\d+")
GENERIC_CHUNK_PATTERN = re.compile(r":v1:chunk:\d+")

HALLUCINATED = "7f6420a62ef22aa5704d549f3cdfd545:v1:chunk:241"


def test_verification_abstention_message_has_no_chunk_ids(client):
    """The live 2026-10-25 case: a draft citing chunks outside the
    retrieved evidence abstains with a clean message."""
    test_client, generation = client
    upload(test_client)
    generation.responder = (
        f"Summary citing things [{HALLUCINATED}] and more."
    )
    response = ask(test_client, "What do the documents say about?")
    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == "ABSTAIN"
    assert body["answer"] is None
    assert CHUNK_ID_PATTERN.search(body["message"]) is None
    assert GENERIC_CHUNK_PATTERN.search(body["message"]) is None
    assert "could not be verified" in body["message"]
    assert "withheld rather than shown unverified" in body["message"]


def test_no_citation_abstention_message_has_no_chunk_ids(client):
    """The no-citations verification failure gets the same clean
    message (no ids to leak, but the contract is uniform)."""
    test_client, generation = client
    upload(test_client)
    generation.responder = "PWNED"
    response = ask(test_client, "What do the documents say about?")
    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == "ABSTAIN"
    assert GENERIC_CHUNK_PATTERN.search(body["message"]) is None
    assert "could not be verified" in body["message"]


def test_detailed_reason_still_exists_below_the_api():
    """The debug detail is not deleted, only kept out of the response:
    ``verify_citations`` still names the invalid ids for the log."""
    verification = verify_citations(
        f"Answer [{HALLUCINATED}].", {"other:v1:chunk:1"}
    )
    assert verification.ok is False
    assert HALLUCINATED in verification.reason
    assert HALLUCINATED in verification.invalid_ids
