# AGENTS.md (Ask Mode)

This file provides guidance to agents when working with code in this repository.

## Documentation Context (Non-Obvious)

- `AgentLintplan.md` in the project root is the **canonical spec** — it is not a README; it is the complete phased implementation blueprint. All architecture, data models, CLI commands, Bob integration design, and acceptance criteria live there.
- The project does not exist yet (only the plan file) — there is no `agentlint/` package, no `app.py`, no `tests/` to reference. All structural questions must be answered from `AgentLintplan.md`.
- `PROGRESS.md` (once created) is the source of truth for current implementation status — check it before answering questions about what is built.
- The `.agentlint/` directory is runtime output from the CLI, not source code — it is gitignored except for `policy.yaml` when committed deliberately.
- "Bob" in this codebase always means IBM Bob 2.0 IDE — not a person or another tool.
- The Bob custom mode is named "Agent Policy Auditor" and is restricted to editing only instruction/policy files, not application code.
