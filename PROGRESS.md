# AgentLint — Implementation Progress

Tracks phase completion per `AgentLintplan.md §21 Rule 3`.

## Phase Checklist

- [x] Phase 0 — Scope Lock, Repository Setup, and Hackathon Compliance
- [x] Phase 1 — Domain Models and Instruction Discovery
- [x] Phase 2 — Repository Truth / Evidence Engine
- [x] Phase 3 — Instruction Parsing and Normalization
- [x] Phase 4 — Deterministic Finding Engine
- [x] Phase 5 — Sample Repositories and Golden Scenarios
- [ ] Phase 6 — Bob Skill, Custom Mode, Slash Commands, and Semantic Audit
- [ ] Phase 7 — Canonical Policy Compiler and Repair Plan
- [ ] Phase 8 — Verification Engine
- [ ] Phase 9 — Streamlit UI
- [ ] Phase 10 — GitHub / CI Integration
- [ ] Phase 11 — Testing, Hardening, and Quality
- [ ] Phase 12 — Deployment, Documentation, Demo, and Submission

---

## Phase 0 — Scope Lock, Repository Setup, and Hackathon Compliance

**Status:** ✅ Complete

### Goal

Create the project skeleton and lock the MVP so the coding agent does not overbuild.

### Files Created

| File | Notes |
|---|---|
| `LICENSE` | MIT, 2024–2026, AgentLint Contributors |
| `README.md` | Placeholder with section headings |
| `CONTRIBUTING.md` | Minimal placeholder |
| `.gitignore` | Python + pytest + Streamlit + `.agentlint/` |
| `pyproject.toml` | `pip install -e ".[dev]"` entry point |
| `requirements.txt` | Runtime deps mirror |
| `app.py` | Streamlit placeholder — no business logic |
| `agentlint/__init__.py` | `__version__ = "0.1.0"` |
| `agentlint/cli.py` | Stub CLI, exits 0 |
| `agentlint/config.py` | Empty stub |
| `agentlint/models.py` | Empty stub |
| `agentlint/discovery/__init__.py` | Empty stub |
| `agentlint/discovery/instruction_sources.py` | Empty stub |
| `agentlint/discovery/repo_files.py` | Empty stub |
| `agentlint/parsing/__init__.py` | Empty stub |
| `agentlint/parsing/markdown_rules.py` | Empty stub |
| `agentlint/parsing/json_parser.py` | Empty stub |
| `agentlint/parsing/yaml_parser.py` | Empty stub |
| `agentlint/parsing/normalization.py` | Empty stub |
| `agentlint/evidence/__init__.py` | Empty stub |
| `agentlint/evidence/package_manager.py` | Empty stub |
| `agentlint/evidence/testing.py` | Empty stub |
| `agentlint/evidence/linting.py` | Empty stub |
| `agentlint/evidence/runtime.py` | Empty stub |
| `agentlint/evidence/commands.py` | Empty stub |
| `agentlint/evidence/paths.py` | Empty stub |
| `agentlint/evidence/repository_truth.py` | Empty stub |
| `agentlint/analysis/__init__.py` | Empty stub |
| `agentlint/analysis/deterministic_rules.py` | Empty stub |
| `agentlint/analysis/conflicts.py` | Empty stub |
| `agentlint/analysis/duplicates.py` | Empty stub |
| `agentlint/analysis/scoring.py` | Empty stub |
| `agentlint/analysis/report_builder.py` | Empty stub |
| `agentlint/policy/__init__.py` | Empty stub |
| `agentlint/policy/schema.py` | Empty stub |
| `agentlint/policy/compiler.py` | Empty stub |
| `agentlint/policy/diff.py` | Empty stub |
| `agentlint/policy/adapters.py` | Empty stub |
| `agentlint/validation/__init__.py` | Empty stub |
| `agentlint/validation/structural.py` | Empty stub |
| `agentlint/validation/commands.py` | Empty stub |
| `agentlint/validation/evidence_check.py` | Empty stub |
| `agentlint/validation/runner.py` | Empty stub |
| `agentlint/ui/__init__.py` | Empty stub |
| `agentlint/ui/components.py` | Empty stub |
| `agentlint/ui/view_models.py` | Empty stub |
| `tests/__init__.py` | Test package |
| `tests/unit/__init__.py` | Unit test package |
| `tests/unit/test_smoke.py` | Phase 0 smoke tests |
| `tests/integration/__init__.py` | Integration test package |
| `tests/fixtures/.gitkeep` | Empty fixture dir |
| `tests/golden/.gitkeep` | Empty golden dir |
| `demo_repos/inconsistent-js-repo/.gitkeep` | Phase 5 placeholder |
| `demo_repos/single-agent-stale-repo/.gitkeep` | Phase 5 placeholder |
| `demo_repos/clean-repo/.gitkeep` | Phase 5 placeholder |
| `artifacts/screenshots/.gitkeep` | Submission placeholder |
| `artifacts/demo/.gitkeep` | Submission placeholder |
| `.github/workflows/test.yml` | CI: pytest on push/PR |
| `.github/workflows/agentlint.yml` | Placeholder for Phase 10 |
| `PROGRESS.md` | This file |

