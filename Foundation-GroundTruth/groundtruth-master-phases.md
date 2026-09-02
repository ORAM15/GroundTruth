FINAL MASTER PHASE PLAN

Project: GroundTruth
Document: Final Master Phase Plan
Status: AUTHORITATIVE — PHASE BASELINE v1.0
Purpose: Dependency-driven progression from the current empty/unimplemented state to the finished, publicly deployed GroundTruth product.

This is deliberately not a calendar.

The plan answers:

What must be true before we are allowed to move forward?

rather than:

"What should we do this week?"

0. Planning Principle

GroundTruth will progress through the following dependency chain:

PHASE 0
Project Foundation
       │
       ▼
PHASE 1
Research & Technology Validation
       │
       ▼
PHASE 2
Evaluation Foundation
       │
       ▼
PHASE 3
Engineering Bootstrap
       │
       ▼
PHASE 4
Ingestion & Evidence Pipeline
       │
       ▼
PHASE 5
Retrieval System
       │
       ▼
PHASE 6
Grounded Answer Engine
       │
       ▼
PHASE 7
Trust, Security & Failure Handling
       │
       ▼
PHASE 8
Product Integration & UX
       │
       ▼
PHASE 9
Observability, Hardening & Production Verification
       │
       ▼
PHASE 10
Deployment & Portfolio Release

There are 11 phases including Phase 0.

I would not reduce this further because several boundaries represent genuinely different engineering dependencies. Conversely, I would not split them into dozens of artificial "frontend phase", "backend phase", "database phase", etc. phases.

PHASE 0 — PROJECT FOUNDATION
Purpose

Establish the authoritative definition of GroundTruth before implementation begins.

Why it exists

The project already has a Constitution, Requirements, Architecture and Technology Specification. This phase converts those documents into the controlled baseline from which implementation operates.

We must prevent:

AI tool suggestion
      ↓
accidental scope change
      ↓
architecture drift
Prerequisites

None.

This is the current starting point.

Inputs
Project Constitution
Requirements & Constraints
Final Architecture
Technology & Tooling Specification
Objectives

Establish:

authoritative project documents
repository source-of-truth model
architecture baseline
requirements traceability
technology decision register
development rules
change-control mechanism.
Major workstreams
Requirements
    ↓
Architecture
    ↓
Technology
    ↓
Development governance

Establish repository documentation and decision records.

Expected artifacts
PRODUCT.md
REQUIREMENTS.md
ARCHITECTURE.md
TECHNOLOGY.md
EVALUATION.md
THREAT_MODEL.md
DEVELOPMENT.md

Plus appropriate decision/change records.

Validation

Verify that:

architecture satisfies requirements
technology choices do not contradict architecture
unresolved technology questions are explicitly marked
no proposal has been silently promoted to a decision.
Dependencies

None.

Risks

Scope drift

AI tools may introduce functionality not approved by the project.

Documentation drift

Repository documents may diverge from the actual project.

Human decisions required

Approve the baseline documents and authorize implementation.

Exit criteria

All baseline documents exist and agree with one another.

Definition of complete

Anyone entering the repository can determine what GroundTruth is, what it must do, what it must not do, and which architectural constraints govern implementation.

Next phase dependency

Phase 1 cannot begin formally until Phase 0 is accepted.

PHASE 1 — RESEARCH & TECHNOLOGY VALIDATION
Purpose

Resolve the remaining implementation-level technology questions through evidence rather than preference.

Why it exists

The architecture intentionally leaves several decisions open:

LLM
Embedding model
AI provider
Authentication
Object storage
Deployment provider
Observability implementation
Frontend testing tooling

These cannot responsibly be selected merely because they are popular.

Prerequisites

Phase 0 complete.

Inputs
Architecture
Requirements
Technology Specification
Research sources
GroundTruth design goals
Objectives

Determine the technology configuration that best satisfies the actual requirements.

Major workstreams
Retrieval research

Study:

dense retrieval
sparse retrieval
hybrid retrieval
reranking.
Document processing research

Study:

parsing
chunking
metadata
structural preservation
tables
difficult documents.
Trust/security research

Study:

grounding
citation correctness
abstention
indirect prompt injection
retrieval poisoning.
Model experiments

Use AI Studio to compare candidate:

LLMs
embedding models
prompt strategies
structured-output approaches
Infrastructure comparison

Compare deployment/storage/authentication options against:

cost
security
complexity
performance
operational burden
Expected artifacts
RESEARCH.md
MODEL_EVALUATION.md
RETRIEVAL_RESEARCH.md
TECHNOLOGY_DECISIONS.md

Potential ADRs for important decisions.

Validation

Technology decisions must be supported by:

requirements
experiments
documented trade-offs.
Dependencies

Phase 0.

Risks
Premature technology commitment

Avoided by keeping experiments separate from production implementation.

Vendor lock-in

Reduced through provider abstraction.

Benchmark chasing

A model with impressive general benchmarks may not be best for GroundTruth.

Human decisions required

Approve:

generation model/provider
embedding model/provider
deployment configuration
authentication approach
storage configuration
observability approach.
Exit criteria

All required implementation-level technology decisions are resolved or explicitly deferred with a documented reason.

Definition of complete

We know what technologies GroundTruth will actually use and can explain why each one exists.

Next phase dependency

Phase 2 requires the selected model/embedding configuration because evaluation data must test the actual intended pipeline.

PHASE 2 — EVALUATION FOUNDATION
Purpose

Build the measurement system before serious RAG implementation.

Why it exists

The most dangerous GroundTruth development pattern is:

Build RAG
   ↓
Ask five questions
   ↓
"It seems good"

Instead:

Golden Dataset
      ↓
System
      ↓
Metrics
      ↓
Evidence
      ↓
Engineering decision
Prerequisites

Phase 1 technology/model decisions.

Inputs
Requirements
Architecture
Research
Selected model configuration
Representative source corpus.
Objectives

Create the initial GroundTruth evaluation corpus.

Major workstreams

Create cases for:

Normal questions
Difficult questions
Multi-hop questions
Unanswerable questions
Adversarial questions
Prompt-injection cases

Define metrics for:

Retrieval
Answer correctness
Groundedness
Citation correctness
Abstention
Security
Latency
Cost
Expected artifacts
evals/
├── datasets/
├── runners/
├── metrics/
└── reports/

Plus:

EVALUATION.md
Validation

The evaluation runner itself must be tested.

At least one known-good and one known-bad scenario should demonstrate that metrics can distinguish them.

Dependencies

Phase 1.

Risks
Bad evaluation dataset

A weak dataset produces misleading confidence.

LLM-as-judge overreliance

Automated judges are useful but not ground truth.

Metric gaming

Optimizing one metric can damage another.

Human decisions required

Approve the initial golden dataset and metric definitions.

Exit criteria

GroundTruth can run a baseline evaluation before production RAG exists.

Definition of complete

We have a repeatable way to determine whether an implementation actually improved GroundTruth.

Next phase dependency

Phase 3 can now safely establish the production codebase.

PHASE 3 — ENGINEERING BOOTSTRAP
Purpose

Create the reproducible software foundation.

Why it exists

Before building features, we need a project that can reliably:

install
run
test
lint
configure
commit
Prerequisites

Phase 0–2.

Inputs
Final technology stack
Architecture
Evaluation subsystem design.
Objectives

Establish:

frontend
backend
database
configuration
testing
CI
development environment
Major workstreams

Create the repository structure.

Establish:

Python environment
Node environment
environment variables
database configuration
API skeleton
frontend skeleton
test infrastructure
GitHub Actions

Establish development conventions.

Expected artifacts

A running but functionally minimal application:

Frontend
    ↕
Backend
    ↕
Database

plus:

CI pipeline
Validation

A clean environment must be able to:

clone repository
↓
install dependencies
↓
configure environment
↓
start application
↓
run tests
↓
pass CI
Dependencies

Phase 2.

