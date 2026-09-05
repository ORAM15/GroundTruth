FINAL ARCHITECTURE SPECIFICATION

Project: GroundTruth
Status: FINAL — Architecture Baseline v1.0
Authority: Verified Project Constitution + Requirements & Constraints Specification
Architecture change policy: This architecture is considered frozen unless the project owner explicitly approves an Architectural Change Request (ACR).

0. Architectural Position

GroundTruth will be architected as a modular, evidence-first RAG application, not as a collection of independent microservices.

The central architectural principle is:

Every generated answer must have an explainable path back to the source evidence that caused it.

The architecture therefore preserves this lineage:

Source Document
      ↓
Document Version
      ↓
Chunk + Metadata
      ↓
Retrieved Evidence
      ↓
Selected Evidence
      ↓
Answer Claim
      ↓
Citation

The architecture does not mandate a particular LLM vendor, embedding model, vector database, cloud provider, or reranking model where the approved requirements do not provide sufficient evidence to make that choice.

That is deliberate—not uncertainty hidden as architecture.

The retrieval research already establishes that dense and lexical retrieval must be benchmarked, while hybrid retrieval remains a candidate and reranking remains conditional on evaluation.

1. System Context

GroundTruth exists between a user and a controlled knowledge collection.

                         ┌──────────────────┐
                         │       USER       │
                         └────────┬─────────┘
                                  │
                           Questions / Files
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │       GROUNDTRUTH       │
                    │                         │
                    │  Trustworthy RAG Engine │
                    └────────────┬────────────┘
                                 │
                 ┌───────────────┼────────────────┐
                 │               │                │
                 ▼               ▼                ▼
           Knowledge         AI Model        Operational
           Storage           Services        Systems
                 │               │                │
                 ▼               ▼                ▼
            Documents        Generation       Evaluation /
            + Evidence       + Embeddings     Observability
External actors

User

Uploads documents, creates/accesses collections, asks questions, inspects citations and provides feedback.

AI Model Provider

Provides model capabilities required for embedding and/or generation.

External Storage/Infrastructure

Provides persistent storage and runtime resources where the selected deployment architecture requires them.

No external actor is trusted with application-level authorization decisions.

GroundTruth remains responsible for deciding whether a user is allowed to access a resource.

2. High-Level Architecture
                                  USER
                                   │
                                   ▼
                         ┌──────────────────┐
                         │   WEB CLIENT     │
                         │                  │
                         │ Collections      │
                         │ Documents        │
                         │ Questions        │
                         │ Answers          │
                         │ Citations        │
                         └────────┬─────────┘
                                  │
                              HTTPS/API
                                  │
                                  ▼
                   ┌─────────────────────────────┐
                   │      APPLICATION API        │
                   │                             │
                   │ Auth / Authorization        │
                   │ Collections / Documents     │
                   │ Query orchestration         │
                   │ Feedback                    │
                   └──────────────┬──────────────┘
                                  │
             ┌────────────────────┼─────────────────────┐
             │                    │                     │
             ▼                    ▼                     ▼
      ┌──────────────┐    ┌──────────────┐     ┌──────────────┐
      │  Ingestion   │    │  Retrieval   │     │  Evaluation  │
      │   Pipeline   │    │   Pipeline   │     │   Subsystem  │
      └──────┬───────┘    └──────┬───────┘     └──────────────┘
             │                   │
             │             ┌─────┴─────────┐
             │             │               │
             │             ▼               ▼
             │       Semantic Search   Lexical Search
             │             │               │
             │             └──────┬────────┘
             │                    ▼
             │                  Fusion
             │                    │
             │               Reranking*
             │                    │
             │                    ▼
             │             Evidence Selection
             │                    │
             └───────────┐        ▼
                         │   Context Builder
                         │        │
                         │        ▼
                         │   LLM Generation
                         │        │
                         │        ▼
                         │  Trust Validation
                         │        │
                         │   ┌────┴─────┐
                         │   ▼          ▼
                         │ Answer     Abstain
                         │   │
                         │   ▼
                         │ Citations
                         │
                         ▼
                 ┌────────────────────┐
                 │ Persistent Storage │
                 │                    │
                 │ Documents          │
                 │ Chunks             │
                 │ Embeddings         │
                 │ Users/Collections  │
                 │ Answers/Feedback   │
                 └────────────────────┘

        * only retained if evaluation justifies it
3. Component Architecture

GroundTruth will be internally modular.

It does not require independently deployed microservices.

3.1 Application/API Layer

Responsibilities:

expose application interfaces
authenticate requests
authorize resource access
validate inputs
orchestrate workflows
return structured responses
expose controlled error states

