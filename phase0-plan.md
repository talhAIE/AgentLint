# Phase 0 Plan — Scope Lock, Repository Setup, and Hackathon Compliance

## Overview

Phase 0 creates the complete project skeleton so every later phase has a stable, installable base to build on. No business logic is written. The goal is: the project installs, `pytest` runs (with zero tests but no errors), `streamlit run app.py` launches a placeholder UI, and `PROGRESS.md` tracks phase status.

The repository already exists (this workspace). Git is already initialized. `AgentLintplan.md` and `AGENTS.md` are already present. Everything else must be created.

---

## Existing State

| Item | Status |
|---|---|
| Git repository | ✅ exists |
| `AgentLintplan.md` | ✅ exists |
| `AGENTS.md`, `.bob/rules-*/AGENTS.md` | ✅ exists |
| MIT LICENSE | ❌ missing |
| `pyproject.toml` | ❌ missing |
| `requirements.txt` | ❌ missing |
| `README.md` | ❌ missing |
| `CONTRIBUTING.md` | ❌ missing |
| `.gitignore` | ❌ missing |
| `PROGRESS.md` | ❌ missing |
| `app.py` (placeholder) | ❌ missing |
| `agentlint/` package scaffold | ❌ missing |
| `tests/` directory scaffold | ❌ missing |
| `demo_repos/` directory | ❌ missing |
| `artifacts/screenshots/` directory | ❌ missing |
| `.github/workflows/test.yml` | ❌ missing |

---

## Sub-Tasks

---

### Sub-Task A — Project Metadata Files

**Intent:** Create the non-code project root files required for a legitimate Python open-source project and hackathon submission.

**Expected Outcomes:**
- `LICENSE` contains the MIT license text with the correct year and placeholder author name
- `README.md` contains the project title, one-sentence description, and `## Coming soon` sections matching the §12.1 README structure (placeholder content only — full content is Phase 12)
- `CONTRIBUTING.md` is a minimal placeholder
- `.gitignore` covers Python, pytest, Streamlit, venv, `.agentlint/` runtime output, and OS artifacts

**Todo List:**
1. Create `LICENSE` — MIT text, year 2024–2026, author "AgentLint Contributors"
2. Create `README.md` — title + tagline + placeholder section headings from §12.1 (Problem, Solution, Architecture, Why IBM Bob 2.0, Features, Setup, Run Demo, Run Against Local Repo, Bob Workflow, Project Structure, Limitations, License)
3. Create `CONTRIBUTING.md` — one paragraph placeholder
4. Create `.gitignore` — standard Python + pytest + venv + Streamlit cache + `.agentlint/` + `__pycache__` + `.env` + OS artifacts

**Relevant Context:** §12.1, §12.3 (public-repo-safe: no secrets), §29 Repository checklist

**Status:** [ ] pending

---

### Sub-Task B — Python Package Scaffold

**Intent:** Create the minimal installable Python package structure so `pip install -e .` works and `import agentlint` succeeds, without implementing any business logic.

**Expected Outcomes:**
- `pyproject.toml` is present and valid; `pip install -e .` succeeds
- `requirements.txt` lists direct runtime dependencies
- `agentlint/__init__.py` exports `__version__ = "0.1.0"`
- All sub-package `__init__.py` stubs exist (empty files) for every directory in §12 structure
- `agentlint/cli.py` contains a stub CLI entry point that exits 0 with a "not implemented" message
- `agentlint/config.py` is an empty module stub

**Files to create:**