Risks
dependency conflicts
environment inconsistency
secrets committed accidentally
AI-generated setup errors.
Human decisions required

Approve repository structure and development workflow.

Exit criteria

Clean setup succeeds from repository instructions.

Definition of complete

A new developer can reproduce the development environment without relying on undocumented local state.

Next phase dependency

Phase 4 needs the backend, database and storage foundations.

PHASE 4 — INGESTION & EVIDENCE PIPELINE
Purpose

Transform source documents into trustworthy, traceable searchable evidence.

Why it exists

Retrieval quality cannot exceed ingestion quality.

Bad extraction
     ↓
Bad chunks
     ↓
Bad retrieval
     ↓
Bad answer
Prerequisites

Phase 3.

Inputs
Source corpus
Document requirements
Storage design
Chunking research.
Objectives

Implement:

Upload
 ↓
Validation
 ↓
Extraction
 ↓
Normalization
 ↓
Metadata
 ↓
Chunking
 ↓
Embedding
 ↓
Indexing
Major workstreams
Document lifecycle
SUBMITTED
PROCESSING
READY
FAILED
Parser

Extract supported document content.

Chunker

Preserve:

document identity
page information where available
sections/headings where available
chunk ordering
source lineage.
Embeddings

Generate and store embeddings.

Indexing

Make chunks searchable.

Expected artifacts

Working ingestion pipeline.

Document/chunk database schema.

Tests for:

valid documents
empty documents
malformed documents
duplicates
unsupported documents
extraction failures.
Validation

A known document must produce:

document
→ version
→ chunks
→ metadata
→ embeddings
→ searchable records

with lineage preserved.

Dependencies

Phase 3.

Risks
poor parsing
malformed files
lost metadata
incorrect chunk boundaries
duplicate ingestion.
Human decisions required

Approve chunking behavior if experiments reveal competing strategies.

Exit criteria

Representative documents are successfully transformed into searchable evidence with traceable provenance.

Definition of complete

GroundTruth can safely ingest real supported documents and produce reliable evidence units.

Next phase dependency

Phase 5 requires indexed chunks and embeddings.

PHASE 5 — RETRIEVAL SYSTEM
Purpose

Build and measure the evidence retrieval subsystem.

Why it exists

Retrieval is the foundation of GroundTruth's trust model.

Prerequisites

Phase 4.

Inputs
Indexed evidence
Golden evaluation dataset
Retrieval research.
Objectives

Implement and benchmark:

Semantic retrieval
Lexical retrieval

Then experimentally evaluate:

Hybrid retrieval

and, if justified:

Reranking
Major workstreams
Semantic retrieval

Evaluate vector similarity.

Lexical retrieval

Evaluate keyword-based retrieval.

Candidate fusion

Test whether combining retrieval approaches improves results.

Reranking

Test whether reranking materially improves evidence quality enough to justify cost/latency.

Expected artifacts
retrieval/

plus benchmark reports.

Validation

Measure:

Recall@K
Precision@K where applicable
MRR
evidence completeness
latency
cost
Dependencies

Phase 2 + Phase 4.

Risks
Vector-only weakness

Exact terms may be missed.

Hybrid complexity

Fusion introduces tuning complexity.

Reranker cost

Quality gains may not justify latency.

Human decisions required

Approve the final production retrieval strategy based on evaluation.

Exit criteria

A retrieval strategy is selected because the evaluation demonstrates it is appropriate.

Definition of complete

Given a question, GroundTruth can retrieve a high-quality evidence set from the authorized knowledge collection.

Next phase dependency

Phase 6 requires reliable evidence retrieval.

PHASE 6 — GROUNDED ANSWER ENGINE
Purpose

Transform retrieved evidence into answers with citations.

Why it exists

This is where GroundTruth becomes an actual answer engine rather than a search system.

Prerequisites

Phase 5.

Inputs
Evidence set
Selected LLM
Citation requirements
Evaluation dataset.
Objectives

Implement:

Question
 ↓
Evidence
 ↓
Context construction
 ↓
LLM
 ↓
Answer
 ↓