### Commands Run

```bash
pip install -e ".[dev]"
pytest
agentlint
```

### Tests

| Test | Result |
|---|---|
| `tests/unit/test_smoke.py::test_import_succeeds` | ✅ PASSED |
| `tests/unit/test_smoke.py::test_version_is_set` | ✅ PASSED |
| `tests/unit/test_smoke.py::test_version_format` | ✅ PASSED |

```
============================= test session starts =============================
platform win32 -- Python 3.12.7, pytest-8.4.2, pluggy-1.6.0
collected 3 items

tests/unit/test_smoke.py::test_import_succeeds PASSED    [ 33%]
tests/unit/test_smoke.py::test_version_is_set PASSED     [ 66%]
tests/unit/test_smoke.py::test_version_format PASSED     [100%]

============================== 3 passed in 0.03s ==============================
```

### Acceptance Criteria

| Criterion | Status |
|---|---|
| Project installs (`pip install -e ".[dev]"` exits 0) | ✅ done |
| `pytest` exits 0 (3 tests pass) | ✅ done |
| `streamlit run app.py` launches placeholder UI | ✅ verified (syntax + import OK) |
| MIT license exists | ✅ done |
| Bob `/init` completed | ✅ already done (`.bob/` rules exist) |
| Public-repo-safe: no secrets | ✅ done |

### Known Issues

- Python 3.12 is in use (spec requires ≥3.11 — 3.12 satisfies this constraint).
- `pyproject.toml` `requires-python = ">=3.11"` correctly set; `tomllib` is stdlib on 3.11+.

---

*Updated after Phase 0 implementation.*

---

## Phase 1 — Domain Models and Instruction Discovery

**Status:** ✅ Complete

### Goal

Implement all six domain model dataclasses and deterministic instruction source discovery.

### Files Created / Modified

| File | Action | Notes |
|---|---|---|
| `agentlint/models.py` | replaced stub | 6 dataclasses: `InstructionSource`, `InstructionRule`, `RepositoryEvidence`, `Finding`, `CanonicalPolicy`, `ValidationResult` + `to_dict()` helpers |
| `agentlint/config.py` | replaced stub | `AgentLintConfig` dataclass, `load_config()`, `AgentLintConfigError` |
| `agentlint/discovery/instruction_sources.py` | replaced stub | `discover_sources()` with stable ordering |
| `agentlint/cli.py` | replaced stub | Typer app with `scan` and `demo` subcommands |
| `demo_repos/single-agent-stale-repo/CLAUDE.md` | created | Minimal stale fixture (npm vs pnpm/vitest mismatch scenario) |
| `demo_repos/single-agent-stale-repo/package.json` | created | Minimal JS fixture (pnpm, vitest, typescript) |
| `tests/unit/test_models.py` | created | 19 tests covering all 6 dataclasses |
| `tests/unit/test_discovery.py` | created | 14 tests covering all discovery scenarios |
| `tests/unit/test_config.py` | created | 7 tests covering config loader |

