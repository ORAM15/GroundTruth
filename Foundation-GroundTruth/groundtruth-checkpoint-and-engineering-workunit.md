# FINAL CHECKPOINT AND ENGINEERING-WORK UNIT SYSTEM

**Project:** GroundTruth
**Document:** Checkpoint & Engineering-Work Unit System
**Status:** FINAL — Execution Baseline v1.0
**Authority:** Final Master Phase Plan + Final Architecture + Requirements & Constraints + Technology Specification

---

# 1. Purpose

This document defines how GroundTruth work is divided into small, bounded, verifiable engineering units.

The hierarchy is:

```text
PROJECT
   │
   └── PHASE
         │
         └── CHECKPOINT
                │
                └── ENGINEERING WORK UNITS
                       │
                       ├── Issue
                       ├── Branch
                       ├── Implementation
                       ├── Tests
                       ├── Validation
                       ├── PR
                       ├── Review
                       └── Closure
```

A **phase** represents a major engineering capability.

A **checkpoint** represents a verifiable state that must be achieved before progressing.

An **engineering work unit** represents the bounded work required to satisfy one checkpoint.

---

# 2. Fundamental Rule

A checkpoint is **not complete** because:

```text
code exists
commit exists
PR exists
tests were written
tests were attempted
AI agent says "done"
```

A checkpoint is complete only when:

```text
Implementation
      +
Validation
      +
Acceptance Criteria
      +
Completion Evidence
      +
Human Approval where required
      ↓
CHECKPOINT COMPLETE
```

The agent's statement that something works is never itself evidence.

---

# 3. Checkpoint State Machine

Every checkpoint follows this lifecycle:

```text
PLANNED
   │
   ▼
READY
   │
   ▼
IN PROGRESS
   │
   ▼
VALIDATION
   │
   ├─────────────── failure ───────────────┐
   │                                       │
   ▼                                       │
PASS                                       │
   │                                       │
   ▼                                       │
REVIEW                                     │
   │                                       │
   ├──────────── rejection ────────────────┘
   │
   ▼
APPROVED
   │
   ▼
MERGED
   │
   ▼
CLOSED
```

A checkpoint may not skip validation.

---

# 4. Checkpoint States

## PLANNED

Checkpoint exists in the master plan but prerequisites are not yet satisfied.

No implementation may begin.

---

## READY

All prerequisites are satisfied and the work is authorized.

---

## IN PROGRESS

An agent or human is actively performing the allowed work.

---

## VALIDATION

Implementation is complete enough to test against the acceptance criteria.

No checkpoint is complete merely because it reaches this state.

---

## PASS

All acceptance criteria have been demonstrated.

---

## REVIEW

Human review is required where specified.

---

## APPROVED

Required reviewer has accepted the demonstrated result.

---

## MERGED

The validated work has been merged into the designated integration branch.

---

## CLOSED

Completion evidence has been recorded and the checkpoint is formally closed.

---

# 5. Checkpoint Design Rules

Every checkpoint must satisfy these properties.

### Bounded

The agent receives a clearly limited objective.

### Observable

Success can be demonstrated.

### Reversible

Changes can be isolated and reverted.

### Independently testable

Validation does not depend solely on human intuition.

### Non-overlapping

A checkpoint should not silently implement another checkpoint's work.

### Dependency-aware

An agent must not implement functionality whose prerequisites are incomplete.

### Scope-controlled

Agents must not redesign the architecture while implementing a checkpoint.

---

# 6. Autonomous Agent Safety Contract

Every AI agent working on GroundTruth must receive the following implicit contract:

```text
1. Read the relevant project documents.
2. Read the checkpoint.
3. Confirm prerequisites.
4. Inspect the existing repository.
5. Do only the allowed work.
6. Do not expand scope.
7. Do not change architecture without authorization.
8. Do not silently introduce technologies.
9. Write tests where required.
10. Execute validation.
11. Report failures honestly.
12. Produce completion evidence.
13. Stop when the checkpoint is satisfied.
```

The agent must **stop rather than improvise** when:

* a prerequisite is missing
* a requirement is ambiguous
* architecture must change
* a new technology appears necessary
* acceptance criteria cannot be demonstrated
* a security decision is required
* a human decision is explicitly required.

---

# 7. Master Checkpoint Structure

The project uses the following checkpoint groups.

```text
PHASE 0  → C0.x
PHASE 1  → C1.x
PHASE 2  → C2.x
PHASE 3  → C3.x
PHASE 4  → C4.x
PHASE 5  → C5.x
PHASE 6  → C6.x
PHASE 7  → C7.x
PHASE 8  → C8.x
PHASE 9  → C9.x
PHASE 10 → C10.x
```

---

# PHASE 0 — PROJECT FOUNDATION

## C0.1 — Repository Baseline

**Objective**

Establish GitHub as the authoritative project source of truth.

**Prerequisites**

None.

**Allowed work**

* repository inspection
* baseline documentation organization
* repository metadata
* contribution/development rules
* branch strategy documentation.

**Expected artifacts**

```text
README.md
PRODUCT.md
REQUIREMENTS.md
ARCHITECTURE.md
TECHNOLOGY.md
EVALUATION.md
THREAT_MODEL.md
DEVELOPMENT.md
```

**Validation method**

Cross-document consistency review.

**Acceptance criteria**

* documents exist
* terminology is consistent
* no conflicting scope
* technology uncertainty remains explicitly marked
* architecture matches requirements.

