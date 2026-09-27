# AGENTS.md (Plan Mode)

This file provides guidance to agents when working with code in this repository.

## Architectural Constraints (Non-Obvious)

- The deterministic findings engine (`agentlint/analysis/`) must produce results independently of Bob — Bob is an optional semantic enrichment layer, not a dependency for core scan functionality. Judges must be able to run the scan without Bob credentials.
- `agentlint/policy/compiler.py` generates a **candidate** policy only — it must never auto-apply. Human approval is a hard architectural requirement (`AgentLintplan.md §11`).
- The Streamlit UI (`app.py`) reads pre-generated JSON artifacts from `.agentlint/` — it does not call the Python engine directly. This decoupling is intentional so the deployed demo can run on bundled sample data without live repo access.
- Two distinct rule extraction layers exist in `agentlint/parsing/`: Layer 1 (deterministic regex/structural), Layer 2 (Bob semantic). They must stay separate so findings can be tagged `deterministic: true/false`.
- The three demo repos in `demo_repos/` are permanent test fixtures that must produce known, stable findings — they are the acceptance criteria for Phases 4 and 5. Do not redesign them without updating golden snapshots in `tests/golden/`.
- Bob slash commands (`/agentlint-audit`, `/agentlint-repair`, `/agentlint-verify`) are IDE workflows, not programmatic API calls — the Streamlit UI must not fake calling them; it displays their output artifacts.
- Phase implementation order is architecturally enforced: each phase's output is the input to the next. Planning out-of-order implementation will create integration gaps.
- `agentlint/analysis/__init__.py` is the single orchestration point for the deterministic engine — `run_deterministic_checks()` calls F01→F02→F03→F04→F05 in order and assigns IDs last. Detectors must return findings with `id=""`.
- Evidence ID prefix scheme (`ev-pm-001`, `ev-tf-001`, etc.) is defined in `agentlint/evidence/repository_truth.py` `_CATEGORY_ABBREV` dict — plan new evidence categories there first.
- `RepositoryEvidence.strength` drives F02 detection logic: strong evidence triggers high-confidence findings; medium-only evidence triggers lower-confidence ones; absent evidence produces no finding (avoids false positives on Python-only repos).
