# GroundTruth

GroundTruth is a trustworthy evidence-grounded document QA system. It allows users to query document collections and receive answers strongly grounded in retrieved evidence with clear citations, while abstaining from answering unsupported queries.

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

## AI Engineering & Checkpoints
All autonomous implementations must strictly follow the rules defined in `DEVELOPMENT.md` and operate through the checkpoint tracking system in `docs/project-state/`.
The PostgreSQL/pgvector adapters are configuration-driven; no credentials are committed. The current query API abstains until an authorized evidence store is configured.

## Validation status

GitHub Actions is configured to run the Python test suite on Python 3.12. This project does not claim CI success until an actual workflow run reports it. Retrieval quality metrics are implemented as evaluation primitives, but no benchmark result is claimed yet.
