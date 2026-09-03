REQUIREMENTS AND CONSTRAINTS SPECIFICATION

Project: GroundTruth
Document: Requirements and Constraints Specification
Status: Draft — derived from verified Project Constitution
Architecture status: Not defined by this document
Technology status: Intentionally unselected

0. Requirement Classification

Every requirement in this document uses one of four status levels:

MANDATORY — GroundTruth cannot satisfy its defined product purpose without it.

IMPORTANT — Strongly expected for the intended serious product, but failure would not invalidate the fundamental product concept.

OPTIONAL — Explicitly permitted or desirable, but not required for the defined target.

DEFERRED — Relevant to the longer-term target, but intentionally not required in the initial implementation.

A requirement marked DEFERRED is not a current implementation commitment.

1. Functional Requirements
ID	Requirement	Reason	Priority	Source	Acceptance interpretation
FR-001	The system SHALL allow a user to create or access a knowledge collection.	GroundTruth operates over controlled knowledge collections.	MANDATORY	Constitution — Product / UX	A user can access a defined collection of knowledge sources.
FR-002	The system SHALL allow supported documents to be uploaded or imported into a knowledge collection.	Documents are the source of GroundTruth's evidence.	MANDATORY	Constitution — Document Ingestion	A supported document can enter the ingestion workflow.
FR-003	The system SHALL process uploaded documents before they become queryable.	Raw files cannot directly serve as reliable retrieval evidence.	MANDATORY	Constitution — Document Ingestion	A document has a defined processing lifecycle before retrieval.
FR-004	The system SHALL extract usable content from supported documents.	Retrieval requires machine-readable content.	MANDATORY	Constitution — Document Ingestion	Extracted content can be inspected and used downstream.
FR-005	The system SHALL divide processed document content into retrievable chunks.	Retrieval operates on appropriately sized evidence units.	MANDATORY	Constitution — Chunking	Processed content produces identifiable chunks.
FR-006	The system SHALL preserve useful document/chunk metadata and source lineage.	Evidence must remain traceable to its source.	MANDATORY	Constitution — Chunking / Citations	A retrieved chunk can be traced back to its source location.
FR-007	The system SHALL generate semantic representations for content when semantic retrieval is used.	Semantic retrieval requires representations suitable for similarity search.	MANDATORY	Constitution — Embeddings	Indexed content can participate in semantic retrieval.
FR-008	The system SHALL retrieve potentially relevant evidence for a user's natural-language question.	Retrieval is the foundation of grounded answering.	MANDATORY	Constitution — RAG Pipeline	A question produces an evidence candidate set.
FR-009	The system SHALL evaluate lexical and semantic retrieval approaches before finalizing the retrieval strategy.	The project explicitly requires evidence-driven retrieval selection.	MANDATORY	Retrieval Research	Both approaches are benchmarked against the evaluation corpus.
FR-010	The system SHOULD support hybrid retrieval if evaluation demonstrates meaningful benefit.	Hybrid retrieval is a leading candidate but not a locked decision.	IMPORTANT	Retrieval Research	Hybrid retrieval is retained only if experiments justify it.
FR-011	The system MAY rerank retrieved candidates if evaluation demonstrates sufficient improvement relative to its cost/latency.	Reranking is intentionally conditional.	DEFERRED	Retrieval Research	Reranking is benchmarked rather than assumed.
FR-012	The system SHALL generate answers using retrieved evidence as contextual input.	Grounded generation is the core product behavior.	MANDATORY	Constitution — Grounded Generation	Generated answers are produced from the selected evidence context.
FR-013	The system SHALL provide source citations for supported answers.	Users must be able to understand where an answer came from.	MANDATORY	Constitution — Citations	An answer's claims can be associated with available supporting source information.
FR-014	The system SHALL provide access to useful supporting source context where technically possible.	Citations must be useful for verification, not merely decorative.	MANDATORY	Constitution — Citations / UX	A user can inspect the relevant source passage/context.
FR-015	The system SHALL be capable of returning an insufficient-evidence/abstention response.	GroundTruth must not reward unsupported confidence.	MANDATORY	Constitution — "I Don't Know"	Insufficient evidence can cause the system to abstain instead of inventing an answer.
FR-016	The system SHALL accept user feedback on answers.	Feedback contributes to product improvement and evaluation.	IMPORTANT	Constitution — Core UX	A user can indicate whether an answer was useful/correct enough for the intended feedback mechanism.
FR-017	The system SHALL expose document processing status.	Users need to know whether documents are usable.	IMPORTANT	Constitution — Document Ingestion / UX	A document has an observable processing state.
2. Non-Functional Requirements
ID	Requirement	Reason	Priority	Source	Acceptance interpretation
NFR-001	The system SHALL prioritize trustworthy answers over confident unsupported answers.	Trust is the defining product objective.	MANDATORY	Project Vision	System behavior favors evidence-backed responses and abstention.
NFR-002	The system SHALL fail gracefully when required processing or AI operations fail.	Real systems encounter failures.	MANDATORY	Reliability / UX	Failure produces a controlled user-visible state rather than an unexplained crash.
NFR-003	The system SHALL provide clear validation and error feedback.	Users must understand invalid operations and failures.	IMPORTANT	UX Requirements	Invalid operations result in understandable feedback.
NFR-004	The system SHALL be testable at component and system levels appropriate to the implemented functionality.	Generated or complex AI systems cannot be trusted without verification.	MANDATORY	Testing Requirements	Critical functionality has repeatable automated/manual verification.
NFR-005	The system SHALL expose sufficient information to diagnose important request failures.	Operational debugging requires visibility into system behavior.	IMPORTANT	Observability Requirements	Important failures can be investigated from recorded diagnostic information.
NFR-006	The system SHOULD minimize unnecessary infrastructure and implementation complexity.	The project explicitly rejects overengineering.	MANDATORY	Development Philosophy	Every major complexity has a documented product/engineering justification.
3. User Requirements
ID	Requirement	Reason	Priority	Source	Acceptance interpretation
UR-001	A user SHALL be able to work with a controlled collection of knowledge sources.	GroundTruth is a controlled-knowledge system.	MANDATORY	Product Vision	User interaction is scoped to an identifiable knowledge collection.
UR-002	A user SHALL be able to ask questions using natural language.	Natural-language querying is the primary interaction model.	MANDATORY	Core UX	User can submit ordinary natural-language questions.
UR-003	A user SHALL receive a concise answer when sufficient evidence exists.	This is the primary value proposition.	MANDATORY	Core UX	Valid answerable questions produce an answer rather than raw search results only.
UR-004	A user SHALL be able to inspect evidence supporting an answer.	Trust requires verification.	MANDATORY	Citations	Supporting source context can be inspected.
UR-005	A user SHALL be informed when the system lacks sufficient evidence.	Preventing false confidence is mandatory.	MANDATORY	Abstention	Insufficient evidence produces an appropriate abstention response.
UR-006	A user SHOULD receive understandable status information while documents are being processed.	Ingestion may not be instantaneous.	IMPORTANT	UX	Processing state is understandable without requiring technical knowledge.
4. System Requirements
ID	Requirement	Reason	Priority	Source	Acceptance interpretation
SYS-001	The system SHALL maintain a defined ingestion-to-answer lifecycle.	GroundTruth is a pipeline rather than a single model call.	MANDATORY	Core Architecture Concept	Documents and questions pass through identifiable processing stages.
SYS-002	The system SHALL maintain source lineage from document content to retrievable evidence.	Citations depend on lineage.	MANDATORY	Trust / Chunking	Evidence retains sufficient provenance for citation.
SYS-003	The system SHALL separate retrieved document content from privileged system instructions.	Retrieved content is untrusted input.	MANDATORY	Security Requirements	Document text cannot automatically become system-level instructions.
SYS-004	The system SHALL support persistent storage of information required by its implemented workflows.	The target is a real product rather than an ephemeral prototype.	MANDATORY	Product Target	Required state survives beyond an individual request/session where applicable.
SYS-005	The system SHALL expose controlled interfaces between major system responsibilities.	Separation makes testing and maintenance possible.	IMPORTANT	Development Philosophy	Retrieval, ingestion, generation, evaluation and other responsibilities have identifiable boundaries.
5. Security Requirements
ID	Requirement	Reason	Priority	Source	Acceptance interpretation
SEC-001	The system SHALL authenticate users where authenticated functionality is provided.	User identity is required to protect user-owned information.	MANDATORY	Security Requirements	Protected functionality cannot be accessed anonymously where authentication is required.
SEC-002	The system SHALL authorize access to user-owned collections/documents.	Authentication alone does not prevent unauthorized access.	MANDATORY	Security Requirements	A user cannot access another user's protected data without authorization.
SEC-003	Retrieved documents SHALL be treated as untrusted data.	Documents may contain malicious instructions.	MANDATORY	Prompt Injection Defense	Retrieved content cannot override higher-priority system instructions.
SEC-004	The system SHALL defend against indirect prompt injection to a reasonable, testable degree.	Malicious documents are an explicitly identified threat.	MANDATORY	Security Requirements	Adversarial documents are tested and the model is prevented from treating their instructions as privileged.
SEC-005	The system SHALL validate uploaded files according to its supported-document policy.	Malicious or malformed files can threaten reliability/security.	MANDATORY	Document Ingestion / Security	Unsupported or invalid files are rejected or safely handled.
SEC-006	Secrets and API credentials SHALL not be exposed through source code or inappropriate client-side mechanisms.	Credential leakage can compromise the system.	MANDATORY	Security Requirements	Sensitive credentials remain protected in appropriate runtime configuration.
SEC-007	The system SHALL validate user inputs relevant to security-sensitive operations.	Unvalidated inputs create avoidable attack surfaces.	MANDATORY	Security Requirements	Invalid/malicious inputs are rejected or safely handled.
SEC-008	The system SHOULD apply rate limiting or equivalent abuse controls where required by the deployed workload.	Public AI systems can be abused and incur cost.	IMPORTANT	Security / Cost Requirements	The deployed system has an abuse-control mechanism appropriate to its actual exposure.
SEC-009	The system SHALL document known security limitations rather than claiming perfect prompt-injection or security protection.	Security claims must remain honest.	MANDATORY	Security Philosophy	Documentation explicitly states relevant limitations.
6. Reliability Requirements
ID	Requirement	Reason	Priority	Source	Acceptance interpretation
REL-001	Failed document ingestion SHALL produce a detectable failure state.	Silent ingestion failures create false knowledge-base completeness.	MANDATORY	Ingestion Requirements	Failed processing is distinguishable from successful processing.
REL-002	Empty or unusable documents SHALL not silently become valid knowledge sources.	Empty evidence cannot support reliable answers.	MANDATORY	Ingestion Requirements	Such documents are rejected, marked unusable, or otherwise clearly handled.
REL-003	Duplicate documents SHALL be detectable or safely handled according to the implemented ingestion policy.	Duplicates can distort retrieval and evaluation.	IMPORTANT	Ingestion Requirements	Duplicate behavior is deterministic and documented.
REL-004	Unsupported document formats SHALL be rejected or clearly identified.	Unsupported input must not create undefined behavior.	MANDATORY	Ingestion Requirements	Unsupported files result in a controlled outcome.
REL-005	Oversized documents SHALL be handled according to an explicit limit/policy.	Unbounded inputs threaten reliability and cost.	MANDATORY	Ingestion Requirements	Oversized input is rejected, constrained, or safely processed according to a defined policy.
REL-006	External AI/service failures SHALL not cause uncontrolled application failure.	AI dependencies can fail independently.	MANDATORY	Reliability Requirements	Dependency failures result in controlled error behavior.
REL-007	The system SHALL avoid returning fabricated citations when supporting evidence is unavailable.	False provenance directly violates GroundTruth's purpose.	MANDATORY	Citation Requirements	Every returned citation corresponds to actual indexed source material.
7. Performance Requirements

