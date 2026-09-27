# Phase 2 Plan — Repository Truth / Evidence Engine

## Overview

Phase 2 builds the deterministic evidence engine that answers: *"What does the
repository actually contain?"*  It detects package managers, test frameworks,
lint/format tools, commands, runtime versions, and the repository path
inventory — all without calling Bob.  The results become the ground truth
against which instruction rules are later validated in Phase 4.

**Definition of Done (from spec §Phase 2):**

> For the `inconsistent-js-repo` demo repository, AgentLint correctly
> identifies pnpm, Vitest, the test command, lint/build commands, and
> relevant paths.

Output: `.agentlint/evidence.json` written by `agentlint scan`.

---

## Existing State

| Item | Status |
|---|---|
| `agentlint/evidence/package_manager.py` | stub (one comment line) |
| `agentlint/evidence/testing.py` | stub |
| `agentlint/evidence/linting.py` | stub |
| `agentlint/evidence/runtime.py` | stub |
| `agentlint/evidence/commands.py` | stub |
| `agentlint/evidence/paths.py` | stub |
| `agentlint/evidence/repository_truth.py` | stub |
| `agentlint/evidence/__init__.py` | stub |
| `agentlint/discovery/repo_files.py` | stub |
| `agentlint/cli.py` | Phase 1 complete: scan → sources → scan.json |
| `demo_repos/inconsistent-js-repo/` | empty (only `.gitkeep`) |
| `demo_repos/single-agent-stale-repo/` | CLAUDE.md + package.json (minimal) |
| `demo_repos/clean-repo/` | empty (only `.gitkeep`) |

---

## Sub-Tasks

---

### Sub-Task A — Repository File Index (`agentlint/discovery/repo_files.py`)

**Intent:** Implement a lightweight function that indexes the files present in a
repository.  This is the foundation for:
- The **path detector** (do referenced paths exist?)
- CI evidence (does `.github/workflows/*.yml` exist?)
- Other detectors that need to check file presence quickly.

**Expected Outcomes:**
- `list_repo_files(repo_path: Path, max_depth: int = 6) -> list[Path]` returns
  every regular file under `repo_path`, up to `max_depth` levels, skipping
  common noise directories (`.git`, `node_modules`, `__pycache__`, `.venv`,
  `dist`, `build`, `.agentlint`).
- Function is deterministic (sorted output).
- Returns paths relative to `repo_path`.
- Handles permission errors without raising (skips unreadable entries).

**Relevant Context:** §8.2 Paths, §Phase 2 Path Detector.

**Status:** [ ] pending

---

### Sub-Task B — Package Manager Detector (`agentlint/evidence/package_manager.py`)

**Intent:** Determine which package manager the repository actually uses.
Evidence sources are checked in priority order; all evidence items are returned
(not just the winner) so Phase 4 can detect instruction-vs-repo mismatches.

**Expected Outcomes:**
- `detect_package_manager(repo_path: Path) -> list[RepositoryEvidence]`
- Priority order:
  1. `package.json` → `packageManager` field (`strong`)
  2. `pnpm-lock.yaml` exists → pnpm (`strong`)
  3. `yarn.lock` exists → yarn (`strong`)
  4. `package-lock.json` exists → npm (`strong`)
  5. `bun.lock` / `bun.lockb` exists → bun (`strong`)
- CI `.github/workflows/*.yml` commands mentioning `pnpm`/`yarn`/`npm`/`bun` →
  `medium` strength evidence
- Each detected item becomes a separate `RepositoryEvidence` with:
  - `category="package_manager"`, `key="package_manager"`, `value=<name>`,
  - `source_path=<file>`, `source_locator=<json-field or None>`,
  - `strength=<strong|medium>`, `explanation=<human-readable>`
- If evidence conflicts (e.g., `packageManager: pnpm` but `package-lock.json`
  also exists), **return both** — never discard conflicting evidence.
