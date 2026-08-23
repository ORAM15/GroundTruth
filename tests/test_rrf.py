import pytest

from groundtruth.domain.models import Chunk
from groundtruth.retrieval.models import RetrievalResult, reciprocal_rank_fusion


def result(chunk_id: str, ordinal: int, rank: int, method: str) -> RetrievalResult:
    return RetrievalResult(
        chunk=Chunk(
            chunk_id=chunk_id,
            document_version_id="doc:v1",
            text=chunk_id,
            section_id=None,
            ordinal=ordinal,
        ),
        rank=rank,
        score=1.0,
        method=method,
    )


def test_rrf_is_deterministic_for_equal_scores():
    fused = reciprocal_rank_fusion(
        [result("b", 2, 1, "lexical")],
        [result("a", 1, 1, "dense")],
    )
    assert [item.chunk.chunk_id for item in fused] == ["a", "b"]


def test_rrf_rejects_invalid_k():
    with pytest.raises(ValueError):
        reciprocal_rank_fusion([], k=0)