### Commands Run

```bash
pip install -e ".[dev]"
pytest --tb=short -v
agentlint --help
agentlint scan --help
agentlint scan demo_repos/single-agent-stale-repo
```

### Test Results

| Test | Result |
|---|---|
| `tests/unit/test_config.py` (7 tests) | ✅ PASSED |
| `tests/unit/test_discovery.py` (14 tests) | ✅ PASSED |
| `tests/unit/test_models.py` (19 tests) | ✅ PASSED |
| `tests/unit/test_smoke.py` (3 tests) | ✅ PASSED |
| **Total** | **41 passed in 0.10s** |

```
============================= test session starts =============================
platform win32 -- Python 3.12.7, pytest-8.4.2, pluggy-1.6.0
collected 41 items

tests/unit/test_config.py::test_no_config_file PASSED
tests/unit/test_config.py::test_extra_paths_loaded PASSED
tests/unit/test_config.py::test_malformed_yaml_raises PASSED
tests/unit/test_config.py::test_empty_yaml_returns_defaults PASSED
tests/unit/test_config.py::test_non_mapping_yaml_raises PASSED
tests/unit/test_config.py::test_extra_paths_not_list_raises PASSED
tests/unit/test_config.py::test_config_ignores_unknown_keys PASSED
tests/unit/test_discovery.py::test_zero_instruction_files PASSED
tests/unit/test_discovery.py::test_one_file_agents_md PASSED
tests/unit/test_discovery.py::test_one_file_claude_md PASSED
tests/unit/test_discovery.py::test_multiple_files PASSED
tests/unit/test_discovery.py::test_bob_mode_files PASSED
tests/unit/test_discovery.py::test_copilot_instructions PASSED
tests/unit/test_discovery.py::test_extra_instruction_paths_config PASSED
tests/unit/test_discovery.py::test_missing_configured_path PASSED
tests/unit/test_discovery.py::test_extra_paths_alphabetical_order PASSED
tests/unit/test_discovery.py::test_content_hash_set PASSED
tests/unit/test_discovery.py::test_content_hash_empty_when_missing PASSED
tests/unit/test_discovery.py::test_stable_ordering PASSED
tests/unit/test_discovery.py::test_total_count_with_extras PASSED
tests/unit/test_discovery.py::test_source_to_dict_round_trip PASSED
tests/unit/test_models.py::test_instruction_source_fields PASSED
tests/unit/test_models.py::test_instruction_source_to_dict PASSED
tests/unit/test_models.py::test_instruction_source_exists_false_empty_hash PASSED
tests/unit/test_models.py::test_instruction_rule_fields PASSED
tests/unit/test_models.py::test_instruction_rule_nullable_fields PASSED
tests/unit/test_models.py::test_repository_evidence_to_dict PASSED
tests/unit/test_models.py::test_repository_evidence_strength_values PASSED
tests/unit/test_models.py::test_finding_defaults PASSED
tests/unit/test_models.py::test_finding_explicit_status PASSED
tests/unit/test_models.py::test_finding_to_dict PASSED
tests/unit/test_models.py::test_finding_deterministic_flag PASSED
tests/unit/test_models.py::test_canonical_policy_fields PASSED
tests/unit/test_models.py::test_canonical_policy_to_dict PASSED
tests/unit/test_models.py::test_validation_result_fields PASSED
tests/unit/test_models.py::test_validation_result_nullable_command PASSED
tests/unit/test_models.py::test_validation_result_to_dict PASSED
tests/unit/test_models.py::test_dataclass_to_dict_utility PASSED
tests/unit/test_smoke.py::test_import_succeeds PASSED
tests/unit/test_smoke.py::test_version_is_set PASSED
tests/unit/test_smoke.py::test_version_format PASSED

============================== 41 passed in 0.10s ==============================
```

### Acceptance Criteria