The Constitution requires performance to be measured, but it does not establish numerical thresholds. Therefore numerical targets must not be invented here.

ID	Requirement	Reason	Priority	Source	Acceptance interpretation
PERF-001	The system SHALL measure relevant request latency.	Performance must be observable rather than assumed.	MANDATORY	Evaluation / Observability	Request latency is recorded for evaluation.
PERF-002	Retrieval performance SHALL be measurable independently from generation performance.	Otherwise retrieval and model latency cannot be distinguished.	IMPORTANT	Observability / RAG Pipeline	Retrieval timing and generation timing can be analyzed separately.
PERF-003	AI model usage SHALL be measurable where the provider exposes relevant usage information.	Cost and performance depend on model usage.	IMPORTANT	Cost / Observability	Relevant token/usage information is captured when available.
PERF-004	Performance optimization SHALL not reduce answer trustworthiness without an explicit engineering trade-off.	Speed cannot silently replace correctness.	MANDATORY	Product Vision	Performance changes are evaluated against quality metrics.
PERF-005	Quantitative latency targets SHALL be established before performance acceptance testing.	No target currently exists in the Constitution.	DEFERRED	Open Questions	A later approved target is used for formal performance acceptance.
8. Scalability Requirements

The project does not claim enterprise-scale capacity.

