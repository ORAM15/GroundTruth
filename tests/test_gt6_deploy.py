"""GT-6: deployment scaffolding — database URL handling for Neon/Render.

Covers the two production blockers that local SQLite tests cannot surface:

1. Neon hands out bare ``postgresql://`` URLs, which SQLAlchemy resolves
   to psycopg2; this project ships psycopg v3, so bare URLs must be
   normalised to ``postgresql+psycopg://`` before ``create_engine``.
2. On a fresh Postgres database the pgvector ``vector`` extension must be
   created before the ``chunk_embeddings`` table; that step must run for
   the postgresql dialect only (SQLite has no extensions).

No live Postgres is used: dialect gating is tested with a recording fake
engine, and the extension only ever executes against a real server via
``create_session_factory`` in production.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Self

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect

from groundtruth.api.app import app
from groundtruth.evidence import db as db_module
from groundtruth.evidence.db import (
    create_session_factory,
    ensure_extensions,
    normalize_database_url,
)

# ---------------------------------------------------------------------------
# 1. URL normalisation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        # Bare provider URLs (what Neon copies into the dashboard) -> psycopg v3.
        (
            "postgresql://user:pass@ep-xyz.us-east-2.aws.neon.tech/neondb?sslmode=require",
            "postgresql+psycopg://user:pass@ep-xyz.us-east-2.aws.neon.tech/neondb?sslmode=require",
        ),
        (
            "postgres://user:pass@host.example.com:5432/db",
            "postgresql+psycopg://user:pass@host.example.com:5432/db",
        ),
        # Already-qualified URLs are untouched, whichever driver they name.
        ("postgresql+psycopg://user:pass@host/db", "postgresql+psycopg://user:pass@host/db"),
        ("postgresql+psycopg2://user:pass@host/db", "postgresql+psycopg2://user:pass@host/db"),
        # Non-Postgres URLs are untouched.
        ("sqlite:///./groundtruth.db", "sqlite:///./groundtruth.db"),
        ("sqlite:///:memory:", "sqlite:///:memory:"),
    ],
)
def test_normalize_database_url(raw, expected):
    assert normalize_database_url(raw) == expected


def test_create_session_factory_normalises_url_before_create_engine(monkeypatch):
    captured: dict[str, str] = {}
    real_create_engine = db_module.create_engine

    def spy(url, **kwargs):
        captured["url"] = url
        # Return a real (SQLite) engine so create_all can run; the point of
        # this test is only which URL string reaches create_engine.
        return real_create_engine("sqlite://", **kwargs)

    monkeypatch.setattr(db_module, "create_engine", spy)
    factory, engine = create_session_factory(
        "postgresql://user:pass@ep-xyz.aws.neon.tech/neondb?sslmode=require"
    )
    try:
        assert (
            captured["url"]
            == "postgresql+psycopg://user:pass@ep-xyz.aws.neon.tech/neondb?sslmode=require"
        )
        assert factory is not None
    finally:
        engine.dispose()


# ---------------------------------------------------------------------------
# 2. pgvector extension gating
# ---------------------------------------------------------------------------


class _RecordingConnection:
    def __init__(self) -> None:
        self.statements: list[str] = []

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc: object) -> bool:
        return False

    def execute(self, clause, *args, **kwargs) -> None:
        self.statements.append(str(clause))


class _FakeEngine:
    """Minimal stand-in for a SQLAlchemy Engine: just a dialect name and a
    ``begin()`` that hands out a recording connection."""

    def __init__(self, dialect_name: str) -> None:
        self.dialect = SimpleNamespace(name=dialect_name)
        self.connection = _RecordingConnection()
        self.begin_calls = 0

    def begin(self) -> _RecordingConnection:
        self.begin_calls += 1
        return self.connection


def test_ensure_extensions_creates_vector_for_postgresql():
    engine = _FakeEngine("postgresql")
    ensure_extensions(engine)
    assert engine.begin_calls == 1
    assert engine.connection.statements == ["CREATE EXTENSION IF NOT EXISTS vector"]


def test_ensure_extensions_is_noop_for_sqlite():
    engine = _FakeEngine("sqlite")
    ensure_extensions(engine)
    assert engine.begin_calls == 0
    assert engine.connection.statements == []


def test_sqlite_session_factory_creates_full_schema_without_extensions(tmp_path):
    """The SQLite path used by every other test and by local development:
    no extension step, and create_all still builds every table (the
    pgvector column type compiles on SQLite with the pinned versions)."""
    factory, engine = create_session_factory(f"sqlite:///{tmp_path}/deploy.db")
    try:
        table_names = set(inspect(engine).get_table_names())
        assert {"documents", "document_versions", "chunks", "chunk_embeddings"} <= table_names
        assert factory is not None
    finally:
        engine.dispose()


# ---------------------------------------------------------------------------
# 3. Deploy-style configuration smoke test
# ---------------------------------------------------------------------------


def test_app_health_and_ready_with_deploy_style_env(monkeypatch, tmp_path):
    """With the two env vars a Render service would carry, the app must
    import, report healthy, and report ready (store configured)."""
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/deploy-smoke.db")
    monkeypatch.setenv("GEMINI_API_KEY", "test-only-placeholder-not-a-real-key")
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json() == {"status": "ok"}
        ready = client.get("/ready")
        assert ready.status_code == 200
        assert ready.json() == {"status": "ready"}
