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