**Definition of Done**

The repository contains the authoritative project baseline.

**Failure conditions**

* undocumented scope
* conflicting architecture
* proposal represented as decision
* missing authoritative documents.

**Dependencies**

None.

**Human approval**

Required.

**GitHub activity**

Issue → branch → documentation commit → PR → review → merge.

**Next checkpoint**

C0.2.

---

## C0.2 — Change-Control Baseline

**Objective**

Establish how future architecture/requirement changes are controlled.

**Prerequisites**

C0.1.

**Allowed work**

* define change-request format
* define decision-record format
* define checkpoint conventions.

**Expected artifacts**

```text
CHANGE_REQUEST_TEMPLATE.md
ADR_TEMPLATE.md
CHECKPOINT_TEMPLATE.md
```

**Validation**

Review against architecture-freeze rule.

**Acceptance**

No architectural change can occur informally.

**Definition of Done**

The repository has an explicit change-control mechanism.

**Human approval**

Required.

**Next**

Phase 1 / C1.1.

---

# PHASE 1 — RESEARCH & TECHNOLOGY VALIDATION

## C1.1 — Retrieval Research Baseline

**Objective**

Establish evidence-based retrieval requirements.

**Prerequisites**

Phase 0 complete.

**Allowed work**

Research:

* dense retrieval
* sparse retrieval
* hybrid retrieval
* reranking.

**Expected artifacts**

Research notes and engineering implications.

**Validation**

Each major conclusion has supporting evidence.

**Acceptance**

No retrieval mechanism is promoted to production architecture solely from general preference.

**Definition of Done**

Retrieval alternatives and their trade-offs are documented.

**Human approval**

Required.

**Next**

C1.2.

---

## C1.2 — Document Processing Research

**Objective**

Establish ingestion/chunking requirements.

**Prerequisites**

C1.1.

**Allowed work**

Research:

* parsing
* chunking
* metadata
* structural preservation
* difficult documents.

**Validation**

Representative document scenarios are identified.

**Acceptance**

Chunking decisions have explicit reasoning.

**Definition of Done**

Ingestion strategy is sufficiently understood to experiment.

**Next**

C1.3.

---

## C1.3 — Model & AI Behavior Experiments

**Objective**

Evaluate candidate generation and embedding approaches.

**Prerequisites**

C1.1, C1.2.

**Allowed work**

AI Studio experiments.

Test:

* grounding
* citation behavior
* abstention
* structured output
* injection resistance
* latency
* cost.

**Expected artifacts**

Model experiment reports.

**Validation**

Controlled comparisons using representative inputs.

**Acceptance**

Selected candidate(s) demonstrate acceptable behavior.

**Failure conditions**

* unsupported model selection
* no reproducible comparison
* unacceptable grounding/citation behavior.

**Human approval**

Required.

**Next**

C1.4.

---

## C1.4 — Infrastructure Decision Closure

**Objective**

Resolve remaining implementation-level technology choices.

**Prerequisites**

C1.3.

**Allowed work**

Evaluate:

* authentication
* storage
* deployment
* observability
* frontend testing.

**Validation**

Requirements/trade-off matrix.

**Acceptance**

Every mandatory implementation dependency has either:

```text
APPROVED
```

or:

```text
EXPLICITLY DEFERRED
```

**Definition of Done**

No critical technology decision remains silently ambiguous.

**Human approval**

Required.

**Next**

Phase 2.

---

# PHASE 2 — EVALUATION FOUNDATION

## C2.1 — Golden Dataset

**Objective**

Create the authoritative GroundTruth evaluation dataset.

**Prerequisites**

Phase 1.

**Allowed work**

Create:

* normal cases
* difficult cases
* unanswerable cases
* adversarial cases
* injection cases.

**Validation**

Dataset review.

**Acceptance**

Dataset represents the major system behaviors.

**Definition of Done**

The dataset can distinguish supported, unsupported and adversarial scenarios.

**Human approval**

Required.

**Next**

C2.2.

---

## C2.2 — Evaluation Runner

**Objective**

Create a repeatable evaluation execution mechanism.

**Prerequisites**

C2.1.

**Allowed work**

Evaluation runner and result recording.

**Validation**

Run against known scenarios.

**Acceptance**

The runner produces deterministic, inspectable evaluation results where deterministic behavior is possible.

**Next**

C2.3.

---

## C2.3 — Metric Baseline

**Objective**

Implement the initial evaluation metrics.

**Prerequisites**

C2.2.

**Allowed work**

Implement metrics for:

* retrieval
* answer quality
* groundedness
* citation correctness
* abstention
* security
* latency
* cost.

**Validation**

Known-good/known-bad comparison.

**Acceptance**

Metrics produce interpretable results.

**Human approval**

Required.

**Next**

Phase 3.

---

# PHASE 3 — ENGINEERING BOOTSTRAP

## C3.1 — Repository Scaffold

**Objective**

Create the minimal application structure.

**Prerequisites**

Phase 2.

**Allowed work**

* frontend scaffold
* backend scaffold
* configuration
* basic project structure.

**Not allowed**

* RAG implementation
* arbitrary libraries
* unrelated UI features.

**Validation**

Clean installation and startup.

**Acceptance**

Frontend and backend start successfully from documented instructions.

**Next**

C3.2.

---

## C3.2 — Database Foundation

**Objective**

Establish persistent application data foundation.

**Prerequisites**

C3.1.

**Allowed work**

