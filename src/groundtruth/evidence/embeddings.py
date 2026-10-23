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


class EmbeddingError(RuntimeError):
    """Raised when embeddings cannot be produced (missing key, API failure,
    or a malformed response)."""


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
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise EmbeddingError(f"Gemini embedding request failed: {exc}") from exc
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
