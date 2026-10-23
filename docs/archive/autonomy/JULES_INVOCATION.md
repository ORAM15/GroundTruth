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