Database connection and initial schema foundation.

**Validation**

Database integration tests.

**Acceptance**

Application can connect and persist a minimal test record.

**Next**

C3.3.

---

## C3.3 — Test & CI Foundation

**Objective**

Make changes automatically verifiable.

**Prerequisites**

C3.1, C3.2.

**Allowed work**

* test configuration
* CI
* basic checks
* lint/format validation where selected.

**Validation**

Pull request triggers successful CI.

**Acceptance**

A clean clone can run tests and CI passes.

**Human approval**

Required.

**Next**

Phase 4.

---

# PHASE 4 — INGESTION & EVIDENCE

## C4.1 — Document Lifecycle

**Objective**

Implement document registration and processing states.

**Prerequisites**

Phase 3.

**Allowed work**

Document metadata and lifecycle states:

```text
SUBMITTED
PROCESSING
READY
FAILED
```

**Validation**

API/integration tests.

**Acceptance**

State transitions behave correctly.

**Next**

C4.2.

---

## C4.2 — Document Extraction

**Objective**

Extract supported document content safely.

**Prerequisites**

C4.1.

**Allowed work**

Parser implementation for approved formats.

**Validation**

Representative documents.

**Acceptance**

Valid documents extract expected content; malformed/unsupported documents fail safely.

**Next**

C4.3.

---

## C4.3 — Chunking & Metadata

**Objective**

Transform extracted content into traceable evidence units.

**Prerequisites**

C4.2.

**Allowed work**

Chunking and metadata preservation.

**Validation**

Golden document fixtures.

**Acceptance**

Every chunk retains sufficient lineage for citation.

**Next**

C4.4.

---

## C4.4 — Embedding & Indexing

**Objective**

Make chunks searchable.

**Prerequisites**

C4.3 + approved embedding configuration.

**Allowed work**

Embedding generation and indexing.

**Validation**

Searchability test.

**Acceptance**

Known relevant chunks can be retrieved from known queries.

**Next**

Phase 5.

---

# PHASE 5 — RETRIEVAL

## C5.1 — Semantic Retrieval

**Objective**

Implement semantic retrieval.

**Prerequisites**

C4.4.

**Allowed work**

Vector/semantic retrieval only.

**Validation**

Golden retrieval dataset.

**Acceptance**

Baseline Recall@K and related metrics are measured.

**Next**

C5.2.

---

## C5.2 — Lexical Retrieval

**Objective**

Implement lexical retrieval.

**Prerequisites**

C5.1.

**Allowed work**

Lexical retrieval only.

**Validation**

Same golden dataset.

**Acceptance**

Lexical baseline is measured independently.

**Next**

C5.3.

---

## C5.3 — Retrieval Comparison

**Objective**

Compare semantic and lexical retrieval.

**Prerequisites**

C5.1, C5.2.

**Allowed work**

Evaluation and analysis.

**Validation**

Metric comparison.

**Acceptance**

Production retrieval direction is evidence-based.

**Human approval**

Required.

**Next**

C5.4.

---

## C5.4 — Hybrid Retrieval Experiment

**Objective**

Determine whether combining retrieval methods materially improves GroundTruth.

**Prerequisites**

C5.3.

**Allowed work**

Fusion experiments.

**Validation**

Compare against strongest single-method baseline.

**Acceptance**

Hybrid retrieval is adopted only if improvement justifies complexity.

**Human approval**

Required.

**Next**

C5.5.

---

## C5.5 — Reranking Decision

**Objective**

Determine whether reranking earns a place in the production pipeline.

**Prerequisites**

C5.4.

**Allowed work**

Reranking experiment.

**Validation**

Quality/latency/cost comparison.

**Acceptance**

Reranking is either:

```text
APPROVED
```

or:

```text
REJECTED / DEFERRED
```

with evidence.

**Human approval**

Required.

**Next**

Phase 6.

---

# PHASE 6 — GROUNDED ANSWER ENGINE

## C6.1 — Context Builder

**Objective**

Create controlled model context from selected evidence.

**Prerequisites**

Phase 5.

**Allowed work**

Context construction.

**Validation**

Context inspection tests.

**Acceptance**

Only authorized selected evidence enters the generation context.

**Next**

C6.2.

---

## C6.2 — Grounded Generation

**Objective**

Generate answers from retrieved evidence.

**Prerequisites**

C6.1 + approved LLM.

**Allowed work**

Generation adapter and prompt behavior.

**Validation**

Golden answer dataset.

**Acceptance**

Supported questions produce evidence-grounded answers.

**Next**

C6.3.

---

## C6.3 — Citation Lineage

**Objective**

Produce citations linked to actual source evidence.

**Prerequisites**

C6.2.

**Allowed work**

Citation resolution and presentation data.

**Validation**

Citation correctness tests.

**Acceptance**

No fabricated citation can pass validation.

**Next**

C6.4.

---

## C6.4 — Answer Validation

**Objective**

Validate generated answers against available evidence.

**Prerequisites**

C6.3.

**Allowed work**

Grounding/citation validation.

**Validation**

Supported and unsupported cases.

**Acceptance**

Unsupported output is rejected, corrected or routed toward abstention according to policy.

**Next**

Phase 7.

---

# PHASE 7 — TRUST, SECURITY & FAILURE

## C7.1 — Abstention

**Objective**

Implement explicit insufficient-evidence behavior.

**Prerequisites**

Phase 6.

**Allowed work**

Evidence sufficiency policy and abstention path.

