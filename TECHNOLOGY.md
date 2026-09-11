TECHNOLOGY AND TOOLING SPECIFICATION

Project: GroundTruth
Document: Technology & Tooling Specification
Status: FINAL TECHNOLOGY BASELINE
Inputs: FINAL ARCHITECTURE + REQUIREMENTS & CONSTRAINTS
Technology selection principle: Requirements → architectural responsibility → alternatives → trade-offs → selection

This document does not change the product scope or architecture.

One important distinction before we begin:

A tool can be approved for GroundTruth without being currently configured.

So every tool below is classified independently by architectural approval and actual setup state.

1. Technology Selection Philosophy

GroundTruth does not need the "largest possible AI stack."

The technology must support:

Reliable ingestion
       ↓
Reliable retrieval
       ↓
Evidence lineage
       ↓
Grounded generation
       ↓
Citation / abstention
       ↓
Evaluation
       ↓
Security
       ↓
Deployment

Therefore:

POPULARITY
    ≠
REQUIREMENT

A technology enters the stack only when it solves an identified problem.

2. Final Technology Stack

The recommended implementation stack is:

┌─────────────────────────────────────────────────────────┐
│                    GROUNTRUTH                           │
├─────────────────────────────────────────────────────────┤
│ Frontend       React + TypeScript                       │
│ Backend        Python + FastAPI                         │
│ Runtime        Node.js (frontend tooling) + Python      │
│ Database       PostgreSQL                               │
│ Search         PostgreSQL-based semantic + lexical     │
│                retrieval initially                       │
│ Embeddings     Provider/model selected experimentally   │
│ LLM            Provider/model selected experimentally   │
│ Storage        S3-compatible object storage             │
│ Auth           Managed authentication solution          │
│ Testing        Pytest + frontend test framework         │
│ API testing    HTTP/API integration tests               │
│ Evaluation     Versioned custom evaluation subsystem     │
│ CI/CD          GitHub Actions                            │
│ Deployment     Managed frontend + backend + database     │
│ Observability  Structured application telemetry          │
│ Documentation  Markdown + architecture records          │
└─────────────────────────────────────────────────────────┘

There is one deliberate qualification:

The exact AI models, authentication provider, object-storage provider, cloud provider and observability vendor remain technology decisions requiring final configuration/experimentation.

The architecture is final; these implementation-level decisions do not alter it.

3. Programming Language
Decision
Python — APPROVED DECISION
Why needed

Python is particularly appropriate for GroundTruth's AI/retrieval pipeline:

document processing
embedding
retrieval experimentation
evaluation
LLM integration
data processing

All are central to the product.

Alternatives considered

TypeScript everywhere

Pros:

one language
excellent web ecosystem

Cons:

weaker fit for experimentation/data/evaluation ecosystem
AI/RAG experimentation is less natural for this project

Go

Pros:

excellent runtime characteristics

Cons:

unnecessary complexity for this project's AI experimentation requirements

Java

Pros:

mature enterprise ecosystem

Cons:

considerably heavier for this student-scale AI product.
Trade-off

Python gives us a very strong AI engineering ecosystem but requires care around runtime performance and dependency management.

Constraints

Python must not become an excuse to write an unstructured backend.

The application must remain modular.

Status

APPROVED DECISION

4. Backend Runtime / Framework
FastAPI — APPROVED DECISION
Purpose

Provide the application/API boundary.

Why needed

GroundTruth requires:

HTTP APIs
validation
authentication integration
document operations
query operations
feedback
structured errors.

FastAPI fits the Python backend without introducing a large application framework.

Alternatives

Flask

Simpler, but requires more manual API infrastructure.

Django

Powerful, but considerably broader than GroundTruth requires.

Node/Express

Viable, but would move the AI/retrieval application into a different ecosystem from the selected Python core.

Selection reason

FastAPI gives us:

Python
+
typed request/response models
+
API documentation
+
async support
+
small framework footprint

without requiring Django-level infrastructure.

Constraints

