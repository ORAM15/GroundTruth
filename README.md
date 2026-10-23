# GroundTruth

GroundTruth is a trustworthy evidence-grounded document QA system. It allows users to query document collections and receive answers strongly grounded in retrieved evidence with clear citations, while abstaining from answering unsupported queries.

**Live demo:** _URL to be added here once the owner completes the deploy steps below._

## Project State

**Current Phase:** Phase 0 — Project Foundation
**Current Status:** Establishing repository baseline and execution substrate.

The project is governed strictly by the following baseline documents:
- `PRODUCT.md`: The definition of the product, user requirements, and scope.
- `REQUIREMENTS.md`: The mandatory, functional, non-functional, and data constraints.
- `ARCHITECTURE.md`: The system modular architecture and flow.
- `TECHNOLOGY.md`: The approved implementation technologies and constraints.
- `EVALUATION.md`: The measurement framework for quality and requirements.
- `THREAT_MODEL.md`: Security boundaries and adversarial defense mechanisms.
- `DEVELOPMENT.md`: Engineering workflow, autonomous agent boundaries, and the checkpoint system.
Phase 0 implementation establishes the execution substrate and repository baseline. The repository intentionally avoids claiming measured retrieval, grounding, citation, security, latency, or quality results until tests/benchmarks have actually produced them.

## Current vertical slice

Repository baseline and documentation established.

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

GitHub Actions is configured to run the Python test suite on Python 3.12. This project does not claim CI success until an actual workflow run reports it. Retrieval quality metrics are implemented as evaluation primitives, but no benchmark result is claimed yet.