Citation mapping
Major workstreams
Context construction

Provide controlled evidence to the model.

Grounded generation

Require answers to remain within evidence.

Citation generation

Tie answer claims to source evidence.

Output structure

Define a stable application-level answer representation.

Expected artifacts

Working answer pipeline.

Citation lineage implementation.

Generation tests.

Validation

Test:

answerable questions
multi-evidence questions
conflicting evidence
unsupported questions
citation mapping.
Dependencies

Phase 5.

Risks
hallucination
citation fabrication
context overload
unsupported claims
model instruction-following failures.
Human decisions required

Approve generation/citation behavior after evaluation.

Exit criteria

Answers can be generated from retrieved evidence and citations can be traced back to actual sources.

Definition of complete

GroundTruth can answer supported questions using retrieved evidence and explain where the answer came from.

Next phase dependency

Phase 7 hardens this pipeline against insufficient evidence and hostile content.

PHASE 7 — TRUST, SECURITY & FAILURE HANDLING
Purpose

Make the answer engine trustworthy under failure and adversarial conditions.

Why it exists

A system that works only with clean documents and answerable questions is not GroundTruth.

Prerequisites

Phase 6.

Inputs
Threat model
Security requirements
Evaluation dataset
Working answer pipeline.
Objectives

Implement and validate:

Abstention
Prompt-injection defense
Input validation
Authorization
Error handling
Failure recovery
Citation validation
Major workstreams
Abstention
Weak evidence
     ↓
ABSTAIN
Prompt-injection defense

Treat retrieved documents as:

untrusted data.

Authorization

Ensure users cannot retrieve another user's protected evidence.

Failure handling

Handle:

AI provider failure
database failure
extraction failure
empty retrieval
invalid files
citation validation failure.
Security testing

Use adversarial documents and queries.

Expected artifacts
THREAT_MODEL.md
security tests
failure-handling tests
abstention evaluation reports
injection evaluation reports
Validation

GroundTruth must demonstrate:

malicious document
      ↓
retrieved
      ↓
still treated as data
      ↓
system instructions preserved

and:

insufficient evidence
      ↓
abstention
Dependencies

Phase 6.

Risks
false confidence
false abstention
incomplete injection defenses
authorization bugs
sensitive data leakage.
Human decisions required

Approve acceptable security limitations and abstention thresholds.

Exit criteria

Security and failure tests meet defined acceptance thresholds.

Definition of complete

GroundTruth fails safely rather than confidently inventing answers.

Next phase dependency

Only after this phase can the complete user-facing workflow safely be assembled.

PHASE 8 — PRODUCT INTEGRATION & UX
Purpose

Turn the validated core engine into a coherent user-facing product.

Why it exists

The backend being correct does not automatically create a usable product.

Prerequisites

Phases 4–7.

The core ingestion/retrieval/generation/trust pipeline must work first.

Inputs
Validated backend
UX requirements
GroundTruth product definition
Stitch design exploration where useful.
Objectives

Implement the complete workflow:

User
 ↓
Collection
 ↓
Document upload
 ↓
Processing status
 ↓
Question
 ↓
Answer
 ↓
Citation
 ↓
Evidence
 ↓
Feedback
Major workstreams
Document UI
upload
processing status
failure state.
Query UI
question input
loading state
answer state
abstention state.
Evidence UI
citations
source metadata
supporting passage.
Feedback

Allow useful user feedback.

Accessibility/responsiveness

Ensure the interface behaves professionally.

Expected artifacts

Complete functional web product.

Validation

Test critical end-to-end workflows.

Dependencies

Phases 4–7.

Risks
frontend masking backend weaknesses
unclear citations
poor failure UX
accessibility problems
inconsistent application states.
Human decisions required

Approve final UX/design direction.

Exit criteria

A user can complete the complete GroundTruth workflow without developer intervention.

Definition of complete

GroundTruth feels like one coherent product rather than a collection of engineering components.

Next phase dependency

Phase 9 requires the integrated product.

PHASE 9 — OBSERVABILITY, HARDENING & PRODUCTION VERIFICATION
Purpose