| Criterion | Status |
|---|---|
| `agentlint scan demo_repos/single-agent-stale-repo` exits 0 | ✅ done |
| Reports exactly one instruction source (`CLAUDE.md`, exists=True) | ✅ done |
| Does not fail (no traceback) | ✅ done |
| All Phase 1 tests pass (41 total, 38 new) | ✅ done |
| Phase 0 smoke tests still pass | ✅ done |
| `scan.json` written to `demo_repos/single-agent-stale-repo/.agentlint/scan.json` | ✅ done |
| `agentlint --help` prints subcommand list | ✅ done |
| `agentlint scan --help` works | ✅ done |

### Known Issues

- Windows `cp1252` terminal encoding: em-dash (`—`) and Unicode check marks replaced with ASCII equivalents in CLI output. JSON output is unaffected (UTF-8).

---

*Updated after Phase 1 implementation.*

---

## Phase 2 — Repository Truth / Evidence Engine

**Status:** ✅ Complete

### Goal

Build deterministic evidence before semantic AI analysis.  All detectors
inspect repository files statically — no shell execution, no network.

### Files Created / Modified

| File | Action | Notes |
|---|---|---|
| `agentlint/discovery/repo_files.py` | replaced stub | `list_repo_files()` — sorted, depth-limited file index |
| `agentlint/evidence/package_manager.py` | replaced stub | `detect_package_manager()` — lockfiles, packageManager field, CI |
| `agentlint/evidence/testing.py` | replaced stub | `detect_test_framework()` — JS deps, config files, pyproject, CI |
| `agentlint/evidence/commands.py` | replaced stub | `detect_commands()` — package.json, pyproject taskipy, Makefile, CI |
| `agentlint/evidence/linting.py` | replaced stub | `detect_linting()` — ESLint, Prettier, Ruff, Black |
| `agentlint/evidence/runtime.py` | replaced stub | `detect_runtime()` — .nvmrc, .node-version, engines.node, .python-version, pyproject |
| `agentlint/evidence/paths.py` | replaced stub | `detect_paths()` + `path_exists_in_repo()` |
| `agentlint/evidence/repository_truth.py` | replaced stub | `collect_evidence()` + `write_evidence_json()` |
| `agentlint/evidence/__init__.py` | replaced stub | public re-exports |
| `agentlint/cli.py` | extended | evidence collection + evidence.json output in `scan` |
| `demo_repos/inconsistent-js-repo/package.json` | created | pnpm + vitest + eslint + prettier fixture |
| `demo_repos/inconsistent-js-repo/pnpm-lock.yaml` | created | minimal lockfile header |
| `demo_repos/inconsistent-js-repo/src/index.ts` | created | minimal TS source file |
| `tests/unit/test_package_manager.py` | created | 8 tests |
| `tests/unit/test_testing.py` | created | 7 tests |
| `tests/unit/test_commands.py` | created | 5 tests |
| `tests/unit/test_linting.py` | created | 6 tests |
| `tests/unit/test_runtime.py` | created | 6 tests |
| `tests/unit/test_paths.py` | created | 8 tests |
| `tests/unit/test_repository_truth.py` | created | 6 tests |

### Commands Run

```bash
pip install -e ".[dev]"
pytest --tb=short -v
agentlint scan demo_repos/inconsistent-js-repo
agentlint --help
```

### Test Results

| Test File | Tests | Result |
|---|---|---|
| `tests/unit/test_package_manager.py` | 8 | ✅ PASSED |
| `tests/unit/test_testing.py` | 7 | ✅ PASSED |
| `tests/unit/test_commands.py` | 5 | ✅ PASSED |
| `tests/unit/test_linting.py` | 6 | ✅ PASSED |
| `tests/unit/test_runtime.py` | 6 | ✅ PASSED |
| `tests/unit/test_paths.py` | 8 | ✅ PASSED |
| `tests/unit/test_repository_truth.py` | 6 | ✅ PASSED |
| Phase 1 tests (config, discovery, models, smoke) | 41 | ✅ PASSED |
| **Total** | **87 passed in 0.26s** | ✅ |

```
============================= test session info ==============================
platform win32 -- Python 3.12.7, pytest-8.4.2, pluggy-1.6.0
collected 87 items

87 passed in 0.26s
```

### Acceptance Criteria

