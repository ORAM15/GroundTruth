"""Persistence of parsed documents into the evidence store.

Writes domain :class:`~groundtruth.domain.models.Document` /
:class:`~groundtruth.domain.models.DocumentVersion` objects into the
SQLAlchemy row models defined in :mod:`groundtruth.evidence.db`.

Idempotency: document versions are content-addressed. If a version row with
the same ``content_hash`` already exists, nothing is written and the existing
ids are returned with ``duplicate=True`` — re-uploading the same file is a
safe no-op.

Two write paths share the row builders below:

* :func:`persist_document` — one transaction for the whole document. Kept
  for store-level callers and tests that persist small documents.
* :func:`persist_document_sliced` — the API upload path (GT-10). Chunks are
  embedded and committed in slices of at most :data:`INGEST_SLICE_SIZE`, so
  the work done inside one HTTP request stays bounded no matter how large
  the document is. A failure in any slice deletes the partially stored
  document before the original error propagates, so callers never observe
  a half-ingested document.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from groundtruth.domain.models import Chunk, Document, DocumentVersion
from groundtruth.evidence.db import (
    ChunkEmbeddingRow,
    ChunkRow,
    DocumentRow,
    DocumentVersionRow,
)

logger = logging.getLogger(__name__)

# Maximum number of chunks embedded + committed per slice by
# persist_document_sliced. Bounds the peak memory and the size of any
# single SQL statement (100 embedding rows of 3072 dimensions is ~4 MB of
# parameters) inside one upload request, independent of document size.
INGEST_SLICE_SIZE = 100


@dataclass(frozen=True)
class StoredDocument:
    document_id: str
    version_id: str
    chunk_count: int
    duplicate: bool


@dataclass(frozen=True)
class DocumentSummary:
    """One row of the documents list: enough for a UI to show what has
    been uploaded without loading chunk content."""

    document_id: str
    title: str
    filename: str | None
    pages: int | None
    chunk_count: int
    created_at: datetime | None


def list_documents(session_factory) -> list[DocumentSummary]:
    """All stored documents, newest first, with their total chunk count
    across versions. ``filename``/``pages`` come from the upload metadata
    recorded at ingest time; documents stored without that metadata (older
    or programmatic writes) report them as ``None``."""
    session = session_factory()
    try:
        chunk_counts = dict(
            session.query(DocumentVersionRow.document_id, func.count(ChunkRow.id))
            .join(ChunkRow, ChunkRow.document_version_id == DocumentVersionRow.id)
            .group_by(DocumentVersionRow.document_id)
            .all()
        )
        rows = (
            session.query(DocumentRow)
            .order_by(DocumentRow.created_at.desc(), DocumentRow.id)
            .all()
        )
        return [
            DocumentSummary(
                document_id=row.id,
                title=row.title,
                filename=(row.metadata_json or {}).get("filename"),
                pages=(row.metadata_json or {}).get("pages"),
                chunk_count=chunk_counts.get(row.id, 0),
                created_at=row.created_at,
            )
            for row in rows
        ]
    finally:
        session.close()


def find_stored_version(session_factory, content_hash: str) -> StoredDocument | None:
    """Return the stored version for ``content_hash``, or ``None``.

    Lets callers detect a duplicate upload before paying for work (such as
    embedding calls) that a duplicate would waste."""
    session = session_factory()
    try:
        row = (
            session.query(DocumentVersionRow)
            .filter_by(content_hash=content_hash)
            .one_or_none()
        )
        if row is None:
            return None
        return StoredDocument(
            document_id=row.document_id,
            version_id=row.id,
            chunk_count=len(row.chunks),
            duplicate=True,
        )
    finally:
        session.close()


def _chunk_row(chunk: Chunk, version_id: str) -> ChunkRow:
    return ChunkRow(
        id=chunk.chunk_id,
        document_version_id=version_id,
        section_id=chunk.section_id,
        ordinal=chunk.ordinal,
        text=chunk.text,
        canonical_embedding_text=chunk.text,
        content_hash=chunk.content_hash,
        page_start=chunk.page_start,
        page_end=chunk.page_end,
        source_span=dict(chunk.source_span),
        structural_path=list(chunk.structural_path),
        representation_version=chunk.representation_version,
    )


def _embedding_row(
    chunk: Chunk,
    vector: Sequence[float],
    *,
    model_provider: str,
    model_name: str,
) -> ChunkEmbeddingRow:
    return ChunkEmbeddingRow(
        chunk_id=chunk.chunk_id,
        model_provider=model_provider,
        model_name=model_name,
        representation_version=chunk.representation_version,
        dimensions=len(vector),
        vector=list(vector),
    )


def _add_document_and_version(session, document: Document, version: DocumentVersion) -> None:
    """Add the document + version rows and flush, so later inserts in the
    same transaction can reference them (GT-8's FK-safe ordering)."""
    if session.get(DocumentRow, document.document_id) is None:
        session.add(
            DocumentRow(
                id=document.document_id,
                title=document.title,
                source_type=document.source_type,
                source_uri=document.source_uri,
                metadata_json=dict(document.metadata),
            )
        )
    session.add(
        DocumentVersionRow(
            id=version.version_id,
            document_id=document.document_id,
            version_label=version.version_label,
            source_uri=version.source_uri,
            content_hash=version.content_hash,
            effective_from=version.effective_from,
            effective_until=version.effective_until,
        )
    )
    session.flush()


def persist_document(
    session_factory,
    document: Document,
    version: DocumentVersion,
    *,
    embeddings: Sequence[Sequence[float]] | None = None,
    model_provider: str = "",
    model_name: str = "",
) -> StoredDocument:
    """Persist ``document`` + ``version`` (+ optional chunk embeddings).

    ``embeddings``, when supplied, must contain exactly one vector per chunk
    in ``version.chunks``; they are written as :class:`ChunkEmbeddingRow`
    rows tagged with ``model_provider`` / ``model_name``.
    """
    if embeddings is not None and len(embeddings) != len(version.chunks):
        raise ValueError(
            f"Got {len(embeddings)} embeddings for {len(version.chunks)} chunks."
        )

    session = session_factory()
    try:
        existing = (
            session.query(DocumentVersionRow)
            .filter_by(content_hash=version.content_hash)
            .one_or_none()
        )
        if existing is not None:
            return StoredDocument(
                document_id=existing.document_id,
                version_id=existing.id,
                chunk_count=len(existing.chunks),
                duplicate=True,
            )

        # Insert order must be deterministic: the row classes declare FK
        # columns but ChunkEmbeddingRow has no ORM relationship to ChunkRow,
        # so the unit of work cannot infer that chunks must be inserted
        # before their embeddings. Without the explicit flushes below, a
        # single commit() may flush chunk_embeddings first, which an
        # FK-enforcing database (Postgres in production) rejects. Flush in
        # dependency order inside this transaction instead: document +
        # version, then chunks, then embeddings.
        try:
            _add_document_and_version(session, document, version)
            for chunk in version.chunks:
                session.add(_chunk_row(chunk, version.version_id))
            session.flush()
            if embeddings is not None:
                for chunk, vector in zip(version.chunks, embeddings, strict=True):
                    session.add(
                        _embedding_row(
                            chunk,
                            vector,
                            model_provider=model_provider,
                            model_name=model_name,
                        )
                    )
            session.commit()
        except IntegrityError:
            # A concurrent upload of the same content won the race; treat this
            # upload as the duplicate instead of failing it.
            session.rollback()
            winner = (
                session.query(DocumentVersionRow)
                .filter_by(content_hash=version.content_hash)
                .one_or_none()
            )
            if winner is None:
                raise
            return StoredDocument(
                document_id=winner.document_id,
                version_id=winner.id,
                chunk_count=len(winner.chunks),
                duplicate=True,
            )
        return StoredDocument(
            document_id=document.document_id,
            version_id=version.version_id,
            chunk_count=len(version.chunks),
            duplicate=False,
        )
    finally:
        session.close()


def _persist_slice(
    session_factory,
    document: Document,
    version: DocumentVersion,
    slice_chunks: Sequence[Chunk],
    vectors: Sequence[Sequence[float]],
    *,
    first: bool,
    model_provider: str,
    model_name: str,
) -> None:
    """Commit one slice of chunks (+ their embeddings) in its own
    transaction. The first slice also creates the document + version rows;
    later slices append to the version the first slice committed. Keeps
    GT-8's deterministic flush order (parents, chunks, embeddings) inside
    the transaction."""
    session = session_factory()
    try:
        if first:
            _add_document_and_version(session, document, version)
        for chunk in slice_chunks:
            session.add(_chunk_row(chunk, version.version_id))
        session.flush()
        for chunk, vector in zip(slice_chunks, vectors, strict=True):
            session.add(
                _embedding_row(
                    chunk,
                    vector,
                    model_provider=model_provider,
                    model_name=model_name,
                )
            )
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def delete_document(session_factory, document_id: str) -> None:
    """Delete a document and everything attached to it, in one transaction.

    Deletes run in FK-safe order — embeddings, chunks, versions, document —
    because the bulk deletes below do not trigger the ORM delete-orphan
    cascades and ChunkEmbeddingRow has no relationship at all. Deleting a
    document that does not exist is a no-op.
    """
    session = session_factory()
    try:
        version_ids = [
            row_id
            for (row_id,) in session.query(DocumentVersionRow.id)
            .filter_by(document_id=document_id)
            .all()
        ]
        if version_ids:
            chunk_ids = [
                row_id
                for (row_id,) in session.query(ChunkRow.id)
                .filter(ChunkRow.document_version_id.in_(version_ids))
                .all()
            ]
            if chunk_ids:
                session.query(ChunkEmbeddingRow).filter(
                    ChunkEmbeddingRow.chunk_id.in_(chunk_ids)
                ).delete(synchronize_session=False)
                session.query(ChunkRow).filter(ChunkRow.id.in_(chunk_ids)).delete(
                    synchronize_session=False
                )
            session.query(DocumentVersionRow).filter(
                DocumentVersionRow.id.in_(version_ids)
            ).delete(synchronize_session=False)
        session.query(DocumentRow).filter_by(id=document_id).delete(
            synchronize_session=False
        )
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _cleanup_partial_document(session_factory, document_id: str) -> None:
    """Best-effort removal of a partially ingested document. A cleanup
    failure is logged and swallowed so it can never mask the original
    ingestion error that triggered the cleanup."""
    try:
        delete_document(session_factory, document_id)
    except Exception:
        logger.exception(
            "Failed to clean up partially ingested document %s", document_id
        )


def persist_document_sliced(
    session_factory,
    document: Document,
    version: DocumentVersion,
    *,
    embed_slice: Callable[[list[str]], Sequence[Sequence[float]]],
    model_provider: str = "",
    model_name: str = "",
) -> StoredDocument:
    """Persist ``document`` + ``version`` in bounded slices (GT-10).

    For each slice of at most :data:`INGEST_SLICE_SIZE` chunks, ``embed_slice``
    is called with just that slice's texts and the returned vectors are
    committed together with the slice's chunk rows in their own transaction.
    Peak memory and per-statement size therefore stay flat as documents
    grow, unlike :func:`persist_document`, whose single transaction grows
    with the document.

    The operation is atomic from the caller's point of view: if embedding
    or persistence fails for any slice, the partially stored document is
    deleted and the original exception re-raised unchanged. A version with
    the same ``content_hash`` already stored short-circuits before any
    embedding call, exactly like the duplicate pre-check in the API.
    """
    existing = find_stored_version(session_factory, version.content_hash)
    if existing is not None:
        return existing

    chunks = list(version.chunks)
    slices = [
        chunks[start : start + INGEST_SLICE_SIZE]
        for start in range(0, len(chunks), INGEST_SLICE_SIZE)
    ] or [[]]
    try:
        for index, slice_chunks in enumerate(slices):
            vectors: Sequence[Sequence[float]] = []
            if slice_chunks:
                vectors = embed_slice([chunk.text for chunk in slice_chunks])
                if len(vectors) != len(slice_chunks):
                    raise ValueError(
                        f"Embedding callback returned {len(vectors)} vectors "
                        f"for {len(slice_chunks)} chunks."
                    )
            if index == 0:
                try:
                    _persist_slice(
                        session_factory,
                        document,
                        version,
                        slice_chunks,
                        vectors,
                        first=True,
                        model_provider=model_provider,
                        model_name=model_name,
                    )
                except IntegrityError:
                    # A concurrent upload of the same content won the race
                    # (ids are content-addressed, so its rows carry the same
                    # primary keys); treat this upload as the duplicate
                    # instead of failing it — and do NOT clean up, the rows
                    # now in the store are the winner's, not ours.
                    winner = find_stored_version(session_factory, version.content_hash)
                    if winner is None:
                        raise
                    return winner
            else:
                _persist_slice(
                    session_factory,
                    document,
                    version,
                    slice_chunks,
                    vectors,
                    first=False,
                    model_provider=model_provider,
                    model_name=model_name,
                )
    except Exception:
        _cleanup_partial_document(session_factory, document.document_id)
        raise
    return StoredDocument(
        document_id=document.document_id,
        version_id=version.version_id,
        chunk_count=len(chunks),
        duplicate=False,
    )