It should not contain retrieval algorithms, document parsing logic or model-specific implementation directly.

3.2 Collection Management

Responsibilities:

create/access collections
enforce ownership
manage collection metadata
associate documents with collections

It establishes the logical boundary within which retrieval operates.

3.3 Document Management

Responsibilities:

accept document operations
validate supported input
create document records
expose processing state
expose document metadata
initiate ingestion

It does not perform the complete ingestion algorithm itself.

3.4 Ingestion Pipeline
Input File
    ↓
Validation
    ↓
Extraction
    ↓
Normalization
    ↓
Structure / Metadata Preservation
    ↓
Chunking
    ↓
Embedding
    ↓
Indexing
    ↓
READY

Responsibilities:

safe file handling
content extraction
document structure preservation
chunk generation
metadata generation
embedding generation
indexing
processing status
failure reporting.
3.5 Retrieval Pipeline
Question
    │
    ├──────────► Semantic Retrieval
    │
    └──────────► Lexical Retrieval
                    │
                    ▼
                  Fusion
                    │
                    ▼
               Candidate Set
                    │
                    ▼
              Reranking*
                    │
                    ▼
             Evidence Set

Responsibilities:

retrieve candidate evidence
apply collection/resource constraints
combine retrieval signals where justified
rank evidence
return provenance-rich results.
4. Data Architecture

The conceptual data model is:

USER
 │
 └── COLLECTION
       │
       ├── DOCUMENT
       │     │
       │     └── DOCUMENT VERSION
       │             │
       │             └── CHUNK
       │                    │
       │                    └── EMBEDDING
       │
       ├── QUERY
       │     │
       │     └── RETRIEVAL RESULT
       │
       ├── ANSWER
       │     │
       │     └── CITATION
       │
       └── FEEDBACK

Evaluation data exists as a logically separate subsystem:

EVALUATION DATASET
       │
       ├── Questions
       ├── Expected Evidence
       ├── Expected Answer Characteristics
       ├── Abstention Cases
       └── Adversarial Cases
5. Application Architecture

The application follows a layered model:

Presentation
     ↓
API / Interface
     ↓
Application Services
     ↓
Domain Logic
     ↓
Infrastructure Adapters
     ↓
External Systems

This prevents application logic from becoming tightly coupled to infrastructure.

For example:

AnswerService
     ↓
RetrievalInterface
     ↓
Concrete Retrieval Implementation

rather than:

AnswerService
     ↓
specific vendor SDK

This is particularly important for AI services.

6. Integration Architecture

External integrations are isolated behind interfaces.

                    GroundTruth
                         │
             ┌───────────┼────────────┐
             ▼           ▼            ▼
        AI Provider   File Storage   Runtime
             │
       ┌─────┴─────┐
       ▼           ▼
   Embeddings   Generation

The application should not allow provider-specific objects to leak throughout the domain/application layers.

7. Security Architecture

The security model follows:

                 USER
                   │
                   ▼
             Authentication
                   │
                   ▼
             Authorization
                   │
                   ▼
              Application
                   │
          ┌────────┴────────┐
          ▼                 ▼
     User-owned data    AI pipeline
                            │
                            ▼
                     UNTRUSTED CONTENT
Security principles

Least privilege

Components receive only the access required for their responsibility.

Input validation

User inputs and files are validated.

Data isolation

Collection/document access is authorization-controlled.

Secret isolation

Credentials never become client-visible application data.

Untrusted retrieval

Retrieved document text is never treated as privileged instructions.

No perfect-security claim

Prompt-injection defense is treated as risk reduction, not a guarantee.

8. Authentication / Authorization Architecture

The architecture separates:

Authentication
      ↓
Who is this user?
      ↓
Authorization
      ↓
Can this user access this resource?

Authorization must be enforced server-side.

Conceptually:

Request
  ↓
Authenticate identity
  ↓
Identify requested collection/document
  ↓
Check ownership/access
  ↓
Allow / Reject

A frontend hiding a document is not considered authorization.

9. AI / LLM Architecture

The AI layer is explicitly divided.

                   AI Layer
                      │
            ┌─────────┴─────────┐
            ▼                   ▼
       Embedding              LLM
        Service             Generation
            │                   │
            ▼                   ▼
      Vector/Search        Answer + Claims
                                │
                                ▼
                       Trust Validation
Generation flow
Question
   ↓
Retrieved Evidence
   ↓
Context Construction
   ↓
Grounded Prompt
   ↓
LLM
   ↓
Generated Answer
   ↓
Grounding/Citation Validation
   ↓
Answer OR Abstention

The LLM is not the knowledge source.

The knowledge source is the retrieved evidence.

10. Storage Architecture

