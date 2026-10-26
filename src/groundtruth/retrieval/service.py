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

Document scoping (issue #65): a query may name one document, and then
*only* that document's chunks form the corpus — the lexical retriever,
the dense retriever (and therefore the dense gate's best score), and
the RRF fusion all see the scoped corpus and nothing else. Unscoped
queries behave exactly as before. A scope naming no stored document
fails loudly (``UnknownDocumentError``) — it never silently falls back
to library-wide search, because a silent fallback would answer from a
document the user did not ask about.

Per-document caps (issue #67): an *unscoped* query no longer runs one
RRF top-k over the whole library, where a large document's many
similar chunks crowd small documents out of the evidence set. Instead
it retrieves per document first (at most ``PER_DOCUMENT_CAP`` chunks
each), then merges those per-document rankings by fused score and
truncates to ``top_k``. The cap is a guarantee of inclusion, not a
promise about final counts: a document's best chunks always reach the
merge, even when another document has hundreds of similar ones. The
scoped path is unchanged — it already searches a single document.
A consequence to know: with few documents stored, the final evidence
set may be smaller than ``top_k`` (at most cap x documents), because
no filler chunks are added past the per-document rankings.
"""

from __future__ import annotations

import os
from collections.abc import Sequence
from dataclasses import dataclass

from groundtruth.domain.models import Chunk
from groundtruth.evidence.db import ChunkEmbeddingRow, ChunkRow, DocumentRow, DocumentVersionRow
from groundtruth.evidence.embeddings import EmbeddingProvider as BatchEmbeddingProvider
from groundtruth.evidence.store import incomplete_document_ids
from groundtruth.retrieval.dense import DenseRetriever
from groundtruth.retrieval.hybrid import HybridRetriever
from groundtruth.retrieval.lexical import LexicalRetriever
from groundtruth.retrieval.models import RetrievalResult

DEFAULT_MIN_EVIDENCE_SCORE = 0.35
MIN_EVIDENCE_SCORE_ENV = "GT_MIN_EVIDENCE_SCORE"

# Issue #67: at most this many chunks per document in an unscoped
# query's per-document retrieval, before the merge. 3 is a deliberate
# small number: enough for a document's best passages to be present,
# small enough that no single document can dominate the merge.
PER_DOCUMENT_CAP = 3


class UnknownDocumentError(ValueError):
    """A query scoped to a document id with no stored document row.

    Raised (and mapped to HTTP 404 by the API) rather than falling back
    to unscoped search: answering from another document when the user
    scoped to one would be the exact failure issue #65 fixes.
    """


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


class _FixedVectorProvider:
    """Serve one already-computed query vector to every retriever in a
    single search. Issue #67 retrieves per document, which would
    otherwise call the embedding provider once per document; the query
    vector is identical every time, so embed it once and reuse it.
    A query now makes exactly one embedding call total — previously
    the gate and the hybrid each embedded the question, so two."""

    def __init__(self, vector: Sequence[float]) -> None:
        self._vector = vector

    def embed(self, text: str) -> Sequence[float]:
        return self._vector


@dataclass(frozen=True)
class EvidenceHit:
    """One fused retrieval result plus everything the API needs to cite it."""

    result: RetrievalResult
    document_id: str
    title: str | None
    filename: str | None
    dense_score: float | None


@dataclass(frozen=True)
class CoverageEntry:
    """One document's contribution to the final evidence set (issue
    #67): how many of the returned chunks came from it. The API
    exposes this as the coverage strip; it is computed from the
    returned hits, never from a separate count, so it cannot drift
    from what the answer was actually grounded in."""

    document_id: str
    title: str | None
    chunk_count: int


@dataclass(frozen=True)
class QueryOutcome:
    sufficient: bool
    reason: str
    hits: tuple[EvidenceHit, ...]
    best_dense_score: float | None
    coverage: tuple[CoverageEntry, ...] = ()


def _load_corpus(session_factory, document_id=None):
    """Load stored chunks as domain objects plus their embeddings and
    per-document citation metadata (title / original filename).

    Chunks belonging to documents whose ingestion has not completed
    (GT-11 background jobs still ``processing`` or ``failed``) are
    excluded: a half-ingested document must never be answered from, even
    though its first slices are already committed.

    When ``document_id`` is given, only that document's chunks are
    loaded (issue #65 scoping); the returned ``documents`` map still
    covers every stored document so callers can tell "unknown document"
    apart from "known document with no searchable chunks".
    """
    session = session_factory()
    try:
        excluded = incomplete_document_ids(session)
        versions = {row.id: row for row in session.query(DocumentVersionRow).all()}
        documents = {row.id: row for row in session.query(DocumentRow).all()}
        chunks: list[Chunk] = []
        for row in session.query(ChunkRow).order_by(ChunkRow.ordinal).all():
            version = versions.get(row.document_version_id)
            if version is None or version.document_id in excluded:
                continue
            if document_id is not None and version.document_id != document_id:
                continue
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
        kept_ids = {chunk.chunk_id for chunk in chunks}
        embeddings: dict[str, list[float]] = {}
        for row in session.query(ChunkEmbeddingRow).all():
            if row.chunk_id in kept_ids:
                embeddings[row.chunk_id] = list(row.vector)

        def citation(chunk: Chunk) -> tuple[str, str | None, str | None]:
            version = versions.get(chunk.document_version_id)
            doc_id = version.document_id if version else ""
            document = documents.get(doc_id)
            if document is None:
                return doc_id, None, None
            filename = (document.metadata_json or {}).get("filename")
            return doc_id, document.title, filename

        return chunks, embeddings, citation, documents, excluded
    finally:
        session.close()


def search(
    session_factory,
    provider: BatchEmbeddingProvider,
    question: str,
    *,
    top_k: int = 10,
    threshold: float | None = None,
    document_id: str | None = None,
) -> QueryOutcome:
    """Run hybrid retrieval for ``question`` over the evidence store and
    apply the abstention gate described in the module docstring.

    When ``document_id`` is given, only that document's chunks form the
    corpus (issue #65); an unknown id raises ``UnknownDocumentError``
    and a known-but-unsearchable document abstains with a scoped reason
    — neither case ever falls back to library-wide search.

    When no scope is given (issue #67), retrieval runs per document
    first (at most ``PER_DOCUMENT_CAP`` chunks each), then merges by
    fused score into the final evidence set of at most ``top_k`` hits.
    The dense gate above the fusion still runs over the whole corpus,
    exactly as before.
    """
    chunks, embeddings, citation, documents, excluded = _load_corpus(
        session_factory, document_id
    )
    if document_id is not None:
        if document_id not in documents:
            raise UnknownDocumentError(
                f"Unknown document id: {document_id}; no scoped search "
                "was performed."
            )
        if document_id in excluded:
            return QueryOutcome(
                sufficient=False,
                reason=(
                    "The scoped document is still being ingested (or its "
                    "ingestion failed); no chunks are searchable yet."
                ),
                hits=(),
                best_dense_score=None,
            )
        if not chunks:
            return QueryOutcome(
                sufficient=False,
                reason="The scoped document has no stored chunks.",
                hits=(),
                best_dense_score=None,
            )
    if not chunks:
        return QueryOutcome(
            sufficient=False,
            reason="The evidence store is empty; no documents have been uploaded yet.",
            hits=(),
            best_dense_score=None,
        )

    # Embed the question once and reuse the vector for the gate and
    # for every retriever below: per-document retrieval must not turn
    # one query into one embedding call per document.
    query_vector = _SingleTextAdapter(provider).embed(question)
    dense = DenseRetriever(
        chunks=chunks, embeddings=embeddings, provider=_FixedVectorProvider(query_vector)
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

    if document_id is not None:
        # Issue #65, unchanged: one hybrid ranking over the scoped
        # corpus only.
        fused = HybridRetriever(
            lexical=LexicalRetriever(chunks), dense=dense
        ).retrieve(question, top_k=top_k)
    else:
        # Issue #67: retrieve per document first, then merge by fused
        # score. Grouping uses the same citation mapping that builds
        # the hits, so a chunk's document is never guessed twice.
        by_document: dict[str, list[Chunk]] = {}
        for chunk in chunks:
            by_document.setdefault(citation(chunk)[0], []).append(chunk)
        seeds: list[RetrievalResult] = []
        for doc_chunks in by_document.values():
            doc_dense = DenseRetriever(
                chunks=doc_chunks,
                embeddings=embeddings,
                provider=_FixedVectorProvider(query_vector),
            )
            seeds.extend(
                HybridRetriever(
                    lexical=LexicalRetriever(doc_chunks), dense=doc_dense
                ).retrieve(question, top_k=PER_DOCUMENT_CAP)
            )
        # Fused scores are per-document RRF ranks, so comparing them
        # across documents is approximate — but it preserves the
        # within-document order that matters, and the deterministic
        # tie-break (chunk ordinal, then chunk id) keeps the merge
        # stable when two documents' top chunks tie.
        ordered = sorted(
            seeds,
            key=lambda result: (
                -result.score,
                result.chunk.ordinal,
                result.chunk.chunk_id,
            ),
        )
        fused = [
            RetrievalResult(
                chunk=result.chunk,
                rank=index,
                score=result.score,
                method=result.method,
                lexical_rank=result.lexical_rank,
                dense_rank=result.dense_rank,
            )
            for index, result in enumerate(ordered[:top_k], start=1)
        ]
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
    counts: dict[str, int] = {}
    titles: dict[str, str | None] = {}
    for hit in hits:
        counts[hit.document_id] = counts.get(hit.document_id, 0) + 1
        titles[hit.document_id] = hit.title
    coverage = tuple(
        CoverageEntry(
            document_id=doc_id,
            title=titles[doc_id],
            chunk_count=count,
        )
        for doc_id, count in sorted(
            counts.items(), key=lambda item: (-item[1], titles[item[0]] or item[0])
        )
    )
    return QueryOutcome(
        sufficient=True,
        reason=f"{len(hits)} chunk(s) cleared the evidence threshold.",
        hits=hits,
        best_dense_score=best_dense_score,
        coverage=coverage,
    )
