# GroundTruth

Trustworthy evidence-grounded document QA.

## Development status

Phase 1 implementation establishes the evidence and retrieval backbone. The repository intentionally avoids claiming measured retrieval, grounding, citation, security, latency, or quality results until tests/benchmarks have actually produced them.

## Current vertical slice

`PDF -> Document IR -> structure-aware chunks -> canonical evidence -> lexical/dense retrieval primitives -> RRF hybrid retrieval -> API contracts`

## Architecture boundary

Retrieval is provider-neutral. The dense retriever depends on an `EmbeddingProvider` contract, so a concrete embedding backend can be introduced and benchmarked without changing the retrieval API. This keeps the core domain independent of a single vendor or runtime.

## Run locally

```bash
uv sync --extra dev
uv run pytest
uv run uvicorn groundtruth.api.app:app --reload
```

The PostgreSQL/pgvector adapters are configuration-driven; no credentials are committed. The current query API abstains until an authorized evidence store is configured.

## Phase 1 validation status

GitHub Actions is configured to run the Python test suite on Python 3.12. This project does not claim CI success until an actual workflow run reports it. Retrieval quality metrics are implemented as evaluation primitives, but no benchmark result is claimed yet.
