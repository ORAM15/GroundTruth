"""Persistence of parsed documents into the evidence store.

Writes domain :class:`~groundtruth.domain.models.Document` /
:class:`~groundtruth.domain.models.DocumentVersion` objects into the
SQLAlchemy row models defined in :mod:`groundtruth.evidence.db`.

Idempotency: document versions are content-addressed. If a version row with
the same ``content_hash`` already exists, nothing is written and the existing
ids are returned with ``duplicate=True`` — re-uploading the same file is a
safe no-op.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from groundtruth.domain.models import Document, DocumentVersion
from groundtruth.evidence.db import (
    ChunkEmbeddingRow,
    ChunkRow,
    DocumentRow,
    DocumentVersionRow,
)


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
        for chunk in version.chunks:
            session.add(
                ChunkRow(
                    id=chunk.chunk_id,
                    document_version_id=version.version_id,
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
            )
        if embeddings is not None:
            for chunk, vector in zip(version.chunks, embeddings, strict=True):
                session.add(
                    ChunkEmbeddingRow(
                        chunk_id=chunk.chunk_id,
                        model_provider=model_provider,
                        model_name=model_name,
                        representation_version=chunk.representation_version,
                        dimensions=len(vector),
                        vector=list(vector),
                    )
                )
        try:
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