```
pyproject.toml
requirements.txt
agentlint/__init__.py
agentlint/cli.py
agentlint/config.py
agentlint/models.py               ← empty stub (implementation is Phase 1)
agentlint/discovery/__init__.py
agentlint/discovery/instruction_sources.py   ← empty stub
agentlint/discovery/repo_files.py            ← empty stub
agentlint/parsing/__init__.py
agentlint/parsing/markdown_rules.py          ← empty stub
agentlint/parsing/json_parser.py             ← empty stub
agentlint/parsing/yaml_parser.py             ← empty stub
agentlint/parsing/normalization.py           ← empty stub
agentlint/evidence/__init__.py
agentlint/evidence/package_manager.py        ← empty stub
agentlint/evidence/testing.py                ← empty stub
agentlint/evidence/linting.py                ← empty stub
agentlint/evidence/runtime.py                ← empty stub
agentlint/evidence/commands.py               ← empty stub
agentlint/evidence/paths.py                  ← empty stub
agentlint/evidence/repository_truth.py       ← empty stub
agentlint/analysis/__init__.py
agentlint/analysis/deterministic_rules.py    ← empty stub
agentlint/analysis/conflicts.py              ← empty stub
agentlint/analysis/duplicates.py             ← empty stub
agentlint/analysis/scoring.py                ← empty stub
agentlint/analysis/report_builder.py         ← empty stub
agentlint/policy/__init__.py
agentlint/policy/schema.py                   ← empty stub
agentlint/policy/compiler.py                 ← empty stub
agentlint/policy/diff.py                     ← empty stub
agentlint/policy/adapters.py                 ← empty stub
agentlint/validation/__init__.py
agentlint/validation/structural.py           ← empty stub
agentlint/validation/commands.py             ← empty stub
agentlint/validation/evidence_check.py       ← empty stub
agentlint/validation/runner.py               ← empty stub
agentlint/ui/__init__.py
agentlint/ui/components.py                   ← empty stub
agentlint/ui/view_models.py                  ← empty stub
```

**pyproject.toml required content:**
- `[project]` with name, version, requires-python = ">=3.11"
- `[project.scripts]` entry point: `agentlint = "agentlint.cli:main"`
- Runtime deps: `streamlit`, `pyyaml`, `typer` (or `typer[all]`)
- Dev deps: `pytest`, `pytest-cov`

**requirements.txt:** mirror runtime deps from pyproject.toml for environments that use it

**Relevant Context:** §12 Proposed Repository Structure, §22 Technology Stack

**Status:** [ ] pending

---

### Sub-Task C — Placeholder Streamlit App

**Intent:** Create `app.py` so that `streamlit run app.py` launches a working (placeholder) UI — one of the explicit Phase 0 acceptance criteria.

**Expected Outcomes:**
- `streamlit run app.py` runs without error
- Page shows project title and a "coming soon" message — no actual scan results, no fake data
- No business logic imported yet

**Files to create:**
- `app.py` — minimal Streamlit page: title, tagline, placeholder sections matching §16 page structure (Overview, Instruction Sources, Findings, Repository Truth, Canonical Contract, Repair Preview, Verification)

**Relevant Context:** §16 Streamlit Dashboard, §21 Rule 5 (no fake functionality), §21 Rule 6 (no fake metrics)

**Status:** [ ] pending

---

### Sub-Task D — Test Scaffold

**Intent:** Create the test directory structure and a minimal smoke test so `pytest` runs and exits 0, satisfying the Phase 0 acceptance criterion.

**Expected Outcomes:**
- `pytest` from project root exits 0
- `tests/unit/`, `tests/integration/`, `tests/fixtures/`, `tests/golden/` directories exist
- One smoke test (`tests/unit/test_smoke.py`) that asserts `import agentlint` succeeds and `agentlint.__version__` is set

**Files to create:**
```
tests/__init__.py
tests/unit/__init__.py
tests/unit/test_smoke.py
tests/integration/__init__.py
tests/fixtures/                   ← empty, .gitkeep
tests/golden/                     ← empty, .gitkeep
```

**No Phase 1+ tests are written here.** The smoke test is the only test.

**Relevant Context:** §21 Rule 2 (end every phase with passing tests), §11 Testing

**Status:** [ ] pending

---

### Sub-Task E — Demo Repos Skeleton

**Intent:** Create the three empty demo repository directories referenced throughout the spec. Phase 5 populates them with content; Phase 0 only creates the skeleton.

