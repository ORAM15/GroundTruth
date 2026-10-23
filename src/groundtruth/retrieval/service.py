"""Query-time retrieval over the persisted evidence store (GT-2).

Loads every stored chunk and its embedding from the database (demo scale:
in-memory scoring is fine and keeps one code path for SQLite/Postgres),
then runs the existing retrievers — lexical, dense, and their RRF hybrid —
without any new ranking math.

Abstention contract (the trust core of GroundTruth):

* If nothing is stored, or no chunk has an embedding, the query abstains.
* Otherwise the *best dense cosine similarity* must clear an explicit
  threshold before any evidence is returned. Lexical matches alone can
  never override a failing dense score: a question can share words with a
  chunk while being about something else entirely, and answering from it
  would be fabrication with citations attached.
* The threshold defaults to 0.35 and is configurable via the
  ``GT_MIN_EVIDENCE_SCORE`` environment variable. 0.35 sits in the
  0.3–0.4 band where Gemini-embedding cosine similarity typically
  separates topical matches from unrelated text; it is a starting value,
  not a measured one — GT-5 will calibrate it against the golden dataset
  and this default will be revisited with that data.
"""

from __future__ import annotations

import os
from collections.abc import Sequence
from dataclasses import dataclass

from groundtruth.domain.models import Chunk
from groundtruth.evidence.db import ChunkEmbeddingRow, ChunkRow, DocumentRow, DocumentVersionRow
from groundtruth.evidence.embeddings import EmbeddingProvider as BatchEmbeddingProvider
from groundtruth.retrieval.dense import DenseRetriever
from groundtruth.retrieval.hybrid import HybridRetriever
from groundtruth.retrieval.lexical import LexicalRetriever
from groundtruth.retrieval.models import RetrievalResult

DEFAULT_MIN_EVIDENCE_SCORE = 0.35
MIN_EVIDENCE_SCORE_ENV = "GT_MIN_EVIDENCE_SCORE"


def min_evidence_score() -> float:
    """The dense-cosine evidence threshold, read per call so operators
    (and tests) can tune it via ``GT_MIN_EVIDENCE_SCORE`` without a
    restart. An unparseable value falls back to the default rather than
    crashing the query path."""
    raw = os.getenv(MIN_EVIDENCE_SCORE_ENV)
    if raw is None:
        return DEFAULT_MIN_EVIDENCE_SCORE
    try:
        return float(raw)
    except ValueError:
        return DEFAULT_MIN_EVIDENCE_SCORE


class _SingleTextAdapter:
    """Adapt the batch embedding provider (GT-1) to the single-text
    protocol :class:`DenseRetriever` was written against."""

    def __init__(self, provider: BatchEmbeddingProvider) -> None:
        self._provider = provider

    def embed(self, text: str) -> Sequence[float]:
        vectors = self._provider.embed([text])
        if not vectors:
            raise ValueError("Embedding provider returned no vector for the query.")
        return vectors[0]


@dataclass(frozen=True)
class EvidenceHit:
    """One fused retrieval result plus everything the API needs to cite it."""

    result: RetrievalResult
    document_id: str
    title: str | None
    filename: str | None
    dense_score: float | None


@dataclass(frozen=True)
class QueryOutcome:
    sufficient: bool
    reason: str
    hits: tuple[EvidenceHit, ...]
    best_dense_score: float | None


def _load_corpus(session_factory):
    """Load all stored chunks as domain objects plus their embeddings and
    per-document citation metadata (title / original filename)."""
    session = session_factory()
    try:
        versions = {row.id: row for row in session.query(DocumentVersionRow).all()}
        documents = {row.id: row for row in session.query(DocumentRow).all()}
        chunks: list[Chunk] = []
        for row in session.query(ChunkRow).order_by(ChunkRow.ordinal).all():
            chunks.append(
                Chunk(
                    chunk_id=row.id,
                    document_version_id=row.document_version_id,
                    text=row.text,
                    section_id=row.section_id,
                    ordinal=row.ordinal,
                    page_start=row.page_start,
                    page_end=row.page_end,
                    source_span=dict(row.source_span or {}),
                    structural_path=tuple(row.structural_path or ()),
                    content_hash=row.content_hash,
                    representation_version=row.representation_version,
                )
            )
        embeddings: dict[str, list[float]] = {}
        for row in session.query(ChunkEmbeddingRow).all():
            embeddings[row.chunk_id] = list(row.vector)

        def citation(chunk: Chunk) -> tuple[str, str | None, str | None]:
            version = versions.get(chunk.document_version_id)
            document_id = version.document_id if version else ""
            document = documents.get(document_id)
            if document is None:
                return document_id, None, None
            filename = (document.metadata_json or {}).get("filename")
            return document_id, document.title, filename

        return chunks, embeddings, citation
    finally:
        session.close()


def search(
    session_factory,
    provider: BatchEmbeddingProvider,
    question: str,
    *,
    top_k: int = 10,
    threshold: float | None = None,
) -> QueryOutcome:
    """Run hybrid retrieval for ``question`` over the evidence store and
    apply the abstention gate described in the module docstring."""
    chunks, embeddings, citation = _load_corpus(session_factory)
    if not chunks:
        return QueryOutcome(
            sufficient=False,
            reason="The evidence store is empty; no documents have been uploaded yet.",
            hits=(),
            best_dense_score=None,
        )

    dense = DenseRetriever(
        chunks=chunks, embeddings=embeddings, provider=_SingleTextAdapter(provider)
    )
    # Score every embedded chunk once: the best dense score is the gate.
    dense_results = dense.retrieve(question, top_k=max(len(chunks), 1))
    if not dense_results:
        return QueryOutcome(
            sufficient=False,
            reason="Stored chunks have no embeddings; semantic evidence cannot be assessed.",
            hits=(),
            best_dense_score=None,
        )
    dense_scores = {result.chunk.chunk_id: result.score for result in dense_results}
    best_dense_score = dense_results[0].score

    minimum = min_evidence_score() if threshold is None else threshold
    if best_dense_score < minimum:
        return QueryOutcome(
            sufficient=False,
            reason=(
                f"Best semantic match scored {best_dense_score:.3f}, below the "
                f"evidence threshold of {minimum:.3f}; abstaining rather than "
                "answering from weak evidence."
            ),
            hits=(),
            best_dense_score=best_dense_score,
        )

    hybrid = HybridRetriever(lexical=LexicalRetriever(chunks), dense=dense)
    fused = hybrid.retrieve(question, top_k=top_k)
    hits = tuple(
        EvidenceHit(
            result=result,
            document_id=(cite := citation(result.chunk))[0],
            title=cite[1],
            filename=cite[2],
            dense_score=dense_scores.get(result.chunk.chunk_id),
        )
        for result in fused
    )
    return QueryOutcome(
        sufficient=True,
        reason=f"{len(hits)} chunk(s) cleared the evidence threshold.",
        hits=hits,
        best_dense_score=best_dense_score,
    )