- Pure Python + `json`/`pathlib` stdlib — no external deps.

**Relevant Context:** §8.2 Package manager, §Phase 2 Package Manager Detector,
§13.3 RepositoryEvidence, §4.3 Deterministic checks.

**Status:** [ ] pending

---

### Sub-Task C — Test Framework Detector (`agentlint/evidence/testing.py`)

**Intent:** Detect which test framework the repository actually uses.

**Expected Outcomes:**
- `detect_test_framework(repo_path: Path) -> list[RepositoryEvidence]`
- Evidence sources (all `category="test_framework"`, `key="test_framework"`):
  - `package.json` `devDependencies` / `dependencies` containing:
    - `vitest` → `strong`
    - `jest` / `@jest/core` → `strong`
    - `playwright` / `@playwright/test` → `strong`
    - `cypress` → `strong`
  - `package.json` scripts containing `vitest`/`jest`/`playwright`/`cypress` →
    `medium`
  - Config files: `vitest.config.*`, `jest.config.*`, `cypress.config.*`,
    `playwright.config.*` exist → `strong`
  - `pyproject.toml` contains `pytest` in dependencies or `[tool.pytest.*]`
    section → `strong` (Python)
  - `pytest.ini`, `setup.cfg` with `[tool:pytest]` section exist → `strong`
  - CI commands mentioning `pytest`/`vitest`/`jest` → `medium`

**Relevant Context:** §8.2 Test framework, §Phase 2 Test Framework Detector.

**Status:** [ ] pending

---

### Sub-Task D — Commands Detector (`agentlint/evidence/commands.py`)

**Intent:** Extract the canonical command strings the repository defines for
install, test, lint, build, and format.

**Expected Outcomes:**
- `detect_commands(repo_path: Path) -> list[RepositoryEvidence]`
- Each evidence item: `category="commands"`, `key=<command_type>`,
  `value=<full command string>`, e.g.
  `key="test"`, `value="vitest run"`.
- Sources (in priority):
  1. `package.json` `scripts` → `strong`
     - Recognise script names: `test`, `lint`, `build`, `format`,
       `dev`, `start`, `install` (and prefixed variants like `test:unit`)
  2. `pyproject.toml` `[tool.taskipy.tasks]` or `[project.scripts]` → `strong`
  3. `Makefile` targets (simple parsing: lines matching `^<target>:`) → `medium`
  4. CI `.github/workflows/*.yml` `run:` steps → `medium`
- No shell execution — only static parsing.

**Relevant Context:** §8.2 Commands, §Phase 2 Commands Detector.

**Status:** [ ] pending

---

### Sub-Task E — Lint/Format Detector (`agentlint/evidence/linting.py`)

**Intent:** Detect which lint/format tools the repository actually uses.

**Expected Outcomes:**
- `detect_linting(repo_path: Path) -> list[RepositoryEvidence]`
- All items: `category="linting"`, `key="linter"` or `key="formatter"`,
  `value=<tool name>`.
- Evidence sources:
  - `package.json` devDependencies: `eslint` → `strong`, `prettier` → `strong`
  - Config files: `.eslintrc*`, `eslint.config.*` → `strong`,
    `.prettierrc*`, `prettier.config.*` → `strong`
  - `pyproject.toml` `[tool.ruff]` section or `ruff` dependency → `strong`
  - `pyproject.toml` `[tool.black]` section or `black` dependency → `strong`
  - `ruff.toml` / `.ruff.toml` exists → `strong`
  - CI commands mentioning `eslint`/`prettier`/`ruff`/`black` → `medium`

**Relevant Context:** §8.2 Lint/format, §Phase 2 Lint/Format Detector.

**Status:** [ ] pending

---

### Sub-Task F — Runtime Detector (`agentlint/evidence/runtime.py`)

**Intent:** Detect the language and runtime version the repository targets.