**Validation**

Unanswerable evaluation dataset.

**Acceptance**

System abstains when evidence is insufficient at the established threshold.

**Human approval**

Required.

**Next**

C7.2.

---

## C7.2 — Prompt Injection Defense

**Objective**

Ensure retrieved content cannot become privileged instructions.

**Prerequisites**

C7.1.

**Allowed work**

Context isolation, validation and security tests.

**Validation**

Adversarial document suite.

**Acceptance**

Injected document instructions do not override system behavior.

**Important**

This checkpoint does not permit claims of perfect prompt-injection prevention.

**Next**

C7.3.

---

## C7.3 — Authorization & Data Isolation

**Objective**

Protect collection/document access.

**Prerequisites**

C7.2 + authentication configuration.

**Allowed work**

Server-side authorization.

**Validation**

Cross-user access tests.

**Acceptance**

Unauthorized access is rejected.

**Next**

C7.4.

---

## C7.4 — Failure Handling

**Objective**

Make critical failures explicit and safe.

**Prerequisites**

C7.3.

**Allowed work**

Handle:

* malformed documents
* extraction failures
* empty retrieval
* AI failures
* database failures
* citation failures.

**Validation**

Fault-injection/integration tests.

**Acceptance**

The system does not fabricate successful results after failures.

**Next**

Phase 8.

---

# PHASE 8 — PRODUCT INTEGRATION & UX

## C8.1 — Document Workflow UI

**Objective**

Expose the ingestion workflow professionally.

**Prerequisites**

Phase 7.

**Allowed work**

* collection UI
* document upload
* processing status
* failure states.

**Validation**

Critical frontend workflow tests.

**Acceptance**

A user can upload and monitor a document without developer intervention.

**Next**

C8.2.

---

## C8.2 — Question/Answer Workflow

**Objective**

Expose the validated answer engine.

**Prerequisites**

C8.1.

**Allowed work**

* query UI
* loading states
* answers
* abstention states.

**Validation**

End-to-end workflow.

**Acceptance**

User can ask a question and receive the actual backend result.

**Next**

C8.3.

---

## C8.3 — Evidence & Citation UX

**Objective**

Make source verification understandable.

**Prerequisites**

C8.2.

**Allowed work**

Citation cards, evidence/source display and navigation.

**Validation**

Manual + workflow validation.

**Acceptance**

A user can understand where the answer came from.

**Next**

C8.4.

---

## C8.4 — Product Quality

**Objective**

Complete critical UX quality requirements.

**Prerequisites**

C8.3.

**Allowed work**

* accessibility
* responsive behavior
* error states
* empty states
* retry behavior
* feedback.

**Validation**

Critical workflow test matrix.

**Acceptance**

No critical workflow leaves the user in an unexplained state.

**Human approval**

Required.

**Next**

Phase 9.

---

# PHASE 9 — HARDENING & PRODUCTION VERIFICATION

## C9.1 — Observability

**Objective**

Instrument the complete request lifecycle.

**Prerequisites**

Phase 8.

**Allowed work**

Record appropriate:

* request identifiers
* retrieval behavior
* model information
* latency
* usage
* errors.

**Validation**

Execute representative requests and inspect telemetry.

**Acceptance**

Important pipeline stages can be diagnosed.

**Next**

C9.2.

---

## C9.2 — Performance & Cost Baseline

**Objective**

Measure real system performance and AI cost.

**Prerequisites**

C9.1.

**Allowed work**

Performance/cost benchmarking.

**Validation**

Representative workload.

**Acceptance**

P50/P95 and cost/query are measured rather than guessed.

**Next**

C9.3.

---

## C9.3 — Full Security Verification

**Objective**

Perform final adversarial verification.

**Prerequisites**

C9.2.

**Allowed work**

Security regression testing.

**Validation**

Threat-model test suite.

**Acceptance**

All defined critical security scenarios have demonstrated behavior.

**Next**

C9.4.

---

## C9.4 — Full Evaluation Regression

**Objective**

Run the complete GroundTruth evaluation suite.

**Prerequisites**

C9.3.

**Allowed work**

Full benchmark execution.

**Validation**

Evaluation reports.

**Acceptance**

Results meet the project's defined release thresholds.

**Human approval**

Required.

**Next**

C9.5.

---

## C9.5 — Production Readiness Review

**Objective**

Determine whether GroundTruth is ready for public deployment.

**Prerequisites**

C9.1–C9.4.

**Allowed work**

Review only; no uncontrolled feature development.

**Validation**

Production-readiness checklist.

**Acceptance**

Functional, AI, security, reliability, performance, cost and observability criteria all pass.

**Human approval**

Mandatory.

**Next**

Phase 10.

---

# PHASE 10 — DEPLOYMENT & RELEASE

## C10.1 — Production Infrastructure

**Objective**

Create the production environment.

**Prerequisites**

C9.5.

**Allowed work**

* frontend deployment
* backend deployment
* database
* storage
* secrets
* AI integration
* observability.

**Validation**

Deployment health checks.

**Acceptance**

All production components communicate successfully.

**Next**

C10.2.

---

## C10.2 — Production End-to-End Verification

**Objective**

Verify the deployed product, not merely the local application.

**Prerequisites**

C10.1.

**Allowed work**

Real deployment verification.

**Validation**

Complete user workflow.

**Acceptance**

External user can:

```text
authenticate
→ access collection
→ upload document
→ process document
→ ask question
→ receive answer
→ inspect citation
→ trigger abstention when appropriate
```