ID	Requirement	Reason	Priority	Source	Acceptance interpretation
SCALE-001	The system SHALL support growth beyond a single demonstration document without redesigning its fundamental product model.	GroundTruth is intended as a usable knowledge system.	IMPORTANT	Product Vision	Multiple documents and collections can be handled coherently.
SCALE-002	The architecture SHALL avoid unnecessary scale-oriented infrastructure before actual workload requirements justify it.	Student resource constraints and anti-overengineering principle.	MANDATORY	Constraints	No distributed infrastructure is introduced without a demonstrated requirement.
SCALE-003	Expected workload limits SHALL be defined before claiming scalability characteristics.	Current scale assumptions are incomplete.	DEFERRED	Unknowns	Capacity claims are made only after workload targets exist.
SCALE-004	The system SHALL not claim production-scale capacity that has not been measured.	Prevents misleading portfolio/interview claims.	MANDATORY	Development Philosophy	Public documentation distinguishes demonstrated capacity from future scalability.
9. Observability Requirements
ID	Requirement	Reason	Priority	Source	Acceptance interpretation
OBS-001	The system SHALL provide sufficient request-level information to understand important request behavior.	AI pipelines are difficult to debug without visibility.	MANDATORY	Observability	Important request stages can be investigated.
OBS-002	Retrieval behavior SHALL be observable for evaluation/debugging purposes.	Poor answers may originate in retrieval rather than generation.	MANDATORY	Observability / Evaluation	Retrieved candidates/results can be inspected in controlled diagnostics.
OBS-003	Model information SHALL be recorded where relevant to reproducing/evaluating an answer.	Model changes can affect quality.	IMPORTANT	Observability	Evaluation records identify relevant model configuration.
OBS-004	Important errors SHALL be observable.	Silent errors undermine reliability.	MANDATORY	Reliability / Observability	Failed operations produce diagnosable records.
OBS-005	Latency SHALL be observable at relevant pipeline stages.	Bottlenecks must be measurable.	IMPORTANT	Observability	Major stages expose timing information.
OBS-006	Token/usage and cost information SHALL be captured where technically available and relevant.	Student cost control is an explicit requirement.	IMPORTANT	Cost / Observability	Usage can be analyzed after representative runs.
OBS-007	Full tracing infrastructure SHALL only be introduced if its value is demonstrated.	Avoids observability for buzzword purposes.	DEFERRED	Development Philosophy	Advanced tracing is adopted only when justified.
10. Maintainability Requirements
ID	Requirement	Reason	Priority	Source	Acceptance interpretation
MAINT-001	The system SHALL have clearly separated responsibilities for ingestion, retrieval, generation, security and evaluation.	Separation supports understanding and modification.	MANDATORY	Development Philosophy	Components have identifiable responsibilities.
MAINT-002	Important engineering decisions SHALL be documented with their rationale and trade-offs.	The project is intended to demonstrate engineering judgment.	MANDATORY	Development Philosophy	Significant decisions have documented reasoning.
MAINT-003	The repository SHALL contain setup and development documentation.	Others must be able to reproduce the project.	MANDATORY	GitHub Standard	A new developer can follow documented setup instructions.
MAINT-004	The repository SHALL document known limitations.	Honest engineering requires explicit boundaries.	MANDATORY	GitHub Standard	Important limitations are visible to users/developers.
MAINT-005	The project SHALL avoid unnecessary framework coupling.	Prevents implementation choices from becoming accidental architecture.	IMPORTANT	Development Philosophy	Frameworks are introduced only where they solve a demonstrated problem.
MAINT-006	AI-generated changes SHALL be reviewed and verified before being considered accepted implementation.	AI assistance does not establish correctness.	MANDATORY	Development Workflow	Generated changes are tested/reviewed before acceptance.
11. Testing Requirements
ID	Requirement	Reason	Priority	Source	Acceptance interpretation
TEST-001	The system SHALL include tests for document ingestion.	Ingestion errors directly affect evidence quality.	MANDATORY	Testing Requirements	Representative ingestion cases have automated or repeatable tests.
TEST-002	The system SHALL include tests for chunking behavior.	Chunking directly affects retrieval and citations.	MANDATORY	Testing Requirements	Chunking behavior and metadata preservation are tested.
TEST-003	The retrieval pipeline SHALL be testable against representative questions.	Retrieval quality is central to GroundTruth.	MANDATORY	Evaluation Requirements	Retrieval results can be evaluated against expected evidence.
TEST-004	API behavior SHALL be tested.	Backend failures can break the entire product.	MANDATORY	Testing Requirements	Critical API workflows have tests.
TEST-005	Authentication/authorization behavior SHALL be tested where implemented.	Security controls must be verified, not merely configured.	MANDATORY	Security / Testing	Unauthorized access scenarios are tested.
TEST-006	Critical frontend workflows SHALL be tested.	The target is a real usable product.	IMPORTANT	Testing Requirements	Core user workflows receive appropriate verification.
TEST-007	Error-handling paths SHALL be tested.	Failure behavior is part of product quality.	MANDATORY	Reliability / Testing	Important failure cases produce expected outcomes.
TEST-008	AI evaluation SHALL remain conceptually separate from ordinary software unit testing.	Correct code does not guarantee good AI behavior.	MANDATORY	Evaluation Methodology	Software correctness tests and AI-quality evaluations are distinct.
TEST-009	Security/adversarial tests SHALL include malicious document content and prompt-injection attempts.	Indirect prompt injection is an explicit threat.	MANDATORY	Security Requirements	Representative attacks are included in testing.
12. Deployment Requirements
ID	Requirement	Reason	Priority	Source	Acceptance interpretation
DEP-001	The final GroundTruth product SHALL be publicly deployed.	Localhost-only delivery is explicitly insufficient.	MANDATORY	Deployment Requirement	A real external user can access the deployed product.
DEP-002	The deployed product SHALL include a usable frontend.	GroundTruth is intended as a user-facing product.	MANDATORY	Product Vision	Users can interact with the system through a deployed interface.
DEP-003	Required backend/API functionality SHALL be deployed and accessible to the frontend.	The product requires functioning server-side behavior.	MANDATORY	Deployment Requirement	Production frontend requests reach functioning backend services.
DEP-004	Required persistent data services SHALL be deployed rather than relying on local-only state.	The product must persist knowledge/application state.	MANDATORY	Deployment Requirement	Required data survives deployment/runtime restarts as appropriate.
DEP-005	Production secrets SHALL be securely configured.	Deployment must not expose credentials.	MANDATORY	Security	Secrets are provided through appropriate deployment configuration.
DEP-006	Production configuration SHALL be documented.	Reproducibility and maintenance.	MANDATORY	GitHub Standard	Deployment setup is documented.
DEP-007	Deployment SHALL include appropriate logging/monitoring for the implemented system.	Public deployment requires operational visibility.	IMPORTANT	Observability	Important production failures can be detected/investigated.
DEP-008	Deployment provider selection SHALL be deferred until workload, cost, storage, database and security requirements are known.	No cloud provider has been approved.	DEFERRED	Constitution / Decision Process	Provider is selected only after requirements analysis.
13. Data Requirements
ID	Requirement	Reason	Priority	Source	Acceptance interpretation
DATA-001	The system SHALL maintain document identity.	Source attribution requires knowing which document produced evidence.	MANDATORY	Ingestion / Citations	Every indexed document has identifiable identity.
DATA-002	The system SHALL maintain chunk identity.	Retrieval and citation require identifiable evidence units.	MANDATORY	Chunking	Every retrievable chunk can be uniquely identified.
DATA-003	Chunk data SHALL preserve useful source metadata.	Enables evidence traceability.	MANDATORY	Chunking	Source/page/section information is retained where available.
DATA-004	The system SHALL maintain document processing status.	Users and operations need to distinguish ready/failed/in-progress content.	MANDATORY	Ingestion	Processing state is persisted or otherwise reliably available.
DATA-005	Stored embeddings SHALL remain associated with the content they represent.	Semantic retrieval requires correct correspondence.	MANDATORY	Embeddings	A vector can be mapped back to its originating chunk.
DATA-006	Feedback data SHALL be associated with the relevant product interaction where required for evaluation/improvement.	Feedback without context has limited value.	IMPORTANT	Feedback / Evaluation	Feedback can be analyzed in relation to the corresponding answer.
DATA-007	Evaluation data SHALL be maintained separately enough to support reproducible evaluation.	Prevents evaluation from becoming indistinguishable from application data.	MANDATORY	Evaluation Methodology	Evaluation datasets can be versioned/reused independently.
DATA-008	User/collection/document data SHALL be isolated according to the system's authorization model.	Prevents cross-user leakage.	MANDATORY	Security	Unauthorized users cannot retrieve protected data.
14. UX Requirements
ID	Requirement	Reason	Priority	Source	Acceptance interpretation
UX-001	The interface SHALL clearly communicate the distinction between generated answers and supporting evidence.	Trust is central to the product.	MANDATORY	Product Vision / Citations	Users can visually distinguish answer content from evidence.
UX-002	The interface SHALL provide clear citation presentation.	Citations are a core feature, not metadata hidden from users.	MANDATORY	Citations	Users can identify and inspect sources.
UX-003	The interface SHALL provide loading states for operations that are not instantaneous.	Prevents uncertainty during processing.	IMPORTANT	UX Requirements	Users receive feedback during waits.
UX-004	The interface SHALL provide meaningful error states.	Failures are expected.	MANDATORY	UX Requirements	Users receive actionable/understandable failure feedback.
UX-005	The interface SHALL provide appropriate empty states.	Empty collections/documents are normal states.	IMPORTANT	UX Requirements	Empty product states explain what the user can do next.
UX-006	The interface SHALL provide retry behavior where retry is technically meaningful.	Recoverable failures should not require unnecessary manual recovery.	IMPORTANT	UX Requirements	Recoverable operations provide an appropriate retry path.
UX-007	The interface SHALL validate user input where appropriate.	Prevents avoidable failures.	MANDATORY	UX / Security	Invalid input is identified before unsafe/invalid processing where possible.
UX-008	The interface SHALL be responsive enough for intended supported devices.	The product is intended for real users.	IMPORTANT	UX Requirements	Core functionality remains usable across supported screen sizes.
UX-009	The interface SHOULD follow accessible interaction practices.	Professional product quality requires usable controls.	IMPORTANT	UX Requirements	Core controls are reasonably accessible and understandable.
UX-010	The system SHALL communicate abstention clearly rather than presenting it as a normal answer.	Users must understand why no answer was given.	MANDATORY	Abstention	An abstention is visibly distinguishable from a generated answer.
15. AI-Specific Requirements
ID	Requirement	Reason	Priority	Source	Acceptance interpretation
AI-001	The system SHALL distinguish retrieval from generation.	RAG consists of retrieval + augmentation + generation rather than a single model call.	MANDATORY	RAG Definition	Retrieval evidence can be identified independently from generated output.
AI-002	The system SHALL provide retrieved evidence to the generation process when producing grounded knowledge-base answers.	Prevents reliance solely on model memory.	MANDATORY	RAG Pipeline	Generation receives controlled evidence context.
AI-003	The generation process SHALL instruct the model to treat retrieved documents as data rather than privileged instructions.	Required for prompt-injection resistance.	MANDATORY	Security	Document instructions cannot override system-level behavior.
AI-004	The generation process SHALL avoid unsupported claims where evidence is insufficient.	Hallucination reduction is a core objective.	MANDATORY	Grounded Generation	Unsupported claims result in qualified response or abstention.
AI-005	The system SHALL acknowledge conflicting evidence rather than silently selecting an unsupported conclusion.	Source collections may contain contradictions.	MANDATORY	Grounded Generation	Conflicting evidence is represented appropriately in answers.
AI-006	Citation output SHALL correspond to actual retrieved/indexed evidence.	Fabricated citations defeat the product's purpose.	MANDATORY	Citations	Citation targets can be verified against source data.
AI-007	AI model choices SHALL be evaluated against GroundTruth requirements rather than selected solely by popularity.	Model behavior directly affects quality/cost.	MANDATORY	Decision Methodology	Model selection is supported by relevant experiments/evidence.
AI-008	Embedding choices SHALL be evaluated for retrieval quality, representation characteristics, latency and cost before being finalized.	Embeddings directly affect retrieval.	MANDATORY	Embedding Requirements	Candidate embedding approaches are compared using the evaluation protocol.
AI-009	Advanced retrieval techniques SHALL not be adopted solely because they are considered modern or sophisticated.	Prevents architecture-by-buzzword.	MANDATORY	Development Philosophy	Each added retrieval technique has measurable justification.
16. Evaluation Requirements

