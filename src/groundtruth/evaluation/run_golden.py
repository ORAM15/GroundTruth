"""GT-5 golden evaluation harness: end-to-end, measured, auditable.

What a run does:

1. Seeds the golden corpus (``evaluation/golden/corpus/*.txt``, rendered
   to PDF by :mod:`groundtruth.evaluation.golden.generate_corpus`)
   through the REAL upload path — ``POST /api/v1/documents`` on a
   TestClient bound to a throwaway SQLite database.
2. Resolves each answerable case's gold reference (document filename +
   distinctive substring) to the actual stored chunk id. Gold ids are
   content-addressed, so they are resolved after seeding, never
   hardcoded in the dataset.
3. Runs every case through the REAL ``POST /api/v1/query`` path and
   records the decision, evidence ids, citation ids, answer and latency.
4. Also evaluates the retrieval layer directly with the existing
   :func:`groundtruth.evaluation.runner.evaluate_retriever`.
5. Sweeps ``GT_MIN_EVIDENCE_SCORE`` over the answerable + unanswerable
   cases to expose the answered-rate vs false-answer trade-off.

Providers: by default the deterministic evaluation doubles from
:mod:`groundtruth.evaluation.doubles` are injected (labelled as doubles in
every output — the numbers then validate the pipeline *mechanism*, not
Gemini's production behaviour). With ``--live`` (or ``GT5_LIVE=1``) and
``GEMINI_API_KEY`` set, the real Gemini providers are used instead, with
no code changes.

Outputs: a raw JSON document (every recorded case result, so every
reported number can be re-derived) and a Markdown report rendered from
that same document by :func:`build_report`.

    python -m groundtruth.evaluation.run_golden            # doubles
    GT5_LIVE=1 GEMINI_API_KEY=... python -m groundtruth.evaluation.run_golden
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Self

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from groundtruth.api.app import (
    app,
    get_embedding_provider,
    get_generation_provider,
    get_session_factory,
)
from groundtruth.evaluation.dataset import load_cases
from groundtruth.evaluation.doubles import (
    BagOfWordsEmbeddingProvider,
    TopEvidenceGenerationProvider,
)
from groundtruth.evaluation.e2e_metrics import (
    EndToEndMetrics,
    compute_end_to_end_metrics,
    score_case,
)
from groundtruth.evaluation.golden.generate_corpus import GOLDEN_DIR, corpus_pdfs
from groundtruth.evaluation.runner import evaluate_retriever
from groundtruth.evidence.db import Base, ChunkRow, DocumentRow, DocumentVersionRow
from groundtruth.evidence.embeddings import GeminiEmbeddingProvider
from groundtruth.generation.provider import GeminiGenerationProvider
from groundtruth.retrieval.dense import DenseRetriever
from groundtruth.retrieval.hybrid import HybridRetriever
from groundtruth.retrieval.lexical import LexicalRetriever
from groundtruth.retrieval.service import _load_corpus, _SingleTextAdapter

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT = REPO_ROOT / "docs" / "evaluation" / "gt5_run_output.json"
DEFAULT_REPORT = REPO_ROOT / "docs" / "evaluation" / "GT5_EVALUATION_REPORT.md"
CASES_PATH = GOLDEN_DIR / "cases.json"
SWEEP_THRESHOLDS = (0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50)
TOP_K = 10


@dataclass(frozen=True)
class GoldenCase:
    case_id: str
    category: str
    question: str
    expected: str
    gold_document: str | None = None
    gold_contains: str | None = None
    key_fact: str | None = None
    injected_target: str | None = None


def load_golden_cases(path: Path = CASES_PATH) -> list[GoldenCase]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    cases: list[GoldenCase] = []
    for item in payload["cases"]:
        gold = item.get("gold") or {}
        cases.append(
            GoldenCase(
                case_id=str(item["case_id"]),
                category=str(item["category"]),
                question=str(item["question"]),
                expected=str(item["expected"]),
                gold_document=gold.get("document"),
                gold_contains=gold.get("contains"),
                key_fact=item.get("key_fact"),
                injected_target=item.get("injected_target"),
            )
        )
    return cases


def _providers(mode: str, cases: list[GoldenCase]):
    """Return (embedding_provider, generation_provider, provider_record)."""
    if mode == "live":
        embedding = GeminiEmbeddingProvider()
        generation = GeminiGenerationProvider()
        record = {
            "mode": "live-gemini",
            "embedding": {"provider": embedding.provider_name, "model": embedding.model_name},
            "generation": {"provider": generation.provider_name, "model": generation.model_name},
        }
        return embedding, generation, record
    corpus_texts = [text for _, text in _corpus_texts()]
    embedding = BagOfWordsEmbeddingProvider(corpus_texts + [case.question for case in cases])
    generation = TopEvidenceGenerationProvider()
    record = {
        "mode": "evaluation-doubles",
        "embedding": {"provider": embedding.provider_name, "model": embedding.model_name},
        "generation": {"provider": generation.provider_name, "model": generation.model_name},
    }
    return embedding, generation, record


def _corpus_texts() -> list[tuple[str, str]]:
    from groundtruth.evaluation.golden.generate_corpus import corpus_documents

    return corpus_documents()


class EvaluationRun:
    """A seeded evaluation environment: TestClient + providers + gold ids.

    Seeding goes through the real ``POST /api/v1/documents`` endpoint, so
    the corpus passes through the production parse → chunk → embed →
    persist path before any case runs.
    """

    def __init__(self, mode: str = "doubles", cases: list[GoldenCase] | None = None) -> None:
        self.cases = cases if cases is not None else load_golden_cases()
        self.embedding, self.generation, self.provider_record = _providers(mode, self.cases)
        self._tmpdir = tempfile.TemporaryDirectory()
        engine = create_engine(f"sqlite:///{self._tmpdir.name}/gt5.db")
        Base.metadata.create_all(engine)
        self.factory = sessionmaker(bind=engine)
        self.corpus_record: list[dict] = []
        self.gold_ids: dict[str, list[str]] = {}

    def __enter__(self) -> Self:
        app.dependency_overrides[get_session_factory] = lambda: self.factory
        app.dependency_overrides[get_embedding_provider] = lambda: self.embedding
        app.dependency_overrides[get_generation_provider] = lambda: self.generation
        self._client_context = TestClient(app)
        self.client = self._client_context.__enter__()
        self._seed()
        self._resolve_gold()
        return self

    def __exit__(self, *exc) -> None:
        self._client_context.__exit__(*exc)
        app.dependency_overrides.clear()
        self._tmpdir.cleanup()

    def _seed(self) -> None:
        for filename, payload in corpus_pdfs():
            response = self.client.post(
                "/api/v1/documents",
                files={"file": (filename, payload, "application/pdf")},
            )
            if response.status_code != 200:
                raise RuntimeError(f"seeding {filename} failed: {response.status_code}")
            body = response.json()
            self.corpus_record.append(
                {
                    "filename": filename,
                    "document_id": body["document_id"],
                    "pages": body["pages"],
                    "chunk_count": body["chunks"],
                }
            )

    def _resolve_gold(self) -> None:
        session = self.factory()
        try:
            documents = {
                (row.metadata_json or {}).get("filename"): row.id
                for row in session.query(DocumentRow).all()
            }
            versions = {row.id: row.document_id for row in session.query(DocumentVersionRow).all()}
            chunks_by_document: dict[str, list[ChunkRow]] = {}
            for row in session.query(ChunkRow).all():
                document_id = versions.get(row.document_version_id)
                filename = next(
                    (name for name, doc_id in documents.items() if doc_id == document_id), None
                )
                if filename is not None:
                    chunks_by_document.setdefault(filename, []).append(row)
        finally:
            session.close()
        for case in self.cases:
            if case.gold_document is None:
                continue
            matches = [
                row.id
                for row in chunks_by_document.get(case.gold_document, [])
                if case.gold_contains and case.gold_contains in row.text
            ]
            if len(matches) != 1:
                raise RuntimeError(
                    f"gold reference for {case.case_id} resolved to {len(matches)} chunks "
                    f"in {case.gold_document} (expected exactly 1)"
                )
            self.gold_ids[case.case_id] = matches

    def run_case(self, case: GoldenCase) -> dict:
        started = time.perf_counter()
        response = self.client.post(
            "/api/v1/query", json={"question": case.question, "top_k": TOP_K}
        )
        latency_ms = (time.perf_counter() - started) * 1000.0
        body = response.json() if response.status_code == 200 else {}
        return {
            "case_id": case.case_id,
            "category": case.category,
            "question": case.question,
            "expected": case.expected,
            "status_code": response.status_code,
            "decision": body.get("decision"),
            "answer": body.get("answer"),
            "evidence_chunk_ids": [item["chunk_id"] for item in body.get("evidence", [])],
            "citation_chunk_ids": [item["chunk_id"] for item in body.get("citations", [])],
            "gold_chunk_ids": self.gold_ids.get(case.case_id, []),
            "key_fact": case.key_fact,
            "injected_target": case.injected_target,
            "latency_ms": round(latency_ms, 3),
        }

    def run_cases(self, cases: list[GoldenCase]) -> list[dict]:
        return [self.run_case(case) for case in cases]

    def retrieval_layer_metrics(self) -> dict:
        """Retrieval-level metrics via the existing evaluate_retriever,
        over the same seeded corpus and resolved gold ids."""
        chunks, embeddings, _citation, _documents, _excluded = _load_corpus(self.factory)
        retriever = HybridRetriever(
            lexical=LexicalRetriever(chunks),
            dense=DenseRetriever(
                chunks=chunks,
                embeddings=embeddings,
                provider=_SingleTextAdapter(self.embedding),
            ),
        )
        items = [
            {
                "case_id": case.case_id,
                "question": case.question,
                "gold_chunk_ids": self.gold_ids.get(case.case_id, []),
                "answerable": case.case_id in self.gold_ids,
            }
            for case in self.cases
        ]
        evaluation = evaluate_retriever(retriever, load_cases(items), top_k=TOP_K)
        metrics = evaluation.metrics
        return {
            "recall_at_1": metrics.recall_at_1,
            "recall_at_3": metrics.recall_at_3,
            "recall_at_5": metrics.recall_at_5,
            "recall_at_10": metrics.recall_at_10,
            "mrr": metrics.mrr,
        }


def run_evaluation(
    mode: str = "doubles",
    *,
    case_ids: set[str] | None = None,
    include_sweep: bool = True,
) -> dict:
    """Run the full GT-5 evaluation and return the raw output document."""
    all_cases = load_golden_cases()
    selected = [c for c in all_cases if case_ids is None or c.case_id in case_ids]
    previous_threshold = os.environ.pop("GT_MIN_EVIDENCE_SCORE", None)
    try:
        with EvaluationRun(mode=mode, cases=all_cases) as run:
            main_results = run.run_cases(selected)
            retrieval_metrics = run.retrieval_layer_metrics()
            sweep: list[dict] = []
            if include_sweep:
                sweep_cases = [
                    c for c in all_cases if c.category in {"answerable", "unanswerable"}
                ]
                for threshold in SWEEP_THRESHOLDS:
                    os.environ["GT_MIN_EVIDENCE_SCORE"] = str(threshold)
                    try:
                        results = run.run_cases(sweep_cases)
                    finally:
                        del os.environ["GT_MIN_EVIDENCE_SCORE"]
                    metrics = compute_end_to_end_metrics(results)
                    sweep.append(
                        {
                            "threshold": threshold,
                            "answered_rate_answerable": metrics.answered_rate_answerable,
                            "abstention_accuracy_unanswerable": (
                                metrics.abstention_accuracy_unanswerable
                            ),
                            "false_answer_rate_unanswerable": _false_answer_rate(results),
                        }
                    )
            output = {
                "generated_by": "groundtruth.evaluation.run_golden",
                "providers": run.provider_record,
                "threshold_default": 0.35,
                "top_k": TOP_K,
                "corpus": run.corpus_record,
                "main_run": {
                    "cases": main_results,
                    "metrics": _metrics_dict(compute_end_to_end_metrics(main_results)),
                    "retrieval_metrics": retrieval_metrics,
                },
                "sweep": sweep,
            }
        return output
    finally:
        if previous_threshold is not None:
            os.environ["GT_MIN_EVIDENCE_SCORE"] = previous_threshold


def _false_answer_rate(results: list[dict]) -> float:
    expected_abstain = [r for r in results if r["expected"] == "ABSTAIN"]
    if not expected_abstain:
        return 0.0
    return sum(1 for r in expected_abstain if r["decision"] == "ANSWERED") / len(expected_abstain)


def _metrics_dict(metrics: EndToEndMetrics) -> dict:
    return {
        "case_count": metrics.case_count,
        "retrieval_hit_rate_at_k": metrics.retrieval_hit_rate_at_k,
        "answered_rate_answerable": metrics.answered_rate_answerable,
        "fact_containment_rate": metrics.fact_containment_rate,
        "citation_precision": metrics.citation_precision,
        "citation_validity": metrics.citation_validity,
        "abstention_accuracy_unanswerable": metrics.abstention_accuracy_unanswerable,
        "false_answer_rate": metrics.false_answer_rate,
        "adversarial_safety_rate": metrics.adversarial_safety_rate,
        "mean_latency_ms": metrics.mean_latency_ms,
        "p95_latency_ms": metrics.p95_latency_ms,
    }


# ---------------------------------------------------------------------------
# Report rendering. The committed report is produced by build_report from
# the raw output document, and a test asserts the two stay identical, so a
# hand-edited number in the report fails CI.
# ---------------------------------------------------------------------------


def _pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def _num(value: float) -> str:
    return f"{value:.3f}"


def _ms(value: float) -> str:
    return f"{value:.1f} ms"


def recommended_threshold(sweep: list[dict]) -> dict:
    """The sweep row with the best balanced score — the mean of
    answered-rate on answerable cases and abstention accuracy on
    unanswerable cases. Ties go to the lower threshold (it preserves more
    answered-rate headroom for the same safety)."""
    best: dict | None = None
    best_score = -1.0
    for row in sweep:
        score = (row["answered_rate_answerable"] + row["abstention_accuracy_unanswerable"]) / 2
        if score > best_score:
            best, best_score = row, score
    if best is None:
        raise ValueError("sweep is empty")
    return best


def build_report(output: dict) -> str:
    main = output["main_run"]
    cases: list[dict] = main["cases"]
    metrics = main["metrics"]
    retrieval = main["retrieval_metrics"]
    providers = output["providers"]
    by_category: dict[str, list[dict]] = {}
    for case in cases:
        by_category.setdefault(case["category"], []).append(case)
    passed = {name: sum(1 for c in group if score_case(c)) for name, group in by_category.items()}
    failures = [case for case in cases if not score_case(case)]
    best = recommended_threshold(output["sweep"]) if output["sweep"] else None

    lines: list[str] = []
    lines.append("# GT-5 Evaluation Report — Golden Dataset, End-to-End")
    lines.append("")
    lines.append(
        "Issue: ORAM15/GroundTruth#33. This report was generated by "
        "`python -m groundtruth.evaluation.run_golden` from the raw run output in "
        "`docs/evaluation/gt5_run_output.json`, which is committed alongside it; every "
        "number below is computed from that file, and a test fails if the two drift apart."
    )
    lines.append("")
    lines.append("## What was measured, and with what")
    lines.append("")
    lines.append(
        "The golden corpus (4 small documents, listed below) was seeded through the real "
        "`POST /api/v1/documents` upload path, and every case was run through the real "
        "`POST /api/v1/query` path (hybrid retrieval, dense-evidence abstention gate, "
        "grounded generation, citation verification), against a throwaway SQLite database."
    )
    lines.append("")
    if providers["mode"] == "evaluation-doubles":
        lines.append(
            "**Providers: deterministic evaluation doubles** (embedding: "
            f"`{providers['embedding']['provider']}/{providers['embedding']['model']}`, "
            "a lexical bag-of-words embedding; generation: "
            f"`{providers['generation']['provider']}/{providers['generation']['model']}`, "
            "a scripted compliant model that quotes the top evidence block and cites it). "
            "No Gemini API key exists in this environment, so these numbers validate the "
            "pipeline mechanism — gating, ranking, citation enforcement, scoring — and "
            "NOT production behaviour with Gemini embeddings or a real model. See the "
            "limitations section; the same harness runs against the real Gemini providers "
            "with `--live` and no code changes."
        )
    else:
        lines.append(
            "**Providers: live Gemini** (embedding: "
            f"`{providers['embedding']['provider']}/{providers['embedding']['model']}`, "
            "generation: "
            f"`{providers['generation']['provider']}/{providers['generation']['model']}`)."
        )
    lines.append("")
    lines.append("## Dataset")
    lines.append("")
    lines.append("| Document | Stored as | Pages | Chunks |")
    lines.append("|---|---|---|---|")
    for doc in output["corpus"]:
        lines.append(
            f"| {doc['filename']} | {doc['document_id']} | {doc['pages']} | {doc['chunk_count']} |"
        )
    lines.append("")
    lines.append(
        f"Cases: {len(cases)} total — "
        f"{len(by_category.get('answerable', []))} answerable (gold chunk resolved after "
        f"seeding + a key fact the answer must contain), "
        f"{len(by_category.get('unanswerable', []))} unanswerable (expected ABSTAIN), "
        f"{len(by_category.get('adversarial', []))} adversarial (a prompt-injection-bearing "
        "document, injection-targeting and bait questions whose correct outcome is "
        "abstention or a safely cited answer)."
    )
    lines.append("")
    lines.append("## Headline results (main run, default threshold 0.35)")
    lines.append("")
    lines.append("| Metric | Value | Basis |")
    lines.append("|---|---|---|")
    lines.append(
        "| Retrieval hit-rate@10 | "
        f"{_pct(metrics['retrieval_hit_rate_at_k'])} | answerable cases with a gold chunk "
        "in the returned evidence |"
    )
    lines.append(
        "| Answered-rate (answerable) | "
        f"{_pct(metrics['answered_rate_answerable'])} | answerable cases decided ANSWERED |"
    )
    lines.append(
        "| Fact containment | "
        f"{_pct(metrics['fact_containment_rate'])} | answered cases with a key fact whose "
        "answer contains it (substring check) |"
    )
    lines.append(
        f"| Citation precision | {_pct(metrics['citation_precision'])} | citations naming a "
        "gold or in-evidence chunk, over all citations |"
    )
    lines.append(
        f"| Citation validity | {_pct(metrics['citation_validity'])} | answered cases whose "
        "citations all resolve to the returned evidence |"
    )
    lines.append(
        "| Abstention accuracy (unanswerable) | "
        f"{_pct(metrics['abstention_accuracy_unanswerable'])} | unanswerable cases decided "
        "ABSTAIN |"
    )
    lines.append(
        f"| False-answer rate | {_pct(metrics['false_answer_rate'])} | cases expected to "
        "abstain that were answered |"
    )
    lines.append(
        f"| Adversarial safety | {_pct(metrics['adversarial_safety_rate'])} | adversarial "
        "cases meeting their safety expectation |"
    )
    lines.append(
        f"| Latency (local, in-process) | mean {_ms(metrics['mean_latency_ms'])}, "
        f"p95 {_ms(metrics['p95_latency_ms'])} | per-case /query latency in this run |"
    )
    lines.append("")
    lines.append("Per-category expectations met:")
    lines.append("")
    for name in ("answerable", "unanswerable", "adversarial"):
        group = by_category.get(name, [])
        lines.append(f"- {name}: {passed.get(name, 0)}/{len(group)}")
    lines.append("")
    lines.append("## Retrieval layer (existing evaluate_retriever, resolved gold ids)")
    lines.append("")
    lines.append("| Recall@1 | Recall@3 | Recall@5 | Recall@10 | MRR |")
    lines.append("|---|---|---|---|---|")
    lines.append(
        f"| {_num(retrieval['recall_at_1'])} | {_num(retrieval['recall_at_3'])} | "
        f"{_num(retrieval['recall_at_5'])} | {_num(retrieval['recall_at_10'])} | "
        f"{_num(retrieval['mrr'])} |"
    )
    lines.append("")
    lines.append("## Threshold sweep (answerable + unanswerable cases)")
    lines.append("")
    lines.append(
        "| GT_MIN_EVIDENCE_SCORE | Answered-rate (answerable) | Abstention accuracy "
        "(unanswerable) | False-answer rate (unanswerable) |"
    )
    lines.append("|---|---|---|---|")
    for row in output["sweep"]:
        lines.append(
            f"| {row['threshold']:.2f} | {_pct(row['answered_rate_answerable'])} | "
            f"{_pct(row['abstention_accuracy_unanswerable'])} | "
            f"{_pct(row['false_answer_rate_unanswerable'])} |"
        )
    lines.append("")
    if best is not None:
        lines.append(
            f"**Recommendation from this data:** {best['threshold']:.2f} — the threshold with "
            "the best balanced score (mean of answered-rate and abstention accuracy) in the "
            f"sweep: answered-rate {_pct(best['answered_rate_answerable'])}, abstention "
            f"accuracy {_pct(best['abstention_accuracy_unanswerable'])}. "
            "**Giant caveat:** this sweep was run with the deterministic bag-of-words "
            "evaluation double, whose similarities are lexical, not semantic. It validates "
            "that the threshold mechanism and the harness behave correctly; it does NOT "
            "calibrate the production threshold for Gemini embeddings. The production "
            "threshold must be re-measured with this same harness in `--live` mode once a "
            "GEMINI_API_KEY is available, before the 0.35 default is changed on the basis "
            "of this report."
        )
        lines.append("")
    lines.append("## Cases that failed their expectation")
    lines.append("")
    if failures:
        lines.append("| Case | Category | Expected | Decision |")
        lines.append("|---|---|---|---|")
        for case in failures:
            lines.append(
                f"| {case['case_id']} | {case['category']} | {case['expected']} | "
                f"{case['decision']} |"
            )
    else:
        lines.append("None — every case met its expectation in this run.")
    lines.append("")
    lines.append("## Limitations")
    lines.append("")
    lines.append(
        "- **Deterministic providers.** The embedding double is lexical (bag-of-words), "
        "so questions were written to share vocabulary with their gold chunks; a semantic "
        "embedding would score paraphrases differently. The generation double is a "
        "scripted compliant model: it always answers from the top evidence block when "
        "the gate passes and never refuses on content grounds, so end-to-end correctness "
        "here measures retrieval + gating + citation enforcement, not a real model's "
        "judgement. Adversarial results therefore demonstrate the structural defences "
        "(gate + citation verification), not that a real model cannot be manipulated."
    )
    lines.append(
        "- **Latency is local and in-process** (TestClient against SQLite on the machine "
        "that ran the harness). It excludes network, Gemini API and Postgres latency and "
        "must not be quoted as production latency."
    )
    lines.append(
        "- **Small, synthetic dataset.** 26 cases over 4 tiny documents with one fact "
        "per chunk. Rates have wide uncertainty; the dataset is a regression harness, "
        "not a benchmark."
    )
    lines.append(
        "- **Fact containment is a substring check** on the returned answer — crude, "
        "mechanical, and stated as such wherever the number is used."
    )
    lines.append(
        "- **Citation validity is enforced by the endpoint by construction** (answers "
        "with unverifiable citations are converted to abstentions), so a 100% validity "
        "figure confirms the gate works; it is not evidence about model behaviour."
    )
    lines.append("")
    lines.append("## Reproduce")
    lines.append("")
    lines.append("```bash")
    lines.append("# Deterministic doubles (no key needed) — regenerates both files:")
    lines.append("python -m groundtruth.evaluation.run_golden")
    lines.append("")
    lines.append("# Live Gemini providers (requires a Gemini API key):")
    lines.append("GT5_LIVE=1 GEMINI_API_KEY=... python -m groundtruth.evaluation.run_golden")
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the GT-5 golden evaluation.")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Use the real Gemini providers (requires GEMINI_API_KEY).",
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--no-sweep", action="store_true", help="Skip the threshold sweep.")
    args = parser.parse_args(argv)

    live = args.live or os.getenv("GT5_LIVE") == "1"
    mode = "live" if live else "doubles"
    if live and not os.getenv("GEMINI_API_KEY"):
        print("GT5_LIVE/--live requires GEMINI_API_KEY to be set.", file=sys.stderr)
        return 2
    output = run_evaluation(mode=mode, include_sweep=not args.no_sweep)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(build_report(output), encoding="utf-8")
    metrics = output["main_run"]["metrics"]
    print(f"mode={output['providers']['mode']} cases={metrics['case_count']}")
    print(f"answered-rate (answerable): {_pct(metrics['answered_rate_answerable'])}")
    print(f"abstention accuracy (unanswerable): {_pct(metrics['abstention_accuracy_unanswerable'])}")
    print(f"false-answer rate: {_pct(metrics['false_answer_rate'])}")
    print(f"wrote {args.out} and {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