**Next**

C10.3.

---

## C10.3 — Documentation & Portfolio Release

**Objective**

Document what actually exists.

**Prerequisites**

C10.2.

**Allowed work**

Finalize:

* README
* architecture
* evaluation report
* security/threat model
* deployment documentation
* screenshots
* demo
* resume material.

**Validation**

Documentation-to-system audit.

**Acceptance**

Every major claim in the documentation can be demonstrated by the repository or deployed system.

**Human approval**

Required.

**Next**

C10.4.

---

## C10.4 — Final Release

**Objective**

Formally release GroundTruth.

**Prerequisites**

C10.3.

**Allowed work**

Final verification and release tagging.

**Validation**

Final release checklist.

**Acceptance**

All Definition-of-Done criteria are satisfied.

**Human approval**

Mandatory.

**Definition of Done**

GroundTruth is publicly deployed, documented, evaluated, security-tested and interview-defensible.

**Next**

None.

---

# 8. Engineering Work Unit System

A checkpoint can contain multiple bounded engineering work units.

For example:

```text
C4.3 Chunking & Metadata
        │
        ├── EU-4.3.1 Define chunk representation
        ├── EU-4.3.2 Implement chunker
        ├── EU-4.3.3 Preserve metadata
        ├── EU-4.3.4 Add fixtures
        └── EU-4.3.5 Validate lineage
```

Each work unit must have:

```text
one objective
one bounded scope
one expected output
one validation method
```

An AI agent should normally receive **one engineering work unit at a time**, not an entire phase.

---

# 9. Work Unit Scope Rules

An engineering work unit must specify:

### Allowed

Exactly what the agent may modify.

### Forbidden

What it must not modify.

### Inputs

Which project documents and existing components it must use.

### Outputs

Exactly what it should produce.

### Validation

Exactly how success is demonstrated.

### Stop conditions

When the agent must stop and ask for human direction.

---

# 10. Standard GitHub Representation

Every checkpoint becomes a GitHub **Issue**.

Recommended title:

```text
[CHECKPOINT C4.3] Chunking & Metadata
```

The issue contains:

```text
Checkpoint ID
Phase
Objective
Prerequisites
Allowed work
Forbidden work
Expected artifacts
Acceptance criteria
Validation method
Dependencies
Human approval requirement
Definition of Done
```

---

# 11. Branch Strategy

A checkpoint should normally receive a dedicated branch:

```text
checkpoint/C4.3-chunking-metadata
```

For smaller work units, branches may be nested by implementation need, but we should avoid excessive branch fragmentation.

Recommended model:

```text
main
  │
  └── checkpoint/C4.3-chunking-metadata
          │
          ├── commits
          │
          └── PR
```

---

# 12. Commit Rules

Commits should represent meaningful engineering states.

Good:

```text
feat(ingestion): add chunk metadata model
test(ingestion): add chunk lineage fixtures
fix(ingestion): preserve page metadata
```

Bad:

```text
stuff
changes
final final
AI generated
working now
```

A commit is evidence of change, **not evidence of completion**.

---

# 13. Pull Request Rules

PR title:

```text
[C4.3] Implement chunking and metadata preservation
```

The PR must contain:

```text
## Checkpoint
C4.3

## Objective
...

## Implemented
...

## Not Implemented
...

## Validation
...

## Acceptance Criteria
- [x] ...
- [x] ...
- [ ] ...

## Evidence
...

## Risks / Limitations
...

## Tests
...

## Scope Changes
None
```

If a checkpoint cannot satisfy an acceptance criterion, the PR must not claim completion.

---

# 14. Review Model

Every checkpoint falls into one of three review classes.

## Class A — Agent-verifiable

Low-risk implementation work where automated validation is sufficient.

Example:

```text
unit test
metadata transformation
parser utility
```

---

## Class B — Human-reviewed

Architecturally meaningful or externally visible changes.

Example:

```text
retrieval strategy
database schema
API contract
UX behavior
```

---

## Class C — Owner approval mandatory

Decisions affecting:

* architecture
* security posture
* AI model
* retrieval strategy
* production release
* cost
* scope.

These cannot be finalized autonomously.

---

# 15. Completion Evidence

Every checkpoint must leave evidence.

Possible evidence includes:

```text
test output
evaluation report
benchmark
screenshot
API response
database verification
security test result
deployment URL
trace
log output
architecture comparison
```

The evidence must answer:

> **How do we know the acceptance criterion is actually satisfied?**

---

# 16. Checkpoint Closure Protocol

A checkpoint is closed only after:

```text
1. Implementation complete
        ↓
2. Tests executed
        ↓
3. Acceptance criteria checked
        ↓
4. Evidence attached
        ↓
5. Required review completed
        ↓
6. PR merged
        ↓
7. Issue updated
        ↓
8. Completion recorded
        ↓
9. Checkpoint CLOSED
```

---

# 17. Failed Checkpoint Protocol

If validation fails:

```text
CHECKPOINT
    ↓
VALIDATION
    ↓
FAIL
    ↓
Issue remains OPEN
    ↓
Failure documented
    ↓
Corrective work
    ↓
Re-validation
```

Never:

```text
FAIL
 ↓
merge anyway
 ↓
"fix later"
```

unless the project owner explicitly accepts the deviation through the appropriate change process.

---

# 18. Blocked Checkpoint Protocol

If an agent encounters a missing decision:

```text
Agent
 ↓
Detects blocker
 ↓
STOP
 ↓
Document blocker
 ↓
Request owner decision
```

Examples:

> "The selected embedding model does not meet the agreed latency requirement."

> "The architecture requires a second datastore, which is not currently approved."

> "The citation requirement cannot be satisfied with the current parser."

The correct behavior is **not improvisation**.

---

# 19. Scope-Creep Protocol

If an agent discovers useful additional work:

```text
Existing checkpoint
        │
        ▼
New requirement discovered
        │
        ▼
Does it belong to current acceptance criteria?
       / \
     YES  NO
      │    │
      ▼    ▼
 Continue  STOP
           │
           ▼
      New checkpoint /
      change request
```

This prevents autonomous agents from gradually redesigning GroundTruth.

---

# 20. Human Approval Gates

The following checkpoints explicitly require owner approval:

```text
C0.1   Project baseline
C0.2   Change-control baseline

C1.3   Model/AI behavior
C1.4   Technology decisions

C2.1   Golden dataset
C2.3   Evaluation baseline

C3.3   Engineering foundation

C5.3   Retrieval strategy comparison
C5.4   Hybrid retrieval decision
C5.5   Reranking decision

C6.4   Answer validation

C7.1   Abstention policy

C8.4   Product UX completion

C9.4   Full evaluation regression
C9.5   Production readiness

C10.3  Final documentation
C10.4  Final release
```

This is intentional.

The agent can implement.

The agent cannot silently become the product owner.

---

# 21. Checkpoint Dependency Graph

```text
C0.1
  ↓
C0.2
  ↓
C1.1
  ↓
C1.2
  ↓
C1.3
  ↓
C1.4
  ↓
C2.1
  ↓
C2.2
  ↓
C2.3
  ↓
C3.1
  ↓
C3.2
  ↓
C3.3
  ↓
C4.1
  ↓
C4.2
  ↓
C4.3
  ↓
C4.4
  ↓
C5.1 ─────┐
  ↓       │
C5.2 ─────┤
  ↓       │
C5.3 ◄────┘
  ↓
C5.4
  ↓
C5.5
  ↓
C6.1
  ↓
C6.2
  ↓
C6.3
  ↓
C6.4
  ↓
C7.1
  ↓
C7.2
  ↓
C7.3
  ↓
C7.4
  ↓
C8.1
  ↓
C8.2
  ↓
C8.3
  ↓
C8.4
  ↓
C9.1
  ↓
C9.2
  ↓
C9.3
  ↓
C9.4
  ↓
C9.5
  ↓
C10.1
  ↓
C10.2
  ↓
C10.3
  ↓
C10.4
```

Some dependencies are intentionally parallel in concept, but the **release dependency remains sequential**.

---

# 22. Checkpoint → Phase Relationship

```text
PHASE 0
 C0.1 → C0.2

PHASE 1
 C1.1 → C1.2 → C1.3 → C1.4

PHASE 2
 C2.1 → C2.2 → C2.3

PHASE 3
 C3.1 → C3.2 → C3.3

PHASE 4
 C4.1 → C4.2 → C4.3 → C4.4

PHASE 5
 C5.1 → C5.2 → C5.3 → C5.4 → C5.5

PHASE 6
 C6.1 → C6.2 → C6.3 → C6.4

PHASE 7
 C7.1 → C7.2 → C7.3 → C7.4

PHASE 8
 C8.1 → C8.2 → C8.3 → C8.4

PHASE 9
 C9.1 → C9.2 → C9.3 → C9.4 → C9.5

PHASE 10
 C10.1 → C10.2 → C10.3 → C10.4
```

---

# 23. Standard CHECKPOINT TEMPLATE

The following template is the canonical reusable template for every GroundTruth checkpoint.

```markdown
# [CHECKPOINT ID] — [CHECKPOINT NAME]

## Phase
[Phase ID + Phase Name]

## Status
PLANNED

## Objective
[One precise objective]

## Why This Checkpoint Exists
[Engineering reason]

## Prerequisites
- [Prerequisite]
- [Prerequisite]

## Inputs
- [Required project document]
- [Required existing component]
- [Required dataset/configuration]

## Allowed Work
- [Explicitly allowed work]
- [Explicitly allowed work]

## Forbidden Work
- [Out-of-scope work]
- [Architecture changes]
- [Unapproved technologies]

## Expected Artifacts
- [Artifact]
- [Artifact]

## Validation Method
[Exact method used to demonstrate success]

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Definition of Done
[Precise statement of completed state]

## Failure Conditions
- [Failure]
- [Failure]

## Dependencies
- [Checkpoint ID]

## Human Approval
Required / Not Required

## GitHub Issue
[Issue URL]

## Branch
[Branch name]

## Expected Commits
[Expected meaningful changes]

## Pull Request
[PR URL]

## Review
[Required reviewer / review class]

## Validation Evidence
- [Test output]
- [Evaluation report]
- [Screenshot]
- [Benchmark]
- [Other evidence]

## Completion Decision
PASS / FAIL / BLOCKED

## Completion Evidence
[Concise evidence demonstrating acceptance criteria]

## Limitations
[Any known limitations]

## Scope Changes
None / [Change Request ID]

## Next Checkpoint
[Checkpoint ID]

## Closure
- [ ] Validation passed
- [ ] Acceptance criteria demonstrated
- [ ] Required review completed
- [ ] PR merged
- [ ] Evidence recorded
- [ ] Issue closed
```

