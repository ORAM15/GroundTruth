# Threat Model

This document delegates to the authoritative foundation documents for security requirements:
- [Architecture Specification](Foundation-GroundTruth/groundtruth-architechture-specification.md)
- [Requirements and Constraints Specification](Foundation-GroundTruth/groundtruth-requirements-and-constraints.md)
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
# GroundTruth Threat Model

This document outlines the threat model for GroundTruth.

## Core Threats

1.  **Indirect Prompt Injection**: Malicious instructions embedded in uploaded documents designed to subvert the LLM's instructions.
2.  **Data Exfiltration**: Unauthorized access to sensitive information within the system or indexed documents.
3.  **Unauthorized Access**: Users accessing documents or functionalities they do not have permission for.
4.  **Denial of Service (DoS)**: Overwhelming the system with large documents or excessive requests.
5.  **Malicious File Uploads**: Uploading unsupported or malformed files to exploit vulnerabilities in processing libraries.
6.  **Fabrication / Hallucination**: The system presenting false information as fact, undermining its trustworthiness.
7.  **Citation Spoofing**: The system generating false citations or linking evidence incorrectly.

## Mitigations

1.  **Prompt Injection**:
    *   Strict separation of instructions and data in prompts.
    *   Treating retrieved documents as untrusted input.
    *   Adversarial testing.
2.  **Data Exfiltration**:
    *   Secure secret management.
    *   No credentials in source control.
3.  **Unauthorized Access**:
    *   Authentication and authorization enforcement at the application and data layers, not by the LLM.
4.  **Denial of Service**:
    *   Explicit limits on document size and processing time.
5.  **Malicious File Uploads**:
    *   Strict validation of supported document types before processing.
6.  **Fabrication**:
    *   Grounded generation requirements.
    *   Explicit abstention policy ("I don't know").
    *   Evaluation against a golden dataset.
7.  **Citation Spoofing**:
    *   Traceable citation lineage from source document to output.

## Trust Boundaries

*   **External vs Internal**: The boundary between external users and the API.
*   **Application vs LLM**: The LLM is NOT a security boundary. All authorization decisions must be made by the application code.
*   **Application vs Data Store**: Secure access to the vector database and document storage.
# GroundTruth Threat Model & Security Requirements

This document represents the baseline security and threat model expectations for GroundTruth, extracted from the project foundation documents.

## Critical Security Requirements

1. **Prompt Injection:** The system MUST defend against indirect prompt injection. Retrieved documents must be treated as untrusted data, and adversarial instructions within those documents must not be allowed to override system behavior or become privileged instructions.
2. **Input Validation & Safety:** Malicious or malformed files must be rejected or safely handled. Oversized input must be bounded according to a defined policy.
3. **Data Isolation & Authorization:** A user MUST NOT be able to retrieve another user's protected evidence or documents. Server-side authorization must be enforced.
4. **Failure Safety:** Critical failures (AI provider failure, DB failure, etc.) must fail safely and explicitly. The system MUST NOT fabricate successful results or confident answers after a failure.
5. **Secrets Management:** Credentials, API keys, tokens, and other secrets MUST NOT be committed to the repository or logged in plaintext.

## Key Threat Vectors Identified

*   **Adversarial / Malicious Documents:** Documents containing crafted payloads designed to exploit the parsing pipeline or the LLM.
*   **Indirect Prompt Injection:** Instructions injected into otherwise valid documents that attempt to hijack the LLM generation phase.
*   **Data Leakage / Cross-Tenant Access:** Unauthorized access to evidence chunks or original documents belonging to another security context.
*   **Denial of Service / Cost Exhaustion:** Processing unbounded inputs or deeply nested, malformed files designed to consume excessive compute or API budget.
*   **Fabrication / Hallucination via Exploitation:** Forcing the system to output confident, uncited claims by bypassing the evidence-grounding constraints.

## Security Validation Expectation

The architecture and implementation must be verified against these threats using explicit adversarial tests (e.g., malformed files, malicious document content, cross-user access attempts) as mandated by the Final Quality and Evaluation System.
# THREAT MODEL
This document will contain the threat model.
# THREAT MODEL\n\nTo be developed in C9.3.
# THREAT MODEL

## Source
Derived from Project Constitution and Requirements & Constraints Specification.

## Threat Assumptions
* **Untrusted Documents:** Retrieved documents and uploaded files are explicitly treated as untrusted data that may contain malicious instructions (SEC-003, SEC-005).
* **Indirect Prompt Injection:** A primary identified threat is malicious documents attempting to override system instructions (SEC-004).
* **Unauthorized Access:** Users attempting to access other users' protected data/collections is an explicit threat requiring authorization controls (SEC-002).
* **Credential Leakage:** Exposure of API credentials in source or client-side is a critical threat (SEC-006).
* **Unvalidated Inputs:** Malicious or malformed inputs to security-sensitive operations create attack surfaces (SEC-007).
* **Resource Abuse:** Unbounded inputs (REL-005) or excessive requests (SEC-008) threaten reliability and cost.

## Security Requirements
The system SHALL satisfy the following security controls:
1. **SEC-001:** Authenticate users where authenticated functionality is provided.
2. **SEC-002:** Authorize access to user-owned collections/documents.
3. **SEC-003:** Treat retrieved documents as untrusted data to defend against prompt injection.
4. **SEC-004:** Defend against indirect prompt injection to a reasonable, testable degree.
5. **SEC-005:** Validate uploaded files according to supported-document policy.
6. **SEC-006:** Protect secrets and API credentials from exposure.
7. **SEC-007:** Validate user inputs relevant to security-sensitive operations.
8. **SEC-008:** Apply rate limiting or equivalent abuse controls where required.
9. **SEC-009:** Document known security limitations rather than claiming perfect protection.

## Testing & Validation
* **TEST-009:** Security/adversarial tests SHALL include malicious document content and prompt-injection attempts.