This is one of the most important sections of the entire specification.

ID	Requirement	Reason	Priority	Source	Acceptance interpretation
EVAL-001	GroundTruth SHALL have a representative evaluation dataset.	AI quality must be measurable.	MANDATORY	Evaluation Methodology	A reusable evaluation corpus exists.
EVAL-002	The evaluation dataset SHALL include answerable questions.	Measures normal successful behavior.	MANDATORY	Golden Dataset	Expected evidence/answer behavior exists for answerable cases.
EVAL-003	The evaluation dataset SHALL include difficult questions.	Tests robustness beyond trivial retrieval.	MANDATORY	Golden Dataset	Difficult/multi-evidence cases are represented.
EVAL-004	The evaluation dataset SHALL include unanswerable questions.	Tests abstention.	MANDATORY	Golden Dataset	Questions without sufficient corpus evidence are represented.
EVAL-005	The evaluation dataset SHALL include adversarial cases.	Tests system weaknesses deliberately.	MANDATORY	Golden Dataset	Adversarial examples are evaluated.
EVAL-006	The evaluation dataset SHALL include prompt-injection document cases.	Tests indirect prompt injection.	MANDATORY	Security / Golden Dataset	Malicious document instructions are included in evaluation.
EVAL-007	Retrieval quality SHALL be measured independently of final answer quality.	A bad answer may originate from retrieval failure.	MANDATORY	Retrieval Research	Retrieval metrics are calculated separately.
EVAL-008	Retrieval evaluation SHALL consider recall at relevant K values.	Retrieval must be measured quantitatively.	MANDATORY	Retrieval Research	Recall@K is measured using defined evaluation rules.
EVAL-009	Ranking quality SHALL be measurable.	Candidate ordering affects final evidence.	IMPORTANT	Retrieval Research	An agreed ranking metric such as MRR is evaluated where applicable.
EVAL-010	Evidence-set completeness SHALL be evaluated for questions requiring multiple pieces of evidence.	Single-hit retrieval is insufficient for multi-hop questions.	IMPORTANT	Retrieval Research	Evaluation determines whether required evidence elements were retrieved.
EVAL-011	Answer correctness SHALL be evaluated.	Retrieval alone does not prove answer quality.	MANDATORY	Evaluation Requirements	Answers are compared against evaluation expectations.
EVAL-012	Groundedness/faithfulness SHALL be evaluated.	An answer can be factually plausible while unsupported by retrieved evidence.	MANDATORY	Trust Requirements	Evaluation measures whether claims are supported by evidence.
EVAL-013	Citation correctness SHALL be evaluated.	A citation must actually support the associated answer.	MANDATORY	Citation Requirements	Citation-source relationships are tested.
EVAL-014	Abstention quality SHALL be evaluated.	Refusing everything is not trustworthy either.	MANDATORY	Abstention Requirements	Correct abstentions and incorrect abstentions are measurable.
EVAL-015	Hallucination/unsupported-answer behavior SHALL be evaluated.	Preventing confident fabrication is a core objective.	MANDATORY	Trust Requirements	Unsupported answers are explicitly measured.
EVAL-016	Latency SHALL be included in evaluation where relevant.	Quality cannot be considered without practical performance.	IMPORTANT	Performance	Evaluation reports timing.
EVAL-017	Cost/usage SHALL be measured where feasible.	Student resources are constrained.	IMPORTANT	Cost Control	Representative AI usage can be estimated/measured.
EVAL-018	Retrieval experiments SHALL change controlled variables and compare results using the same evaluation rules.	Prevents misleading comparisons.	MANDATORY	Retrieval Research	Experiments use a consistent corpus/evaluation protocol.
EVAL-019	The evaluation test set SHALL not be silently used for unlimited tuning.	Prevents overfitting to the benchmark.	MANDATORY	Evaluation Methodology	Dataset partitioning/usage rules are documented.
EVAL-020	No performance or quality metric SHALL be claimed publicly unless it has actually been measured.	Prevents fabricated portfolio claims.	MANDATORY	Project Philosophy	Published metrics can be traced to evaluation results.