---

# 24. Standard ENGINEERING WORK UNIT TEMPLATE

Every autonomous coding task should use this smaller template.

```markdown
# [EU-ID] — [WORK UNIT NAME]

## Parent Checkpoint
[Cx.x]

## Objective
[One bounded objective]

## Context
[Relevant architecture/requirements]

## Allowed Files / Components
[List]

## Forbidden Changes
[List]

## Inputs
[List]

## Expected Output
[Exact output]

## Tests Required
[List]

## Validation
[Exact command/procedure]

## Acceptance Criteria
- [ ] ...
- [ ] ...

## Stop Conditions
Stop and report if:
- architecture must change
- new dependency is required
- requirement is ambiguous
- existing behavior conflicts with specification
- validation cannot pass

## Completion Evidence
[What must be attached]

## Commit
[Expected commit]

## Pull Request
[Parent checkpoint PR]

## Status
PLANNED / IN PROGRESS / VALIDATION / COMPLETE / BLOCKED
```

---

# 25. Autonomous Agent Prompt Contract

When assigning a checkpoint/work unit to Antigravity, Jules, Gemini CLI or another coding agent, the task should conceptually be framed as:

```text
You are implementing CHECKPOINT [ID].

Read:
- Project Constitution
- Requirements
- Architecture
- Technology Specification
- Relevant checkpoint definition

Before changing anything:
1. Inspect the repository.
2. Verify prerequisites.
3. Identify the existing implementation state.
4. Confirm that the requested work is within scope.

Implement ONLY the allowed work.

Do NOT:
- redesign architecture
- introduce unapproved technologies
- implement future checkpoints
- modify unrelated components
- fabricate successful validation

After implementation:
1. Run required tests.
2. Run the specified validation.
3. Compare results against every acceptance criterion.
4. Report failures honestly.
5. Provide completion evidence.

If a prerequisite or architectural decision is missing:
STOP and report the blocker.

Do not declare the checkpoint complete merely because code or tests exist.
```

---

# 26. GitHub Lifecycle Standard

The standard GroundTruth engineering lifecycle is:

```text
              CHECKPOINT
                   │
                   ▼
              GitHub Issue
                   │
                   ▼
                READY
                   │
                   ▼
             Feature Branch
                   │
                   ▼
          Engineering Work Units
                   │
                   ▼
            Implementation
                   │
                   ▼
                Tests
                   │
                   ▼
              Validation
                   │
          ┌────────┴────────┐
          │                 │
         FAIL              PASS
          │                 │
          ▼                 ▼
       Correct          Pull Request
                            │
                            ▼
                         Review
                            │
                     ┌──────┴──────┐
                     │             │
                  Reject         Approve
                     │             │
                     ▼             ▼
                  Fix/retest     Merge
                                   │
                                   ▼
                              Evidence
                                   │
                                   ▼
                              Close Issue
```

---

# 27. What "Done" Means

GroundTruth adopts the following strict rule:

> **Done means demonstrated, not produced.**

For example:

### Bad completion claim

> "Implemented hybrid retrieval."

Not sufficient.

### Valid completion claim

> "Implemented hybrid retrieval, executed the retrieval evaluation dataset, compared Recall@K/MRR against the strongest single-retrieval baseline, documented the measured trade-off, and received approval to retain hybrid retrieval."

That is engineering evidence.

---

# 28. AI-Agent Authority Boundary

The agents have implementation authority, not project authority.

```text
                    PROJECT OWNER
                         │
                 Final authority
                         │
                         ▼
                   PROJECT RULES
                         │
                         ▼
                   CHECKPOINT
                         │
                         ▼
                    AI AGENT
                         │
                    Implements
                         │
                         ▼
                     TESTS
                         │
                         ▼
                    VALIDATION
```

An AI agent cannot:

```text
change requirements
change architecture
select an unapproved technology
expand scope
lower acceptance criteria
declare failed validation successful
```

without the appropriate owner-approved change.

---

# 29. Checkpoint Evidence Hierarchy

Evidence should be preferred in roughly this order:

```text
1. Automated test result
2. Evaluation result
3. Reproducible benchmark
4. Integration/system test
5. Deployment verification
6. Inspection/screenshot
7. Human assertion
```

The lower levels should not substitute for stronger evidence when stronger evidence is reasonably available.

---

# 30. Final Engineering Control Model

The complete GroundTruth execution model is:

```text
                 PROJECT CONSTITUTION
                          │
                          ▼
                    REQUIREMENTS
                          │
                          ▼
                    ARCHITECTURE
                          │
                          ▼
                     TECHNOLOGY
                          │
                          ▼
                   MASTER PHASE PLAN
                          │
                          ▼
                     CHECKPOINT
                          │
                          ▼
                 ENGINEERING WORK UNIT
                          │
                          ▼
                      AI AGENT
                          │
                          ▼
                       CODE
                          │
                          ▼
                       TESTS
                          │
                          ▼
                    VALIDATION
                          │
                    ┌─────┴─────┐
                    │           │
                  FAIL         PASS
                    │           │
                    ▼           ▼
                  FIX        REVIEW
                                │
                                ▼
                              MERGE
                                │
                                ▼
                           EVIDENCE
                                │
                                ▼
                             CLOSE
                                │
                                ▼
                       NEXT CHECKPOINT
```

---

# 31. Final System Rules

The following rules are now authoritative for GroundTruth execution.

### Rule 1