Do not put the entire RAG pipeline directly inside route handlers.

Status

APPROVED DECISION

5. Frontend
React + TypeScript — APPROVED DECISION
Purpose

Build the public GroundTruth web application.

Why needed

GroundTruth requires a real interactive product:

collection management
document upload
processing status
question input
answer presentation
citations
evidence inspection
feedback
error/loading states.
Alternatives

Next.js

Very strong option and remains technically viable.

Vue

Good framework, but no requirement specifically favors it.

Plain JavaScript

Insufficient maintainability for the intended product.

Selection

React + TypeScript provides a mature component model while keeping frontend/backend responsibilities clear.

Important distinction

We are not selecting React because it is popular.

We are selecting it because the requirements need a maintainable interactive web client, and React provides that without introducing unnecessary architectural infrastructure.

Status

APPROVED DECISION

6. Database
PostgreSQL — APPROVED DECISION

This is the strongest infrastructure decision in the stack.

Why needed

GroundTruth needs persistent structured data for:

Users
Collections
Documents
Versions
Chunks
Metadata
Queries
Answers
Citations
Feedback
Evaluation information

A relational model naturally represents these relationships.

Alternatives

MongoDB

Flexible document model, but GroundTruth has strong relationships between users → collections → documents → chunks → citations.

Dedicated vector database

Potentially useful later, but not required by current requirements.

Multiple databases

Explicitly violates our anti-overengineering principle unless workload evidence requires it.

Selection

PostgreSQL gives us one durable relational foundation.

It also allows us to investigate whether semantic retrieval can initially coexist with the primary database rather than immediately introducing another infrastructure component.

Status

APPROVED DECISION

7. Vector Storage
Dedicated vector database — NOT REQUIRED

This deserves emphasis.

We do not currently approve:

Pinecone
Weaviate
Milvus
Qdrant
etc.

as mandatory infrastructure.

Why?

The requirement is:

semantic retrieval

It is not:

use a dedicated vector database.

A dedicated vector system introduces:

another service
another deployment
another credential
another operational dependency
another failure mode
potentially another cost.

Therefore we first evaluate whether PostgreSQL-based storage/search is sufficient for our target workload.

Status

NOT REQUIRED

A future measured scalability requirement could trigger an Architectural Change Request.

8. Lexical Search
PostgreSQL lexical search — APPROVED DECISION

GroundTruth requires evaluation of lexical retrieval.

We do not need a separate search engine initially.

The initial architecture should therefore investigate:

PostgreSQL
   │
   ├── structured data
   ├── semantic representation
   └── lexical search
Alternatives

Dedicated search engine.

Why not initially?

No current requirement establishes a workload large enough to justify another search infrastructure.

Status

APPROVED DECISION

9. Embedding Model
Exact embedding model — OPEN QUESTION

This is intentionally not selected yet.

Why?

Embedding quality directly affects:

semantic retrieval
Recall@K
evidence completeness
answer quality

The project therefore needs an experiment.

Candidate models should be compared using the GroundTruth evaluation dataset.

Evaluation dimensions
Recall@K
MRR
Evidence completeness
Latency
Cost
Storage footprint
Alternatives

Different hosted embedding APIs or locally runnable embedding models.

Selection rule

The winner is not the model with the biggest benchmark reputation.

It is the model that provides the best GroundTruth trade-off.

Status

OPEN QUESTION

10. LLM
Exact LLM — OPEN QUESTION

The architecture deliberately does not hard-code a final model yet.

Why?

The generation model must be evaluated for:

grounded answering
citation behavior
abstention
instruction/data separation
hallucination
latency
cost
structured output reliability.
Current experimental environment

Google AI Studio — AVAILABLE

This gives us an appropriate environment for controlled model/prompt experiments before application integration.

Important rule

AI Studio experimentation does not automatically mean the final production model must be Google's model.

The model earns selection through evaluation.

Status

LLM provider/model: OPEN QUESTION

