# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Project

AgentLint — a Python CLI + Streamlit tool that audits AI coding-agent instruction files (AGENTS.md, CLAUDE.md, etc.) for drift against the actual repository. Built for the IBM Bob 2.0 Hackathon. Full specification: `AgentLintplan.md`.

## Stack

- Python 3.11+, pytest, Streamlit, Typer, PyYAML, `tomllib` (stdlib)
- Optional: Pydantic, `rapidfuzz` — avoid LangChain
- Install: `pip install -e ".[dev]"` (dev extras required for pytest)

## Commands

```bash
pip install -e ".[dev]"          # install with dev deps (pytest, pytest-cov)
pytest                           # run all tests
pytest tests/unit/               # run unit tests only
pytest tests/integration/        # run integration tests
pytest tests/unit/test_models.py # run a single test file
pytest tests/unit/test_models.py::test_finding_defaults  # run a single test
streamlit run app.py             # launch UI
agentlint scan <repo-path>       # primary CLI entry point
agentlint demo                   # runs against bundled demo repos
python -m agentlint.cli demo     # equivalent without installed entry point
```

## Implementation Order (CRITICAL)

Phases must be built in strict order per `AgentLintplan.md §21`:

`models/discovery → evidence → parsing → deterministic findings → demo repos → Bob workflow → policy/repair → verification → UI → CI → hardening → submission`

**Never jump to UI before the deterministic engine is complete.**

## Architecture

```
agentlint/          # Python package
  models.py         # InstructionSource, InstructionRule, RepositoryEvidence, Finding, ValidationResult
  discovery/        # finds AGENTS.md, CLAUDE.md, .github/copilot-instructions.md, .bob/rules-*/AGENTS*.md
  evidence/         # detects package manager, test framework, commands, lint, runtime, paths from repo files
  parsing/          # extracts and normalizes rules from instruction files (deterministic + Bob semantic)
  analysis/         # conflict/duplicate/staleness detection (deterministic rules engine)
  policy/           # generates .agentlint/policy.yaml canonical contract
  validation/       # re-verifies after repair; runs commands with timeout + allowlist
  ui/               # Streamlit view models only (no business logic)
demo_repos/         # three packaged sample repos used in tests and demo mode
tests/unit/         # per-module unit tests
tests/integration/  # tests using demo_repos/
tests/golden/       # snapshot comparisons of normalized reports (JSON, regenerate intentionally)
.agentlint/         # runtime output: scan.json, evidence.json, findings.json, policy.yaml, repair-plan.md, verification.json
.bob/               # Bob skills, custom mode, slash commands
```

## Key Conventions

- Every phase ends with passing tests before the phase is marked complete in `PROGRESS.md`
- `PROGRESS.md` must be kept updated with phase checklist, commands run, and known issues
- Commit message format: `feat: <phase description>` (see `AgentLintplan.md §21 Rule 4`)
- Use dataclasses (no external ORM) for all domain models; `from __future__ import annotations` on every module
- Config lives in `.agentlint/config.yaml`; extra instruction paths are user-defined there
- Command runner **must** have a timeout and an allowlist — no unbounded shell execution
- Writes outside allowed paths (`.agentlint/`, instruction files) must be rejected

## Bob Integration Rules

- No fake Bob buttons in Streamlit — only display artifacts actually produced by Bob workflows
- No fabricated metrics — all numbers come from scan results
- Bob slash commands: `.bob/commands/agentlint-audit.md`, `agentlint-repair.md`, `agentlint-verify.md`
- Bob skill: `.bob/skills/agent-policy-audit/SKILL.md`
- Custom Bob mode restricts edits to instruction/policy files only — never production code
- Bob usage: reserve for semantic document understanding, parallel subagent investigation, repair reasoning, and verification — not for Streamlit layout or CRUD code
