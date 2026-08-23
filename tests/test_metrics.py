import pytest

from groundtruth.evaluation.metrics import retrieval_metrics


def test_retrieval_metrics_are_deterministic():
    metrics = retrieval_metrics([1, 3, None, 12])
    assert metrics.recall_at_1 == 0.25
    assert metrics.recall_at_3 == 0.5
    assert metrics.recall_at_5 == 0.5
    assert metrics.recall_at_10 == 0.5
    assert metrics.mrr == pytest.approx((1 + 1 / 3 + 1 / 12) / 4)
