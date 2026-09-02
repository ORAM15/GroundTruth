FINAL PROJECT STATE AND HANDOFF PROTOCOL

Project: GroundTruth
Document: Project State & Handoff Protocol
Status: FINAL — ENGINEERING BASELINE v1.0

1. Purpose

GroundTruth must never depend on hidden conversational memory for engineering continuity.

The authoritative state must be reconstructable from persistent project artifacts.

The governing principle is:

If an important engineering fact cannot be recovered from the repository/GitHub state and its associated records, it does not reliably exist as project state.

The system therefore establishes five canonical records:

PROJECT_STATE
     │
     ├── DECISION_LOG
     ├── CHECKPOINT_LOG
     ├── VALIDATION_RECORD
     └── HANDOFF_RECORD

Together they provide the complete operational state of GroundTruth.

2. Canonical State Model

The project state is:

                    PROJECT_STATE
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
     Progress         Decisions        Quality
        │                │                │
        ▼                ▼                ▼
 CHECKPOINT_LOG      DECISION_LOG   VALIDATION_RECORD
        │
        ▼
    Repository
        │
        ▼
   GitHub state
        │
        └──────────────┐
                       ▼
                 HANDOFF_RECORD
                       │
                       ▼
                Fresh AI session

A fresh agent must reconstruct its understanding from these records before touching implementation.

3. Source-of-Truth Hierarchy

When information exists in multiple places, the following hierarchy applies:

1. Approved project documents
2. GitHub repository state
3. GitHub Issues / PRs / reviews
4. Validation artifacts
5. Current PROJECT_STATE
6. Handoff record
7. Notebook research/context
8. AI conversation memory

There is an important distinction:

Project decisions and implementation state belong in the repository/GitHub.

Research material and exploratory reasoning may live in Notebook reference material.

Conversation history is never the authoritative source.

4. What Must Be Persistent

The following information must survive the current AI session:

Current phase
Current checkpoint
Completed checkpoints
Active work
Blocked work
Failed attempts
Open decisions
Required approvals
Latest validation
Repository state
Known defects
Known limitations
Next permitted action

If any of these are known, they must be recorded in the appropriate persistent artifact.

5. PROJECT_STATE

PROJECT_STATE is the current operational snapshot of GroundTruth.

Recommended location:

PROJECT_STATE.md

This file answers:

Where are we right now?

It should be concise and current.

It is not a historical diary.

6. Canonical PROJECT_STATE Structure
# PROJECT STATE

## Project
GroundTruth

## State Version
1.0

## Last Updated
YYYY-MM-DD HH:MM UTC

## Current Phase
[Px — Phase Name]

## Current Checkpoint
[Cx.x — Checkpoint Name]

## Checkpoint Status
PLANNED / READY / IN PROGRESS / VALIDATION /
REVIEW / APPROVED / MERGED / CLOSED /
BLOCKED / FAILED

## Completed Checkpoints
- [C0.1]
- [C0.2]

## Active Work
[Current engineering work unit]

## Active Branch
[branch]

