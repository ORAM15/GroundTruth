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