| Criterion | Status |
|---|---|
| `inconsistent-js-repo` → package manager: pnpm | ✅ `ev-pm-001` (strong, packageManager field) + `ev-pm-002` (strong, lockfile) |
| `inconsistent-js-repo` → test framework: vitest | ✅ `ev-tf-001` (strong, devDependencies.vitest) |
| `inconsistent-js-repo` → test command: `vitest run` | ✅ `ev-cmd-002` (strong, scripts.test) |
| `inconsistent-js-repo` → lint command: `eslint src/` | ✅ `ev-cmd-003` (strong, scripts.lint) |
| `inconsistent-js-repo` → build command: `tsc` | ✅ `ev-cmd-001` (strong, scripts.build) |
| `inconsistent-js-repo` → path `src/` detected | ✅ `ev-path-002` (strong, directory index) |
| `evidence.json` written to `.agentlint/evidence.json` | ✅ done |
| `agentlint scan` still exits 0, still writes `scan.json` | ✅ done |
| All Phase 1 tests still pass | ✅ 41/41 |
| All Phase 2 tests pass | ✅ 46/46 new tests |
| Conflicting evidence preserved (not discarded) | ✅ tested in `test_conflicting_evidence_both_returned` |
| No new external dependencies | ✅ only stdlib (`json`, `tomllib`, `re`, `pathlib`) |

### Known Issues

- `.agentlint/` directory created inside `demo_repos/inconsistent-js-repo/` by `agentlint scan` shows up in the path detector output (`ev-path-001`).  This is expected behaviour — the directory genuinely exists after the first scan.  Phase 4 can filter it from stale-path checks if needed.

---

*Updated after Phase 2 implementation.*

---

## Phase 3 — Instruction Parsing and Normalization

**Status:** ✅ Complete

### Goal

Implement Layer 1 deterministic Markdown parser that turns raw instruction files into traceable `InstructionRule` objects with source file and line location.

### Files Created / Modified

| File | Action | Notes |
|---|---|---|
| `agentlint/parsing/markdown_rules.py` | replaced stub | `parse_markdown_blocks()` — splits MD into typed blocks with line numbers |
| `agentlint/parsing/normalization.py` | replaced stub | `normalize_blocks()` — keyword-based category + value detection |
| `agentlint/parsing/__init__.py` | replaced stub | `extract_rules()` + `write_rules_json()` public API |
| `agentlint/cli.py` | extended | Phase 3 rule extraction after evidence collection; writes `rules.json` |
| `tests/unit/test_parsing.py` | created | 38 tests covering all parsing components |

### Commands Run

```bash
pip install -e ".[dev]"
pytest --tb=short -v
agentlint scan demo_repos/single-agent-stale-repo
agentlint --help
```

### Test Results

| Test Class | Tests | Result |
|---|---|---|
| `TestParseMarkdownBlocks` (markdown_rules) | 15 | ✅ PASSED |
| `TestNormalizeBlocks` (normalization) | 15 | ✅ PASSED |
| `TestExtractRules` (parsing init) | 4 | ✅ PASSED |
| `TestWriteRulesJson` | 3 | ✅ PASSED |
| `TestExtractRulesRealFixture` | 1 | ✅ PASSED |
| Phase 1+2 tests | 87 | ✅ PASSED |
| **Total** | **125 passed in 0.28s** | ✅ |

```
============================= test session starts =============================
platform win32 -- Python 3.12.7, pytest-8.4.2, pluggy-1.6.0
collected 125 items

125 passed in 0.28s
```

### Acceptance Criteria

| Criterion | Status |
|---|---|
| `agentlint scan demo_repos/single-agent-stale-repo` exits 0 | ✅ no traceback |
| At least 1 rule extracted from CLAUDE.md | ✅ 18 rules extracted |
| `npm` detected as package_manager rule | ✅ `category=package_manager, value=npm` |
| `src/` detected as path reference | ✅ `category=paths, value=src/` |
| All rules have `extraction_method="deterministic"` | ✅ no "bob" entries |
| `rules.json` written to `.agentlint/rules.json` | ✅ file written |
| `rules.json` schema: `agentlint_version`, `repo_path`, `rules` | ✅ all top-level keys present |
| `linting` category detected (ESLint, Prettier) | ✅ `value=eslint`, `value=prettier` |
| Phase 1+2 tests still pass (87) | ✅ 87/87 — no regressions |
| New Phase 3 tests pass (38) | ✅ 38/38 all green |