## Active Issue
[#number]

## Active PR
[#number / None]

## Blocked Work
[None / description]

## Failed Attempts
[None / references]

## Open Decisions
- [Decision ID — description]

## Required Approvals
- [Approval required]

## Latest Validation
[Validation Record ID]
[PASS / FAIL / BLOCKED]

## Repository State
[Clean / modified / conflicted]
[Relevant branch/commit]

## Known Defects
- [DEF-ID]

## Known Limitations
- [...]

## Next Permitted Action
[Exactly one next authorized action]

## Forbidden Next Actions
- [...]

## State Authority
[Relevant checkpoint / decision / validation records]
7. PROJECT_STATE Rules

PROJECT_STATE.md must always describe the current state, not every historical event.

Therefore:

Bad:

"On August 18 we discussed..."

Good:

"Current checkpoint: C1.2 — Document Processing Research."

Historical information belongs elsewhere.

8. The Most Important Field

The most important field in PROJECT_STATE.md is:

Next Permitted Action

It should be specific enough that a fresh AI agent can understand what it may do next.

For example:

Next Permitted Action:
Review the approved retrieval research findings and prepare
the C1.3 model/AI behavior experiment plan.

Not:

Next Permitted Action:
Continue project.
9. Forbidden Next Actions

This field prevents a fresh agent from jumping ahead.

Example:

Forbidden Next Actions:
- Do not implement retrieval.
- Do not select a production embedding model.
- Do not modify the database schema.
- Do not begin frontend implementation.

This is particularly important for AI-assisted development.

10. DECISION_LOG

The DECISION_LOG records decisions that affect the project.

Recommended location:

docs/DECISION_LOG.md

For major architectural decisions, individual ADRs may additionally exist under:

docs/decisions/

The decision log answers:

Why does the project work this way?

11. Decision States

Every decision must have a state:

PROPOSED
OPEN
APPROVED
REJECTED
DEFERRED
SUPERSEDED

An AI agent must never treat:

PROPOSED

as:

APPROVED
12. Canonical DECISION_LOG Structure
# DECISION LOG

## D-001 — [Decision Title]

Status:
APPROVED / OPEN / PROPOSED / REJECTED / DEFERRED / SUPERSEDED

Date:
YYYY-MM-DD

Context:
[Why this decision was necessary]

Question:
[What needed to be decided]

Options Considered:
1. ...
2. ...
3. ...

Decision:
[Chosen approach]

Rationale:
[Why]

Trade-offs:
[...]

Requirements Affected:
[...]

Architecture Affected:
[...]

Technology Affected:
[...]

Approved By:
[Project owner / authority]

Evidence:
[Research / experiment / validation reference]

Related Checkpoints:
[Cx.x]

Supersedes:
[Decision ID / None]
13. CHECKPOINT_LOG

CHECKPOINT_LOG is the historical and operational record of checkpoint progression.

Recommended location:

docs/CHECKPOINT_LOG.md

It answers:

What has the project actually completed?

14. Checkpoint States

Use the states already established:

PLANNED
READY
IN PROGRESS
VALIDATION
REVIEW
APPROVED
MERGED
CLOSED
FAILED
BLOCKED
15. Canonical CHECKPOINT_LOG Entry
## C4.3 — Chunking & Metadata

Phase:
Phase 4

Status:
CLOSED

Issue:
#42

Branch:
checkpoint/C4.3-chunking-metadata

PR:
#47

Started:
YYYY-MM-DD

Completed:
YYYY-MM-DD

Objective:
[...]

Acceptance Criteria:
- [x] ...
- [x] ...
- [x] ...

Validation:
VR-004

Human Approval:
APPROVED

Evidence:
- test report
- fixture results
- review

Known Limitations:
[...]

Next Checkpoint:
C4.4
16. CHECKPOINT_LOG Rule

The checkpoint log must never say:

C4.3 — DONE

without evidence.

Instead:

C4.3
Status: CLOSED
Validation: VR-004
Gate: PASS
Approval: APPROVED

The evidence chain matters.

17. VALIDATION_RECORD

The validation record answers:

How do we know the claimed result is actually true?

Recommended location:

docs/validation/

or, for machine-generated evaluation results:

evals/results/

The exact storage follows the approved technology specification.

18. Canonical VALIDATION_RECORD
# VALIDATION RECORD

## Validation ID
VR-004

## Checkpoint
C4.3

## Date
YYYY-MM-DD

## Validation Type
UNIT / INTEGRATION / E2E / AI /
SECURITY / PERFORMANCE / UX /
DEPLOYMENT / FAILURE / REGRESSION

## Requirement(s)
REQ-...

## Environment
[Environment details]

## Version
[Commit SHA / release]

## Inputs
[Dataset / fixtures / scenario]

## Procedure
[How validation was performed]

## Expected Result
[...]

## Actual Result
[...]

## Metrics
[...]

## Result
PASS / FAIL / BLOCKED

## Acceptance Criteria
- [PASS] ...
- [PASS] ...
- [FAIL] ...

## Evidence
[Links/paths/artifacts]

## Known Limitations
[...]

## Reviewer
[...]

## Approval
[...]

## Related PR
[...]

## Related Issue
[...]
19. Validation Immutability

Once a validation record represents a completed evaluation, it should not be silently rewritten to make a failed result disappear.

If a later implementation produces better results:

VR-004 → FAIL
VR-005 → PASS

not:

VR-004 → magically becomes PASS

This preserves engineering history.

20. HANDOFF_RECORD

A handoff record is designed specifically for a fresh AI session.

Recommended location:

HANDOFF.md

or:

docs/HANDOFF.md

It answers:

If another engineer/AI opened this repository right now, what must they know before doing anything?

Unlike PROJECT_STATE, it may contain a little more context.

21. Canonical HANDOFF_RECORD
# GROUNDTRUTH HANDOFF RECORD

## Handoff ID
HO-YYYYMMDD-###

## Generated
YYYY-MM-DD HH:MM UTC

## Project State
[One-paragraph current state]

## Current Phase
[...]

## Current Checkpoint
[...]

## Checkpoint Status
[...]

## What Has Been Completed
[...]

## What Is Currently Being Worked On
[...]

## What Is Blocked
[...]

## Failed Attempts
[...]

## Open Decisions
[...]

## Required Human Approvals
[...]

## Latest Validation
[...]

## Repository State
Branch:
Commit:
Working tree:
Relevant PR:
Relevant Issue:

## Known Defects
[...]

## Known Limitations
[...]

## Important Recent Changes
[...]

## What Must NOT Be Changed
[...]

## Next Permitted Action
[...]

## Resume Instructions
[Exact sequence]

## Authoritative References
- Project Constitution
- Requirements
- Architecture
- Technology Specification
- Phase Plan
- Checkpoint System
- AI Engineering Contract
- Quality & Evaluation System
- GitHub Workflow
- PROJECT_STATE
- DECISION_LOG
- CHECKPOINT_LOG
- VALIDATION_RECORDS
22. Notebook vs Repository

This distinction is extremely important.

Repository/GitHub owns:
Requirements
Architecture
Technology decisions
Project scope
Checkpoint state
Acceptance criteria
Implementation
Tests
Evaluation results
Security findings
Known defects
Approved decisions
API contracts
Database schema
Deployment configuration
Current project state
Handoff state

These are operationally authoritative.

Notebook reference material owns:
Research papers
Source collections
Exploratory research
Literature summaries
Comparative research
Unresolved research questions
Long-form technical notes
External references
Model comparisons during exploration
Early hypotheses
Research synthesis

Notebook material informs decisions.

It does not silently become a project decision.

23. Research-to-Decision Flow

The relationship is:

Notebook
   │
   ▼
Research
   │
   ▼
Finding
   │
   ▼
Engineering implication
   │
   ▼
Proposal
   │
   ▼
Human decision
   │
   ▼
DECISION_LOG
   │
   ▼
Architecture / Technology / Requirements

Therefore:

A Notebook conclusion is not automatically an approved architecture decision.

24. Why This Separation Matters

Without this distinction, a fresh AI could read a research notebook containing:

"PostgreSQL + pgvector seems appropriate."

and incorrectly conclude:

"PostgreSQL + pgvector is approved."

That is precisely the kind of state corruption this protocol prevents.

25. Repository as Operational Memory

The repository should eventually allow a fresh agent to reconstruct:

WHAT
 ↓
WHY
 ↓
HOW
 ↓
WHERE WE ARE
 ↓
WHAT PASSED
 ↓
WHAT FAILED
 ↓
WHAT IS BLOCKED
 ↓
WHAT CAN HAPPEN NEXT

without requiring the original conversation.

26. Fresh AI Resume Protocol

This is the exact sequence a fresh AI agent must follow.

STEP 1 — Do not touch code

The first action is read-only inspection.

No modifications.

No generated files.

No dependency installation that changes the repository.

No code generation.

27. STEP 2 — Inspect Git State

The agent first determines:

current branch
current commit
working-tree status
untracked files
existing branches
relevant PRs/issues if available

The purpose is to understand the actual repository state.

28. STEP 3 — Read PROJECT_STATE

Read:

PROJECT_STATE.md

Determine:

current phase
current checkpoint
checkpoint status
active work
blocked work
open decisions
latest validation
known defects
next permitted action
29. STEP 4 — Read HANDOFF

Read:

HANDOFF.md

Compare it with PROJECT_STATE.md.

If they disagree:

STOP.

Do not guess which one is correct.

30. STEP 5 — Read the Governing Documents

The agent must then inspect:

PRODUCT.md
REQUIREMENTS.md
ARCHITECTURE.md
TECHNOLOGY.md

and the relevant:

PHASE PLAN
CHECKPOINT SYSTEM
AI ENGINEERING CONTRACT
QUALITY & EVALUATION SYSTEM
GITHUB WORKFLOW

The agent does not necessarily need to reread every historical document in full if the handoff clearly identifies the relevant sections, but it must verify the governing constraints before implementation.

31. STEP 6 — Read Relevant Decision Records

The agent checks:

DECISION_LOG

and any ADRs relevant to the current checkpoint.

Especially inspect:

open decisions
recently approved decisions
superseded decisions
deferred decisions.
32. STEP 7 — Read Checkpoint Definition

The active checkpoint is then inspected in full.

The agent must know:

objective
prerequisites
allowed work
forbidden work
expected artifacts
acceptance criteria
validation method
dependencies
human approval requirement
next checkpoint
33. STEP 8 — Verify Prerequisites

Do not trust the state file blindly.

The agent must verify that prerequisites actually exist.

For example:

PROJECT_STATE:
C4.3 READY

Agent verifies:

C4.2 = actually closed?
required parser exists?
required tests pass?
required artifacts present?

If the declared state contradicts repository reality:

STOP

and record the inconsistency.

34. STEP 9 — Inspect Existing Implementation

Only now should the agent inspect the relevant implementation.

Determine:

what exists
what works
what is incomplete
what tests exist
what interfaces exist
what dependencies exist
what behavior must be preserved

The agent must understand before modifying.

35. STEP 10 — Inspect Existing Validation

The agent must inspect the latest relevant validation records.

Determine:

what has already been proven
what has failed
what remains unverified

This prevents repeating already-failed approaches without learning.

36. STEP 11 — Determine Permission

The agent asks:

What am I actually authorized to do right now?

The answer comes from:

current checkpoint
+
engineering work unit
+
approved decisions

If the desired action is outside those boundaries:

DO NOT IMPLEMENT
37. STEP 12 — Check for Blockers

Before writing code, determine whether there is:

open decision
missing requirement
missing dependency
architecture uncertainty
repository inconsistency
external-service blocker
required human approval

If one prevents safe implementation:

BLOCKED

and stop.

38. STEP 13 — Only Now Modify Code

Once all preceding checks pass:

inspect
→ understand
→ verify
→ authorize
→ modify

The agent may begin the bounded engineering work.

39. STEP 14 — Validate

After implementation:

tests
→ evaluation
→ security checks
→ relevant validation

as required by the checkpoint.

40. STEP 15 — Update State

After validation, update the appropriate persistent records:

PROJECT_STATE
CHECKPOINT_LOG
VALIDATION_RECORD
DECISION_LOG
HANDOFF

Only the records relevant to the event need updating.

41. STEP 16 — GitHub Synchronization

The agent then ensures:

Issue
Branch
Commit
PR
Validation
Review

accurately reflect reality.

No artificial GitHub activity.

42. STEP 17 — Produce Handoff

At the end of an AI session involving meaningful project work, the agent should leave enough state for the next agent to resume.

The next agent should not have to ask:

"What were we doing?"

The repository should already answer it.

43. Resume Decision Tree

A fresh AI session follows:

                NEW AI SESSION
                      │
                      ▼
                READ-ONLY FIRST
                      │
                      ▼
                Git state check
                      │
                      ▼
               PROJECT_STATE
                      │
                      ▼
                  HANDOFF
                      │
                ┌─────┴─────┐
                │           │
             CONSISTENT  INCONSISTENT
                │           │
                ▼           ▼
            CONTINUE       STOP
                │
                ▼
        Governing documents
                │
                ▼
          Decision records
                │
                ▼
        Active checkpoint
                │
                ▼
         Verify prerequisites
                │
          ┌─────┴─────┐
          │           │
         FAIL        PASS
          │           │
          ▼           ▼
        STOP       Inspect code
                      │
                      ▼
                Check blockers
                      │
                 ┌────┴────┐
                 │         │
              BLOCKED    CLEAR
                 │         │
                 ▼         ▼
                STOP      PLAN
                           │
                           ▼
                       IMPLEMENT
44. State Consistency Rule

Three states must agree:

DOCUMENTED STATE
      ↕
GITHUB STATE
      ↕
REPOSITORY STATE

For example:

PROJECT_STATE:
C5.1 CLOSED

GitHub:
Issue closed
PR merged

Repository:
retrieval implementation exists
tests exist
validation passed

Good.

But:

PROJECT_STATE:
C5.1 CLOSED

GitHub:
PR still open

Repository:
implementation incomplete

Bad.

This is a state inconsistency, not something the AI should silently repair.

45. State Update Events

PROJECT_STATE should be updated whenever one of these occurs:

phase changes
checkpoint changes
checkpoint becomes blocked
checkpoint fails
checkpoint passes
approval changes
major defect discovered
important decision approved
validation result changes
active branch changes
major work starts/stops
repository state materially changes
next permitted action changes
46. Failed Attempts Must Survive Handoffs

Suppose an embedding experiment fails.

The next agent must not rediscover the same failure accidentally.

Record:

Attempt
Hypothesis
Implementation
Validation
Result
Why it failed
Lesson

Example:

Attempt:
Embedding configuration A

Result:
FAIL

Reason:
Recall@10 below baseline

Lesson:
Do not adopt configuration A without changing the retrieval strategy.

Status:
REJECTED
47. Failed ≠ Forgotten

The project must preserve meaningful failures.

Why?

Because:

Failure
 ↓
Learning
 ↓
Better decision

is engineering progress.

Repeatedly making the same failed attempt because previous sessions forgot it is not.

48. Known Defects

Known defects should have stable identifiers where useful:

DEF-001
DEF-002

Example:

## DEF-003

Title:
Citation panel fails for multi-page source.

Severity:
Medium

Detected:
C8.3

Status:
OPEN

Affected Component:
Citation UX

Workaround:
None

Related Checkpoint:
C8.3

Related Issue:
#81

A defect must not disappear merely because the current agent did not encounter it.

49. Open Decisions

Open decisions should be explicit:

D-007
Status: OPEN

Question:
Should reranking remain enabled in production?

Blocked Checkpoint:
C5.5

Decision Required:
Owner approval

Options:
A
B

Current Evidence:
VR-...

This allows a fresh agent to know:

Why can't I proceed?

50. Required Approvals

State should distinguish:

NOT REQUIRED
PENDING
APPROVED
REJECTED

Example:

Human Approval:
PENDING

Required For:
C5.5 reranking decision

A fresh agent must not interpret:

PENDING

as permission.

51. Latest Validation

PROJECT_STATE should point to the latest relevant validation:

Latest Validation:
VR-021 — PASS

The actual detailed record lives separately.

This keeps state concise while preserving evidence.

52. State Does Not Replace Evidence

PROJECT_STATE may say:

C4.3 CLOSED

but it is not the evidence.

The evidence remains:

CHECKPOINT_LOG
+
VALIDATION_RECORD
+
GitHub PR
+
test/evaluation artifacts

This distinction prevents state files from becoming self-declared truth.

53. Handoff Does Not Grant Authority

A handoff record may say:

Next:
Implement C5.1

but the agent must still verify:

C5.1 prerequisites
current Git state
approved architecture
technology decisions
acceptance criteria

Handoff is a continuity mechanism, not a permission escalation mechanism.

54. Fresh Session Must Never Do This

A new AI agent must not:

open repository
 ↓
see TODO
 ↓
start coding

Nor:

read README
 ↓
assume current architecture
 ↓
rewrite implementation

Nor:

see "next: retrieval"
 ↓
implement retrieval

without reconstructing the actual state.

55. Mandatory Fresh-Session Checklist

Before touching code:

[ ] Git state inspected
[ ] PROJECT_STATE read
[ ] HANDOFF read
[ ] State consistency checked
[ ] Requirements checked
[ ] Architecture checked
[ ] Technology decisions checked
[ ] Active checkpoint read
[ ] Prerequisites verified
[ ] Relevant decision records read
[ ] Latest validation inspected
[ ] Known defects inspected
[ ] Open decisions inspected
[ ] Required approvals checked
[ ] Repository implementation inspected
[ ] Scope confirmed
[ ] Blockers checked
[ ] Next permitted action confirmed

Only after all applicable items pass may implementation begin.

56. Canonical Information Ownership
Information	Repository/GitHub	Notebook
Product definition	Authoritative	Reference
Requirements	Authoritative	Reference
Architecture	Authoritative	Research input
Technology decisions	Authoritative	Research input
Research papers	Reference	Primary research store
Research synthesis	Reference	Primary exploratory store
Approved decisions	Authoritative	Reference
Checkpoint state	Authoritative	Not authoritative
Implementation	Authoritative	Not authoritative
Tests	Authoritative	Reference
Evaluation results	Authoritative	Analysis/reference
Security findings	Authoritative	Reference
Known defects	Authoritative	Reference
Deployment state	Authoritative	Reference
Handoff state	Authoritative	Not authoritative

The important rule is:

Notebook can inform the repository. Repository state governs engineering execution.

57. Recommended State Files

The permanent repository should therefore eventually contain:

groundtruth/
│
├── PROJECT_STATE.md
├── HANDOFF.md
│
├── PRODUCT.md
├── REQUIREMENTS.md
├── ARCHITECTURE.md
├── TECHNOLOGY.md
├── EVALUATION.md
├── THREAT_MODEL.md
│
├── docs/
│   ├── DECISION_LOG.md
│   ├── CHECKPOINT_LOG.md
│   │
│   ├── decisions/
│   └── validation/
│
├── evals/
│   ├── datasets/
│   ├── runners/
│   ├── metrics/
│   ├── reports/
│   └── results/
│
└── .github/
    ├── ISSUE_TEMPLATE/
    ├── PULL_REQUEST_TEMPLATE.md
    └── workflows/

The actual implementation structure remains governed by the approved architecture.

58. State Update Protocol

Whenever meaningful work ends, the agent follows:

WORK
 ↓
VALIDATE
 ↓
RECORD RESULT
 ↓
UPDATE CHECKPOINT
 ↓
UPDATE PROJECT_STATE
 ↓
UPDATE HANDOFF
 ↓
SYNC GITHUB

The order matters.

We should not have:

GitHub says merged

while:

PROJECT_STATE says in progress

for an extended period.

59. Emergency Handoff

If a session terminates unexpectedly, the next agent should use:

Git state
+
latest committed PROJECT_STATE
+
GitHub Issue/PR
+
latest validation record

to reconstruct state.

This means critical state should not exist only in an uncommitted conversation-generated file.

Where possible, important state changes should be committed.

60. Final Resume Protocol

The canonical fresh-agent sequence is:

1. STOP — do not modify anything
       ↓
2. Inspect Git/repository state
       ↓
3. Read PROJECT_STATE
       ↓
4. Read HANDOFF
       ↓
5. Compare state for consistency
       ↓
6. Read governing project documents
       ↓
7. Read relevant decisions
       ↓
8. Identify current checkpoint
       ↓
9. Verify checkpoint prerequisites
       ↓
10. Inspect latest validation
       ↓
11. Inspect known defects/failures
       ↓
12. Inspect active implementation
       ↓
13. Check approvals/blockers
       ↓
14. Confirm permitted scope
       ↓
15. Determine exact next action
       ↓
16. Only now plan implementation
       ↓
17. Implement bounded work
       ↓
18. Validate
       ↓
19. Record evidence
       ↓
20. Update project state
       ↓
21. Synchronize GitHub
       ↓
22. Prepare next handoff
61. Final Continuity Model

GroundTruth now has a persistent-memory architecture independent of AI conversation history:

                 GROUNDTRUTH
                      │
              ┌───────┴────────┐
              ▼                ▼
          REPOSITORY         NOTEBOOK
              │                │
              │                └── Research
              │                    Sources
              │                    Exploration
              │                    Hypotheses
              │
              ├── Constitution
              ├── Requirements
              ├── Architecture
              ├── Technology
              ├── Phase Plan
              ├── Checkpoints
              │
              ├── PROJECT_STATE
              ├── DECISION_LOG
              ├── CHECKPOINT_LOG
              ├── VALIDATION_RECORDS
              └── HANDOFF
                      │
                      ▼
                FRESH AI SESSION
                      │
                      ▼
                 RECONSTRUCT
                      │
                      ▼
                 VERIFY STATE
                      │
                      ▼
               RESUME SAFELY
62. Final Principle

The deepest rule of this protocol is:

Conversation is temporary. Project state is permanent.

A future AI should never need to know what we remember discussing.

It should be able to know:

What GroundTruth is
        ↓
What it must do
        ↓
How it is architected
        ↓
What has been decided
        ↓
What has been completed
        ↓
What has been validated
        ↓
What has failed
        ↓
What is blocked
        ↓
What it is allowed to do next

from the project's persistent engineering record.

63. FINAL STATUS

PROJECT STATE & HANDOFF PROTOCOL v1.0 — FINAL

The complete GroundTruth governance system is now:

PROJECT CONSTITUTION
       ↓
REQUIREMENTS
       ↓
ARCHITECTURE
       ↓
TECHNOLOGY
       ↓
MASTER PHASE PLAN
       ↓
CHECKPOINT SYSTEM
       ↓
AI ENGINEERING CONTRACT
       ↓
QUALITY & EVALUATION
       ↓
GITHUB ENGINEERING WORKFLOW
       ↓
PROJECT STATE
       ↓
VALIDATION EVIDENCE
       ↓
HANDOFF
       ↓
FRESH AI SESSION
       ↓
SAFE RESUMPTION

And the non-negotiable resume rule is:

A fresh AI session must inspect and reconstruct project state before touching code.

That gives us the missing property we wanted from the beginning: GroundTruth becomes resumable by design, rather than dependent on whoever—or whichever AI session—happened to build it.