Determine whether the integrated system is actually ready for production deployment.

Why it exists

A product can function correctly and still be:

slow
expensive
fragile
difficult to diagnose
insecure
unreliable.
Prerequisites

Phase 8.

Inputs

Complete integrated product.

Objectives

Establish:

observability
performance measurements
cost measurements
reliability verification
security verification
regression evaluation
Major workstreams
Observability

Capture useful request lifecycle information.

Performance

Measure:

P50
P95
retrieval latency
generation latency
end-to-end latency
Cost

Measure:

cost/query
embedding cost
generation cost
storage cost
Reliability

Test failures of:

LLM
embedding service
database
storage
malformed input.
Regression evaluation

Run the complete evaluation suite.

Expected artifacts
OBSERVABILITY.md
PERFORMANCE.md
COST.md
PRODUCTION_READINESS.md

Evaluation reports.

Validation

The system must pass:

functional tests
AI evaluation
security tests
failure tests
performance checks
Dependencies

Phase 8.

Risks
Optimizing without evidence

Only measured bottlenecks should be optimized.

Observability overload

Do not log everything.

Cost surprises

AI usage must be measured before public deployment.

Human decisions required

Go/no-go decision for production deployment.

Exit criteria

The project owner determines that the measured system satisfies production-readiness thresholds.

Definition of complete

We have evidence that the system works, is reasonably secure, is observable, and behaves acceptably under failure.

Next phase dependency

Phase 10 deployment.

PHASE 10 — DEPLOYMENT & PORTFOLIO RELEASE
Purpose

Move GroundTruth from verified engineering system to publicly usable product.

Why it exists

Public deployment is mandatory.

Prerequisites

Phase 9 production-readiness approval.

Inputs
Production-ready application
Deployment configuration
Security configuration
Documentation
Evaluation results.
Objectives

Deploy:

Frontend
Backend/API
Database
Object storage
AI integrations
Observability
Major workstreams
Production configuration

Environment variables and secrets.

Deployment

Deploy frontend/backend/database/storage.

Domain/public URL

Establish public access.

Production verification

Run real end-to-end workflows.

Documentation

Finalize:

README
setup
architecture
evaluation
security
deployment
limitations
Portfolio

Produce:

screenshots
demo
architecture explanation
resume bullets
interview narrative.
Expected artifacts
PUBLIC URL
DEPLOYMENT.md
FINAL README
EVALUATION REPORT
SECURITY/THREAT MODEL
ARCHITECTURE DIAGRAM
PROJECT DEMO
PORTFOLIO MATERIAL
Validation

A clean external user should be able to:

open product
 ↓
authenticate
 ↓
access/create collection
 ↓
upload supported document
 ↓
wait for processing
 ↓
ask question
 ↓
receive answer/citations
 ↓
inspect evidence
 ↓
receive honest abstention when evidence is insufficient
Dependencies

Phase 9.

Risks
production configuration errors
exposed secrets
unexpected AI costs
deployment-specific failures
database/storage misconfiguration.
Human decisions required

Final public-release approval.

Exit criteria

Public deployment works and documentation accurately represents the actual system.

Definition of complete

GroundTruth is publicly usable, technically defensible, measurable, documented and ready to demonstrate in a serious AI engineering interview.

Next phase dependency

None.

This is the terminal phase of the current master plan.

11. Dependency Graph

The strict dependency graph is:

                         ┌──────────────────┐
                         │ PHASE 0          │
                         │ FOUNDATION       │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ PHASE 1          │
                         │ RESEARCH /       │
                         │ TECHNOLOGY       │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ PHASE 2          │
                         │ EVALUATION       │
                         │ FOUNDATION       │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ PHASE 3          │
                         │ ENGINEERING      │
                         │ BOOTSTRAP        │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ PHASE 4          │
                         │ INGESTION        │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ PHASE 5          │
                         │ RETRIEVAL        │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ PHASE 6          │
                         │ GROUNDED         │
                         │ GENERATION       │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ PHASE 7          │
                         │ TRUST / SECURITY │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ PHASE 8          │
                         │ PRODUCT / UX     │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ PHASE 9          │
                         │ HARDENING /      │
                         │ OBSERVABILITY    │
                         └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ PHASE 10         │
                         │ DEPLOY / RELEASE │
                         └──────────────────┘

