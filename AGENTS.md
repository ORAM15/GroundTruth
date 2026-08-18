# AGENTS.md

## Project purpose

GroundTruth is intended to become a production-grade trustworthy RAG answer engine. The project should demonstrate grounded retrieval and generation, citations, abstention, prompt-injection defenses, evaluation, observability, security, testing, deployment, and professional UX.

## Current repository state

This repository is intentionally reserved and currently contains no implementation. Do not fabricate scaffolding, sample metrics, fake evaluation results, or placeholder production behavior merely to make the repository appear active.

## Engineering principles

- Build from explicit product and architecture requirements.
- Prefer evidence and measurable behavior over claims.
- Treat GitHub as the source of truth.
- AI agents are implementation assistants, not architectural authorities.
- Explain and review important engineering decisions.
- Keep changes small, testable, and reviewable.

## Trustworthiness requirements

- Never fabricate citations or source support.
- Implement explicit abstention / "I don't know" behavior where evidence is insufficient.
- Treat retrieved documents as untrusted input and defend against prompt injection.
- Keep model output separate from authorization and security decisions.
- Do not report evaluation, latency, cost, or quality metrics unless they were actually measured.

## Development workflow

1. Inspect current repository state and project documentation.
2. Establish or review the architecture before substantial implementation.
3. Implement bounded changes.
4. Test retrieval, generation, failure cases, and security-sensitive behavior as applicable.
5. Inspect the diff and report what changed, what was tested, failures, and remaining uncertainty.

## Security and secrets

- Never commit API keys, tokens, credentials, `.env` files, or private data.
- Use environment variables or an appropriate secret manager for credentials.
- Do not treat the LLM as a security boundary.
- Enforce authentication, authorization, validation, and other security controls in application code/infrastructure.

## Git discipline

- Keep commits and pull requests focused.
- Do not make unrelated cleanup changes.
- Do not claim a feature is complete without relevant validation.
- Review AI-generated changes before merging.