**Expected Outcomes:**
- `demo_repos/inconsistent-js-repo/`, `demo_repos/single-agent-stale-repo/`, `demo_repos/clean-repo/` exist and are tracked by git (via `.gitkeep`)

**Files to create:**
```
demo_repos/inconsistent-js-repo/.gitkeep
demo_repos/single-agent-stale-repo/.gitkeep
demo_repos/clean-repo/.gitkeep
```

**Relevant Context:** §12 Repository Structure, §25 Acceptance Test Scenarios

**Status:** [ ] pending

---

### Sub-Task F — Artifacts Directory

**Intent:** Create the `artifacts/` directory for screenshots and demo output required by the hackathon submission.

**Expected Outcomes:**
- `artifacts/screenshots/` and `artifacts/demo/` exist and are tracked by git

**Files to create:**
```
artifacts/screenshots/.gitkeep
artifacts/demo/.gitkeep
```

**Relevant Context:** §12, §29 Repository checklist, §17.1 (capture screenshots)

**Status:** [ ] pending

---

### Sub-Task G — GitHub Actions CI

**Intent:** Add the basic CI workflow that runs pytest on every push/PR, satisfying the Phase 0 task "Add basic CI running pytest."

**Expected Outcomes:**
- `.github/workflows/test.yml` triggers on push and pull_request
- Runs on `ubuntu-latest`, Python 3.11
- Steps: checkout, setup-python, `pip install -e ".[dev]"`, `pytest`
- Placeholder `.github/workflows/agentlint.yml` exists (Phase 10 will populate it) with a `# TODO: Phase 10` comment

**Files to create:**
```
.github/workflows/test.yml
.github/workflows/agentlint.yml   ← placeholder only
```

**Relevant Context:** §20 Phase 10, §29 Repository checklist (Tests passing)

**Status:** [ ] pending

---

### Sub-Task H — PROGRESS.md

**Intent:** Create the mandatory `PROGRESS.md` phase tracker as required by §21 Rule 3.

**Expected Outcomes:**
- `PROGRESS.md` lists all phases (0–12) as checkboxes
- Phase 0 is marked `[ ]` (will be checked after all acceptance criteria pass)
- File includes sections for Commands Run, Tests, and Known Issues

**Files to create:**
```
PROGRESS.md
```

**Relevant Context:** §21 Rule 3, §21 Rule 4 (commit message: `feat: bootstrap AgentLint project`)

**Status:** [ ] pending

---

## Files Created/Modified Summary

| File | Action |
|---|---|
| `LICENSE` | create |
| `README.md` | create |
| `CONTRIBUTING.md` | create |
| `.gitignore` | create |
| `PROGRESS.md` | create |
| `pyproject.toml` | create |
| `requirements.txt` | create |
| `app.py` | create |
| `agentlint/__init__.py` | create |
| `agentlint/cli.py` | create |
| `agentlint/config.py` | create |
| `agentlint/models.py` | create (stub) |
| `agentlint/discovery/__init__.py` … (6 files) | create (stubs) |
| `agentlint/parsing/__init__.py` … (5 files) | create (stubs) |
| `agentlint/evidence/__init__.py` … (8 files) | create (stubs) |
| `agentlint/analysis/__init__.py` … (6 files) | create (stubs) |
| `agentlint/policy/__init__.py` … (5 files) | create (stubs) |
| `agentlint/validation/__init__.py` … (5 files) | create (stubs) |
| `agentlint/ui/__init__.py`, `components.py`, `view_models.py` | create (stubs) |
| `tests/__init__.py`, `tests/unit/__init__.py`, `tests/unit/test_smoke.py` | create |
| `tests/integration/__init__.py`, fixtures, golden `.gitkeep` | create |
| `demo_repos/*/gitkeep` (3) | create |
| `artifacts/screenshots/.gitkeep`, `artifacts/demo/.gitkeep` | create |
| `.github/workflows/test.yml` | create |
| `.github/workflows/agentlint.yml` | create (placeholder) |

