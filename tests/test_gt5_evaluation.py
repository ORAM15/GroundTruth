"""GT-5: the golden evaluation dataset, harness and committed report.

Three guards:
1. The dataset is valid and mechanically scoreable (category counts,
   expectations, gold references pointing at real corpus documents).
2. The harness runs end-to-end on a small subset and produces metrics
   (gold references resolve against the seeded store, cases are recorded).
3. The committed report matches the committed raw run output — the
   report is re-rendered from the JSON and must be identical, so a
   hand-edited number in the report fails this test.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from groundtruth.evaluation.e2e_metrics import compute_end_to_end_metrics
from groundtruth.evaluation.golden.generate_corpus import CORPUS_DIR
from groundtruth.evaluation.run_golden import (
    DEFAULT_OUTPUT,
    DEFAULT_REPORT,
    build_report,
    load_golden_cases,
    run_evaluation,
)

EXPECTED_CATEGORIES = {"answerable": 12, "unanswerable": 8, "adversarial": 6}
EXPECTED_OUTCOMES = {"ANSWERED", "ANSWERED_SAFE", "SAFE", "ABSTAIN"}


def test_golden_dataset_shape_and_references():
    cases = load_golden_cases()
    assert Counter(case.category for case in cases) == EXPECTED_CATEGORIES
    ids = [case.case_id for case in cases]
    assert len(ids) == len(set(ids)), "case ids must be unique"
    corpus_files = {path.name.replace(".txt", ".pdf") for path in CORPUS_DIR.glob("*.txt")}
    for case in cases:
        assert case.expected in EXPECTED_OUTCOMES
        assert case.question.strip()
        if case.category == "answerable":
            assert case.expected == "ANSWERED"
            assert case.key_fact
        if case.gold_contains is not None:
            assert case.gold_document in corpus_files
            assert case.key_fact
        if case.category in {"unanswerable", "adversarial"} and case.expected != "ANSWERED_SAFE":
            assert case.gold_contains is None or case.category == "adversarial"
        if case.expected in {"ANSWERED_SAFE", "SAFE"}:
            assert case.injected_target


def test_corpus_sources_have_one_fact_per_line():
    # The harness's gold resolution assumes each source line becomes one
    # chunk; blank or heading-like lines would break that mapping.
    for path in CORPUS_DIR.glob("*.txt"):
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        assert len(lines) >= 5
        for line in lines:
            assert not line.rstrip().endswith(":")
            assert not line.isupper()


def test_harness_smoke_run_on_subset():
    output = run_evaluation(
        mode="doubles",
        case_ids={"ans-01", "unans-01", "adv-01", "adv-02"},
        include_sweep=False,
    )
    assert output["providers"]["mode"] == "evaluation-doubles"
    assert len(output["corpus"]) == 4
    assert all(doc["chunk_count"] >= 5 for doc in output["corpus"])
    results = output["main_run"]["cases"]
    assert {r["case_id"] for r in results} == {"ans-01", "unans-01", "adv-01", "adv-02"}
    by_id = {r["case_id"]: r for r in results}
    # Gold resolution happened: the answerable case carries a real chunk id.
    assert by_id["ans-01"]["gold_chunk_ids"]
    assert by_id["ans-01"]["status_code"] == 200
    assert by_id["ans-01"]["latency_ms"] >= 0
    metrics = compute_end_to_end_metrics(results)
    assert metrics.case_count == 4
    for value in (
        metrics.retrieval_hit_rate_at_k,
        metrics.answered_rate_answerable,
        metrics.abstention_accuracy_unanswerable,
        metrics.adversarial_safety_rate,
    ):
        assert 0.0 <= value <= 1.0
    retrieval = output["main_run"]["retrieval_metrics"]
    assert 0.0 <= retrieval["mrr"] <= 1.0


def test_committed_report_matches_committed_raw_output():
    output = json.loads(Path(DEFAULT_OUTPUT).read_text(encoding="utf-8"))
    report = Path(DEFAULT_REPORT).read_text(encoding="utf-8")
    assert build_report(output) == report
    # And the headline metrics re-derive from the raw per-case records.
    recomputed = compute_end_to_end_metrics(output["main_run"]["cases"])
    recorded = output["main_run"]["metrics"]
    assert recomputed.retrieval_hit_rate_at_k == recorded["retrieval_hit_rate_at_k"]
    assert recomputed.answered_rate_answerable == recorded["answered_rate_answerable"]
    assert recomputed.false_answer_rate == recorded["false_answer_rate"]
    assert recomputed.adversarial_safety_rate == recorded["adversarial_safety_rate"]