11. AI Provider Abstraction
Provider adapter — APPROVED DECISION

The backend will conceptually expose:

EmbeddingProvider
GenerationProvider

rather than allowing vendor-specific APIs to spread through GroundTruth.

For example:

Application
    ↓
GenerationProvider
    ↓
Concrete Model Adapter
    ↓
External AI API
Why?

It allows controlled experiments without rewriting the application.

Status

APPROVED DECISION

12. Storage
Object/File Storage — OPEN QUESTION

GroundTruth needs to retain original uploaded documents.

The architectural requirement is:

Original file
     +
Derived searchable representation

The exact provider is not yet justified.

Alternatives
managed object storage
cloud object storage
database binary storage

Database blob storage is not preferred unless experiments demonstrate that the workload is tiny enough to justify it.

Selection criteria
reliability
security
cost
integration
file-size limits
lifecycle management.
Status

OPEN QUESTION

13. Authentication
Managed authentication — PROPOSAL

GroundTruth requires authentication and authorization, but the requirements do not justify building authentication infrastructure from scratch.

Why?

Authentication is security-critical and is not GroundTruth's product differentiator.

Building:

password hashing
sessions
email verification
password reset
token lifecycle

ourselves creates avoidable security risk.

Alternatives
managed authentication provider
self-managed authentication
custom authentication.
Recommendation

Use a managed authentication system that integrates cleanly with the selected deployment/database environment.

Status

PROPOSAL

The exact provider remains OPEN QUESTION.

14. Authorization
Application-level authorization — APPROVED DECISION

Regardless of authentication provider:

Authentication
      ↓
Identity
      ↓
Authorization
      ↓
Resource access

must remain under GroundTruth's application control.

The frontend cannot decide whether a user owns a collection.

Status

APPROVED DECISION

15. Testing
Backend — Pytest — APPROVED DECISION
Purpose

Test:

parsers
chunking
metadata
retrieval
services
APIs
security
failures.
Why

Python is the selected backend language.

Status

APPROVED DECISION

Frontend testing — OPEN QUESTION

The frontend requires component/workflow testing, but the exact framework/tool has not been proven necessary yet.

Likely candidates can be evaluated once the UI implementation begins.

Status

OPEN QUESTION

16. AI Evaluation System
Custom versioned evaluation subsystem — APPROVED DECISION

We do not make an external evaluation platform a mandatory dependency.

GroundTruth needs:

evals/
   datasets/
   runners/
   metrics/
   reports/
Why?

The evaluation dataset is part of GroundTruth's engineering identity.

We need complete control over:

dataset versions
questions
expected evidence
adversarial cases
metrics
regression comparisons.
External evaluation tooling

PROPOSAL / OPTIONAL

It can be introduced if it provides measurable value.

Status

APPROVED DECISION — evaluation architecture

17. CI/CD
GitHub Actions — APPROVED DECISION
Why needed

The project already treats GitHub as the:

Source of Truth

CI should therefore automatically verify changes.

Conceptually:

Pull Request
     ↓
GitHub Actions
     ↓
Tests
     ↓
Lint / validation
     ↓
Evaluation checks where appropriate
     ↓
PASS / FAIL
Alternatives

External CI platforms.

Why GitHub Actions?

It keeps source control and CI in the same ecosystem and avoids introducing another platform without need.

Status

APPROVED DECISION

18. Deployment
Managed deployment — APPROVED DECISION

The deployment model is approved:

Frontend
    ↓
Backend
    ↓
Database
    ↓
Object Storage
    ↓
AI Provider

But the exact provider remains:

OPEN QUESTION

Candidates

The requirements permit evaluating platforms such as:

Vercel
Render
Railway
Cloudflare
AWS
GCP
Azure
Supabase.
Selection criteria
Cost
Security
Python support
Database integration
Background processing
Deployment simplicity
Logs
Environment variables
Network behavior
Latency
Important

We will not select Vercel/AWS/etc. simply because they are common portfolio choices.

Status

Deployment architecture: APPROVED