Storage has two conceptual classes.

Persistent application data
Users
Collections
Documents
Versions
Chunks
Embeddings
Queries
Answers
Citations
Feedback
Original files
Uploaded document
       ↓
Object/file storage

The architecture intentionally separates:

original source artifact

from:

derived searchable representation.

This allows a chunk to remain traceable to the original source.

11. API Architecture

The API is resource-oriented.

Conceptually:

/auth/*
/collections/*
/documents/*
/queries/*
/answers/*
/feedback/*

The exact endpoint names remain implementation details.

Important API principles
authenticated operations require identity
resource access is authorization-controlled
request schemas are validated
errors are structured
internal implementation details are not exposed unnecessarily
AI-provider-specific API structures do not become public contracts.
12. Deployment Architecture

The deployment architecture is intentionally simple:

                    INTERNET
                       │
                       ▼
                ┌─────────────┐
                │ Web Client  │
                └──────┬──────┘
                       │
                      HTTPS
                       │
                       ▼
                ┌─────────────┐
                │ Application │
                │ API/Runtime │
                └──────┬──────┘
                       │
           ┌───────────┼───────────┐
           ▼           ▼           ▼
       Database     File Store   AI APIs

There is no architectural requirement for Kubernetes, service meshes, Kafka, Redis, or multiple independently deployed backend services.

Those are NOT REQUIRED by the current requirements.

The exact cloud/deployment providers remain unresolved because workload, cost and infrastructure experiments have not yet established them.

13. Observability Architecture

Observability follows the request lifecycle.

Request
  │
  ├── Authentication
  ├── Query processing
  ├── Retrieval
  ├── Ranking
  ├── Context construction
  ├── Generation
  ├── Validation
  └── Response

Each important stage should expose appropriate diagnostic information.

A conceptual request record:

Request ID
│
├── Query
├── Collection
├── Retrieval configuration
├── Retrieved evidence identifiers
├── Ranking information
├── Model information
├── Latency
├── Token/usage information
├── Errors
├── Final answer
└── Feedback

Sensitive data should not automatically be logged merely because it is available.

14. Testing Architecture

Testing has two distinct dimensions.

                    TESTING
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
       Software Testing      AI Evaluation
             │                   │
       "Does it work?"     "Is it good?"
Software tests

Cover:

ingestion
chunking
metadata
APIs
authorization
error handling
critical frontend workflows
security controls.
AI evaluation

Covers:

retrieval relevance
Recall@K
ranking
evidence completeness
answer correctness
groundedness
citation correctness
abstention
hallucination
adversarial cases
latency
cost.

The distinction is architectural, not merely organizational.

15. Failure-Handling Architecture

GroundTruth should use explicit failure states rather than pretending every pipeline succeeds.

                    Operation
                       │
                       ▼
                  Processing
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
          Success              Failure
             │                   │
             ▼                   ▼
         Continue          Classified Error
                                 │
                       ┌─────────┴─────────┐
                       ▼                   ▼
                  Recoverable         Non-recoverable
                       │                   │
                     Retry             Report
Retrieval failure
No useful evidence
       ↓
Do NOT generate unsupported answer
       ↓
ABSTAIN
AI provider failure
Generation unavailable
       ↓
Controlled error
       ↓
No fabricated answer
Document extraction failure
Extraction failure
       ↓
Document = FAILED
       ↓
User informed
       ↓
Document excluded from normal retrieval
Citation failure
Answer generated
       ↓
Citation cannot be validated
       ↓
Do not present fabricated citation
       ↓
Reject / regenerate / abstain according to validated policy
16. Trust Boundaries

There are several important trust boundaries.

Boundary 1 — User → Application
USER INPUT
    │
    ▼
VALIDATION

Everything coming from the user is untrusted input.

Boundary 2 — Uploaded File → Ingestion
UNTRUSTED FILE
       ↓
Validation / Safe Processing
       ↓
Extracted Data
Boundary 3 — Retrieved Document → LLM

This is the most important boundary.

             SYSTEM INSTRUCTIONS
                     │
                     ▼
               ┌───────────┐
               │    LLM    │
               └─────▲─────┘
                     │
            UNTRUSTED DATA
                     │
              Retrieved Docs

Retrieved content can provide facts.

It cannot provide authority.

Boundary 4 — Application → External AI Provider

Only required data should cross the provider boundary.

The architecture must account for the implications of sending document/query content to an external AI service.

Boundary 5 — User → Another User's Data
User A
  │
  ▼
Authorization
  │
  X
User B's Collection

Cross-user access must be rejected.

17. Primary Data Flows
Flow A — Document ingestion
User
 ↓
API
 ↓
Authorization
 ↓
File validation
 ↓
Document record
 ↓
Extraction
 ↓
Chunking
 ↓
Metadata
 ↓
Embedding
 ↓
Index
 ↓
READY
Flow B — Question answering
User Question
      ↓
API
      ↓
Authentication
      ↓
Authorization
      ↓
Query Processing
      ↓
Semantic Retrieval ─┐
                     ├──→ Fusion
Lexical Retrieval ──┘
                     ↓
                 Candidates
                     ↓
                 Reranking*
                     ↓
              Evidence Selection
                     ↓
              Context Construction
                     ↓
                  LLM
                     ↓
            Trust Validation
                     ↓
             ┌───────┴────────┐
             ▼                ▼
          Answer           Abstention
             │
             ▼
          Citations
18. Control Flows

There are three important control flows.

Ingestion control
SUBMITTED
   ↓
PROCESSING
   ↓
READY

or:

PROCESSING
   ↓
FAILED
Query control
REQUEST
  ↓
VALIDATE
  ↓
AUTHORIZE
  ↓
RETRIEVE
  ↓
ASSESS EVIDENCE
  ↓
GENERATE / ABSTAIN
  ↓
VALIDATE OUTPUT
  ↓
RESPOND
Evaluation control
Dataset
  ↓
Run System
  ↓
Collect Results
  ↓
Calculate Metrics
  ↓
Compare Baseline
  ↓
Accept / Reject Change

This prevents "it feels better" from becoming the evaluation methodology.

19. External Dependencies

At the architecture level, GroundTruth requires these categories of external dependency:

Dependency	Classification	Why
AI generation capability	OPEN QUESTION	Required to generate grounded answers
Embedding capability	OPEN QUESTION	Required for semantic retrieval if retained
Persistent database	OPEN QUESTION	Required for application/data persistence
File/object storage	OPEN QUESTION	Required to retain source documents
Public application hosting	OPEN QUESTION	Required for final public deployment
AI/model provider	OPEN QUESTION	Exact provider/model not established
Dedicated vector database	NOT REQUIRED	No requirement currently proves it necessary
Dedicated search engine	NOT REQUIRED	No requirement currently proves it necessary
Distributed message broker	NOT REQUIRED	No established scale requirement
Kubernetes	NOT REQUIRED	No established operational requirement
Redis/cache	NOT REQUIRED	No measured bottleneck justifying it
Agent orchestration framework	NOT REQUIRED	Not part of GroundTruth's core product requirements
20. Internal Interfaces

The architecture requires stable conceptual interfaces between major responsibilities.

DocumentProcessor
      ↓
Chunker
      ↓
EmbeddingProvider
      ↓
Indexer

Retriever
      ↓
Ranker
      ↓
EvidenceSelector
      ↓
ContextBuilder
      ↓
Generator
      ↓
TrustValidator
      ↓
CitationResolver

These interfaces matter more than the eventual framework names.

For example:

Retriever interface

Conceptually:

retrieve(
    query,
    collection,
    constraints
) → candidates
Generator interface
generate(
    question,
    evidence
) → answer
Trust validator
validate(
    answer,
    evidence
) → validation result

The exact programming-language syntax is implementation-specific.

21. Component Responsibilities
Component	Responsibility	Must NOT own
Web Client	User interaction	Authorization decisions
API	Application boundary/orchestration	Retrieval algorithms
Auth	Identity	Business authorization logic alone
Authorization	Resource access	UI state
Collection Manager	Collection lifecycle	AI generation
Document Manager	Document lifecycle	Retrieval ranking
Ingestion	Transform source into searchable evidence	User interface
Chunker	Produce retrievable evidence units	LLM answers
Embedding Adapter	Produce semantic representations	Application authorization
Indexer	Make evidence searchable	Answer generation
Retriever	Find candidates	Final answer generation
Ranker	Order candidates	User permissions
Evidence Selector	Determine usable evidence set	Source creation
Context Builder	Construct controlled model context	Model selection
Generator	Generate candidate answer	Source verification
Trust Validator	Assess support/safety/citations	Document storage
Citation Resolver	Map claims/evidence to sources	Generate unsupported sources
Evaluation	Measure system behavior	Modify production behavior implicitly
Observability	Record operational diagnostics	Business decisions
22. Major Architectural Invariants

These are the rules that must remain true regardless of implementation technology.

INV-001 — Evidence lineage

Every answer citation must ultimately trace to actual source material.

Citation
 → Evidence
 → Chunk
 → Document
INV-002 — No evidence, no fabricated answer

Insufficient evidence must never be converted into an invented confident answer.

INV-003 — Retrieved content is untrusted

A retrieved document cannot elevate itself to system/developer authority.

INV-004 — Authorization precedes protected retrieval

The system must establish that the requester is allowed to access a collection before returning its protected evidence.

INV-005 — Evaluation is external to model confidence

The LLM saying something confidently is not evidence that the answer is correct.

INV-006 — Metrics must be measured

No quality, latency, cost or scalability claim becomes a project fact without measurement.

INV-007 — Source of truth is the stored source artifact

Derived chunks/embeddings must not become the only representation of the original source.

INV-008 — Retrieval and generation are separate responsibilities

The generator must not silently substitute model memory for missing retrieval evidence.

INV-009 — Complexity requires justification

A component does not belong in GroundTruth merely because it is popular in RAG architectures.

INV-010 — AI-generated code is not automatically trusted

Implementation must be verified through testing/review.

23. Major Architectural Decisions
AD-001 — Modular application rather than microservices
Decision

Use a modular single application architecture initially.

Why required

The requirements demand separation of responsibilities but do not establish scale requiring independently deployed services.

Alternatives
microservices
serverless-per-component
distributed service architecture
Trade-offs

A modular application is simpler and easier to operate but gives less independent scaling.

Consequences

Ingestion, retrieval, evaluation and API responsibilities remain logically separated while sharing one application deployment where appropriate.

Requirements satisfied

NFR-006, CON-003, CON-004, SCALE-002, MAINT-001.

Technology classification: APPROVED DECISION — architectural style, not a vendor technology.

AD-002 — Evidence-first architecture
Decision

Evidence is a first-class object in the application flow.

Why required

GroundTruth's defining purpose is trustworthy, verifiable answers.

Alternatives
answer-first chatbot architecture
citations generated after the answer
Trade-off

More metadata and validation are required.

Consequence

The system can trace:

answer → citation → evidence → chunk → document
Requirements satisfied

FR-006, FR-013–FR-015, AI-004–AI-006, DATA-001–DATA-005, EVAL-012–EVAL-015.

Technology classification: APPROVED DECISION.

AD-003 — Separate retrieval from generation
Decision

Retrieval and generation are distinct pipeline stages.

Why required

A model's internal knowledge must not be confused with controlled knowledge-base evidence.

Alternatives
direct LLM question answering
single combined retrieval/generation framework
Trade-off

More pipeline coordination.

Consequence

Retrieval quality can be evaluated independently.

Requirements satisfied

AI-001, AI-002, EVAL-007–EVAL-012.

Technology classification: APPROVED DECISION.

AD-004 — Evaluate lexical and semantic retrieval independently
Decision

Both retrieval paradigms must be experimentally evaluated.

Why required

The requirements explicitly call for evidence-driven retrieval selection.

Alternatives
vector-only
keyword-only
hybrid without benchmarking
Trade-off

Additional experimentation.

Consequence

The final retrieval strategy is evidence-based.

Requirements satisfied

FR-009, AI-008, EVAL-007–EVAL-010, EVAL-018.

Technology classification: APPROVED DECISION — evaluation requirement.

AD-005 — Hybrid retrieval is conditional
Decision

Hybrid retrieval is architecturally supported but not guaranteed to be the final production retrieval mode.

Why required

The research identifies hybrid retrieval as a leading candidate but explicitly does not lock it before experimentation.

Alternatives
semantic-only
lexical-only
hybrid
Trade-off

Hybrid retrieval increases implementation and tuning complexity.

Consequence

The architecture can support it without pretending it has already proven superior.

Requirements satisfied

FR-010, AI-009, EVAL-018.

Technology classification: PROPOSAL / EXPERIMENTAL ARCHITECTURAL OPTION.

AD-006 — Reranking is conditional
Decision

Reranking is not a mandatory production component.

Why required

The requirements explicitly make reranking conditional on measurable improvement.

Alternatives
no reranker
model-based reranking
other ranking mechanisms
Trade-off

Potential relevance improvement versus latency/cost.

Consequence

Reranking must be benchmarked before becoming production architecture.

Requirements satisfied

FR-011, AI-009, EVAL-018.

Technology classification: DEFERRED / NOT YET APPROVED.

AD-007 — Source lineage is preserved during chunking
Decision

Chunks must preserve document/page/section/source lineage wherever source structure provides it.

Why required

Without lineage, useful citations cannot be reliably constructed.

Alternatives
plain text chunks
chunks with source metadata
Trade-off

More metadata handling.

Consequence

Citation quality becomes possible.

Requirements satisfied

FR-006, DATA-001–DATA-005, UX-002, AI-006.

Technology classification: APPROVED DECISION.

AD-008 — Explicit abstention path
Decision

Abstention is a first-class application outcome.

Answer
  OR
Abstention
Why required

It is mandatory to avoid unsupported confident answers.

Alternatives
always answer
generic error
answer with uncertainty wording
Trade-off

The system may sometimes refuse answerable questions.

Consequence

Abstention precision/recall-like behavior must be evaluated.

Requirements satisfied

FR-015, AI-004, EVAL-004, EVAL-014, UX-010.

Technology classification: APPROVED DECISION.

AD-009 — Document content is untrusted
Decision

Retrieved documents are treated as data, never as privileged instructions.

Why required

Indirect prompt injection is an explicit threat.

Alternatives

None that satisfy the trust requirement as reliably.

Trade-off

Prompt construction and validation become more deliberate.

Consequence

The system must maintain a clear instruction/data boundary.

Requirements satisfied

SEC-003, SEC-004, AI-003, TEST-009, EVAL-006.

Technology classification: APPROVED DECISION.

AD-010 — AI provider abstraction
Decision

Model-specific implementation is isolated behind an internal AI interface.

Why required

The requirements do not approve a specific provider, and model selection must be evidence-driven.

Alternatives
hard-code one provider throughout application
abstraction layer
Trade-off

A small abstraction layer introduces some engineering overhead.

Consequence

Model/provider experiments can occur without rewriting the application domain.

Requirements satisfied

AI-007, AI-008, CON-008, MAINT-005.

Technology classification: APPROVED DECISION — architectural abstraction.

Specific provider/model remains OPEN QUESTION.

AD-011 — Evaluation as a separate subsystem
Decision

AI evaluation is architecturally separated from normal application testing.

Why required

Software correctness and AI quality answer different questions.

Alternatives
only unit tests
only manual testing
evaluation embedded invisibly in application code
Trade-off

Additional evaluation infrastructure/files.

Consequence

Retrieval and generation improvements can be measured independently.

Requirements satisfied

TEST-008, EVAL-001–EVAL-020.

Technology classification: APPROVED DECISION.

AD-012 — No dedicated vector/search infrastructure by default
Decision

The architecture does not require a separate vector database or dedicated search engine.

Why required

The requirements establish capabilities, not a requirement for specialized infrastructure.

Alternatives
dedicated vector database
dedicated search engine
unified persistent data/search system
Trade-off

A unified approach may have less specialized scaling capability later.

Consequence

Specialized infrastructure can only be introduced through an architectural change if future measured requirements justify it.

Requirements satisfied

CON-002–CON-004, SCALE-002, RES-006.

Technology classification: NOT REQUIRED at present.

This does not mean a particular database has been selected.

AD-013 — Public deployment without predetermined cloud provider
Decision

GroundTruth SHALL be publicly deployable, but the architecture does not lock a specific provider.

Why required

Public deployment is mandatory; provider choice is not.

Alternatives

Any infrastructure capable of satisfying deployment requirements.

Trade-off

Provider-neutrality delays optimization for a particular platform.

Consequence

Deployment selection follows workload/cost/security evidence.

Requirements satisfied

DEP-001–DEP-008, RES-001–RES-006.

Technology classification: APPROVED DECISION — provider-neutral deployment architecture.

Specific provider: OPEN QUESTION.

24. Technology Decision Register

This is the definitive technology status at architecture freeze.

Technology / Category	Status	Reason
Web application technology	OPEN QUESTION	Requirements define UX, not framework
Backend language/framework	OPEN QUESTION	Requirements don't justify one specific choice yet
Database	OPEN QUESTION	Persistent database required; implementation choice not proven
Vector database	NOT REQUIRED	No demonstrated need for a dedicated system
Lexical search engine	NOT REQUIRED	No demonstrated need for a dedicated system
Embedding model	OPEN QUESTION	Must be benchmarked
LLM	OPEN QUESTION	Must be experimentally evaluated
Reranker	DEFERRED	Only if evaluation justifies it
Object storage technology	OPEN QUESTION	Source-file persistence required
Authentication provider	OPEN QUESTION	Authentication required; provider not selected
Cloud provider	OPEN QUESTION	Deployment required; provider not established
Cache	NOT REQUIRED	No measured requirement
Message broker	NOT REQUIRED	No established scale requirement
Microservices	NOT REQUIRED	No requirement justifying them
Kubernetes	NOT REQUIRED	No operational requirement
Agent framework	NOT REQUIRED	Not required by GroundTruth product
Observability platform	OPEN QUESTION	Observability required; specific platform not justified
Evaluation framework	OPEN QUESTION	Evaluation required; implementation technology not selected
CI/CD platform	OPEN QUESTION	Deployment automation is desirable, but exact mechanism isn't established

This is an intentional result of the architecture review.

Architecture is final; unproven vendor choices are not being fabricated into decisions.

25. Architectural Constraints

These constraints are now frozen.

AC-001

GroundTruth remains an evidence-grounded RAG system.

AC-002

No architecture may remove source evidence from the answer-generation trust chain.

AC-003

No component may treat retrieved document text as privileged instructions.

AC-004

Authorization must be enforced server-side.

AC-005

Citations must originate from actual source lineage.

AC-006

Abstention must remain a valid terminal outcome.

AC-007

Retrieval quality must be independently measurable.

AC-008

AI quality evaluation must remain separate from ordinary software testing.

AC-009

Advanced retrieval mechanisms must earn their inclusion through evaluation.

AC-010

No specialized infrastructure may be added solely for architectural fashion.

AC-011

The system must remain compatible with low-cost/student resource constraints.

AC-012

No unsupported scale or quality claims may be made.

AC-013

Architecture changes require explicit owner approval.

26. Architecture Consistency Audit

Now we test the architecture against the requirements, rather than merely presenting an architecture diagram.

Requirement Area	Covered?	Architectural evidence
Document ingestion	✅	Ingestion pipeline
Text extraction	✅	Extraction stage
Chunking	✅	Dedicated chunking stage
Metadata	✅	Lineage/metadata model
Embeddings	✅	Embedding interface
Semantic retrieval	✅	Retrieval pipeline
Lexical retrieval	✅	Retrieval pipeline
Hybrid retrieval	✅ Conditional	Fusion stage
Reranking	✅ Conditional	Reranking extension point
Grounded generation	✅	Context → LLM
Citations	✅	Evidence lineage + citation resolver
Abstention	✅	Explicit terminal path
Prompt injection defense	✅	Untrusted-data boundary
Authentication	✅	Auth boundary
Authorization	✅	Server-side authorization
Data isolation	✅	Collection authorization
File validation	✅	Ingestion boundary
Failure handling	✅	Explicit failure paths
Evaluation	✅	Separate evaluation subsystem
Retrieval evaluation	✅	Independent retrieval metrics
Answer evaluation	✅	AI evaluation
Citation evaluation	✅	Evaluation subsystem
Abstention evaluation	✅	Golden dataset
Security testing	✅	Adversarial test path
Observability	✅	Pipeline-level diagnostics
Latency measurement	✅	Stage-level observability
Cost measurement	✅	AI usage observation
Testing	✅	Software + AI testing split
Public deployment	✅	Deployment architecture
Low cost	✅	Minimal infrastructure constraint
Maintainability	✅	Modular architecture
No unnecessary microservices	✅	Single modular application
No unnecessary databases	✅	Dedicated systems not required
No fake scale claims	✅	Architectural constraint
Professional UX	✅	Web client + explicit states
Feedback	✅	Feedback component
API	✅	Application API layer
Audit result

PASS — architectural requirements are covered.

There are no identified mandatory requirements that require an architectural component absent from the specification.

27. Architecture Completeness Audit

We can also test the architecture against the requested architecture dimensions.

1.  System context                 ✓
2.  High-level architecture       ✓
3.  Component architecture        ✓
4.  Data architecture             ✓
5.  Application architecture      ✓
6.  Integration architecture      ✓
7.  Security architecture         ✓
8.  Authentication/authorization  ✓
9.  AI/LLM architecture           ✓
10. Storage architecture           ✓
11. API architecture              ✓
12. Deployment architecture       ✓
13. Observability architecture    ✓
14. Testing architecture          ✓
15. Failure handling              ✓
16. Trust boundaries              ✓
17. Data flows                    ✓
18. Control flows                 ✓
19. External dependencies         ✓
20. Internal interfaces           ✓
21. Component responsibilities   ✓
22. Major invariants              ✓
23. Architectural constraints     ✓

Architecture specification: COMPLETE.

28. Final Architecture in One Diagram

This is the diagram I would consider the canonical GroundTruth architecture:

                                  ┌──────────────┐
                                  │     USER     │
                                  └──────┬───────┘
                                         │
                                      HTTPS
                                         │
                                         ▼
                         ┌───────────────────────────┐
                         │       WEB CLIENT          │
                         │                           │
                         │ Collections / Documents  │
                         │ Questions / Answers       │
                         │ Evidence / Citations      │
                         └────────────┬──────────────┘
                                      │
                                      ▼
                         ┌───────────────────────────┐
                         │      APPLICATION API      │
                         │                           │
                         │ Authentication            │
                         │ Authorization             │
                         │ Validation                │
                         │ Workflow orchestration    │
                         └────────────┬──────────────┘
                                      │
                ┌─────────────────────┼──────────────────────┐
                │                     │                      │
                ▼                     ▼                      ▼
       ┌────────────────┐    ┌──────────────────┐    ┌───────────────┐
       │    INGESTION   │    │    RETRIEVAL     │    │  EVALUATION   │
       │                │    │                  │    │               │
       │ Validate       │    │ Semantic         │    │ Golden Data   │
       │ Extract        │    │ Lexical          │    │ Metrics       │
       │ Normalize      │    │ Fusion*          │    │ Regression    │
       │ Chunk          │    │ Rerank*          │    │ Adversarial   │
       │ Embed          │    │ Evidence Select  │    │               │
       │ Index          │    │                  │    │               │
       └───────┬────────┘    └────────┬─────────┘    └───────────────┘
               │                      │
               │                      ▼
               │              ┌─────────────────┐
               │              │ CONTEXT BUILDER │
               │              └────────┬────────┘
               │                       │
               │                       ▼
               │              ┌─────────────────┐
               │              │      LLM        │
               │              │   Generation    │
               │              └────────┬────────┘
               │                       │
               │                       ▼
               │              ┌─────────────────┐
               │              │  TRUST LAYER    │
               │              │                 │
               │              │ Grounding       │
               │              │ Citation        │
               │              │ Safety          │
               │              │ Abstention      │
               │              └────────┬────────┘
               │                       │
               │                  ┌────┴────┐
               │                  ▼         ▼
               │               ANSWER    ABSTAIN
               │                  │
               │                  ▼
               │             CITATIONS
               │
               ▼
      ┌─────────────────────────────────────────┐
      │             PERSISTENT DATA              │
      │                                         │
      │ Users / Collections / Documents        │
      │ Versions / Chunks / Embeddings          │
      │ Queries / Answers / Citations            │
      │ Feedback / Evaluation Data               │
      └─────────────────────────────────────────┘

              ┌────────────────────────────────┐
              │       OBSERVABILITY            │
              │                                │
              │ Requests / Retrieval / Models  │
              │ Latency / Usage / Errors       │
              └────────────────────────────────┘

* conditional on evaluation
29. Architecture Freeze
FINAL DECISIONS

The following are now architectural decisions:

GroundTruth will be a modular evidence-first RAG application.

Retrieval and generation are separate responsibilities.

Source lineage is preserved from document to evidence to citation.

Abstention is a first-class outcome.

Retrieved content is untrusted data.

Authentication and server-side authorization protect user data.

Evaluation is a separate subsystem from ordinary software testing.

Lexical and semantic retrieval will be evaluated.

Hybrid retrieval is supported as an experimental candidate, not assumed superior.

Reranking is conditional and remains deferred until evaluation justifies it.

A dedicated vector database, dedicated search engine, cache, message broker, Kubernetes deployment, microservice architecture and agent framework are not required by the current requirements.

The deployment architecture is provider-neutral until infrastructure requirements justify a specific provider.

AI providers/models are abstracted rather than embedded throughout the application.

STILL OPEN

These are not architectural omissions; they are implementation-level technology decisions that the Constitution and Requirements do not currently justify fixing:

Exact programming language
Exact web framework
Exact backend framework
Exact database implementation
Exact vector implementation
Exact embedding model
Exact LLM
Exact reranker
Exact authentication provider
Exact object storage provider
Exact cloud provider
Exact observability platform
Exact evaluation tooling

They must be selected through the next engineering process:

Architecture
     ↓
Technology requirements
     ↓
Research
     ↓
Controlled experiments
     ↓
Technology Decision Records
     ↓
Implementation
FINAL ARCHITECTURAL VERDICT

GroundTruth Architecture v1.0 is internally consistent with the approved requirements.

The architecture is intentionally not technologically bloated.

Its fundamental shape is:

          SOURCE
            ↓
        INGESTION
            ↓
        EVIDENCE
            ↓
        RETRIEVAL
            ↓
        SELECTION
            ↓
       GENERATION
            ↓
      TRUST VALIDATION
         ↙       ↘
     ANSWER     ABSTAIN
        ↓
    CITATIONS
        ↓
   EVALUATION
        ↓
  OBSERVABILITY

The architecture's strongest property is that trust is structural rather than cosmetic.

We are not saying:

"Here is an LLM answer, and here is a citation we generated afterward."

We are designing:

"Here is the answer, here is the evidence selected for it, here is the source lineage of that evidence, and here is the mechanism by which GroundTruth decides whether the evidence is sufficient."

That is the architectural identity of GroundTruth.

This specification is now the architectural baseline. Future changes should be treated as explicit Architectural Change Requests rather than informal redesigns.