from datetime import datetime

from groundtruth.domain.models import Chunk
from groundtruth.evaluation.dataset import RetrievalCase
from groundtruth.evaluation.runner import evaluate_retriever
from groundtruth.retrieval.lexical import LexicalRetriever


def chunk(chunk_id: str, text: str, ordinal: int) -> Chunk:
    return Chunk(
        chunk_id=chunk_id,
        document_version_id="version-1",
        text=text,
        section_id=None,
        ordinal=ordinal,
    )


def test_evaluation_uses_explicit_gold_evidence():
    chunks = [
        chunk("c1", "Python is used for data analysis.", 1),
        chunk("c2", "PostgreSQL stores relational data.", 2),
    ]
    retriever = LexicalRetriever(chunks)
    cases = [
        RetrievalCase("answerable", "Python data analysis", frozenset({"c1"})),
        RetrievalCase("unanswerable", "Kubernetes orchestration", frozenset(), answerable=False),
    ]

    evaluation = evaluate_retriever(retriever, cases, top_k=2)

    assert evaluation.results[0].first_relevant_rank == 1
    assert evaluation.results[1].first_relevant_rank is None
    assert evaluation.metrics.recall_at_1 == 1.0
    assert evaluation.metrics.mrr == 1.0


def test_answerable_case_without_gold_evidence_is_rejected():
    try:
        RetrievalCase("bad", "question", frozenset())
    except ValueError as exc:
        assert "gold chunk" in str(exc)
    else:
        raise AssertionError("expected ValueError")
