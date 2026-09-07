PROJECT CONSTITUTION — DRAFT

Project: GroundTruth
Document status: Draft / forensic reconstruction
Purpose: Establish an evidence-based baseline before requirements and architecture are finalized.

Important: This is a reconstruction, not a redesign. I am deliberately separating what is actually established from what was merely proposed. Where the project history contains a conflict, I preserve it rather than silently resolving it.

1. Project Identity
FACT

GroundTruth is the name of the project.

It is intended to become a production-grade, trustworthy RAG answer engine rather than a conventional chatbot. The project description explicitly rejects the idea of GroundTruth becoming "another PDF chatbot."

FACT

The central product concept is:

A trustworthy RAG answer engine that can determine whether answers are supported by retrieved evidence, cite that evidence, and abstain when evidence is insufficient.

FACT

GroundTruth is one of the user's primary serious AI portfolio projects.

2. Problem Being Solved
FACT

The project identifies a problem with large document collections: useful information is difficult for humans to search, understand, locate precisely, compare, and verify.

GroundTruth is intended to let users ask natural-language questions and receive:

concise answers
supporting evidence
source citations
appropriate confidence/grounding information
an honest insufficient-evidence response when necessary.

The underlying requirement is explicitly about trust in AI-generated answers, not merely question answering.

UNKNOWN

The precise initial business/domain problem has not yet been selected. We do not yet have an officially designated industry, organization, or corpus.

3. Target Users
FACT

The project is intended for real users and should behave like a real SaaS product rather than a college demonstration.

FACT

The established workflow implies users who possess or need to query controlled collections of documents.

PROPOSAL

Earlier discussion suggested:

students / knowledge workers
research-oriented users
technical users who care about evidence

These were reasonable user hypotheses, but they were not formally approved user personas.

UNKNOWN

We do not yet have:

formally approved personas
user interviews
validated user pain points
user volume assumptions
organizational buyer/user distinctions.
4. Intended User Experience
FACT

The intended experience includes:

Create/access knowledge collection
        ↓
Upload/import documents
        ↓
Process/index documents
        ↓
Ask natural-language question
        ↓
Retrieve evidence
        ↓
Generate grounded answer
        ↓
Inspect citations
        ↓
Open supporting context
        ↓
Provide feedback

This workflow is explicitly established.

FACT

Citations should provide useful source information such as document, page, section, or chunk/context, and should not be fabricated.

FACT

The product should include professional UX qualities including loading states, error states, empty states, retry behavior, validation, responsive design, accessibility, clear citations, feedback, document status, and graceful failure.

UNKNOWN

The final UI, interaction design, navigation structure, and exact citation presentation have not been approved.

5. Core Product Vision
FACT

GroundTruth's core vision is a knowledge system that:

uses controlled knowledge sources
retrieves evidence
generates grounded answers
cites supporting evidence
recognizes insufficient evidence
evaluates retrieval and answer quality
defends against malicious content.

FACT

Trustworthiness is the defining product characteristic.

DECISION

The project should not be developed as a generic chatbot or simplistic PDF Q&A application. This exclusion is explicitly established.

6. Primary Objectives
FACT

The established objectives are to demonstrate:

document ingestion
document processing
chunking
embeddings
retrieval
hybrid retrieval where justified
reranking where justified
grounded generation
citations
abstention
prompt-injection defenses
evaluation
observability
security
testing
deployment
professional UX.

FACT

The project should be publicly deployed rather than remaining localhost-only.

FACT

The project must produce measurable quality rather than relying on subjective claims that "it works." The Golden Dataset is intended to be central to this.

7. Secondary Objectives
FACT

GroundTruth is also intended to demonstrate modern AI engineering and product thinking suitable for portfolio and interview use.

The final project should support explanation of:

RAG
embeddings
chunking
vector search
BM25
hybrid retrieval
reranking
hallucination
grounding
citations
prompt injection
database decisions
APIs
authentication
deployment
observability
evaluation.