Exact provider: OPEN QUESTION

19. Monitoring

Monitoring is required conceptually but should remain proportional.

We need to know:

Is the system healthy?
Are requests failing?
Is latency increasing?
Are AI calls failing?
Are costs increasing?
Dedicated monitoring platform

OPEN QUESTION

It should be selected only after deployment architecture is known.

20. Observability
Structured application observability — APPROVED DECISION

The application must record meaningful operational information.

At minimum:

request ID
request lifecycle
retrieval timing
generation timing
model information
usage where available
errors
Distributed tracing platform

PROPOSAL

Useful later if the pipeline becomes sufficiently complex.

It is not mandatory on day one.

Status

Core observability:

APPROVED DECISION

Specific platform:

OPEN QUESTION

21. Security Tooling

Security is a combination of architecture + implementation + testing.

Required areas:

Input validation
File validation
Authentication
Authorization
Secret management
Prompt-injection defenses
Access isolation
Rate limiting
Security testing
Dedicated security platform

NOT REQUIRED initially.

We do not need an elaborate security platform simply to claim "production security."

22. Documentation
Markdown + GitHub repository — APPROVED DECISION

Documentation belongs directly with the codebase.

Required documents include:

README.md
PRODUCT.md
REQUIREMENTS.md
ARCHITECTURE.md
EVALUATION.md
THREAT_MODEL.md

And, where useful:

DECISIONS/
    ADR-001-...
    ADR-002-...
Why?

GroundTruth is intended to demonstrate engineering judgment.

The repository must explain not only:

what we built

but:

why we built it this way.

Status

APPROVED DECISION

23. Design Tools
Stitch — AVAILABLE / PROPOSED FOR USE
Purpose

Explore the UI/UX direction after core product behavior is established.

The project workflow explicitly positions Stitch here:

Requirements
     ↓
Working product behavior
     ↓
Stitch
     ↓
Selected design
     ↓
Implementation
Important constraint

Stitch must not dictate backend architecture.

Status

AVAILABLE

GroundTruth role: PROPOSAL

24. Google AI Studio
AI Studio — AVAILABLE

This is now one of the most useful parts of the workflow.

Purpose

AI behavior laboratory.

Use it for:

Model comparison
Prompt experiments
Structured output
Citation experiments
Abstention experiments
Injection-defense experiments
Do not use it as

The production GroundTruth application runtime.

Status

AVAILABLE

APPROVED TOOL ROLE

25. Gemini GroundTruth Notebook
Gemini Notebook — AVAILABLE

A dedicated GroundTruth notebook already exists.

Purpose

Independent reasoning/research context.

Use it for:

RAG research
retrieval research
security research
evaluation methodology
source synthesis
architecture challenges
Important

It is not the repository source of truth.

Gemini Notebook
      ↓
Research / reasoning
      ↓
Decision
      ↓
GitHub
Status

AVAILABLE

APPROVED TOOL ROLE

26. Gemini

Gemini has a broader project reasoning role.

The established workflow is:

ChatGPT
    ↓
Architecture / strategy

Gemini
    ↓
Independent project reasoning / research

GitHub
    ↓
Source of truth
Status

AVAILABLE

APPROVED TOOL ROLE

27. Gemini CLI
Gemini CLI — ALREADY CONFIGURED

Current setup state:

installed
authenticated
launches successfully
setup completed.

Therefore this is not hypothetical.

Purpose

Local AI-assisted development/reasoning through the terminal.

It can be useful for:

repository inspection
targeted analysis
documentation assistance
local development support
bounded coding tasks.
Important distinction

Gemini CLI is optional local tooling.

It is not the foundation of the cloud automation architecture.

Status

ALREADY CONFIGURED

APPROVED OPTIONAL TOOL

28. Antigravity
Antigravity — AVAILABLE / PRIMARY IMPLEMENTATION TOOL
Purpose

Main AI-assisted development environment.

The intended workflow is:

Requirements
      ↓
Architecture
      ↓
