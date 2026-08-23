from __future__ import annotations

from dataclasses import dataclass

from groundtruth.retrieval.models import RetrievalResult, Retriever, reciprocal_rank_fusion


@dataclass(frozen=True)
class HybridRetriever:
    lexical: Retriever
    dense: Retriever
    fusion_k: int = 60

    def retrieve(self, query: str, top_k: int = 10) -> list[RetrievalResult]:
        if top_k < 1:
            raise ValueError("top_k must be at least 1")
        lexical_results = self.lexical.retrieve(query, top_k=top_k)
        dense_results = self.dense.retrieve(query, top_k=top_k)
        return reciprocal_rank_fusion(lexical_results, dense_results, k=self.fusion_k)[:top_k]
