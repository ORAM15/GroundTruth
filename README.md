# GroundTruth

Trustworthy evidence-grounded document QA.

## Development status

Phase 1 implementation begins with the evidence backbone. The repository intentionally avoids claiming measured retrieval, grounding, citation, security, latency, or quality results until tests/benchmarks have actually produced them.

## Current vertical slice

`PDF -> Document IR -> structure-aware chunks -> canonical evidence -> retrieval primitives -> API contracts`

## Run

```bash
uv sync --extra dev
uv run pytest
uv run uvicorn groundtruth.api.app:app --reload
```

The PostgreSQL/pgvector adapters are configuration-driven; no credentials are committed.