The current research specifically proposes establishing the retrieval experiment protocol—including retrieval hits, multi-hop scoring, Recall@K, MRR, evidence completeness, context-noise ratio, latency, chunk-size comparisons, protection against test-set tuning, and criteria for justifying hybrid + reranking—before selecting embedding/vector technologies.

17. Explicit Constraints
ID	Constraint	Priority	Acceptance interpretation
CON-001	GroundTruth SHALL remain a trustworthy RAG product rather than a generic chatbot.	MANDATORY	Product decisions must preserve the evidence-grounded identity.
CON-002	The project SHALL NOT blindly adopt AI frameworks or infrastructure components for buzzword value.	MANDATORY	Every significant dependency has a demonstrated purpose.
CON-003	The project SHALL avoid unnecessary microservices.	MANDATORY	Service boundaries exist only where justified.
CON-004	The project SHALL avoid unnecessary databases.	MANDATORY	Each persistent system has a concrete requirement.
CON-005	The project SHALL NOT claim scale that has not been demonstrated.	MANDATORY	Documentation distinguishes actual results from aspirations.
CON-006	The project SHALL NOT fabricate users, metrics or performance results.	MANDATORY	All claims are backed by evidence.
CON-007	The project SHALL document limitations rather than hide them.	MANDATORY	Known weaknesses appear in project documentation.
CON-008	Architecture and technology decisions SHALL follow requirements, research and experiments.	MANDATORY	No final technology is selected solely from popularity.
CON-009	Substantial implementation SHALL not begin before the necessary requirements and architectural decisions are sufficiently established.	MANDATORY	Development proceeds through bounded, reviewed milestones.
CON-010	AI-generated code SHALL be verified before acceptance.	MANDATORY	Generated implementation is treated as untrusted until tested/reviewed.
18. Resource Constraints
ID	Requirement / Constraint	Priority	Acceptance interpretation
RES-001	Infrastructure SHALL be appropriate for a student budget.	MANDATORY	Architecture avoids unnecessary recurring expense.
RES-002	AI model usage SHALL be monitored for cost.	MANDATORY	Representative model usage can be measured/estimated.
RES-003	Embedding usage SHALL be monitored for cost.	IMPORTANT	Embedding generation has an identifiable cost/usage profile.
RES-004	Storage costs SHALL be considered.	IMPORTANT	Document/storage requirements are included in deployment planning.
RES-005	Hosting and bandwidth costs SHALL be considered before public deployment.	IMPORTANT	Deployment selection accounts for recurring cost.
RES-006	Expensive infrastructure SHALL not be introduced without demonstrated need.	MANDATORY	Complexity/cost must have an explicit justification.