There are also important cross-phase dependencies:

PHASE 2 ───────────────────────────────► PHASE 5
  │                                       │
  │                                       ▼
  └──────────────────────────────────► PHASE 6
                                          │
                                          ▼
PHASE 2 ───────────────────────────────► PHASE 7
                                          │
                                          ▼
PHASE 8 ───────────────────────────────► PHASE 9
                                          │
PHASE 2 ───────────────────────────────► PHASE 9
                                          │
                                          ▼
                                      PHASE 10

In other words, evaluation does not end after Phase 2.

Phase 2 creates the evaluation foundation; later phases continuously use it.

12. Critical Dependency Gates

These are the gates I would enforce most strictly.

Gate A — Before implementation
Requirements
     +
Architecture
     +
Technology decisions
     +
Evaluation foundation
     ↓
IMPLEMENTATION ALLOWED
Gate B — Before generation
Ingestion
     +
Retrieval
     ↓
Generation allowed

We don't build the answer layer around fake retrieval.

Gate C — Before UI polish
Ingestion
     +
Retrieval
     +
Generation
     +
Trust/Security
     ↓
Product UX

We don't polish an unreliable engine.

Gate D — Before deployment
Functional tests
+
AI evaluation
+
Security
+
Failure handling
+
Observability
+
Performance
+
Cost
        ↓
PUBLIC DEPLOYMENT
13. What We Deliberately Do NOT Make Into Phases

This is important.

There is no separate phase for:

LangChain
agents
microservices
Kubernetes
Redis
vector database
"AI integration"
"database integration"
"frontend styling"
"DevOps"
"MLOps"
"multi-agent development."

Those are implementation details or optional technologies, not independent project outcomes.

Likewise:

Stitch
Flow
Canva
Jules
Gemini
AI Studio

are tools used across phases, not phases themselves.

14. Tool Participation Across Phases
Phase 0
ChatGPT + Gemini + GitHub
        │
Phase 1
Gemini Notebook + AI Studio + ChatGPT
        │
Phase 2
ChatGPT + Gemini + GitHub
        │
Phase 3
Antigravity + Gemini CLI + GitHub
        │
Phase 4
Antigravity + Jules + GitHub
        │
Phase 5
AI Studio + Antigravity + Jules + evaluation
        │
Phase 6
AI Studio + Antigravity + Jules + evaluation
        │
Phase 7
Antigravity + Jules + adversarial evaluation
        │
Phase 8
Stitch + Antigravity + GitHub
        │
Phase 9
Antigravity + Jules + GitHub + evaluation
        │
Phase 10
Deployment + GitHub + Flow/Canva

The principle remains:

Tools serve the phase; phases do not exist to justify tools.

15. Master Definition of Done

The project is complete only when all ten gates have been satisfied:

[✓] Product scope established
[✓] Architecture validated
[✓] Technology decisions justified
[✓] Evaluation dataset operational
[✓] Engineering foundation reproducible
[✓] Real ingestion works
[✓] Retrieval is measured
[✓] Grounded generation works
[✓] Citations are traceable
[✓] Abstention works
[✓] Security defenses tested
[✓] Failure handling verified
[✓] Product UX complete
[✓] Observability operational
[✓] Performance measured
[✓] Cost measured
[✓] Regression evaluation passes
[✓] Public deployment works
[✓] Documentation matches reality
[✓] Portfolio/interview evidence exists
16. Final Consistency Check Against FINAL ARCHITECTURE

Now the important audit.