### Implementation Notes

- **Layer 1 only** — all rules have `extraction_method="deterministic"`. Layer 2 (Bob semantic) is left for Phase 6.
- **Pattern ordering** — linting/test_framework patterns are checked before package_manager so mixed-signal rules like "Use ESLint: `npm run lint`" resolve to `linting` (the more specific category).
- **Relative path resolution** — `extract_rules(sources, repo_path=...)` accepts an optional `repo_path` to resolve the relative paths stored in `InstructionSource.path` by Phase 1 discovery.
- **Per-source ID namespace** — each instruction file gets its own counter (`rule-claude-001`, `rule-agents-001`) to avoid namespace collisions when multiple sources exist.
- **Confidence table** — `code_block=0.9`, `bullet/numbered=0.8`, `heading=0.7`, `paragraph=0.6`, no-keyword=`0.4`.

### Known Issues

None.

---

*Updated after Phase 3 implementation.*

---

## Phase 4 — Deterministic Finding Engine

**Status:** ✅ Complete

### Goal

Implement the deterministic lint engine that compares parsed instruction rules against
collected repository evidence to produce `Finding` objects, written to `.agentlint/findings.json`.
All findings are produced without LLM, Bob, or network access.

### Files Created / Modified

| File | Action | Notes |
|---|---|---|
| `agentlint/analysis/deterministic_rules.py` | replaced stub | F01, F02, F03, F04 detectors |
| `agentlint/analysis/duplicates.py` | replaced stub | F05 exact duplicate detector |
| `agentlint/analysis/__init__.py` | replaced stub | `run_deterministic_checks()` + `write_findings_json()` public API |
| `agentlint/analysis/conflicts.py` | replaced stub | Re-exports `detect_f01_cross_file_conflicts` |
| `agentlint/analysis/scoring.py` | replaced stub | `SEVERITY_ORDER` dict + `severity_rank()` helper |
| `agentlint/analysis/report_builder.py` | replaced stub | `format_findings_summary()` for CLI stdout |
| `agentlint/cli.py` | extended | Phase 4 findings phase: calls `run_deterministic_checks`, prints summary, writes `findings.json` |
| `demo_repos/inconsistent-js-repo/AGENTS.md` | created | Minimal instruction file with npm+Jest contradicting pnpm+Vitest reality |
| `tests/unit/test_analysis.py` | created | 35 tests covering all Phase 4 detectors |

### Commands Run

```bash
pip install -e ".[dev]"
pytest --tb=short -v
agentlint scan demo_repos/single-agent-stale-repo
agentlint scan demo_repos/inconsistent-js-repo
agentlint --help
```

### Test Results

| Test Class | Tests | Result |
|---|---|---|
| `TestF02PackageManagerMismatch` | 7 | ✅ PASSED |
| `TestF01CrossFileConflicts` | 5 | ✅ PASSED |
| `TestF03StalePaths` | 5 | ✅ PASSED |
| `TestF04InvalidCommands` | 5 | ✅ PASSED |
| `TestF05Duplicates` | 5 | ✅ PASSED |
| `TestRunDeterministicChecks` | 5 | ✅ PASSED |
| `TestWriteFindingsJson` | 3 | ✅ PASSED |
| Phase 1–3 tests | 125 | ✅ PASSED |
| **Total** | **160 passed in 0.29s** | ✅ |

```
============================= test session starts =============================
platform win32 -- Python 3.12.7, pytest-8.4.2, pluggy-1.6.0
collected 160 items

160 passed in 0.29s
==============================
```

### Acceptance Criteria