**Not created in Phase 0 (reserved for later phases):**
- `.bob/commands/`, `.bob/skills/`, `.bob/modes/` — Phase 6
- `.agentlint/config.yaml` — Phase 1 (runtime config, not source)
- Any content in `demo_repos/` — Phase 5
- Full `agentlint/models.py` implementation — Phase 1

---

## Dependencies Required

### Runtime (pyproject.toml `[project.dependencies]`)
| Package | Reason |
|---|---|
| `streamlit` | Placeholder UI and eventual dashboard |
| `pyyaml` | Parse `.agentlint/config.yaml`, YAML instruction files |
| `typer` | CLI entry point |

### Development (pyproject.toml `[project.optional-dependencies.dev]`)
| Package | Reason |
|---|---|
| `pytest` | Test runner |
| `pytest-cov` | Coverage — expected by CI |

**tomllib** is Python 3.11 stdlib — no install required.  
**Do not add** `pydantic`, `rapidfuzz`, or `langchain` in Phase 0 — add only if a concrete need arises in a later phase (§22, §21 Rule 7).

---

## Tests Required

Phase 0 requires exactly one test:

**`tests/unit/test_smoke.py`**
- `import agentlint` succeeds without error
- `agentlint.__version__` is a non-empty string

That is the entire Phase 0 test suite. No Phase 1 tests are written here.

---

## Commands That Must Be Run (Verification)

After all files are created, run these commands to verify acceptance criteria:

```bash
pip install -e ".[dev]"      # must complete without error
pytest                        # must exit 0
streamlit run app.py          # must launch without error (Ctrl+C to stop)
agentlint                     # must print stub help/not-implemented and exit 0
```

---

## Acceptance Criteria (from AgentLintplan.md §Phase 0)

| Criterion | How Verified |
|---|---|
| Project installs | `pip install -e ".[dev]"` exits 0 |
| `pytest` can run | `pytest` exits 0 (smoke test passes) |
| `streamlit run app.py` launches placeholder UI | command runs without error |
| MIT license exists | `LICENSE` file present with MIT text |
| Bob `/init` completed | **Manual step** — must be run in Bob IDE; commit resulting context files |
| Public-repo-safe: no secrets | No `.env`, API keys, or tokens in any committed file |

> **Note on Bob `/init`:** This is an interactive IDE action, not a script command. The plan assumes the developer runs `/init` in the Bob IDE after Phase 0 files are committed, then commits any Bob-generated context files (AGENTS.md updates, etc.). This plan does not simulate or fake this step.

---

## Risks and Conflicts with Existing Code

| Risk | Detail | Mitigation |
|---|---|---|
| `AGENTS.md` already exists | The file was created before Phase 0. Running Bob `/init` may regenerate or overwrite it. | Keep the existing `AGENTS.md` unless Bob `/init` produces a better version; commit whichever is more complete. |
| `.bob/` already has `rules-agent/`, `rules-ask/`, `rules-plan/` | These exist from the AGENTS.md creation step. The spec's `.bob/` structure adds `commands/`, `skills/`, `modes/` (Phase 6). | No conflict — Phase 0 does not touch `.bob/`. Phase 6 adds the new subdirectories. |
| No `pyproject.toml` dev extras group yet | CI uses `pip install -e ".[dev]"` — if `[dev]` extras aren't defined, CI breaks. | Define `[project.optional-dependencies] dev = [...]` in `pyproject.toml`. |
| `tomllib` is stdlib only on Python 3.11+ | If someone runs on 3.10, imports will fail. | Set `requires-python = ">=3.11"` in `pyproject.toml` and document this in README. |
| Streamlit placeholder may show import errors | If `app.py` imports `agentlint` submodules before stubs exist, it crashes. | `app.py` must not import any `agentlint` submodule in Phase 0 — pure Streamlit only. |
| CI `agentlint.yml` must not run before Phase 10 | Creating it as a real workflow now would fail CI. | Create it as a placeholder with only a comment, no jobs defined, or gate it with `if: false`. |