Bounded implementation task
      ↓
Antigravity
      ↓
Code + tests
      ↓
Review
      ↓
GitHub
Why needed

GroundTruth is large enough that AI-assisted implementation can accelerate development, but the architecture requires bounded tasks rather than uncontrolled autonomous coding.

Constraints

Antigravity does not become the project's source of truth.

GitHub does.

AI-generated code must be reviewed and tested.

Status

AVAILABLE

APPROVED TOOL ROLE

29. Jules
Jules — AVAILABLE FOR GROUNDTRUTH

A GroundTruth Jules repository is already configured.

Purpose

Asynchronous bounded engineering work.

Good tasks:

Add tests
Fix isolated bug
Improve validation
Add integration test
Refactor a well-defined component

Bad task:

"Build GroundTruth."

Jules should operate against explicit boundaries.

Workflow
GitHub
   ↓
Jules
   ↓
Plan
   ↓
Bounded implementation
   ↓
Tests
   ↓
PR
   ↓
Human review
Status

AVAILABLE

APPROVED TOOL ROLE

30. GitHub
GitHub — APPROVED DECISION / SOURCE OF TRUTH

This is not optional.

GitHub contains the authoritative project state:

Code
Documentation
Architecture
Requirements
Tests
Evaluation
Issues
Pull Requests
History
Why

Multiple AI tools are being used.

Without one authoritative source:

AI Studio says X
Gemini says Y
Antigravity implements Z
Jules modifies W

becomes unmanageable.

GitHub resolves that.

Status

APPROVED DECISION

31. GitHub Branch / PR Discipline

The development model should remain:

main
 │
 ├── feature branch
 │
 ├── AI implementation
 │
 ├── tests
 │
 ├── PR
 │
 └── review
       ↓
    merge

main should remain protected once the repository workflow is established.

Status

APPROVED TOOLING PRACTICE

32. Opal
Opal — NOT REQUIRED

Opal may be useful for rapid AI workflow/prototype experimentation, but GroundTruth already has:

AI Studio
Gemini
Gemini Notebook
Antigravity

There is currently no requirement that Opal uniquely satisfies.

Introducing it would add another tool without a demonstrated gap.

Status

NOT REQUIRED

33. Flow
Google Flow — OPTIONAL / LATE-STAGE TOOL

Flow is not part of GroundTruth engineering.

Its useful role is:

Completed GroundTruth
       ↓
Portfolio/demo visual
       ↓
Flow
       ↓
Project trailer

It must not influence architecture or implementation.

Status

AVAILABLE TOOL CATEGORY / OPTIONAL

34. Canva
Canva — OPTIONAL

Canva is useful for:

final presentation
portfolio graphics
architecture visuals
project showcase assets.

It is not required for engineering.

Status

AVAILABLE / OPTIONAL

35. Google Drive
Google Drive — AVAILABLE / SUPPORTING TOOL

Purpose:

research material
project documents
supporting artifacts

It is not the source of truth for the codebase.

Status

AVAILABLE

OPTIONAL SUPPORT TOOL

36. Gmail
Gmail — NOT PART OF CORE ENGINEERING

Relevant later for:

recruiter communication
internship applications
professional communication.

It has no role in the GroundTruth runtime.

Status

NOT REQUIRED for GroundTruth engineering

37. Google Calendar
Calendar — OPTIONAL PROJECT MANAGEMENT TOOL

Useful for:

implementation milestones
evaluation checkpoints
deployment deadlines
interview preparation.

It does not belong in the product architecture.

Status

AVAILABLE / OPTIONAL

38. Tooling We Explicitly Reject for Now

These are intentionally excluded.

