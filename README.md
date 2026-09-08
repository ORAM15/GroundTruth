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

## Run locally

```bash
uv sync --extra dev
uv run pytest
uv run uvicorn groundtruth.api.app:app --reload
```

## AI Engineering & Checkpoints
All autonomous implementations must strictly follow the rules defined in `DEVELOPMENT.md` and operate through the checkpoint tracking system in `docs/project-state/`.
