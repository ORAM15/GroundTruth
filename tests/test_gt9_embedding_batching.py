"""GT-9: Gemini embedding batching + API error-message surfacing.

Production root cause: a 46-page PDF parsed to 966 chunks and
``GeminiEmbeddingProvider.embed()`` sent all of them in ONE
``batchEmbedContents`` request. Google accepts at most 100 inputs per
batch request, so the upload failed with a bare ``400 Bad Request`` whose
response body (which names the actual problem) was never surfaced.

These tests use a recording httpx MockTransport — no network, no key.
The vector for text ``"text-<i>"`` is ``[float(i)]`` so concatenation
order across batches is directly assertable.
"""

from __future__ import annotations

import json

import httpx
import pytest

from groundtruth.evidence.embeddings import (
    MAX_BATCH_INPUTS,
    EmbeddingError,
    GeminiEmbeddingProvider,
)
from groundtruth.generation import GeminiGenerationProvider, GenerationError


class RecordingEmbeddingClient:
    """Wraps an httpx.Client whose handler records each request's inputs
    and answers with one distinguishable vector per input text."""

    def __init__(self) -> None:
        self.request_sizes: list[int] = []

        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content)
            requests = body["requests"]
            self.request_sizes.append(len(requests))
            embeddings = []
            for item in requests:
                text = item["content"]["parts"][0]["text"]
                index = float(text.removeprefix("text-"))
                embeddings.append({"values": [index]})
            return httpx.Response(200, json={"embeddings": embeddings})

        self.client = httpx.Client(transport=httpx.MockTransport(handler))


def make_provider(client: httpx.Client) -> GeminiEmbeddingProvider:
    return GeminiEmbeddingProvider(api_key="<redacted>", client=client)


def test_250_texts_are_batched_100_100_50_and_concatenated_in_order():
    recording = RecordingEmbeddingClient()
    provider = make_provider(recording.client)
    texts = [f"text-{i}" for i in range(250)]
    vectors = provider.embed(texts)
    assert recording.request_sizes == [100, 100, 50]
    assert all(size <= MAX_BATCH_INPUTS for size in recording.request_sizes)
    assert vectors == [[float(i)] for i in range(250)]


def test_exactly_100_texts_are_a_single_request():
    recording = RecordingEmbeddingClient()
    provider = make_provider(recording.client)
    vectors = provider.embed([f"text-{i}" for i in range(100)])
    assert recording.request_sizes == [100]
    assert vectors == [[float(i)] for i in range(100)]


def test_small_input_stays_a_single_request():
    recording = RecordingEmbeddingClient()
    provider = make_provider(recording.client)
    vectors = provider.embed([f"text-{i}" for i in range(6)])
    assert recording.request_sizes == [6]
    assert vectors == [[float(i)] for i in range(6)]


def test_101_texts_split_into_two_requests():
    recording = RecordingEmbeddingClient()
    provider = make_provider(recording.client)
    provider.embed([f"text-{i}" for i in range(101)])
    assert recording.request_sizes == [100, 1]


def test_error_response_surfaces_googles_message():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400,
            json={
                "error": {
                    "code": 400,
                    "message": "Request contains an invalid argument.",
                    "status": "INVALID_ARGUMENT",
                }
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = make_provider(client)
    with pytest.raises(EmbeddingError) as excinfo:
        provider.embed(["anything"])
    assert "Request contains an invalid argument." in str(excinfo.value)
    assert "test-key" not in str(excinfo.value)


def test_error_in_a_later_batch_still_surfaces_googles_message():
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            body = json.loads(request.content)
            return httpx.Response(
                200,
                json={"embeddings": [{"values": [0.0]}] * len(body["requests"])},
            )
        return httpx.Response(
            400, json={"error": {"message": "Request contains an invalid argument."}}
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = make_provider(client)
    with pytest.raises(EmbeddingError) as excinfo:
        provider.embed([f"text-{i}" for i in range(150)])
    assert "Request contains an invalid argument." in str(excinfo.value)


def test_error_without_json_body_falls_back_to_status_line():
    client = httpx.Client(
        transport=httpx.MockTransport(lambda request: httpx.Response(500, text="oops"))
    )
    provider = make_provider(client)
    with pytest.raises(EmbeddingError) as excinfo:
        provider.embed(["anything"])
    assert "500" in str(excinfo.value)


def test_generation_error_response_surfaces_googles_message():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400,
            json={"error": {"message": "Request contains an invalid argument."}},
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    provider = GeminiGenerationProvider(api_key="<redacted>", client=client)
    with pytest.raises(GenerationError) as excinfo:
        provider.generate("anything")
    assert "Request contains an invalid argument." in str(excinfo.value)
    assert "test-key" not in str(excinfo.value)
