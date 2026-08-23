from groundtruth.domain.models import Chunk
from groundtruth.retrieval.dense import DenseRetriever, cosine_similarity
from groundtruth.retrieval.hybrid import HybridRetriever
from groundtruth.retrieval.lexical import LexicalRetriever


class FakeEmbedder:
    vectors = {
        "database question": (1.0, 0.0),
        "postgres": (0.9, 0.1),
        "vector search": (0.0, 1.0),
    }

    def embed(self, text: str):
        return self.vectors[text]


def chunk(chunk_id: str, text: str, ordinal: int) -> Chunk:
    return Chunk(
        chunk_id=chunk_id,
        document_version_id="doc:v1",
        text=text,
        section_id=None,
        ordinal=ordinal,
    )


def test_cosine_similarity_handles_zero_vectors():
    assert cosine_similarity((0.0, 0.0), (1.0, 0.0)) == 0.0


def test_dense_retriever_ranks_by_cosine_similarity():
    chunks = [
        chunk("a", "postgres", 1),
        chunk("b", "vector search", 2),
    ]
    retriever = DenseRetriever(
        chunks=chunks,
        embeddings={"a": (0.9, 0.1), "b": (0.0, 1.0)},
        provider=FakeEmbedder(),
    )

    results = retriever.retrieve("database question")

    assert [result.chunk.chunk_id for result in results] == ["a", "b"]
    assert results[0].method == "dense"
    assert results[0].rank == 1


def test_hybrid_retriever_fuses_lexical_and_dense_rankings():
    chunks = [
        chunk("a", "postgres database", 1),
        chunk("b", "vector search", 2),
    ]
    lexical = LexicalRetriever(chunks)
    dense = DenseRetriever(
        chunks=chunks,
        embeddings={"a": (0.9, 0.1), "b": (0.0, 1.0)},
        provider=FakeEmbedder(),
    )

    results = HybridRetriever(lexical=lexical, dense=dense).retrieve("database question")

    assert results[0].method == "hybrid"
    assert results[0].lexical_rank == 1
    assert results[0].dense_rank == 1
