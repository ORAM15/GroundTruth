"""Text-generation providers (GT-3).

The API depends on the :class:`GenerationProvider` protocol, never on a
concrete vendor class, so tests can substitute a deterministic fake through
FastAPI dependency injection — the same pattern GT-1 established for
embeddings. There is deliberately no silent fallback: if the Gemini key is
missing or the API call fails, a :class:`GenerationError` is raised and the
query fails loudly (503/502) instead of returning a fabricated answer.
"""

from __future__ import annotations

import os
from typing import Protocol, runtime_checkable

import httpx

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_MODEL = "gemini-2.5-flash"
MODEL_ENV = "GT_GENERATION_MODEL"
PROVIDER_NAME = "google-gemini"

# Cap on how much of Google's error message is surfaced in GenerationError.
MAX_ERROR_MESSAGE_CHARS = 500


class GenerationError(RuntimeError):
    """Raised when an answer cannot be generated (missing key, API failure,
    or a malformed response)."""


def _api_error_detail(response: httpx.Response) -> str:
    """Best-effort human-readable detail for an error response: Google's
    ``error.message`` from the JSON body when present (it contains no
    secrets), otherwise the HTTP status line. Truncated so a pathological
    body cannot flood logs or the UI. Mirrors the embeddings provider."""
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
class GenerationProvider(Protocol):
    """Anything that can turn a fully-built prompt into answer text."""

    provider_name: str
    model_name: str

    def generate(self, prompt: str) -> str:
        """Return the model's answer text for ``prompt``."""
        ...


class GeminiGenerationProvider:
    """Generation provider backed by the Gemini API (generateContent)."""

    provider_name = PROVIDER_NAME

    def __init__(
        self,
        api_key: str | None = None,
        *,
        model: str | None = None,
        client: httpx.Client | None = None,
        timeout: float = 30.0,
    ) -> None:
        key = api_key if api_key is not None else os.getenv("GEMINI_API_KEY")
        if not key:
            raise GenerationError(
                "GEMINI_API_KEY is not set; the Gemini generation provider cannot "
                "run. Set the environment variable or inject a different provider."
            )
        self._api_key = key
        self.model_name = model or os.getenv(MODEL_ENV) or DEFAULT_MODEL
        self._client = client or httpx.Client(timeout=timeout)

    def generate(self, prompt: str) -> str:
        url = f"{GEMINI_BASE_URL}/models/{self.model_name}:generateContent"
        body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}]}
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
            raise GenerationError(f"Gemini generation request failed: {exc}") from exc
        if response.is_error:
            raise GenerationError(
                f"Gemini generation request failed with HTTP {response.status_code}: "
                f"{_api_error_detail(response)}"
            )
        try:
            payload = response.json()
            parts = payload["candidates"][0]["content"]["parts"]
            text = "".join(str(part.get("text", "")) for part in parts)
        except (KeyError, IndexError, TypeError) as exc:
            raise GenerationError(f"Malformed Gemini generation response: {exc}") from exc
        if not text.strip():
            raise GenerationError("Gemini generation returned an empty answer.")
        return text
