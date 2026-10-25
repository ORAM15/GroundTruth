# GroundTruth

GroundTruth is a trustworthy evidence-grounded document QA system. It allows users to query document collections and receive answers strongly grounded in retrieved evidence with clear citations, while abstaining from answering unsupported queries.

**Live demo:** https://groundtruth-nf8i.onrender.com

## Project State

**Current Phase:** v1 — deployed (GT-1 through GT-5, plus GT-8–GT-11 production
fixes). See `docs/portfolio/GT7_PORTFOLIO_PACK.md` for the demo script,
interview Q&A, measured results, and the production-debugging story.
**Current Status:** Live on Render (free tier) + Neon Postgres + Gemini free tier.

The project is governed strictly by the following baseline documents:
- `PRODUCT.md`: The definition of the product, user requirements, and scope.
- `REQUIREMENTS.md`: The mandatory, functional, non-functional, and data constraints.
- `ARCHITECTURE.md`: The system modular architecture and flow.
- `TECHNOLOGY.md`: The approved implementation technologies and constraints.
- `EVALUATION.md`: The measurement framework for quality and requirements.
- `THREAT_MODEL.md`: Security boundaries and adversarial defense mechanisms.
- `DEVELOPMENT.md`: Engineering workflow, autonomous agent boundaries, and the checkpoint system.
Phase 0 implementation establishes the execution substrate and repository baseline. The repository intentionally avoids claiming measured retrieval, grounding, citation, security, latency, or quality results until tests/benchmarks have actually produced them.

## Architecture

One modular FastAPI application, one Postgres database, one-page vanilla UI.
The request path is deliberately linear so every answer keeps an explainable
lineage back to source evidence:

```
PDF upload
  → extract text per page (pypdf), keep page lineage on every chunk
  → chunk (line-based, split on long lines) with content-hash idempotency
  → embed (Gemini, batched at ≤100 inputs per request)
  → Postgres + pgvector (documents → versions → chunks → embeddings)
  → question
  → hybrid retrieval: dense cosine + term-count lexical, fused with
    reciprocal rank fusion (k=60)
  → dense-cosine abstention gate: the best dense score must clear 0.35
    (env GT_MIN_EVIDENCE_SCORE) before any evidence is returned — lexical
    matches alone can never override a failing dense score
  → grounded generation: evidence is passed as labelled DATA blocks, never
    as instructions
  → pure citation verification: every citation in the draft answer must
    resolve to a chunk in the returned evidence, or the answer is withheld
    and the user gets an honest abstention instead
  → one-page UI (vanilla JS, textContent-only rendering)
```