**Expected Outcomes:**
- `detect_runtime(repo_path: Path) -> list[RepositoryEvidence]`
- All items: `category="runtime"`.
- Node version evidence (`key="node_version"`):
  - `.nvmrc` exists → read content → `strong`
  - `.node-version` exists → read content → `strong`
  - `package.json` `engines.node` field → `strong`
- Python version evidence (`key="python_version"`):
  - `.python-version` exists → read content → `strong`
  - `pyproject.toml` `requires-python` field → `strong`
  - `pyproject.toml` `[tool.poetry.dependencies].python` → `strong`
- Language detection (`key="language"`):
  - `package.json` exists and `*.ts` / `*.js` files found → `"typescript"` /
    `"javascript"` as `weak` (just a hint — not authoritative)
  - `pyproject.toml` / `setup.py` / `*.py` files found → `"python"` as `weak`

**Relevant Context:** §8.2 Runtime/language, §Phase 2 Runtime Detector.

**Status:** [ ] pending

---

### Sub-Task G — Path Detector (`agentlint/evidence/paths.py`)

**Intent:** Build a repository path inventory so Phase 4 can validate paths
referenced in instruction files.  Phase 2 only builds the index; Phase 4 uses it.

**Expected Outcomes:**
- `detect_paths(repo_path: Path) -> list[RepositoryEvidence]`
- Returns one `RepositoryEvidence` per notable top-level directory or
  conventional path found:
  - `category="paths"`, `key="directory"`, `value=<relative path>`,
    `strength="strong"`.
  - Notable paths to include: any direct subdirectory of `repo_root` that
    exists, plus well-known nested paths like `src/`, `tests/`, `test/`,
    `dist/`, `build/`, `.github/`.
- A helper `path_exists_in_repo(repo_path: Path, query: str) -> bool` is also
  exported — Phase 4 uses it to check whether an instruction-referenced path
  is real.