Tool/category	Status	Reason
Kubernetes	NOT REQUIRED	No demonstrated scale/operations requirement
Microservices	NOT REQUIRED	Modular application is sufficient
Kafka/message broker	NOT REQUIRED	No established asynchronous scale requirement
Redis	NOT REQUIRED	No measured caching requirement
Dedicated vector DB	NOT REQUIRED	PostgreSQL-based evaluation comes first
Dedicated search engine	NOT REQUIRED	No demonstrated need
LangChain	NOT REQUIRED	RAG pipeline can be implemented directly
LangGraph	NOT REQUIRED	GroundTruth does not require agent orchestration
Multi-agent framework	NOT REQUIRED	Not a product requirement
Custom authentication system	NOT REQUIRED	Security risk without product value
Multiple databases	NOT REQUIRED	Explicit anti-overengineering constraint
Local LLM infrastructure	NOT REQUIRED	Not required by current product target
Opal	NOT REQUIRED	No unique requirement
Heavy MLOps platform	NOT REQUIRED	Excessive for current scale

This is important for interviews.

Being able to explain what you deliberately did not build is a strong engineering signal.

39. Installation / Configuration Matrix
Tool	Current state	What must happen
Git	REQUIRES SETUP/VERIFY	Verify installation and identity
GitHub	ALREADY AVAILABLE	Create/configure repository workflow
Python	REQUIRES SETUP/VERIFY	Establish project Python environment
Node.js	REQUIRES SETUP/VERIFY	Required for frontend tooling
PostgreSQL tooling	REQUIRES SETUP/VERIFY	Local development/test environment
Gemini Notebook	ALREADY CONFIGURED	GroundTruth notebook exists
Gemini	AVAILABLE	Use for project reasoning
Gemini CLI	ALREADY CONFIGURED	Installed + authenticated
AI Studio	AVAILABLE	Use for model experiments
Antigravity	AVAILABLE	Main implementation environment
Jules	ALREADY CONFIGURED	GroundTruth repository configured
Stitch	AVAILABLE	Use when UI exploration begins
Flow	AVAILABLE/OPTIONAL	Use only near portfolio stage
Canva	AVAILABLE	Optional presentation assets
Authentication provider	REQUIRES SETUP	Select provider first
AI provider credentials	REQUIRES SETUP	After model experiment/selection
Object storage	REQUIRES SETUP	Select provider
Production database	REQUIRES SETUP	Select deployment environment
Production hosting	REQUIRES SETUP	Select after infrastructure comparison
Monitoring provider	REQUIRES SETUP	Select appropriate lightweight solution
40. Required Accounts / Services

The minimum external ecosystem is:

                    GROUNDTRUTH
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
      GitHub          AI Provider      Hosting
        │                │                │
        ▼                ▼                ▼
      Source         LLM/Embed          Runtime
       Truth                              │
                                         ▼
                                      Database
                                         │
                                         ▼
                                    File Storage
Already available/configured
GitHub
GroundTruth Gemini Notebook
Gemini
Gemini CLI
Google AI Studio
Antigravity
GroundTruth Jules repository
Still requiring setup/selection
production AI provider/model
embedding model/provider
authentication provider
object storage
production PostgreSQL
frontend hosting
backend hosting
observability/monitoring implementation.
41. Cost Architecture

The cost model should be:

Fixed/minimal infrastructure
          +
AI usage
          +
Storage
          +
Bandwidth

The largest variable cost is expected to be AI usage.

Therefore evaluation must measure:

cost/query

alongside:

quality/query

The cheapest model is not automatically the correct model.

Likewise, the most powerful model is not automatically the correct model.

We want:

best trustworthy-answer quality per practical cost.

42. Security Configuration Principles

Regardless of provider, the tooling stack must enforce:

Secrets
  ↓
Server/runtime environment

NOT

Secrets
  ↓
Frontend source code

AI API keys must never be embedded into the browser application.

Uploaded documents must be treated as untrusted.

Authentication credentials must not be committed to GitHub.

Production and development credentials must remain separable.

43. Tool Responsibility Map

