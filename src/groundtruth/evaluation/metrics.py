from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class RetrievalMetrics:
    recall_at_1: float
    recall_at_3: float
    recall_at_5: float
    recall_at_10: float
    mrr: float


def _recall_at(ranks: Sequence[int | None], k: int) -> float:
    if not ranks:
        return 0.0
    return sum(1 for rank in ranks if rank is not None and rank <= k) / len(ranks)


def retrieval_metrics(first_relevant_ranks: Sequence[int | None]) -> RetrievalMetrics:
    values = [rank for rank in first_relevant_ranks if rank is not None]
    mrr = sum(1.0 / rank for rank in values) / len(first_relevant_ranks) if first_relevant_ranks else 0.0
    return RetrievalMetrics(
        recall_at_1=_recall_at(first_relevant_ranks, 1),
        recall_at_3=_recall_at(first_relevant_ranks, 3),
        recall_at_5=_recall_at(first_relevant_ranks, 5),
        recall_at_10=_recall_at(first_relevant_ranks, 10),
        mrr=mrr,
    )
