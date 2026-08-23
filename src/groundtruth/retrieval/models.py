from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

from groundtruth.domain.models import Chunk


@dataclass(frozen=True)
class RetrievalResult:
    chunk: Chunk
    rank: int
    score: float
    method: str
    lexical_rank: int | None = None
    dense_rank: int | None = None


class Retriever(Protocol):
    def retrieve(self, query: str, top_k: int = 10) -> Sequence[RetrievalResult]: ...


def reciprocal_rank_fusion(*ranked_lists: Sequence[RetrievalResult], k: int = 60) -> list[RetrievalResult]:
    """Fuse independent rankings without assuming score calibration."""
    fused: dict[str, dict] = {}
    for results in ranked_lists:
        for result in results:
            key = result.chunk.chunk_id
            entry = fused.setdefault(key, {"chunk": result.chunk, "score": 0.0, "lexical_rank": None, "dense_rank": None})
            entry["score"] += 1.0 / (k + result.rank)
            if result.method == "lexical":
                entry["lexical_rank"] = result.rank
            if result.method == "dense":
                entry["dense_rank"] = result.rank
    ordered = sorted(fused.values(), key=lambda item: item["score"], reverse=True)
    return [
        RetrievalResult(
            chunk=item["chunk"],
            rank=index,
            score=item["score"],
            method="hybrid",
            lexical_rank=item["lexical_rank"],
            dense_rank=item["dense_rank"],
        )
        for index, item in enumerate(ordered, start=1)
    ]
