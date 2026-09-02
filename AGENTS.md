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

## AI Fresh Session Resume Protocol

**CRITICAL:** Every fresh AI session must follow this exact sequence before making any changes.

1. STOP — do not modify anything
2. Inspect Git/repository state
3. Read `docs/project-state/PROJECT_STATE.md`
4. Read `docs/project-state/HANDOFF_RECORD.md`
5. Compare state for consistency
6. Read governing project documents (Constitution, Requirements, Architecture, Technology, Phase Plan)
7. Read relevant decisions in `docs/project-state/DECISION_LOG.md`
8. Identify current checkpoint
9. Verify checkpoint prerequisites
10. Inspect latest validation in `docs/project-state/VALIDATION_RECORD.md`
11. Inspect known defects/failures
12. Inspect active implementation
13. Check approvals/blockers
14. Confirm permitted scope based on checkpoint
15. Determine exact next action
16. Only now plan implementation
17. Implement bounded work
18. Validate
19. Record evidence
20. Update project state
21. Synchronize GitHub
22. Prepare next handoff

AI agents must operate within the boundaries of the AUTONOMOUS_EXECUTION_CONTRACT (see `docs/autonomy/AUTONOMOUS_EXECUTION_CONTRACT.md`) and respect the constraints of the Checkpoint System.

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
