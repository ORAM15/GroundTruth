"""GT-61 objective 4: questions handled the way people ask.

Program issue #61. Three behaviours, each locked by tests:

- Specific questions -> specific cited answers (unchanged behaviour).
- Topic-scoped broad questions ("what does the document say about
  X?") -> the normal retrieval + generation + verification path, so a
  grounded overview with citations when evidence exists. Verification
  is NEVER weakened to make these "work".
- Topic-less questions ("what do the documents say about?", "tell me
  everything") -> guidance naming what is stored and teaching the
  question shape that works. Guidance fabricates nothing: example
  questions are templates derived from stored titles only, it claims
  no citations, and it never consults the generation provider.

Detection is conservative by design: anything with a discernible
topic — including "tell me everything about deployment" — takes the
normal path, never guidance.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from test_gt1_persistence import TWO_PAGE_PDF
from test_gt2_retrieval import CitingGenerationProvider, TopicEmbeddingProvider
from test_gt3_generation import FakeGenerationProvider

from groundtruth.api.app import (
    app,
    get_embedding_provider,
    get_generation_provider,
    get_session_factory,
)
from groundtruth.evidence.db import Base
from groundtruth.generation.guidance import (
    guidance_examples,
    guidance_message,
    is_topicless_question,
)

HEX_ID = re.compile(r"\b[0-9a-f]{32}\b")

TOPICLESS = [
    "what do the documents say about?",
    "What do the document say about?",  # the owner's actually-asked wording
    "what do these documents say about",
    "what do my documents say",
    "please tell me everything!",
    "summarize everything",
    "summarise all documents",
    "what is in these documents?",
    "give me a summary of everything",
]

TOPICAL = [
    "what does the document say about retrieval and citations?",
    "tell me everything about deployment",
    "How does GroundTruth stores uploaded documents as evidence?",
    "what is the capital of France?",
    "summarize the deployment section",
]


@pytest.mark.parametrize("question", TOPICLESS)
def test_topicless_detection_matches_generic_prompts(question):
    assert is_topicless_question(question) is True


@pytest.mark.parametrize("question", TOPICAL)
def test_topicless_detection_leaves_topical_prompts_alone(question):
    assert is_topicless_question(question) is False


def test_guidance_message_and_examples_fabricate_nothing():
    message = guidance_message(2)
    assert "2 stored documents" in message
    assert not HEX_ID.search(message)
    examples = guidance_examples(["notes", "field-guide"])
    assert examples == [
        'What does "notes" say about ...?',
        'What does "field-guide" say about ...?',
    ]
    # Templates only: the "..." marks the slot the user must fill.
    assert all("..." in example for example in examples)
    assert guidance_examples(["a", "b", "c", "d"]) == [
        'What does "a" say about ...?',
        'What does "b" say about ...?',
        'What does "c" say about ...?',
    ]


@pytest.fixture()
def client(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path}/gt61guide.db")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    generation = FakeGenerationProvider(responder=CitingGenerationProvider().generate)
    app.dependency_overrides[get_session_factory] = lambda: factory
    app.dependency_overrides[get_embedding_provider] = lambda: TopicEmbeddingProvider()
    app.dependency_overrides[get_generation_provider] = lambda: generation
    with TestClient(app) as test_client:
        yield test_client, generation
    app.dependency_overrides.clear()


def _upload(test_client):
    response = test_client.post(
        "/api/v1/documents",
        files={"file": ("notes.pdf", TWO_PAGE_PDF, "application/pdf")},
    )
    assert response.status_code == 200


def test_generic_question_gets_guidance_not_a_decline(client):
    test_client, generation = client
    _upload(test_client)
    response = test_client.post(
        "/api/v1/query", json={"question": "what do the documents say about?"}
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["decision"] == "GUIDANCE"
    assert payload["answer"] is None
    assert payload["citations"] == []
    assert payload["guidance"]["documents"] == ["notes"]
    assert payload["guidance"]["examples"] == ['What does "notes" say about ...?']
    assert "stored" in payload["message"].lower()
    assert generation.calls == 0, "guidance must never consult generation"
    assert not HEX_ID.search(payload["message"])
    assert not any(HEX_ID.search(e) for e in payload["guidance"]["examples"])


def test_generic_question_with_empty_library_still_abstains(client):
    test_client, _generation = client
    response = test_client.post(
        "/api/v1/query", json={"question": "tell me everything"}
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["decision"] == "ABSTAIN"
    assert payload["guidance"] is None


def test_topic_scoped_broad_question_gets_a_cited_answer(client):
    test_client, _generation = client
    _upload(test_client)
    response = test_client.post(
        "/api/v1/query",
        json={"question": "what does the document say about retrieval and citations?"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["decision"] == "ANSWERED"
    assert payload["citations"], "a grounded overview must carry citations"


def test_topical_phrasing_never_routes_to_guidance(client):
    test_client, _generation = client
    _upload(test_client)
    response = test_client.post(
        "/api/v1/query", json={"question": "tell me everything about deployment"}
    )
    assert response.status_code == 200
    # "deployment" shares no vocabulary with the stored chunks, so the
    # honest outcome is abstention — but it must NOT be guidance, which
    # is reserved for prompts with no topic at all.
    assert response.json()["decision"] == "ABSTAIN"


def test_specific_question_behaviour_unchanged(client):
    test_client, _generation = client
    _upload(test_client)
    response = test_client.post(
        "/api/v1/query",
        json={"question": "How does GroundTruth stores uploaded documents as evidence?"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["decision"] == "ANSWERED"
    assert payload["guidance"] is None


def test_frontend_renders_guidance_distinctly():
    app_js = Path("src/groundtruth/api/static/app.js").read_text()
    assert 'payload.decision === "GUIDANCE"' in app_js
    assert "turn-guidance" in app_js
    # Guidance is neither the answer box nor the decline box.
    guidance_block = app_js.split('decision === "GUIDANCE"')[1].split(
        'decision === "ABSTAIN"'
    )[0]
    assert "turn-answer" not in guidance_block
    assert "turn-decline" not in guidance_block
    # Example questions fill the composer (textContent only, no HTML).
    assert 'question-input' in guidance_block
    assert ".value = example" in guidance_block