FACT

The project should produce measurable metrics rather than invented metrics.

8. Explicit Non-Objectives
DECISION

GroundTruth must not become:

a generic ChatGPT clone
a basic PDF chatbot
a simple "upload PDF and ask questions" demo
a thin LLM API wrapper
a local-only prototype
a static frontend.

DECISION

The project should not blindly adopt:

LangChain/LangGraph or equivalent frameworks
unnecessary agents
unnecessary microservices
unnecessary databases
artificial production-scale claims
fabricated metrics
tutorial architecture.

DECISION

Technology should not be selected merely because it is popular. This principle was explicitly reinforced in the latest pre-implementation discussion.

FACT

Agents are not the product's defining requirement. GroundTruth is fundamentally a trustworthy RAG system.

9. Existing Implementation
FACT

No production implementation has begun.

The user explicitly stated that implementation has not begun, and the documented project workflow repeatedly says not to begin coding before requirements, trust definitions, evaluation, research, architecture, and experiments are established.

UNKNOWN

There is no verified evidence in the GroundTruth-specific material of:

a working backend
a working frontend
a functioning ingestion pipeline
a production database
deployed RAG
working authentication
a public GroundTruth application.

Therefore none of these should be described as implemented.

10. Existing Repository State
FACT

GitHub is intended to be the source of truth for GroundTruth.

FACT

The intended repository model is one canonical repository per serious project.

UNKNOWN

The actual current GroundTruth repository, repository URL, branch, commit history, local directory, and current working-tree contents are not established by the available GroundTruth-specific evidence.

We must inspect the actual repository before making repository-specific claims.

11. Existing Functionality
FACT

No verified production functionality is established.

PROPOSAL

The documented future slices describe functionality that is intended to be implemented:

document
→ parser
→ chunks
→ metadata

chunks
→ embeddings
→ retrieval

retrieval
→ reranking
→ evidence

evidence
→ LLM
→ answer
→ citation

weak evidence
→ abstention

malicious document
→ security testing

These are planned implementation stages, not existing functionality.

12. Existing Technologies
FACT

The project has established an AI-assisted development ecosystem, including:

ChatGPT
Gemini
Gemini Notebook / NotebookLM
Google AI Studio
Antigravity
Jules
GitHub
Stitch
Flow
Google Workspace.

Their intended roles are explicitly documented.

UNKNOWN

No final production programming language, backend framework, frontend framework, database, vector database, embedding model, LLM, cloud provider, or deployment platform has been formally approved.

This is important because an earlier discussion proposed technologies such as Next.js, FastAPI, PostgreSQL/pgvector and Supabase, but those were proposals, not approved decisions.

13. Existing Integrations
FACT

The intended development workflow integrates:

GitHub
 ↕
Antigravity
 ↕
Jules

with GitHub remaining the source of truth.

FACT

The broader Google environment includes:

Google Workspace
Google Search
YouTube
GitHub
Canva

as connected services in the documented workstation setup.

FACT

Custom MCP/Spark integration has not been configured in the documented Google environment.

FACT

AI Studio is intended as the AI experimentation environment, not the actual GroundTruth production application.

FACT

Antigravity is intended to be the main implementation environment and Jules the bounded asynchronous worker.

14. Existing Limitations
FACT

The project has not yet reached implementation, so there is currently no demonstrated production system.

FACT

There is not yet verified evidence for:

retrieval accuracy
answer accuracy
citation accuracy
abstention accuracy
latency
cost/query
security robustness
deployment reliability.
UNKNOWN

Actual performance characteristics are completely unknown until experiments are conducted.

15. Future Ideas
PROPOSAL

Potential future capabilities include:

richer document formats
structural document preservation
tables
scanned documents
stronger retrieval
reranking
improved citation lineage
stronger adversarial security testing
richer observability
evaluation regression detection
improved UX
document versioning
broader deployment capabilities.

These are directions, not committed features.

PROPOSAL