This is the important operational separation.

                         YOU
                          │
                          ▼
                       CHATGPT
                 Architecture / Strategy
                          │
          ┌───────────────┼────────────────┐
          ▼               ▼                ▼
       Gemini        Gemini Notebook    GitHub
   Independent       Research/source    SOURCE OF
    reasoning          synthesis         TRUTH
                          │                │
                          └──────┬─────────┘
                                 ▼
                           AI STUDIO
                       Model experiments
                                 │
                                 ▼
                           ANTIGRAVITY
                       Main implementation
                                 │
                                 ▼
                              JULES
                     Bounded async work
                                 │
                                 ▼
                           TEST / EVAL
                                 │
                   ┌─────────────┴─────────────┐
                   ▼                           ▼
                SECURITY                 OBSERVABILITY
                   │                           │
                   └─────────────┬─────────────┘
                                 ▼
                             DEPLOYMENT
                                 │
                                 ▼
                         PUBLIC GROUNDTRUTH
                                 │
                         ┌───────┴───────┐
                         ▼               ▼
                      STITCH            FLOW
                    UI/design        portfolio/demo
44. Definitive Toolchain Map
Engineering Core
GitHub
  │
  ├── Requirements
  ├── Architecture
  ├── Source
  ├── Tests
  ├── Evaluation
  └── Documentation
        │
        ▼
   GitHub Actions
        │
        ▼
     Verification

Status: APPROVED

Application
React + TypeScript
        │
       HTTPS
        │
        ▼
Python + FastAPI
        │
        ├──────────────┐
        ▼              ▼
   PostgreSQL       Object Storage
        │
        ▼
 Evidence / Metadata

Status: APPROVED architectural technology baseline

AI
                    AI Layer
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
       Embedding API          LLM API
             │                   │
             ▼                   ▼
       Semantic Search      Grounded Answer
             │                   │
             └─────────┬─────────┘
                       ▼
                Trust Validation

Provider/model: OPEN QUESTION

Retrieval
                 QUERY
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
  Semantic Search        Lexical Search
        │                     │
        └──────────┬──────────┘
                   ▼
                 Fusion*
                   │
                 Rank*
                   │
                   ▼
             Evidence Set

* conditional on evaluation.

Semantic + lexical evaluation: APPROVED

Hybrid: PROPOSAL

Reranking: DEFERRED

Dedicated vector database: NOT REQUIRED

Trust
Retrieved Evidence
        │
        ▼
Context Builder
        │
        ▼
       LLM
        │
        ▼
Grounding Validation
        │
        ├───────────────┐
        ▼               ▼
     Answer          Abstain
        │
        ▼
    Citation
        │
        ▼
   Source Lineage

Status: APPROVED

Development AI
Gemini Notebook → Research
Gemini           → Independent reasoning
AI Studio        → AI experiments
Antigravity      → Main implementation
Jules            → Bounded async implementation
Gemini CLI       → Local optional assistance

Status: APPROVED WORKFLOW

Design / Presentation
Stitch
  ↓
UI exploration
  ↓
Antigravity
  ↓
Actual product UI

Flow
  ↓
Final product trailer

Canva
  ↓
Presentation / portfolio assets

Status: OPTIONAL / LATE-STAGE

