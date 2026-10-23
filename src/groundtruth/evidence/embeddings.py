"""Embedding providers.

The API depends on the :class:`EmbeddingProvider` protocol, never on a
concrete vendor class, so tests can substitute a deterministic fake provider
through FastAPI dependency injection. There is deliberately no silent
fallback: if the Gemini key is missing or the API call fails, an
:class:`EmbeddingError` is raised and the upload fails loudly instead of
persisting fake vectors.
"""

from __future__ import annotations

import os
from collections.abc import Sequence
from typing import Protocol, runtime_checkable

import httpx

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_MODEL = "gemini-embedding-001"
PROVIDER_NAME = "google-gemini"

# batchEmbedContents rejects requests with more than 100 inputs
# (400 INVALID_ARGUMENT), so embed() splits larger inputs into groups
# of at most this size — a 46-page PDF can parse to ~1000 chunks.
MAX_BATCH_INPUTS = 100

# Cap on how much of Google's error message is surfaced in EmbeddingError.
MAX_ERROR_MESSAGE_CHARS = 500


class EmbeddingError(RuntimeError):
    """Raised when embeddings cannot be produced (missing key, API failure,
    or a malformed response)."""


def _api_error_detail(response: httpx.Response) -> str:
    """Best-effort human-readable detail for an error response: Google's
    ``error.message`` from the JSON body when present (it contains no
    secrets), otherwise the HTTP status line. Truncated so a pathological
    body cannot flood logs or the UI."""
    detail = ""
    try:
        message = response.json()["error"]["message"]
        if isinstance(message, str):
            detail = message
    except (ValueError, KeyError, TypeError):
        detail = ""
    if not detail:
        detail = response.reason_phrase or f"HTTP {response.status_code}"
    return detail[:MAX_ERROR_MESSAGE_CHARS]


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Anything that can turn texts into embedding vectors."""

    provider_name: str
    model_name: str

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Return one vector per input text, in the same order."""
        ...


class GeminiEmbeddingProvider:
    """Embedding provider backed by the Gemini API (batchEmbedContents)."""

    provider_name = PROVIDER_NAME

    def __init__(
        self,
        api_key: str | None = None,
        *,
        model: str = DEFAULT_MODEL,
        client: httpx.Client | None = None,
        timeout: float = 30.0,
    ) -> None:
        key = api_key if api_key is not None else os.getenv("GEMINI_API_KEY")
        if not key:
            raise EmbeddingError(
                "GEMINI_API_KEY is not set; the Gemini embedding provider cannot "
                "run. Set the environment variable or inject a different provider."
            )
        self._api_key = key
        self.model_name = model
        self._client = client or httpx.Client(timeout=timeout)

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors: list[list[float]] = []
        for start in range(0, len(texts), MAX_BATCH_INPUTS):
            batch = texts[start : start + MAX_BATCH_INPUTS]
            vectors.extend(self._embed_batch(batch))
        if len(vectors) != len(texts):
            raise EmbeddingError(
                f"Gemini returned {len(vectors)} embeddings for {len(texts)} texts."
            )
        return vectors

    def _embed_batch(self, texts: Sequence[str]) -> list[list[float]]:
        """One batchEmbedContents call for at most MAX_BATCH_INPUTS texts."""
        url = f"{GEMINI_BASE_URL}/models/{self.model_name}:batchEmbedContents"
        body = {
            "requests": [
                {
                    "model": f"models/{self.model_name}",
                    "content": {"parts": [{"text": text}]},
                }
                for text in texts
            ]
        }
        try:
            response = self._client.post(
                url,
                json=body,
                headers={
                    "x-goog-api-key": self._api_key,
                    "Content-Type": "application/json",
                },
            )
        except httpx.HTTPError as exc:
            raise EmbeddingError(f"Gemini embedding request failed: {exc}") from exc
        if response.is_error:
            raise EmbeddingError(
                f"Gemini embedding request failed with HTTP {response.status_code}: "
                f"{_api_error_detail(response)}"
            )
        try:
            payload = response.json()
            embeddings = payload["embeddings"]
            vectors = [list(map(float, item["values"])) for item in embeddings]
        except (KeyError, TypeError, ValueError) as exc:
            raise EmbeddingError(f"Malformed Gemini embedding response: {exc}") from exc
        if len(vectors) != len(texts):
            raise EmbeddingError(
                f"Gemini returned {len(vectors)} embeddings for {len(texts)} texts."
            )
        return vectors