| Criterion | Status |
|---|---|
| `inconsistent-js-repo` produces F02 package_manager finding (npm vs pnpm) | ✅ `find-f02-001` through `find-f02-003` |
| `inconsistent-js-repo` produces F02 test_framework finding (jest vs vitest) | ✅ `find-f02-004` |
| `single-agent-stale-repo` produces F02 package_manager finding (npm vs pnpm) | ✅ `find-f02-001` through `find-f02-003` |
| All findings have `deterministic=True` | ✅ verified |
| `findings.json` schema: `agentlint_version`, `repo_path`, `findings` | ✅ all keys present |
| Phase 1–3 tests still pass (125) | ✅ no regressions |
| New Phase 4 tests pass (35) | ✅ all green |
| `agentlint scan` exits 0 for both demo repos | ✅ no traceback |
| No LLM, Bob, or network used | ✅ pure deterministic Python stdlib |

### Finding Engine Summary

| Detector | Finding Type | Status |
|---|---|---|
| `detect_f01_cross_file_conflicts` | F01 Cross-Instruction Conflict | ✅ implemented |
| `detect_f02_mismatch` | F02 Instruction vs Repository Mismatch | ✅ implemented (pm, tf, linting) |
| `detect_f03_stale_paths` | F03 Stale Path (conservative matching) | ✅ implemented |
| `detect_f04_invalid_commands` | F04 Invalid/Stale Command | ✅ implemented |
| `detect_f05_duplicates` | F05 Exact Duplicate Rules | ✅ implemented |

### Implementation Notes

- **F02 severity**: `high` for package_manager/test_framework; `medium` for linting.
- **F02 confidence**: `0.95` for strong evidence conflicts; `0.7` for medium-only conflicts.
- **F03 conservative matching**: a rule referencing `src/services/` does NOT fire F03 if `src/` root exists in evidence.
- **F04 guard**: only fires when at least one `commands` evidence item exists (avoids false positives on Python-only repos).
- **F05 threshold**: only fires for rules with ≥ 10 normalized characters (suppresses heading noise).
- **Finding IDs**: `find-{type_lower}-{seq:03d}` scheme, counters reset per call to `run_deterministic_checks`.
- **Severity sort**: findings sorted critical → info before ID assignment.

### Known Issues

None.

---

*Updated after Phase 4 implementation.*

## Phase 5 — Sample Repositories and Golden Scenarios

**Status:** ✅ Complete

### Goal

Create deterministic demo cases for all three packaged repositories, store golden
snapshot files, wire integration tests, and implement `agentlint demo`.

### Files Created / Modified

| File | Action | Notes |
|---|---|---|
| `demo_repos/inconsistent-js-repo/AGENTS.md` | modified | Added `src/services/` path reference |
| `demo_repos/inconsistent-js-repo/CLAUDE.md` | created | pnpm + Vitest instruction; shared DoD rule for F05 |
| `demo_repos/inconsistent-js-repo/.github/copilot-instructions.md` | created | References absent `npm run test:unit` (F04); duplicates DoD rule (F05) |
| `demo_repos/inconsistent-js-repo/.bob/rules-code/AGENTS-code.md` | created | References absent `npm run deploy` (F04) |
| `demo_repos/single-agent-stale-repo/CLAUDE.md` | modified | Added `src/services/` stale path reference |
| `demo_repos/single-agent-stale-repo/src/index.ts` | created | Makes `src/` exist so F03 fires conservatively for `src/services/` |
| `demo_repos/clean-repo/package.json` | created | pnpm@9.0.0 + Vitest + ESLint + Prettier |
| `demo_repos/clean-repo/pnpm-lock.yaml` | created | Minimal lockfile header |
| `demo_repos/clean-repo/src/index.ts` | created | Minimal TS source |
| `demo_repos/clean-repo/AGENTS.md` | created | Correct pnpm + Vitest instructions matching repo |
| `tests/golden/inconsistent-js-repo.json` | created | Golden snapshot: ≥7 findings, all 5 types required |
| `tests/golden/single-agent-stale-repo.json` | created | Golden snapshot: F02 + F03 required |
| `tests/golden/clean-repo.json` | created | Golden snapshot: no_high_severity=true |
| `tests/integration/test_demo_repos.py` | created | 25 integration tests across 5 test classes |
| `agentlint/cli.py` | extended | `demo` command replaced with real multi-repo scan; `_run_scan_for_path` helper |
| `agentlint/analysis/deterministic_rules.py` | modified | F03 updated: now fires with confidence=0.6 when root exists but sub-path absent (satisfies §25 Scenario C) |
| `tests/unit/test_analysis.py` | modified | Updated `test_f03_root_match_*` test to match new F03 behavior |

