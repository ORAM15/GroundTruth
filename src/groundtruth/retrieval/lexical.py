from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Sequence

from groundtruth.domain.models import Chunk
from groundtruth.retrieval.models import RetrievalResult


@dataclass(frozen=True)
class LexicalRetriever:
    chunks: Sequence[Chunk]

    def retrieve(self, query: str, top_k: int = 10) -> list[RetrievalResult]:
        terms = self._terms(query)
        scored: list[tuple[float, Chunk]] = []
        for chunk in self.chunks:
            haystack = chunk.text.lower()
            score = sum(haystack.count(term) for term in terms)
            if score:
                scored.append((float(score), chunk))
        scored.sort(key=lambda item: (-item[0], item[1].ordinal))
        return [RetrievalResult(chunk=c, rank=i, score=s, method="lexical") for i, (s, c) in enumerate(scored[:top_k], 1)]

    @staticmethod
    def _terms(query: str) -> Iterable[str]:
        return [term for term in re.findall(r"[\w-]+", query.lower()) if len(term) > 1]