45. Final Classification Matrix
Category	Final status
Python	APPROVED DECISION
FastAPI	APPROVED DECISION
React	APPROVED DECISION
TypeScript	APPROVED DECISION
PostgreSQL	APPROVED DECISION
PostgreSQL lexical search	APPROVED DECISION
PostgreSQL semantic/vector capability	APPROVED INITIAL APPROACH
Dedicated vector DB	NOT REQUIRED
Dedicated search engine	NOT REQUIRED
Embedding model	OPEN QUESTION
LLM	OPEN QUESTION
AI provider	OPEN QUESTION
Object storage provider	OPEN QUESTION
Authentication provider	OPEN QUESTION
Authorization architecture	APPROVED DECISION
Pytest	APPROVED DECISION
Frontend test framework	OPEN QUESTION
Custom evaluation subsystem	APPROVED DECISION
GitHub Actions	APPROVED DECISION
Hosting model	APPROVED DECISION
Hosting provider	OPEN QUESTION
Observability architecture	APPROVED DECISION
Observability vendor	OPEN QUESTION
Gemini Notebook	AVAILABLE / APPROVED ROLE
Gemini	AVAILABLE / APPROVED ROLE
Gemini CLI	ALREADY CONFIGURED
Google AI Studio	AVAILABLE / APPROVED ROLE
Antigravity	AVAILABLE / APPROVED ROLE
Jules	AVAILABLE / APPROVED ROLE
GitHub	APPROVED DECISION / SOURCE OF TRUTH
Stitch	AVAILABLE / PROPOSED ROLE
Flow	OPTIONAL
Canva	OPTIONAL
Drive	AVAILABLE / SUPPORTING
Gmail	NOT REQUIRED for engineering
Calendar	OPTIONAL
Opal	NOT REQUIRED
LangChain	NOT REQUIRED
LangGraph	NOT REQUIRED
Kubernetes	NOT REQUIRED
Redis	NOT REQUIRED
Kafka	NOT REQUIRED
Microservices	NOT REQUIRED
Multi-agent framework	NOT REQUIRED
FINAL TOOLCHAIN

So, Brdr, this is the stack I would now freeze as the implementation baseline:

                         GROUNTRUTH
                              │
                              ▼
                   ┌────────────────────┐
                   │      GITHUB        │
                   │  SOURCE OF TRUTH   │
                   └─────────┬──────────┘
                             │
                 ┌───────────┴───────────┐
                 ▼                       ▼
            ANTIGRAVITY                 JULES
          Main implementation       Bounded async work
                 │                       │
                 └───────────┬───────────┘
                             ▼
                         TEST / EVAL
                             │
                             ▼
       ┌──────────────────────────────────────────┐
       │              APPLICATION                 │
       │                                          │
       │ React + TypeScript                       │
       │          │                               │
       │       HTTPS                             │
       │          ▼                               │
       │ Python + FastAPI                         │
       │          │                               │
       │    ┌─────┴────────┐                      │
       │    ▼              ▼                      │
       │ PostgreSQL    Object Storage             │
       │    │                                     │
       │    ▼                                     │
       │ Retrieval → Evidence → LLM              │
       │                  │                       │
       │                  ▼                       │
       │          Grounding / Citation            │
       │                  │                       │
       │             Answer / Abstain             │
       └──────────────────────────────────────────┘
                             │
                    ┌────────┴────────┐
                    ▼                 ▼
               OBSERVABILITY       SECURITY
                    │                 │
                    └────────┬────────┘
                             ▼
                         DEPLOYMENT
                             │
                             ▼
                    PUBLIC PRODUCT

And around that core:

ChatGPT
  → architecture / engineering decisions

Gemini Notebook
  → research / evidence

Gemini
  → independent reasoning

AI Studio
  → model experiments

Antigravity
  → primary implementation

Jules
  → bounded asynchronous engineering

Gemini CLI
  → optional local assistance

GitHub
  → absolute source of truth

Stitch
  → UI exploration

Flow
  → final demo visual

Canva
  → portfolio/presentation
The important unresolved technology decisions are now deliberately reduced to a small set:

1. Exact embedding model

2. Exact generation model

3. AI provider

4. Authentication provider

5. Object-storage provider

6. Production hosting provider

7. Frontend test framework

8. Observability implementation/provider

Those are the only major technology questions I would carry forward.

Everything else has either been approved, deliberately deferred, or explicitly rejected as unnecessary.

That gives us a very clean next phase:

TECHNOLOGY BASELINE
        ↓
AI / RETRIEVAL EXPERIMENTS
        ↓
Finalize model choices
        ↓
Finalize deployment services
        ↓
LOCAL PROJECT BOOTSTRAP
        ↓
FIRST VERTICAL SLICE

And importantly, we do not need to start coding GroundTruth yet merely because the stack is now defined. The next engineering artifact should be the bounded implementation/bootstrap specification that turns this technology baseline into an actual reproducible development environment.