No numerical budget has been established in the Constitution; therefore no artificial dollar limit is introduced here.

19. Technology Constraints

This section is deliberately different from a technology stack.

CON-TECH-001 — MANDATORY

No specific programming language, frontend framework, backend framework, database, vector database, cloud provider, LLM provider, embedding model, or orchestration framework is currently mandated by this specification.

Reason: technology selection is explicitly required to follow requirements, research and experimentation.

CON-TECH-002 — MANDATORY

Any future technology choice SHALL be justified by:

Requirement
   ↓
Problem solved
   ↓
Alternatives considered
   ↓
Evidence/experiment
   ↓
Trade-off
   ↓
Decision
CON-TECH-003 — IMPORTANT

AI provider/model coupling SHOULD be minimized where doing so does not introduce unnecessary complexity.

CON-TECH-004 — MANDATORY

The project SHALL NOT introduce a dedicated vector database, reranker, cache, queue, agent framework, observability platform, or other specialized infrastructure merely because it is commonly used in RAG systems.

CON-TECH-005 — DEFERRED

Final technology selection remains a subsequent engineering activity after requirements, research and evaluation protocol are established.

20. Scope Boundaries
In Scope

The defined GroundTruth target includes:

Document ingestion
       ↓
Document processing
       ↓
Chunking + metadata
       ↓