### Commands Run

```bash
agentlint scan demo_repos/inconsistent-js-repo
agentlint scan demo_repos/single-agent-stale-repo
agentlint scan demo_repos/clean-repo
agentlint demo
pytest --tb=short -v
```

### Test Results

| Test File | Tests | Result |
|---|---|---|
| `tests/integration/test_demo_repos.py` | 25 | ✅ PASSED |
| `tests/unit/test_analysis.py` | 35 | ✅ PASSED (1 test updated) |
| All prior unit tests (Phases 0–4) | 125 | ✅ PASSED |
| **Total** | **185 passed in 0.62s** | ✅ |

```
============================= test session starts =============================
platform win32 -- Python 3.12.7, pytest-8.4.2, pluggy-1.6.0
collected 185 items

185 passed in 0.62s
==============================
```

### Acceptance Criteria

| Criterion | Status |
|---|---|
| `inconsistent-js-repo` → F01 cross-file conflict (package_manager) | ✅ `find-f01-001`: AGENTS.md npm vs CLAUDE.md pnpm |
| `inconsistent-js-repo` → F01 cross-file conflict (test_framework) | ✅ `find-f01-002`: AGENTS.md jest vs CLAUDE.md vitest |
| `inconsistent-js-repo` → F02 repo mismatch (package_manager) | ✅ `find-f02-001` through `find-f02-005` |
| `inconsistent-js-repo` → F02 repo mismatch (test_framework) | ✅ `find-f02-006` |
| `inconsistent-js-repo` → F03 stale path (`src/services/`) | ✅ fires with confidence=0.6 |
| `inconsistent-js-repo` → F04 invalid command (`test:unit`) | ✅ `find-f04-001` |
| `inconsistent-js-repo` → F04 invalid command (`deploy`) | ✅ `find-f04-002` |
| `inconsistent-js-repo` → F05 duplicate (DoD rule) | ✅ `find-f05-009`, `find-f05-010` |
| `single-agent-stale-repo` → F02 (npm vs pnpm) | ✅ `find-f02-001` through `find-f02-003` |
| `single-agent-stale-repo` → F03 (`src/services/`) | ✅ `find-f03-001` (confidence=0.6) |
| `clean-repo` → zero critical/high findings | ✅ 0 critical, 0 high (1 medium F03 for dist/ is acceptable) |
| `agentlint demo` exits 0 | ✅ all three repos scanned |
| Golden snapshots stored in `tests/golden/` | ✅ 3 files: `inconsistent-js-repo.json`, `single-agent-stale-repo.json`, `clean-repo.json` |
| All 160 existing tests still pass | ✅ no regressions |
| New integration tests pass (≥ 7) | ✅ 25 new integration tests all green |
| All findings have `deterministic=True` | ✅ verified by tests |

### Implementation Notes

- **F03 behavior change**: The conservative "no-fire when root exists" logic from Phase 4 was updated to fire with `confidence=0.6` (vs the high-confidence `0.8` path) when the root directory exists but the exact sub-path does not. This satisfies §25 Scenario C which states `src/services/` should produce a stale-path finding. Top-level paths (no `/`) never get a root-match boost.
- **F05 DoD duplicate**: The "Definition of Done" section in `CLAUDE.md` and `copilot-instructions.md` both contain `"Always run pnpm lint and pnpm test before completing a task."` (>20 chars normalized) — well above the 10-char threshold for the F05 detector.
- **Demo command path resolution**: `_DEMO_REPOS_DIR = Path(__file__).resolve().parent.parent / "demo_repos"` — works for editable installs; guarded with existence check.

### Known Issues

None.

---

*Updated after Phase 5 implementation.*

---
