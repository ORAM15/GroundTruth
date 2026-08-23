from groundtruth.domain.models import Chunk
from groundtruth.retrieval.models import RetrievalResult, reciprocal_rank_fusion


def chunk(name: str) -> Chunk:
    return Chunk(chunk_id=name, document_version_id="doc:v1", text=name, section_id=None, ordinal=1)


def test_rrf_promotes_consensus():
    a = RetrievalResult(chunk("a"), 1, 1.0, "lexical")
    b = RetrievalResult(chunk("b"), 2, 0.5, "lexical")
    c = RetrievalResult(chunk("c"), 1, 1.0, "dense")
    a_dense = RetrievalResult(a.chunk, 2, 0.5, "dense")
    result = reciprocal_rank_fusion([a, b], [a_dense, c])
    assert result[0].chunk.chunk_id == "a"
    assert result[0].lexical_rank == 1
    assert result[0].dense_rank == 2


def test_chunk_hash_is_deterministic():
    one = chunk("same")
    two = chunk("same")
    assert one.content_hash == two.content_hash
