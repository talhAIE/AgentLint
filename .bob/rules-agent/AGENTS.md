# AGENTS.md (Agent Mode)

This file provides guidance to agents when working with code in this repository.

## Coding Rules (Non-Obvious)

- Implement phases in strict order — `AgentLintplan.md §21` defines the mandatory sequence; skipping ahead breaks the acceptance criteria chain.
- Every phase must end with passing tests; do not mark a phase complete because files exist — only mark complete when acceptance criteria pass.
- `PROGRESS.md` is a required deliverable, not optional documentation — update it after every phase commit.
- `agentlint/validation/commands.py` must enforce a command allowlist and per-command timeout; the spec calls this out explicitly as a safety requirement (§11 Safety Tests).
- Discovery in `agentlint/discovery/instruction_sources.py` must return sources in **stable ordering** — tests depend on deterministic output.
- The `extraction_method` and `confidence` fields on `InstructionRule` must be populated — the Bob semantic layer uses these to distinguish deterministic from inferred rules.
- `RepositoryEvidence.strength` is a controlled enum: `strong`, `medium`, `weak` only.
- `Finding.deterministic: bool` distinguishes engine-produced findings from Bob-inferred ones — never conflate them.
- Integration tests must use the three demo repos in `demo_repos/` as fixtures; do not write integration tests against live external repositories.
- Golden snapshot tests in `tests/golden/` compare normalized report output — regenerate snapshots intentionally, not automatically.
- No writes outside `.agentlint/` and instruction file paths — path traversal must be rejected in the validation layer.