Final Architecture Element	Master Plan Coverage
System context	Phase 0
Modular application	Phase 3
Frontend	Phase 8
Backend/API	Phase 3 onward
Collection management	Phase 8
Document management	Phase 4 + 8
Ingestion	Phase 4
Extraction	Phase 4
Chunking	Phase 4
Metadata	Phase 4
Embeddings	Phase 4
Semantic retrieval	Phase 5
Lexical retrieval	Phase 5
Hybrid retrieval	Phase 5
Reranking	Phase 5, conditional
Evidence selection	Phase 5
Context construction	Phase 6
LLM generation	Phase 6
Grounding validation	Phase 7
Citation validation	Phase 6–7
Abstention	Phase 7
Authentication	Phase 8 / 9
Authorization	Phase 7–8
Storage	Phase 3–4
API architecture	Phase 3 onward
Security	Phase 7 + continuous
Trust boundaries	Phase 4–7
Evaluation	Phase 2 + continuous
Testing	Phase 3 onward
Observability	Phase 9
Failure handling	Phase 7 + 9
Deployment	Phase 10
Documentation	Phase 0 + 10
Portfolio	Phase 10
Audit result

PASS.

No major architectural component is left without a phase.

No phase introduces a mandatory architectural component that the Final Architecture does not contain.

No phase requires a technology explicitly classified as NOT REQUIRED.

Hybrid retrieval and reranking remain conditional rather than being incorrectly promoted to mandatory implementation.

17. Final Phase Baseline

The authoritative GroundTruth progression is therefore:

┌──────────────────────────────────────────────┐
│ 0. PROJECT FOUNDATION                        │
│ Define and lock the engineering baseline     │
└──────────────────────┬───────────────────────┘
                       ▼
┌──────────────────────────────────────────────┐
│ 1. RESEARCH & TECHNOLOGY VALIDATION         │
│ Resolve evidence-dependent technology choices│
└──────────────────────┬───────────────────────┘
                       ▼
┌──────────────────────────────────────────────┐
│ 2. EVALUATION FOUNDATION                     │
│ Build the golden dataset + metrics           │
└──────────────────────┬───────────────────────┘
                       ▼
┌──────────────────────────────────────────────┐
│ 3. ENGINEERING BOOTSTRAP                     │
│ Make the repo reproducible and testable      │
└──────────────────────┬───────────────────────┘
                       ▼
┌──────────────────────────────────────────────┐
│ 4. INGESTION & EVIDENCE                      │
│ Documents → traceable searchable evidence   │
└──────────────────────┬───────────────────────┘
                       ▼
┌──────────────────────────────────────────────┐
│ 5. RETRIEVAL                                 │
│ Evidence retrieval + measured optimization   │
└──────────────────────┬───────────────────────┘
                       ▼
┌──────────────────────────────────────────────┐
│ 6. GROUNDED ANSWER ENGINE                   │
│ Evidence → answer → citations                │
└──────────────────────┬───────────────────────┘
                       ▼
┌──────────────────────────────────────────────┐
│ 7. TRUST, SECURITY & FAILURE HANDLING       │
│ Abstention + adversarial resilience          │
└──────────────────────┬───────────────────────┘
                       ▼
┌──────────────────────────────────────────────┐
│ 8. PRODUCT INTEGRATION & UX                  │
│ Turn validated engine into usable product    │
└──────────────────────┬───────────────────────┘
                       ▼
┌──────────────────────────────────────────────┐
│ 9. HARDENING & PRODUCTION VERIFICATION      │
│ Observe, measure, attack, verify             │
└──────────────────────┬───────────────────────┘
                       ▼
┌──────────────────────────────────────────────┐
│ 10. DEPLOYMENT & PORTFOLIO RELEASE           │
│ Public, documented, defensible GroundTruth   │
└──────────────────────────────────────────────┘
Final verdict

This is the phase structure I recommend freezing.

The most important sequencing decision is:

Evaluation precedes serious implementation.

And the second is:

The trustworthy core precedes UI polish.

And the third:

Production deployment comes only after the system has been measured, attacked, observed and verified.

So the next actionable point is Phase 0 execution, not coding the RAG pipeline.

No later phase should be started simply because we are eager to build it. Its entry gate must be satisfied first.