The B.Tech syllabus has been identified as a potentially useful realistic corpus because it contains headings, course codes, semester structures, tables, and academic metadata.

It has not been established as the final GroundTruth corpus.

16. Requirements
FACT / DECISION

The system is expected to support a real ingestion pipeline capable of:

accepting supported documents
extracting text
preserving useful metadata
identifying document boundaries
chunking
generating embeddings
storing chunks
indexing content
detecting failures
reporting ingestion status.

It must account for malformed, empty, duplicate, oversized, unsupported, and extraction-failure cases.

FACT / DECISION

Chunking must preserve useful lineage:

document → page → section → chunk

The retrieval research specifically reinforces this requirement.

FACT / DECISION

Retrieval must be evaluated rather than assumed to be effective.

FACT / DECISION

Grounded generation must:

use retrieved evidence
treat retrieved documents as data rather than instructions
avoid unsupported claims
acknowledge conflicts
abstain when evidence is inadequate.

FACT / DECISION

Citations are a core product requirement.

FACT / DECISION

Abstention / "I don't know" behavior is mandatory.

FACT / DECISION

Prompt-injection defenses are required.

FACT / DECISION

Evaluation must cover relevant dimensions including retrieval, answer quality, groundedness, citation correctness, hallucination/abstention behavior, latency and cost.

FACT / DECISION

Security must consider authentication, authorization, access control, malicious uploads, prompt injection, sensitive-information leakage, rate limiting, input validation, secrets, and data isolation where applicable.

FACT / DECISION

The final system must be publicly deployed.

17. Constraints
FACT

The user is a student and wants free/low-cost infrastructure.

FACT

The system should not be overengineered.

FACT

Technology choices must be requirement-driven.

FACT

The project should use AI heavily for development, but AI must not replace engineering understanding.

FACT

Generated code must be tested, verified, reviewed, and understood before being treated as trustworthy.

FACT

GitHub is intended to remain the source of truth.

FACT

Repository/project contexts must remain isolated; information from sibling projects must not silently become GroundTruth architecture or implementation.

18. Assumptions
ASSUMPTION / OPEN QUESTION

The system will probably initially operate on a relatively bounded document corpus rather than internet-scale data, but the actual scale has not been formally specified.

ASSUMPTION

The first implementation should be incremental and experimental rather than a complete application generated in one step.

ASSUMPTION

The system will need some form of persistent document/chunk/evaluation storage, but the actual storage technology is not decided.

UNKNOWN

Exact expected:

number of users
documents/user
document size
chunks
queries/day
concurrency
latency target
budget.

These must eventually be specified.

19. Decisions Already Explicitly Approved

The following are the strongest currently established decisions.

DECISION 1

GroundTruth is a trustworthy RAG answer engine, not a generic chatbot/PDF chatbot.

DECISION 2

Trust/evidence is central to the product.

DECISION 3

The system must support citations.

DECISION 4

The system must be able to abstain when evidence is insufficient.

DECISION 5

Retrieved documents must be treated as untrusted data, not privileged instructions.

DECISION 6

Evaluation must be built around a Golden Dataset.

DECISION 7

Security and prompt-injection resistance are first-class concerns.

DECISION 8

GitHub is the source of truth.

DECISION 9

AI-assisted development is intentional, but the human remains responsible for understanding and verification.

DECISION 10

Technology choices must follow requirements/research/experiments rather than precede them.

DECISION 11

Hybrid retrieval is worth investigating, but has not been approved as the final retrieval architecture.

DECISION 12

Reranking remains optional until experiments demonstrate sufficient value.

20. Proposals That Were Never Approved

This section is important because earlier conversations contained many concrete technical suggestions.

PROPOSAL — Next.js + TypeScript

Suggested previously, but not approved.

PROPOSAL — FastAPI + Python

Suggested previously, but not approved.

PROPOSAL — PostgreSQL + pgvector

