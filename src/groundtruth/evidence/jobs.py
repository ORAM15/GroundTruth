"""Background ingestion jobs (GT-11).

Large documents (> one slice) cannot be embedded synchronously: the
free-tier quota allows ~100 embedded items per minute, so a multi-slice
document needs minutes of paced calls — longer than a request may stay
open on Render's free edge. The upload endpoint therefore records a job
row, returns 202, and runs this module's worker as a FastAPI background
task in the same process (no new service; free tier only).

Job lifecycle: ``processing`` → ``succeeded`` | ``failed``. A job row is
created synchronously by the endpoint, so the documents list and
retrieval can exclude the document from the moment the 202 is returned.
On terminal failure the worker deletes the partial document (GT-10's
``delete_document``) and marks the job failed; the job row itself is
kept, so a later re-upload of the same content can reset it instead of
colliding on the unique ``document_id``.

A ``processing`` job left behind by a dead process (issue #53: instance
spin-down or restart mid-job) can never complete — the worker is
in-process — so application startup recovers it (see
``recover_stale_processing_jobs``): the job is marked failed and any
partial document rows are removed, making the content re-uploadable.
The partial-row cleanup is load-bearing, not cosmetic: without it a
re-upload's first slice would collide with the leftover rows and
``persist_document_sliced`` would mistake the partial document for a
concurrent winner's complete one, marking the job succeeded with only
some slices stored.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.exc import IntegrityError

from groundtruth.domain.models import Document, DocumentVersion
from groundtruth.evidence import store
from groundtruth.evidence.db import IngestionJobRow
from groundtruth.evidence.embeddings import EmbeddingError
from groundtruth.evidence.pacing import QuotaPacer, pacer_from_env

logger = logging.getLogger(__name__)

MAX_EMBED_RETRIES = 5
MAX_ERROR_CHARS = 1000

# Stable prefix of the error text recovery writes on an interrupted job.
# The UI keys its "ingestion interrupted — retry" message off this
# prefix (no schema change: the jobs table has no status vocabulary
# beyond processing | succeeded | failed, and the deployed table is
# created by create_all, which cannot add a column).
INTERRUPTED_ERROR_PREFIX = "Ingestion was interrupted"


@dataclass(frozen=True)
class IngestionJob:
    """Detached snapshot of an ingestion job row (safe to use after the
    session that loaded it is closed)."""

    document_id: str
    version_id: str
    filename: str | None
    status: str  # processing | succeeded | failed
    chunks_done: int
    chunks_total: int
    error: str | None
    created_at: datetime | None
    updated_at: datetime | None


def _to_job(row: IngestionJobRow) -> IngestionJob:
    return IngestionJob(
        document_id=row.document_id,
        version_id=row.version_id,
        filename=row.filename,
        status=row.status,
        chunks_done=row.chunks_done,
        chunks_total=row.chunks_total,
        error=row.error,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def create_ingestion_job(
    session_factory,
    *,
    document_id: str,
    version_id: str,
    filename: str | None,
    chunks_total: int,
) -> IngestionJob:
    """Insert a ``processing`` job row, or return the existing row if a
    concurrent upload of the same content already created one (the
    ``document_id`` unique constraint makes the race safe to absorb)."""
    session = session_factory()
    try:
        row = IngestionJobRow(
            document_id=document_id,
            version_id=version_id,
            filename=filename,
            status="processing",
            chunks_done=0,
            chunks_total=chunks_total,
            error=None,
        )
        session.add(row)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            existing = (
                session.query(IngestionJobRow)
                .filter_by(document_id=document_id)
                .one_or_none()
            )
            if existing is None:
                raise
            return _to_job(existing)
        return _to_job(row)
    finally:
        session.close()


def get_ingestion_job(session_factory, document_id: str) -> IngestionJob | None:
    """Return the job snapshot for ``document_id``, or ``None``."""
    session = session_factory()
    try:
        row = (
            session.query(IngestionJobRow)
            .filter_by(document_id=document_id)
            .one_or_none()
        )
        return _to_job(row) if row is not None else None
    finally:
        session.close()


def update_ingestion_job(session_factory, document_id: str, **fields) -> None:
    """Apply field updates to a job row; a no-op when the row is gone."""
    session = session_factory()
    try:
        row = (
            session.query(IngestionJobRow)
            .filter_by(document_id=document_id)
            .one_or_none()
        )
        if row is None:
            return
        for key, value in fields.items():
            setattr(row, key, value)
        session.commit()
    finally:
        session.close()


def reset_ingestion_job(session_factory, document_id: str) -> None:
    """Return a failed job to ``processing`` for a fresh upload attempt."""
    update_ingestion_job(
        session_factory, document_id, status="processing", chunks_done=0, error=None
    )


def recover_stale_processing_jobs(session_factory) -> int:
    """Recover ``processing`` jobs left behind by a dead process (#53).

    The worker is in-process, so a ``processing`` job cannot survive a
    restart by definition: any such row found at startup belongs to a
    worker that will never report again. Each is marked ``failed`` with
    an interruption error (so a re-upload takes the existing failed-job
    path and schedules a fresh worker) and its partial document rows
    are removed first — without that cleanup a re-upload's first slice
    would collide with the leftovers and be mistaken for a concurrent
    winner's complete document (see the module docstring). Succeeded
    and failed jobs are untouched. Returns how many jobs recovered.
    Idempotent: a second run finds nothing to do.
    """
    session = session_factory()
    try:
        stale_ids = [
            row_id
            for (row_id,) in session.query(IngestionJobRow.document_id)
            .filter(IngestionJobRow.status == "processing")
            .all()
        ]
    finally:
        session.close()
    for document_id in stale_ids:
        try:
            store.delete_document(session_factory, document_id)
        except Exception:
            # The DB is unusable if even the cleanup fails; still mark
            # the job failed rather than leave it stuck processing —
            # the next restart retries the cleanup.
            logger.exception(
                "Failed to clean up partially ingested document %s during "
                "stale-job recovery",
                document_id,
            )
        update_ingestion_job(
            session_factory,
            document_id,
            status="failed",
            error=(
                f"{INTERRUPTED_ERROR_PREFIX} (the service restarted before "
                "the job finished); upload the document again to retry."
            ),
        )
    return len(stale_ids)


def embed_with_retry(
    embed_fn: Callable[[list[str]], Sequence[Sequence[float]]],
    texts: list[str],
    pacer: QuotaPacer,
    max_retries: int = MAX_EMBED_RETRIES,
) -> Sequence[Sequence[float]]:
    """Embed one slice with quota pacing and bounded 429 retries.

    Only 429s are retried: the pacer waits out the provider's
    ``Retry-After`` delay when one is known, otherwise the rest of the
    quota window. Any other error fails immediately — retrying a
    rejection (e.g. 400) cannot succeed. After ``max_retries`` failed
    retries the last error propagates.
    """
    pacer.acquire(len(texts))
    attempts = 0
    while True:
        try:
            return embed_fn(texts)
        except EmbeddingError as exc:
            if exc.status_code != 429 or attempts >= max_retries:
                raise
            attempts += 1
            pacer.note_rate_limit(exc.retry_after)


def run_ingestion_job(
    session_factory,
    embedding_provider,
    document: Document,
    version: DocumentVersion,
    *,
    model_provider: str = "",
    model_name: str = "",
    pacer: QuotaPacer | None = None,
    max_retries: int = MAX_EMBED_RETRIES,
) -> None:
    """Background worker for one large document.

    Embeds + persists slice by slice through GT-10's
    ``persist_document_sliced`` (which already deletes a partial
    document if a slice fails), updating the job's progress after each
    slice. On success the job is marked succeeded; on failure the job
    is marked failed with the error text and the partial document is
    gone (deleted by the sliced persist, with an idempotent
    ``delete_document`` here as a safety net for failures outside it).
    Progress-update failures are logged and swallowed — they must never
    mask the ingestion outcome they report.
    """
    quota = pacer if pacer is not None else pacer_from_env()
    embedded = 0

    def embed_slice(texts: list[str]) -> Sequence[Sequence[float]]:
        nonlocal embedded
        vectors = embed_with_retry(embedding_provider.embed, texts, quota, max_retries)
        embedded += len(texts)
        try:
            update_ingestion_job(
                session_factory, document.document_id, chunks_done=embedded
            )
        except Exception:
            logger.exception(
                "Failed to update ingestion progress for %s", document.document_id
            )
        return vectors

    try:
        stored = store.persist_document_sliced(
            session_factory,
            document,
            version,
            embed_slice=embed_slice,
            model_provider=model_provider,
            model_name=model_name,
        )
        update_ingestion_job(
            session_factory,
            document.document_id,
            status="succeeded",
            chunks_done=stored.chunk_count,
        )
    except Exception as exc:
        # The job row is the durable record of this failure (the UI
        # polls it), so the worker deliberately does NOT re-raise:
        # re-raising would surface as an unhandled background-task
        # exception after the 202 was already sent, and under
        # TestClient it would even break the 202 response itself.
        logger.exception("Ingestion job failed for %s", document.document_id)
        try:
            store.delete_document(session_factory, document.document_id)
        except Exception:
            logger.exception(
                "Failed to clean up partially ingested document %s",
                document.document_id,
            )
        try:
            update_ingestion_job(
                session_factory,
                document.document_id,
                status="failed",
                error=str(exc)[:MAX_ERROR_CHARS],
            )
        except Exception:
            logger.exception(
                "Failed to mark ingestion job failed for %s", document.document_id
            )
