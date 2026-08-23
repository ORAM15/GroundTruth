from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping, Protocol, Sequence

from groundtruth.domain.models import Chunk
from groundtruth.retrieval.models import RetrievalResult


class EmbeddingProvider(Protocol):
    """Provider-neutral embedding contract; concrete providers are wired later."""

    def embed(self, text: str) -> Sequence[float]: ...


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right):
        raise ValueError("Embedding dimensions must match")
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return sum(a * b for a, b in zip(left, right)) / (left_norm * right_norm)


@dataclass(frozen=True)
class DenseRetriever:
    chunks: Sequence[Chunk]
    embeddings: Mapping[str, Sequence[float]]
    provider: EmbeddingProvider

    def retrieve(self, query: str, top_k: int = 10) -> list[RetrievalResult]:
        if top_k < 1:
            raise ValueError("top_k must be at least 1")
        query_vector = self.provider.embed(query)
        scored: list[tuple[float, Chunk]] = []
        for chunk in self.chunks:
            vector = self.embeddings.get(chunk.chunk_id)
            if vector is None:
                continue
            scored.append((cosine_similarity(query_vector, vector), chunk))
        scored.sort(key=lambda item: (-item[0], item[1].ordinal))
        return [
            RetrievalResult(chunk=chunk, rank=rank, score=score, method="dense")
            for rank, (score, chunk) in enumerate(scored[:top_k], start=1)
        ]