Strongly suggested previously and supported by project research, but not formally locked. The research specifically says PostgreSQL/pgvector should be evaluated against alternatives.

PROPOSAL — Supabase

Previously proposed for PostgreSQL/storage/auth, but not approved.

PROPOSAL — Vercel

Previously proposed as a frontend deployment candidate, but not approved.

PROPOSAL — Render/Railway

Previously proposed as backend deployment candidates, but not approved.

PROPOSAL — Tailwind/shadcn

Previously proposed, but not approved.

PROPOSAL — Specific LLM

No specific final LLM has been approved.

PROPOSAL — Specific embedding model

No specific embedding model has been approved.

PROPOSAL — Specific reranker

No specific reranker has been approved.

PROPOSAL — RRF

RRF is the first fusion method worth testing, not a final decision.

PROPOSAL — Dedicated vector database

No dedicated vector database has been approved.

PROPOSAL — LangChain/LangGraph

Explicitly not to be adopted blindly.

21. Unknowns

The most important unknowns are:

Exact target user/persona.
Initial domain/corpus.
Supported file formats.
Maximum document size.
Expected corpus size.
Expected query volume.
Latency target.
Cost target.
Formal definition of "grounded."
Formal definition of sufficient evidence.
Citation correctness criteria.
Abstention criteria.
Golden Dataset contents.
Evaluation thresholds.
Exact retrieval architecture.
Whether reranking materially improves results.
Embedding model.
LLM.
Database/search implementation.
Authentication approach.
Storage architecture.
Deployment infrastructure.
Observability implementation.
Actual repository state.
Whether a working prototype exists outside the evidence currently available.
22. Risks
FACT

The project explicitly recognizes these risks:

Hallucination / unsupported answers

→ mitigated through grounding, evidence checks, citations and abstention.

Poor retrieval

→ mitigated through evaluation and retrieval experiments.

Prompt injection

→ mitigated by treating documents as untrusted data and testing adversarial documents.

Overengineering

→ mitigated by adding complexity only when justified.

AI-generated code that the developer doesn't understand

→ mitigated by bounded implementation, testing, inspection and review.

Cost

→ mitigated through cost tracking and low-cost infrastructure.

Scope explosion

→ mitigated by staged vertical slices.

False confidence from subjective demos

→ mitigated through the Golden Dataset and measurable evaluation.

23. Dependencies
FACT

GroundTruth depends conceptually on:

Product definition
      ↓
Trust definition
      ↓
Golden Dataset
      ↓
Research
      ↓
Architecture
      ↓
Experiments
      ↓
Technology decisions
      ↓
Implementation

This order is explicitly established in the project's methodology.

FACT

The development ecosystem depends on:

GitHub as source of truth
Gemini Notebook for research
AI Studio for AI experiments
Antigravity for primary implementation
Jules for bounded asynchronous tasks
testing/evaluation before accepting changes.
UNKNOWN

Actual third-party production dependencies have not yet been selected.

24. Success Criteria
FACT

The final definition of done requires much more than:

frontend renders + API responds + one PDF can be queried.

The established target includes:

real document ingestion
reliable retrieval
hybrid retrieval where justified
reranking where justified
grounded generation
useful citations
abstention
security defenses
evaluation dataset
measurable quality
observability
error handling
tests
public deployment
professional UI
GitHub documentation
portfolio presentation
interview-ready architectural understanding.
FACT

The ultimate qualitative success criterion is:

Would a real user trust this enough to use it?

UNKNOWN

No quantitative acceptance thresholds have yet been established.

For example, we do not yet have approved targets such as:

Recall@5 ≥ X%
Citation accuracy ≥ Y%
Abstention precision ≥ Z%
P95 latency ≤ N seconds
Cost/query ≤ $N

Those should not be invented.

Consolidated State
Facts extracted

GroundTruth is intended to be a trustworthy, production-grade RAG answer engine focused on evidence, citations, abstention, evaluation, security and observability. It is explicitly not intended to become a generic PDF chatbot.