Retrieval
       ↓
Evidence selection
       ↓
Grounded generation
       ↓
Citations
       ↓
Abstention
       ↓
Security
       ↓
Evaluation
       ↓
Observability
       ↓
Testing
       ↓
Deployment

These capabilities constitute the core product/system boundary.

Out-of-Scope Capabilities
OOS-001 — DECISION

GroundTruth SHALL NOT become a generic ChatGPT clone.

OOS-002 — DECISION

GroundTruth SHALL NOT be reduced to a basic "upload PDF and ask questions" demonstration.

OOS-003 — DECISION

GroundTruth SHALL NOT be a thin wrapper around an LLM API.

OOS-004 — DECISION

GroundTruth SHALL NOT require autonomous agents merely to demonstrate agentic technology.

This is particularly important because the broader training context involves Agentic AI, but GroundTruth's product definition is independently a trustworthy RAG system.

OOS-005 — DECISION

GroundTruth SHALL NOT introduce microservices merely for architectural sophistication.

OOS-006 — DECISION

GroundTruth SHALL NOT introduce multiple databases without demonstrated requirements.

OOS-007 — DEFERRED

Enterprise-scale infrastructure and claims are outside the currently established target unless future requirements justify them.

OOS-008 — DEFERRED

Large-scale multimodal document understanding is not currently an approved requirement.

