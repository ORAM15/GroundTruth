from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from groundtruth.evaluation.dataset import RetrievalCase
from groundtruth.evaluation.metrics import RetrievalMetrics, retrieval_metrics
from groundtruth.retrieval.models import RetrievalResult, Retriever


@dataclass(frozen=True)
class RetrievalCaseResult:
    case_id: str
    first_relevant_rank: int | None
    retrieved_chunk_ids: tuple[str, ...]


@dataclass(frozen=True)
class RetrievalEvaluation:
    results: tuple[RetrievalCaseResult, ...]
    metrics: RetrievalMetrics


def evaluate_retriever(
    retriever: Retriever,
    cases: Sequence[RetrievalCase],
    *,
    top_k: int = 10,
) -> RetrievalEvaluation:
    """Evaluate retrieval against explicit gold chunk IDs.

    Unanswerable cases are retained in the result set but do not contribute a
    retrieval rank because there is no gold evidence to retrieve.
    """

    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    case_results: list[RetrievalCaseResult] = []
    ranks: list[int | None] = []
    for case in cases:
        retrieved: Sequence[RetrievalResult] = retriever.retrieve(case.question, top_k=top_k)
        ids = tuple(result.chunk.chunk_id for result in retrieved)
        first_rank = next(
            (result.rank for result in retrieved if result.chunk.chunk_id in case.gold_chunk_ids),
            None,
        ) if case.answerable else None
        case_results.append(
            RetrievalCaseResult(
                case_id=case.case_id,
                first_relevant_rank=first_rank,
                retrieved_chunk_ids=ids,
            )
        )
        if case.answerable:
            ranks.append(first_rank)

    return RetrievalEvaluation(results=tuple(case_results), metrics=retrieval_metrics(ranks))