**No checkpoint without prerequisites.**

### Rule 2

**No implementation outside checkpoint scope.**

### Rule 3

**No completion without demonstrated acceptance criteria.**

### Rule 4

**A commit is not completion evidence by itself.**

### Rule 5

**A PR is not completion evidence by itself.**

### Rule 6

**Tests being written is not equivalent to tests passing.**

### Rule 7

**AI-agent self-reported success is not validation.**

### Rule 8

**Failed validation keeps the checkpoint open.**

### Rule 9

**Architectural changes require explicit approval.**

### Rule 10

**Technology changes require appropriate decision review.**

### Rule 11

**Scope expansion creates a new work unit/checkpoint or approved change request.**

### Rule 12

**Every completed checkpoint leaves reproducible evidence.**

### Rule 13

**GitHub remains the authoritative record of engineering state.**

### Rule 14

**The project owner remains the final decision-maker.**

### Rule 15

**The next checkpoint may begin only after the current checkpoint's exit conditions are satisfied.**

---

# 32. Final Checkpoint Baseline

The authoritative execution structure is therefore:

```text
PHASE 0
 C0.1 Repository Baseline
 C0.2 Change-Control Baseline

PHASE 1
 C1.1 Retrieval Research
 C1.2 Document Processing Research
 C1.3 Model & AI Experiments
 C1.4 Infrastructure Decision Closure

PHASE 2
 C2.1 Golden Dataset
 C2.2 Evaluation Runner
 C2.3 Metric Baseline

PHASE 3
 C3.1 Repository Scaffold
 C3.2 Database Foundation
 C3.3 Test & CI Foundation

PHASE 4
 C4.1 Document Lifecycle
 C4.2 Document Extraction
 C4.3 Chunking & Metadata
 C4.4 Embedding & Indexing

PHASE 5
 C5.1 Semantic Retrieval
 C5.2 Lexical Retrieval
 C5.3 Retrieval Comparison
 C5.4 Hybrid Retrieval Experiment
 C5.5 Reranking Decision

PHASE 6
 C6.1 Context Builder
 C6.2 Grounded Generation
 C6.3 Citation Lineage
 C6.4 Answer Validation

PHASE 7
 C7.1 Abstention
 C7.2 Prompt Injection Defense
 C7.3 Authorization & Data Isolation
 C7.4 Failure Handling

PHASE 8
 C8.1 Document Workflow UI
 C8.2 Question/Answer Workflow
 C8.3 Evidence & Citation UX
 C8.4 Product Quality

PHASE 9
 C9.1 Observability
 C9.2 Performance & Cost
 C9.3 Security Verification
 C9.4 Full Evaluation Regression
 C9.5 Production Readiness

PHASE 10
 C10.1 Production Infrastructure
 C10.2 Production E2E Verification
 C10.3 Documentation & Portfolio
 C10.4 Final Release
```

This gives GroundTruth **39 bounded checkpoints**.

That number is intentional: it is large enough to prevent dangerous leaps such as *"build the entire RAG system"*, but small enough that we are not creating meaningless administrative checkpoints for every function or file.

---

# 33. Final Definition of the System

The relationship between our four planning layers is now:

```text
┌──────────────────────────────────────────┐
│ PROJECT CONSTITUTION                     │
│ What GroundTruth IS                     │
└────────────────────┬─────────────────────┘
                     ▼
┌──────────────────────────────────────────┐
│ REQUIREMENTS & CONSTRAINTS               │
│ What GroundTruth MUST satisfy            │
└────────────────────┬─────────────────────┘
                     ▼
┌──────────────────────────────────────────┐
│ FINAL ARCHITECTURE                       │
│ How the system is structurally organized │
└────────────────────┬─────────────────────┘
                     ▼
┌──────────────────────────────────────────┐
│ TECHNOLOGY SPECIFICATION                 │
│ What implementation technologies support │
│ that architecture                        │
└────────────────────┬─────────────────────┘
                     ▼
┌──────────────────────────────────────────┐
│ MASTER PHASE PLAN                        │
│ In what dependency order we build it     │
└────────────────────┬─────────────────────┘
                     ▼
┌──────────────────────────────────────────┐
│ CHECKPOINT SYSTEM                        │
│ What must be demonstrably true           │
│ before we move forward                   │
└────────────────────┬─────────────────────┘
                     ▼
┌──────────────────────────────────────────┐
│ ENGINEERING WORK UNITS                   │
│ What the AI/human actually does          │
└────────────────────┬─────────────────────┘
                     ▼
                   CODE
                     │
                     ▼
              TEST + EVALUATE
                     │
                     ▼
                  EVIDENCE
                     │
                     ▼
                 DECISION
```

## Final status

**CHECKPOINT & ENGINEERING-WORK UNIT SYSTEM v1.0 — ESTABLISHED.**

From this point onward, GroundTruth development should not be driven by:

> "What should we code next?"

It should be driven by:

> **"Which approved checkpoint is currently READY, what bounded work does it authorize, and what evidence will prove that it is complete?"**

That gives us the control mechanism needed to use **Antigravity and Jules aggressively without letting autonomous coding turn into autonomous architecture.**

The next actual engineering action is therefore **not "start coding GroundTruth."**

It is:

```text
C0.1
  ↓
Create/verify repository baseline
  ↓
Validate project documents
  ↓
Human approval
  ↓
C0.2
```

Only after those gates are demonstrated do we enter research/technology validation and subsequently implementation.