OOS-009 — DEFERRED

Broad autonomous web research is not currently an approved GroundTruth capability.

OOS-010 — DEFERRED

Advanced multi-agent orchestration is not currently an approved GroundTruth capability.

21. Requirement Priority Summary

The hierarchy emerging from the specification is:

                    GROUNDTRUTH
                         │
                         ▼
              ┌─────────────────────┐
              │ TRUSTWORTHY ANSWERS │
              └──────────┬──────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
     Evidence         Citations       Abstention
        │                │                │
        └────────────────┼────────────────┘
                         ▼
                     Evaluation
                         │
             ┌───────────┼───────────┐
             ▼           ▼           ▼
          Security   Reliability   Quality
             │           │           │
             └───────────┼───────────┘
                         ▼
                     Product UX
                         │
                         ▼
                     Deployment

Everything else should support this hierarchy.

22. Requirements Traceability Summary

This is the most important final cross-check.

Project Goal	Major Requirements Supporting It
Build a trustworthy RAG answer engine	FR-008, FR-012, AI-001, AI-002, NFR-001
Answer from controlled knowledge	FR-001–FR-006, UR-001–UR-003
Retrieve relevant evidence	FR-008–FR-011, EVAL-007–EVAL-010
Use semantic + lexical retrieval intelligently	FR-009, FR-010, AI-008, EVAL-018
Avoid unnecessary retrieval complexity	FR-011, AI-009, CON-002–CON-004
Produce verifiable citations	FR-013–FR-014, DATA-001–DATA-003, REL-007, AI-006, EVAL-013
Avoid hallucinated answers	FR-015, AI-004, EVAL-012, EVAL-015
Know when evidence is insufficient	FR-015, UX-010, AI-004, EVAL-004, EVAL-014
Defend against prompt injection	SEC-003–SEC-005, SEC-009, AI-003, TEST-009, EVAL-006
Support real users	UR-001–UR-006, UX-001–UX-010
Handle failures reliably	REL-001–REL-007, NFR-002–NFR-003, TEST-007
Make AI quality measurable	EVAL-001–EVAL-020
Make system behavior observable	OBS-001–OBS-007, PERF-001–PERF-003
Keep the system maintainable	MAINT-001–MAINT-006, CON-008–CON-010
Control student costs	RES-001–RES-006, PERF-003, EVAL-017
Become a real deployed product	DEP-001–DEP-007
Avoid false engineering claims	SCALE-004, EVAL-020, CON-005–CON-007
Preserve the project's identity	CON-001–CON-004, OOS-001–OOS-006
23. Current Requirement Baseline

At this point, the formal requirement boundary can be summarized as:

                         GroundTruth
                              │
             ┌────────────────┴────────────────┐
             │                                 │
        USER VALUE                       ENGINEERING TRUST
             │                                 │
      Ask questions                     Evidence
             │                              ↓
      Get answers                    Retrieval quality
             │                              ↓
      Inspect sources                 Grounding
             │                              ↓
      Give feedback                  Citation validity
             │                              ↓
                                  Abstention
                                        ↓
                              Security / Injection
                                        ↓
                                  Evaluation
                                        ↓
                               Observability
                                        ↓
                                    Reliability
                                        ↓
                                   Deployment

The crucial boundary is:

Requirements tell us what GroundTruth must accomplish. They do not yet tell us which technology must accomplish it.

That means this specification intentionally does not say "use PostgreSQL," "use pgvector," "use FastAPI," "use Next.js," "use OpenAI," "use Gemini," or any equivalent technology decision.

Those belong to the next decision layer.

Formal status

Requirements specification: Established as a draft baseline.

Final architecture: NOT DESIGNED by this document.

Technology stack: NOT SELECTED by this document.

Retrieval strategy: NOT LOCKED. Dense and lexical retrieval are to be benchmarked; hybrid retrieval remains a candidate; reranking remains conditional.

Quantitative performance thresholds: NOT YET DEFINED.

Quantitative evaluation thresholds: NOT YET DEFINED.

Final document-format scope: NOT YET DEFINED.

Final deployment provider: NOT YET DEFINED.

This is therefore a requirements baseline, not an architecture disguised as a requirements document.