- Does **not** recursively enumerate all files (that is `list_repo_files`'s job).

**Relevant Context:** §8.2 Paths, §Phase 2 Path Detector, §Phase 4 F03 Stale Paths.

**Status:** [ ] pending

---

### Sub-Task H — Repository Truth Aggregator (`agentlint/evidence/repository_truth.py`)

**Intent:** Single entry point that runs all detectors and returns the
consolidated evidence list, plus writes `evidence.json`.

**Expected Outcomes:**
- `collect_evidence(repo_path: Path) -> list[RepositoryEvidence]` calls all
  six detectors in order: package_manager, test_framework, commands, linting,
  runtime, paths.
- Returns the combined list (no deduplication — callers need all evidence).
- IDs are auto-assigned: `ev-<category>-<zero-padded-index>` e.g. `ev-pm-001`.
- `write_evidence_json(repo_path: Path, evidence: list[RepositoryEvidence]) -> Path`
  writes `.agentlint/evidence.json` and returns the output path.
- `evidence.json` schema:
  ```json
  {
    "agentlint_version": "0.1.0",
    "repo_path": "...",
    "evidence": [ { ...RepositoryEvidence fields... } ]
  }
  ```

**Relevant Context:** §14 Output Files, §Phase 2 Output.

**Status:** [ ] pending

---

### Sub-Task I — `__init__.py` public API (`agentlint/evidence/__init__.py`)

**Intent:** Export the top-level API so callers use
`from agentlint.evidence import collect_evidence` cleanly.

**Expected Outcomes:**
- Re-exports: `collect_evidence`, `write_evidence_json` from `repository_truth`.
- File is a real module, not a stub.

**Status:** [ ] pending

---

### Sub-Task J — Demo Repository A Seed (`demo_repos/inconsistent-js-repo/`)

**Intent:** Create a minimal but realistic JavaScript repository fixture so the
Phase 2 Definition of Done check can run.

The spec (§Phase 5 Demo A) says the *actual* repo truth must be pnpm + Vitest +
ESLint.  Phase 2 only needs the evidence collection to work correctly; Phase 5
adds the instruction file problems.  A minimal seed is enough for the
acceptance check.

**Expected Outcomes:**
- `demo_repos/inconsistent-js-repo/package.json` — pnpm packageManager,
  Vitest + ESLint + Prettier devDependencies, test/lint/build scripts.
- `demo_repos/inconsistent-js-repo/pnpm-lock.yaml` — minimal valid lockfile
  (just the header/lockfile version is enough; we don't need a real lockfile).
- `demo_repos/inconsistent-js-repo/src/index.ts` — a few lines (so `src/` path
  is real).
- Remove `.gitkeep` when adding real files.

**Relevant Context:** §Phase 2 Definition of Done, §Phase 5 Demo Repository A.

**Status:** [ ] pending

---

### Sub-Task K — CLI Extension (`agentlint/cli.py`)

**Intent:** Extend the `scan` command to run evidence collection after
discovery and write `evidence.json` to `.agentlint/`.

**Expected Outcomes:**
- After writing `scan.json`, the `scan` command:
  1. Calls `collect_evidence(path)`.
  2. Assigns sequential IDs to evidence items.
  3. Prints a brief evidence summary to stdout (e.g.
     `"Evidence: 7 item(s) collected — package_manager: pnpm, test_framework: vitest, ..."`).
  4. Writes `.agentlint/evidence.json` via `write_evidence_json`.
- No new CLI flags needed.
- Phase 1 tests must continue to pass.

**Relevant Context:** §15 `agentlint scan`, §14 Output Files.

**Status:** [ ] pending

---

### Sub-Task L — Tests

**Intent:** Add unit tests for every Phase 2 module. All tests use `tmp_path`
and stdlib only — no network, no real subprocess.

**Test files to create:**

#### `tests/unit/test_package_manager.py`

| Test | Scenario |
|---|---|
| `test_pnpm_lock_detected` | `pnpm-lock.yaml` → pnpm strong |
| `test_package_json_package_manager_field` | `packageManager: pnpm@9` → pnpm strong |
| `test_npm_lock_detected` | `package-lock.json` → npm strong |
| `test_yarn_lock_detected` | `yarn.lock` → yarn strong |
| `test_no_package_manager_evidence` | empty dir → empty list |
| `test_conflicting_evidence_both_returned` | `packageManager: pnpm` + `package-lock.json` → both items returned |
| `test_ci_medium_evidence` | `.github/workflows/ci.yml` with `pnpm install` → medium evidence |

#### `tests/unit/test_testing.py`

| Test | Scenario |
|---|---|
| `test_vitest_in_devdeps` | package.json devDependencies.vitest → strong |
| `test_jest_in_devdeps` | package.json devDependencies.jest → strong |
| `test_vitest_config_file` | `vitest.config.ts` exists → strong |
| `test_pytest_in_pyproject` | `pyproject.toml` with pytest dep → strong |
| `test_pytest_ini_exists` | `pytest.ini` exists → strong |
| `test_no_test_framework` | empty dir → empty list |

#### `tests/unit/test_commands.py`

| Test | Scenario |
|---|---|
| `test_package_json_scripts` | `scripts.test = "vitest run"` → test command strong |
| `test_package_json_multiple_scripts` | build + lint + format → multiple items |
| `test_no_scripts` | package.json without scripts → empty list |
| `test_pyproject_taskipy` | `[tool.taskipy.tasks]` → commands extracted |
| `test_makefile_targets` | simple `test:` target → medium evidence |

#### `tests/unit/test_linting.py`

| Test | Scenario |
|---|---|
| `test_eslint_in_devdeps` | package.json devDependencies.eslint → strong |
| `test_prettier_config_file` | `.prettierrc` exists → strong |
| `test_ruff_in_pyproject` | `[tool.ruff]` section → strong |
| `test_black_in_pyproject` | `[tool.black]` section → strong |
| `test_no_linting_evidence` | empty dir → empty list |

#### `tests/unit/test_runtime.py`

| Test | Scenario |
|---|---|
| `test_nvmrc_detected` | `.nvmrc` with `20` → node_version strong |
| `test_node_version_file` | `.node-version` → strong |
| `test_package_engines_node` | `engines.node = ">=18"` → strong |
| `test_python_version_file` | `.python-version` with `3.11` → strong |
| `test_pyproject_requires_python` | `requires-python = ">=3.11"` → strong |
| `test_no_runtime_evidence` | empty dir → empty list |

#### `tests/unit/test_paths.py`

| Test | Scenario |
|---|---|
| `test_src_directory_detected` | `src/` dir exists → evidence item |
| `test_tests_directory_detected` | `tests/` dir exists → evidence item |
| `test_nested_path_detected` | `.github/` dir exists → evidence item |
| `test_path_exists_in_repo_true` | path present → True |
| `test_path_exists_in_repo_false` | path absent → False |
| `test_no_directories` | empty dir → empty list |

#### `tests/unit/test_repository_truth.py`

| Test | Scenario |
|---|---|
| `test_collect_evidence_empty_repo` | empty dir → empty list (no crashes) |
| `test_collect_evidence_js_repo` | package.json with pnpm/vitest → both detected |
| `test_ids_are_assigned` | all evidence items have non-empty `id` |
| `test_write_evidence_json_creates_file` | file created at correct path |
| `test_write_evidence_json_schema` | JSON has `agentlint_version` + `evidence` |
| `test_collect_evidence_returns_all_categories` | full fixture → multiple categories in result |

**Fixtures:** All tests use `tmp_path` + inline file creation. No permanent test
fixtures added to `tests/fixtures/` in Phase 2.

**Relevant Context:** §Phase 2 Tests, §21 Rule 2.

**Status:** [ ] pending

---

### Sub-Task M — PROGRESS.md Update

**Intent:** Mark Phase 2 complete after all criteria pass.

**Expected Outcomes:**
- `- [x] Phase 2` in the checklist.
- Phase 2 section with: files created, commands run, test results, acceptance
  criteria status.

**Status:** [ ] pending

---

## Files Created / Modified

| File | Action | Notes |
|---|---|---|
| `agentlint/discovery/repo_files.py` | replace stub | `list_repo_files()` |
| `agentlint/evidence/package_manager.py` | replace stub | `detect_package_manager()` |
| `agentlint/evidence/testing.py` | replace stub | `detect_test_framework()` |
| `agentlint/evidence/commands.py` | replace stub | `detect_commands()` |
| `agentlint/evidence/linting.py` | replace stub | `detect_linting()` |
| `agentlint/evidence/runtime.py` | replace stub | `detect_runtime()` |
| `agentlint/evidence/paths.py` | replace stub | `detect_paths()` + `path_exists_in_repo()` |
| `agentlint/evidence/repository_truth.py` | replace stub | `collect_evidence()` + `write_evidence_json()` |
| `agentlint/evidence/__init__.py` | replace stub | public re-exports |
| `agentlint/cli.py` | extend | add evidence collection + evidence.json output to `scan` |
| `demo_repos/inconsistent-js-repo/package.json` | create | pnpm + vitest + eslint fixture |
| `demo_repos/inconsistent-js-repo/pnpm-lock.yaml` | create | minimal lockfile header |
| `demo_repos/inconsistent-js-repo/src/index.ts` | create | minimal TS file |
| `tests/unit/test_package_manager.py` | create | 7 tests |
| `tests/unit/test_testing.py` | create | 6 tests |
| `tests/unit/test_commands.py` | create | 5 tests |
| `tests/unit/test_linting.py` | create | 5 tests |
| `tests/unit/test_runtime.py` | create | 6 tests |
| `tests/unit/test_paths.py` | create | 6 tests |
| `tests/unit/test_repository_truth.py` | create | 6 tests |
| `PROGRESS.md` | update | Phase 2 section |

**Not modified in Phase 2:**
- `agentlint/models.py` — no changes needed.
- `agentlint/config.py` — no changes needed.
- `agentlint/discovery/instruction_sources.py` — no changes needed.
- Any `parsing/`, `analysis/`, `policy/`, `validation/`, `ui/` stubs — later phases.
- `app.py` — Phase 9.
- `demo_repos/clean-repo/` — Phase 5.

---

## Dependencies Required

No new dependencies needed. All parsing is pure Python stdlib:
- `json` — parse `package.json`.
- `pathlib` — file presence checks.
- `tomllib` (stdlib, Python 3.11+) — parse `pyproject.toml`.
- `re` — simple CI YAML line-level scanning.
- `pyyaml` — already installed; used for CI workflow file scanning
  (`.github/workflows/*.yml`).

---

## Commands That Must Be Run

```bash
pip install -e ".[dev]"           # re-install after any pyproject changes
pytest --tb=short -v              # all tests must pass (41 existing + ~41 new)
agentlint scan demo_repos/inconsistent-js-repo
                                  # must identify: pnpm, vitest, eslint,
                                  # test/build/lint commands, src/ path
                                  # must create demo_repos/inconsistent-js-repo/.agentlint/evidence.json
agentlint --help                  # must still work
```

---

## Acceptance Criteria (from §Phase 2 Definition of Done)

For `demo_repos/inconsistent-js-repo`, `agentlint scan` must correctly identify:

| Evidence | Expected |
|---|---|
| Package manager | pnpm |
| Test framework | Vitest |
| Test command | `vitest run` (or equivalent from scripts) |
| Lint command | `eslint` (from scripts) |
| Build command | `tsc` or similar |
| Path `src/` | detected as existing directory |

---

## Risks and Conflicts

| Risk | Detail | Mitigation |
|---|---|---|
| **`tomllib` vs `tomli`** | `tomllib` is stdlib on Python 3.11+. The project targets ≥3.11 (currently runs 3.12). No issue. | Use `import tomllib` directly; no fallback needed. |
| **CI YAML parsing scope** | Spec says "do not implement a full YAML workflow interpreter". Only extract `run:` step strings via line-level regex scan, not full YAML parse. | Use `re` + line scan on raw text, not PyYAML structure walk. |
| **Conflicting evidence** | Multiple package-manager signals may exist (e.g., `packageManager: pnpm` in `package.json` + `package-lock.json`). Spec says: "preserve all evidence instead of guessing." | Return all items; never pick one winner inside the detector. |
| **`paths.py` scope creep** | Path detector could become a full file indexer. Phase 2 only builds the index; Phase 4 uses it for validation. | Limit to top-level directories + known nested paths. Full traversal is `list_repo_files`. |
| **CLI scan order** | `evidence.json` must be written after `scan.json`. The `scan` command must remain a single coherent pass, not two separate commands. | Extend the existing `scan()` function in `cli.py`; add evidence step after sources step. |
| **ID assignment** | `RepositoryEvidence.id` must be non-empty and stable per-run. | Assign `ev-<short_category>-<three_digit_index>` in `collect_evidence()` after all detectors run. |
| **Windows path separators in `evidence.json`** | Same issue as `scan.json` in Phase 1. `Path` on Windows uses backslashes. | Use `source_path.as_posix()` or store as `str()` consistently — document the choice. |
| **Phase 1 smoke tests** | Phase 1 CLI tests only call `import agentlint` and `__version__`. They will not break. Existing discovery tests use `tmp_path` and won't be affected. | No action needed; all 41 existing tests must still pass. |
| **`repo_files.py` is still imported by nothing in Phase 1** | It's a new stub replacement — no existing code imports it. | Import it from `paths.py` (Sub-Task G uses `list_repo_files` internally). |

---

*Ready for implementation.*
