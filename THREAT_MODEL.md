# THREAT MODEL

## Context
This document outlines the high-level security boundary, threat model, and failure handling policies for GroundTruth. The detailed threat modeling and implementation of security defenses is scheduled for Phase 7 (Trust, Security & Failure Handling).

## Security Boundaries & Principles
- **Authentication & Authorization**: Must be enforced at the application API layer. The LLM is not a security boundary. Users cannot access collections or documents they are not authorized to view.
- **Untrusted Input**: Retrieved evidence is treated as untrusted input. GroundTruth must defend against prompt injection and data poisoning.
- **Abstention**: The system must explicitly abstain (i.e., refuse to answer) when evidence is insufficient or when a user query attempts to bypass system instructions.
- **Secrets Management**: No API keys, credentials, or private information should be committed to the repository.

## Known Risks
- **Data Leakage**: Incorrect authorization could leak documents between users.
- **Prompt Injection**: Malicious instructions embedded in uploaded documents could override system instructions.
- **Hallucination / False Confidence**: The system may present fabricated answers as grounded truth if citation and grounding defenses fail.

## Next Steps (Phase 7)
- Formally evaluate prompt injection vectors and evaluate defenses.
- Implement explicit validation and sanitization for document ingestion.
- Execute a comprehensive security and threat model evaluation against the deployed system.
