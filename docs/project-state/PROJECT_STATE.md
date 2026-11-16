> **OWNER DECISION — 2026-10-23 (Phase 0):** Checkpoint C0.2 is recorded as ACCEPTED /
> superseded by the project owner. The checkpoint-gate model is replaced by an
> issue-backlog model (see the new `AGENTS.md`): work proceeds issue by issue, CI is the
> gate, and human approval happens at PR merge. The former autonomy contract files are
> preserved as history under `docs/archive/autonomy/`. First milestone issues: GT-1 to
> GT-7 (persistence, retrieval wiring, grounded answers, UI, evaluation, deploy,
> portfolio pack).

# PROJECT STATE

## Project
GroundTruth

## State Version
1.3

## Last Updated
2026-11-16

## Current Phase
V1 — cited document Q&A (issue-backlog model; no checkpoint phases)

## Current Checkpoint
None — C0.2 is superseded (see owner decision above). There is no pending
checkpoint approval and no approval blocker.

## Checkpoint Status
SUPERSEDED — C0.2 retired 2026-10-23 by owner decision. Work is not blocked
on C0.2.

## Completed Checkpoints
- C0.1
- C0.2 (superseded, not pending — see owner decision above)

## Active Work
Issue-based work on main. Most recent merged work: PR #72 (Slice 1, issue #67 —
per-document retrieval caps + coverage strip, merged 2026-10-26); PR #66
(document-scoped querying, issue #65, merged 2026-10-25). Open rebuild issues
#67–#71 (Slices 1–5). Live page-7 proof still pending a clean-file re-upload
(the original test fixture had no extractable text).

## Active Branch
main (issue branches per PR; one issue = one branch = one PR)

## Active Issue
Open rebuild issues #67–#71; pick the top unblocked issue from the backlog.

## Active PR
None waiting on checkpoint approval. Open PRs #73 and #74 conflict with the
2026-10-23 decision (they would reinstate the retired C0.2 approval blocker)
and should be closed, not merged — see HANDOFF_RECORD.md HO-20261116-001.

## Blocked Work
None. If an issue is blocked, note it once in that issue and move to the next
independent issue. Never open a PR whose only purpose is to report a blocker.

## Failed Attempts
None

## Open Decisions
None

## Required Approvals
None before work starts. Human approval happens at PR merge, by the owner.

## Latest Validation
CI is the gate: a PR may be proposed for merge only when tests pass in CI, the
change matches the issue's acceptance criteria, and the PR description states
what changed, what was tested, and what remains uncertain.

## Repository State
Main carries the v1 cited document-QA flow (ingestion, retrieval, grounded
answers/abstention, one-page UI, deployment config). See AGENTS.md for the
current workflow.

## Known Defects
None recorded here — see open GitHub issues.

## Known Limitations
Gemini free-tier quota; public demo has no login by design, so keep personal
files off it.

## Next Permitted Action
Pick the top unblocked issue, implement, test, open a PR.

## Forbidden Next Actions
- Do not reinstate the C0.2 approval blocker or any checkpoint gate.
- Do not open a PR whose only purpose is to report a blocker.
- Do not fabricate validation, citations, or metrics that were not measured.

## State Authority
Owner decision 2026-10-23, as recorded in AGENTS.md (this file's banner).
Historical checkpoint documents are preserved under docs/archive/autonomy/
and in the handoff record below; they no longer gate work.
