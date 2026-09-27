# AGENTS.md (Ask Mode)

This file provides guidance to agents when working with code in this repository.

## Documentation Context (Non-Obvious)

- `AgentLintplan.md` in the project root is the **canonical spec** — it is not a README; it is the complete phased implementation blueprint. All architecture, data models, CLI commands, Bob integration design, and acceptance criteria live there.
- `PROGRESS.md` is the source of truth for current implementation status — check it before answering questions about what is or isn't built yet. Phases 0–5 are complete; Phases 6–12 are pending.
- The `.agentlint/` directory is runtime output from the CLI, not source code — it is gitignored except for `policy.yaml` when committed deliberately.
- "Bob" in this codebase always means IBM Bob 2.0 IDE — not a person or another tool.
- The Bob custom mode is named "Agent Policy Auditor" and is restricted to editing only instruction/policy files, not application code.
- The Streamlit UI (`app.py`) reads pre-generated JSON artifacts from `.agentlint/` — it does not call the Python engine directly. Questions about "how the UI calls the engine" should be answered: it doesn't — the UI is a read-only viewer of scan artifacts.
- `agentlint/discovery/instruction_sources.py` hard-codes the built-in discovery list — the Bob rule paths scanned are `.bob/rules-code/AGENTS-code.md`, `.bob/rules-plan/AGENTS-plan.md`, `.bob/rules-ask/AGENTS-ask.md` (not the `rules-agent/` naming used in this repo itself).
- Two distinct parsing layers exist: Layer 1 (deterministic regex in `parsing/normalization.py`) and Layer 2 (Bob semantic, Phase 6 not yet implemented). Finding `deterministic=True` means it came from Layer 1.
