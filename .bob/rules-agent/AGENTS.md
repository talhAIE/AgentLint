# AGENTS.md (Agent Mode)

This file provides guidance to agents when working with code in this repository.

## Coding Rules (Non-Obvious)

- Implement phases in strict order — `AgentLintplan.md §21` defines the mandatory sequence; skipping ahead breaks the acceptance criteria chain.
- Every phase must end with passing tests; do not mark a phase complete because files exist — only mark complete when acceptance criteria pass.
- `PROGRESS.md` is a required deliverable, not optional documentation — update it after every phase commit.
- `agentlint/validation/commands.py` must enforce a command allowlist and per-command timeout; the spec calls this out explicitly as a safety requirement (§11 Safety Tests).
- Discovery in `agentlint/discovery/instruction_sources.py` must return sources in **stable ordering** — tests depend on deterministic output. Built-in sources follow a fixed list; config extras are sorted case-insensitively.
- The `extraction_method` and `confidence` fields on `InstructionRule` must always be populated — the Bob semantic layer uses these to distinguish deterministic from inferred rules.
- `RepositoryEvidence.strength` is a controlled enum: `strong`, `medium`, `weak` only.
- `Finding.deterministic: bool` distinguishes engine-produced findings from Bob-inferred ones — never conflate them.
- Integration tests must use the three demo repos in `demo_repos/` as fixtures; do not write integration tests against live external repositories.
- Golden snapshot tests in `tests/golden/` compare normalized report output (JSON) — regenerate snapshots intentionally, not automatically.
- No writes outside `.agentlint/` and instruction file paths — path traversal must be rejected in the validation layer.
- Finding IDs are assigned in `analysis/__init__.py` via `_assign_finding_ids()` — detectors return findings with `id=""` and should never set IDs themselves.
- `from __future__ import annotations` is required at the top of every module (already present in all existing modules — maintain this).
- The `_CATEGORY_PATTERNS` list in `agentlint/parsing/normalization.py` is ORDER-SENSITIVE — more-specific patterns must come first (linting before package_manager, test_framework before package_manager).
- Evidence IDs follow scheme `ev-<abbrev>-<seq:03d>` (e.g. `ev-pm-001`); Finding IDs follow `find-<type_lower>-<seq:03d>` (e.g. `find-f02-001`). Never set these manually in tests — assert on type/title/severity instead.
- The `agentlint demo` CLI sub-command is invoked as `python -m agentlint.cli demo` when no entry-point is installed (used in integration subprocess tests).