The project has not yet established a verified production implementation. GitHub is intended to be its source of truth. The development methodology deliberately postpones serious implementation until product, trust, evaluation, research and architecture are understood.

The retrieval research has reached Phase 0.4.2: Chunking & Retrieval Research, with BM25/lexical and dense retrieval identified for benchmarking, hybrid retrieval as a leading candidate, RRF as the first fusion method to test, and reranking remaining optional.

Decisions extracted

The strongest decisions are:

Trustworthy RAG
      ↓
Evidence-first
      ↓
Citations
      ↓
Abstention
      ↓
Evaluation
      ↓
Security
      ↓
Observability
      ↓
Public deployment

along with:

GitHub as source of truth
AI-assisted development with human verification
Golden Dataset before serious retrieval optimization
no blind framework/technology adoption
hybrid retrieval and reranking must earn their place experimentally.
Unresolved questions

The biggest unresolved area is what exactly "trustworthy" will mean operationally.

We still need to define:

What counts as evidence?
        ↓
What counts as sufficient evidence?
        ↓
What counts as a supported claim?
        ↓
What makes a citation correct?
        ↓
When must the system abstain?
        ↓
How do we measure each?

We also need the initial corpus, user, scale, latency/cost requirements and evaluation thresholds.

Contradictions
1. Technology stack

Earlier discussion proposed a concrete stack such as Next.js/FastAPI/PostgreSQL/pgvector/Supabase/Vercel/Render.

The later methodology explicitly states that technology choices must not be made before requirements, research and experiments.

Resolution status: The concrete stack remains PROPOSAL, not DECISION.

2. Reranking

Some architectural diagrams show:

Hybrid retrieval
 ↓
Reranker

while the retrieval research explicitly states that reranking remains optional until the Golden Dataset demonstrates its value.

Resolution: Treat reranking as PROPOSAL / experiment candidate, not mandatory architecture.

3. Hybrid retrieval

The project description frequently uses "hybrid retrieval," while the retrieval research explicitly says hybrid retrieval is a leading candidate, not a locked decision.

Resolution: The requirement is to evaluate hybrid retrieval, not blindly guarantee it as the final implementation.

4. "Production-grade"

The project calls itself production-grade, while there is currently no implementation.

This is not necessarily a contradiction: it describes the target quality level, not current status.

Status: Target, not current capability.

Missing information requiring owner input

These are the questions I would put directly in front of you before we create the next permanent project document:

Product
Who is the first real user?
What specific document domain should GroundTruth initially serve?
What is the first realistic corpus?
What should the user be able to do in the first release?
Trust
What exactly qualifies as grounded?
What qualifies as sufficient evidence?
What exactly makes a citation correct?
When should GroundTruth abstain?
Evaluation
What will the first Golden Dataset contain?
How will we label expected evidence?
What quantitative thresholds constitute success?
Which metrics are mandatory versus exploratory?
System constraints
How many documents should the first version support?
What maximum document size is reasonable?
What approximate query volume should we design for?
What response latency is acceptable?
What monthly infrastructure/AI budget is acceptable?
Repository
What is the actual GroundTruth GitHub repository?
What is the actual local project directory?
Does any code currently exist outside the evidence reviewed here?
Constitution Status

GroundTruth is not ready for final architecture yet.

And that's actually a good thing.

We have enough information to establish the project's identity, philosophy, non-objectives, trust direction, evaluation-first methodology and major requirements.

We do not yet have enough information to honestly lock the architecture or technology stack.

The correct next stage is therefore:

PROJECT CONSTITUTION
        ↓
PRODUCT CONTRACT
        ↓
TRUST CONTRACT
        ↓
GOLDEN DATASET DEFINITION
        ↓
RESEARCH PROTOCOL
        ↓
ARCHITECTURE

Not:

PROJECT CONSTITUTION
        ↓
"Let's use Next.js + FastAPI + pgvector"

That distinction is now part of the GroundTruth foundation.