Large documents take a different ingestion path: uploads over 100 chunks
return `202` plus an ingestion job, and a background worker embeds and saves
in slices of ≤100 chunks under a quota pacer (≤100 embedded items per 60s,
matching the Gemini free-tier limit). Processing and failed documents are
excluded from the document list and from retrieval. See GT-11 (issue #49).

## Design decisions and trade-offs

- **Chunking rationale.** Chunks are small, page-anchored text units produced
  from PDF text lines (long lines split), not fixed-size windows. Small
  chunks keep citations precise — a citation points at one claim-sized unit
  on a known page — at the cost of more embedding calls per document, which
  is exactly what the free-tier quota then constrains. The trade-off is
  deliberate: citation precision over ingestion throughput.
- **Hybrid retrieval, not vector-only.** Dense retrieval catches paraphrase;
  lexical retrieval catches exact terms, codes, and names. RRF fusion (k=60)
  combines the two rankings without a tuned weighting scheme. Cost: two
  retrieval passes and a fusion step per query; benefit: neither signal
  alone decides what counts as evidence.
- **The 0.35 abstention threshold.** The gate exists because a question can
  share words with a chunk while being about something else entirely, and
  answering from it would be fabrication with citations attached. 0.35 was
  chosen from a threshold sweep on the GT-5 golden dataset
  (`docs/evaluation/GT5_EVALUATION_REPORT.md`): it is the lowest threshold
  at which abstention accuracy on unanswerable cases reached 100% while
  answered-rate on answerable cases stayed at 100%. Honest caveat: that
  sweep ran against deterministic lexical evaluation doubles, not Gemini
  embeddings, so 0.35 is a validated mechanism with an uncalibrated
  production value — live re-measurement with the `--live` harness is still
  outstanding before the default is treated as production-calibrated.
- **Pure citation verification, not model self-checking.** After generation,
  code — not the model — checks that every citation resolves to retrieved
  evidence. Unverified answer text is never returned, and abstention paths
  never call generation at all. This is what makes the abstention guarantee
  structural rather than a prompt instruction the model might ignore.
- **Prompt-injection defence is a boundary, not a filter.** Retrieved
  documents are untrusted data: the prompt marks them as DATA blocks and
  explicitly orders the model to ignore instructions inside them. No
  claim is made that this is unbreakable — GT-5's adversarial cases are
  the honest measure of it, and they are the known weak spot (see below).
- **Single modular app, no queue service.** Async ingestion runs as
  FastAPI background tasks in the same process, not a separate worker or
  broker. That keeps the free-tier footprint at one service, at the cost
  that a `processing` job does not survive an instance restart — a known
  follow-up, not a hidden one (see the portfolio pack).
- **No login on the demo, by design for v1.** Anyone with the demo link can
  see the documents list. Personal files should not be uploaded to it.

## Measured results (GT-5, local deterministic doubles)

From `docs/evaluation/GT5_EVALUATION_REPORT.md` (26 golden cases, 4 small
documents, seeded and queried through the real API paths; embedding and
generation doubles, not Gemini):

| Metric | Value |
|---|---|
| Answered-rate (answerable) | 100% |
| Retrieval hit@10 | 100% |
| Abstention accuracy (unanswerable) | 100% |
| Adversarial safety | **66.7% (4/6) — the known weak spot** |

These numbers validate the pipeline mechanism (gating, ranking, citation
enforcement, scoring), not production behaviour with Gemini. They must not
be quoted as production accuracy. The full report, including its
limitations, is in `docs/evaluation/GT5_EVALUATION_REPORT.md`.

## Architecture boundary

Retrieval is provider-neutral. The dense retriever depends on an `EmbeddingProvider` contract, so a concrete embedding backend can be introduced and benchmarked without changing the retrieval API. This keeps the core domain independent of a single vendor or runtime.

## Run locally

```bash
uv sync --extra dev
uv run pytest
uv run uvicorn groundtruth.api.app:app --reload
```

Copy `.env.example` to `.env` and fill in `DATABASE_URL` and `GEMINI_API_KEY`
(a local SQLite `DATABASE_URL` works for exercising the API surface).

## Deploy your own

The stack is free-tier end to end: Render (web service) + Neon (Postgres with
pgvector) + a Gemini API key. The repo ships a `Dockerfile` and a Render
Blueprint (`render.yaml`); deployment is a few dashboard steps:

1. **Neon:** create a free project at [neon.tech](https://neon.tech) and copy
   its connection string (it looks like
   `postgresql://user:password@ep-….aws.neon.tech/neondb?sslmode=require`).
   No manual schema setup — the app creates the pgvector extension and all
   tables on first start.
2. **Gemini:** create an API key in
   [Google AI Studio](https://aistudio.google.com/apikey) (free tier).
3. **Render:** create a new Web Service (or Blueprint) from this repository —
   Render picks up `render.yaml` / the `Dockerfile` automatically. In the
   service's Environment settings, paste the two values:
   `DATABASE_URL` (from step 1) and `GEMINI_API_KEY` (from step 2). They are
   declared `sync: false` in `render.yaml` so they never enter git.
4. **Deploy.** Render builds the image and starts the service; check
   `/health` on the assigned `*.onrender.com` URL, then add that URL to the
   "Live demo" line at the top of this README.

Free-tier caveats:

- **Render free services spin down after ~15 minutes idle.** The next request
  wakes the service but can take ~a minute; this is expected, not an outage.
- **Neon free tier** is sized for development/demo workloads (storage and
  compute limits apply) and scales to zero when idle, adding a short cold
  start to the first query after a pause.
- **Gemini free tier** has per-minute/daily request quotas; heavy evaluation
  runs may need to be spread out.

## AI Engineering & Checkpoints
All autonomous implementations must strictly follow the rules defined in `DEVELOPMENT.md` and operate through the checkpoint tracking system in `docs/project-state/`.
The PostgreSQL/pgvector adapters are configuration-driven; no credentials are committed. The current query API abstains until an authorized evidence store is configured.

## Validation status

GitHub Actions runs the Python test suite on Python 3.12. Measured results
live in `docs/evaluation/GT5_EVALUATION_REPORT.md` (local doubles) and in
the portfolio pack's production-debugging story (live deployment). No
unmeasured quality, latency, or scale claim is made anywhere in this repo.
