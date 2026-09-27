# Phase 5 Plan — Sample Repositories and Golden Scenarios

## Overview

Phase 5 makes the three demo repositories fully representative of the five §25
acceptance-test scenarios, stores their expected findings as golden JSON snapshots,
and wires integration tests that assert the scanner produces those exact outputs on
every run — with no LLM involved.

**Definition of Done (from spec §Phase 5):**

> The packaged inconsistent repo produces known golden findings with no LLM.

More concretely, after Phase 5:

1. `agentlint scan demo_repos/inconsistent-js-repo` produces at least:
   - F01 cross-file conflict (package_manager: npm vs pnpm between AGENTS.md and CLAUDE.md)
   - F01 cross-file conflict (test_framework: jest vs vitest)
   - F02 repo mismatch (AGENTS.md npm vs repo pnpm)
   - F02 repo mismatch (AGENTS.md jest vs repo vitest)
   - F03 stale path (src/services/)
   - F04 invalid command (npm run test:unit from copilot instructions)
   - F05 duplicate (copilot instructions duplicates a rule from CLAUDE.md)

2. `agentlint scan demo_repos/single-agent-stale-repo` produces at least:
   - F02 repo mismatch (CLAUDE.md npm vs repo pnpm)
   - F02 repo mismatch (CLAUDE.md npm test vs repo vitest)
   - F03 stale path (src/services/)

3. `agentlint scan demo_repos/clean-repo` produces:
   - zero high-severity findings

4. `agentlint demo` runs all three scans non-interactively and exits 0.

5. Golden snapshots in `tests/golden/` match actual scanner output.

6. Integration tests in `tests/integration/` assert 1, 2, 3, 4, and 5 above.

---

## Files That Need to Be Created or Modified

### New files

| File | Notes |
|---|---|
| `demo_repos/inconsistent-js-repo/CLAUDE.md` | pnpm + Vitest instruction; one rule duplicated from copilot file |
| `demo_repos/inconsistent-js-repo/.github/copilot-instructions.md` | references nonexistent `npm run test:unit`; duplicates DoD rule |
| `demo_repos/inconsistent-js-repo/.bob/rules-code/AGENTS-code.md` | stale Bob rule (references old command) |
| `demo_repos/single-agent-stale-repo/src/services/.gitkeep` | makes `src/` exist so only `src/services/` triggers F03 |
| `demo_repos/clean-repo/AGENTS.md` | correct pnpm + vitest instruction, matching all repo facts |
| `demo_repos/clean-repo/package.json` | pnpm project, vitest, eslint, prettier scripts |
| `demo_repos/clean-repo/pnpm-lock.yaml` | minimal lockfile header |
| `demo_repos/clean-repo/src/index.ts` | minimal TS source |
| `tests/golden/inconsistent-js-repo.json` | expected findings snapshot |
| `tests/golden/single-agent-stale-repo.json` | expected findings snapshot |
| `tests/golden/clean-repo.json` | expected findings snapshot (empty/no-high-severity) |
| `tests/integration/test_demo_repos.py` | integration tests against the three demo repos |

### Modified files

| File | Change |
|---|---|
| `demo_repos/inconsistent-js-repo/AGENTS.md` | Add `src/services/` path reference; ensure npm/Jest stay; no other changes |
| `demo_repos/single-agent-stale-repo/CLAUDE.md` | Add `src/services/` stale path reference; add explicit outdated test command `npm test` |
| `agentlint/cli.py` | Replace stub `demo` command with real multi-repo scan |

### Files NOT modified in Phase 5

- All `agentlint/` Python source (finding engine already works)
- `agentlint/models.py`
- `agentlint/parsing/`
- `agentlint/evidence/`
- `agentlint/analysis/`
- `tests/unit/` (no changes to unit tests)
- `pyproject.toml` / `requirements.txt` (no new dependencies)

---

## Sub-Tasks

---

### Sub-Task A — Complete `inconsistent-js-repo` instruction files

**Intent:** Make Repo A exercise every finding type the engine can produce.
The repo's actual tooling (pnpm, Vitest, ESLint, Prettier) stays unchanged;
only instruction files are added or updated.

**Expected Outcomes:**

- `AGENTS.md` (already exists) — currently says npm + Jest and references `dist/`.
  Add one more reference to `src/services/` so a stale-path F03 fires for a
  specific sub-path (not just `dist/`).

- `CLAUDE.md` (new) — says pnpm + Vitest, matching the repo.
  Contains one rule that is intentionally identical (after normalization) to a
  rule in the copilot instructions, so F05 fires across files.

- `.github/copilot-instructions.md` (new) — says `npm run test:unit` (script
  absent from `package.json`) so F04 fires.  Also contains the same DoD rule
  as CLAUDE.md so F05 fires.

- `.bob/rules-code/AGENTS-code.md` (new) — contains one stale command
  (`npm run deploy`, which is absent from package scripts), so another F04 fires.

**Findings expected after this sub-task:**

| Type | Source | Detail |
|---|---|---|
| F01 | AGENTS.md vs CLAUDE.md | package_manager: npm vs pnpm |
| F01 | AGENTS.md vs CLAUDE.md | test_framework: jest vs vitest |
| F02 | AGENTS.md | package_manager: npm but repo=pnpm |
| F02 | AGENTS.md | test_framework: jest but repo=vitest |
| F03 | AGENTS.md | src/services/ absent |
| F04 | copilot-instructions | npm run test:unit absent |
| F04 | .bob/rules-code | npm run deploy absent |
| F05 | CLAUDE.md + copilot | identical DoD rule |

**Relevant Context:**
- `demo_repos/inconsistent-js-repo/AGENTS.md` — current content (npm + Jest)
- `demo_repos/inconsistent-js-repo/package.json` — scripts: build, test, lint, format
- `agentlint/parsing/normalization.py` — keyword patterns used to classify rules
- `agentlint/analysis/deterministic_rules.py` — F01/F02/F03/F04 detectors
- `agentlint/analysis/duplicates.py` — F05 detector (min length 10, punctuation stripped)
- §25 Scenarios A, C, D

**Status:** [ ] pending

---

### Sub-Task B — Complete `single-agent-stale-repo` instruction file

**Intent:** Make Repo B (one file only) exercise Scenarios B and C from §25.
The repo has pnpm + Vitest; CLAUDE.md must say npm and reference `src/services/`
(a path that does not exist in this repo).

**Expected Outcomes:**

- `CLAUDE.md` updated:
  - Retains the npm reference (F02 package_manager mismatch).
  - Retains `npm test` but adds a clearer stale-command pattern if not already
    producing F04 (check whether `npm run test:unit` needs adding).
  - Adds explicit reference to `src/services/` (F03 stale path).

- `demo_repos/single-agent-stale-repo/src/` directory created with a minimal
  placeholder (`src/index.ts` or `src/.gitkeep`) so that `src/` exists in evidence
  but `src/services/` does not — causing F03 to fire conservatively only for the
  sub-path.

**Findings expected after this sub-task:**

| Type | Detail |
|---|---|
| F02 | package_manager: npm but repo=pnpm |
| F02 | test_framework: npm test but repo=vitest (if jest reference added) |
| F03 | src/services/ absent (src/ exists) |

**Relevant Context:**
- `demo_repos/single-agent-stale-repo/CLAUDE.md` — current content
- `demo_repos/single-agent-stale-repo/package.json` — pnpm@8.15.0, vitest
- F03 conservative matching in `deterministic_rules.py`: root segment `src` exists
  in evidence → `src/services/` fires; `src/` alone does NOT fire
- §25 Scenarios B, C

**Status:** [ ] pending

---

### Sub-Task C — Build `clean-repo`

**Intent:** Make Repo C a correct-instruction repository that produces zero
high-severity findings. This is the control case for the demo.

**Expected Outcomes:**

- `package.json` with pnpm@9.0.0 + Vitest + ESLint + Prettier, build/test/lint/format scripts.
- `pnpm-lock.yaml` minimal header.
- `src/index.ts` minimal placeholder.
- `AGENTS.md` that correctly says:
  - Use pnpm.
  - Test with Vitest: `pnpm run test`.
  - Lint with ESLint: `pnpm run lint`.
  - Build with: `pnpm run build`.
  - Source in `src/`.
- After scanning: `findings.json` contains zero findings with severity `high` or `critical`.
  Low/info findings (e.g. no duplicates) are acceptable.

**Relevant Context:**
- `demo_repos/inconsistent-js-repo/package.json` — model for package.json shape
- `agentlint/analysis/__init__.py` — severity sort order
- §25 Scenario E

**Status:** [ ] pending

---

### Sub-Task D — Generate and store golden snapshot files

**Intent:** Capture the deterministic findings output for each demo repo as a
committed reference JSON, so future changes that accidentally alter the output
are caught immediately.

**Approach:**

1. Run `agentlint scan demo_repos/<repo>` for each of the three repos.
2. Copy `.agentlint/findings.json` into `tests/golden/<repo-name>.json`.
3. The golden file stores a **normalized** subset, not the full output, to avoid
   brittle path-absolute failures:
   - Keep: `finding.type`, `finding.severity`, `finding.title` (or a `title_contains`
     substring), `finding.deterministic`.
   - Drop: absolute `repo_path`, absolute `source_path` values, `agentlint_version`.

**Golden file schema** (hand-crafted, not machine-dumped verbatim):

```json
{
  "description": "Expected findings for inconsistent-js-repo",
  "minimum_finding_count": 7,
  "required_types": ["F01", "F02", "F03", "F04", "F05"],
  "no_high_severity": false,
  "findings": [
    { "type": "F01", "severity": "high", "title_contains": "package_manager" },
    { "type": "F01", "severity": "high", "title_contains": "test_framework" },
    ...
  ]
}
```

This schema is purpose-built for snapshot assertion — not a verbatim dump.

**Relevant Context:**
- `tests/golden/.gitkeep` placeholder
- `agentlint/models.py` — `Finding.to_dict()` fields

**Status:** [ ] pending

---

### Sub-Task E — Integration tests (`tests/integration/test_demo_repos.py`)

**Intent:** Write integration tests that run the full scanner against each demo
repo and assert the golden expected outputs are met.

**Expected Outcomes:**

- `test_inconsistent_js_repo_produces_known_findings` — asserts:
  - at least one F01 for package_manager
  - at least one F01 for test_framework
  - at least one F02 for package_manager
  - at least one F02 for test_framework
  - at least one F03 (stale path)
  - at least one F04 (invalid command)
  - at least one F05 (duplicate)
  - all findings have `deterministic=True`
  - `findings.json` is written

- `test_single_agent_stale_repo_produces_known_findings` — asserts:
  - at least one F02 for package_manager (npm vs pnpm)
  - at least one F03 (src/services/ stale path)
  - all findings have `deterministic=True`

- `test_clean_repo_no_high_severity` — asserts:
  - zero findings with severity `high` or `critical`

- `test_golden_snapshot_inconsistent` — loads `tests/golden/inconsistent-js-repo.json`
  and asserts each entry in `required_types` is present in actual output, and
  `minimum_finding_count` is met.

- `test_golden_snapshot_single_agent` — same pattern for single-agent repo.

- `test_golden_snapshot_clean` — asserts `no_high_severity=true` from golden.

- `test_agentlint_demo_command_exits_zero` — calls `agentlint demo` and asserts
  exit code 0 and stdout contains all three repo names.

**Test design constraints:**
- Tests invoke `run_deterministic_checks(rules, evidence)` directly (not via CLI
  subprocess) to avoid OS path complications; golden tests may use subprocess.
- Tests must not write to the demo repos' `.agentlint/` during the test run
  (use `tmp_path` or read pre-existing `.agentlint/` files).
- All tests must be deterministic — no randomness, no network.

**Relevant Context:**
- `tests/integration/__init__.py` — currently just a docstring
- `tests/unit/test_analysis.py` — model for how to call the analysis pipeline
- `agentlint/analysis/__init__.py` — `run_deterministic_checks()`
- `agentlint/evidence/__init__.py` — `collect_evidence()`
- `agentlint/parsing/__init__.py` — `extract_rules()`
- `agentlint/discovery/instruction_sources.py` — `discover_sources()`
- `agentlint/config.py` — `load_config()`

**Status:** [ ] pending

---

### Sub-Task F — Implement `agentlint demo` CLI command

**Intent:** Replace the stub `demo` command with a real implementation that
runs the scanner against all three packaged demo repos and prints a summary.

**Expected Outcomes:**

- `agentlint demo` (no arguments):
  1. Resolves the three demo repo paths relative to the installed package location
     (using `importlib.resources` or `__file__`-relative path detection).
  2. Runs the full scan pipeline (discover → evidence → rules → findings) for each repo.
  3. Prints a brief per-repo summary to stdout.
  4. Exits 0.

- Does NOT write to arbitrary filesystem locations (uses the repo's own `.agentlint/`
  subdirectory, which is the same behavior as `agentlint scan`).

**Path resolution strategy** (important for portability):

```python
# Resolve demo repos relative to this package's install location
_DEMO_REPOS_DIR = Path(__file__).resolve().parent.parent / "demo_repos"
```

This works for both editable installs (`pip install -e .`) and regular installs
as long as `demo_repos/` is included in the package (via `pyproject.toml`
`[tool.setuptools] packages`).  Verify `pyproject.toml` includes `demo_repos/`.

**Relevant Context:**
- `agentlint/cli.py` — stub `demo()` command
- `pyproject.toml` — package configuration; check whether `demo_repos/` is in scope
- `agentlint/analysis/report_builder.py` — `format_findings_summary()`

**Status:** [ ] pending

---

### Sub-Task G — Update PROGRESS.md

**Intent:** Mark Phase 5 complete with commands run, test results, and
acceptance criteria.

**Status:** [ ] pending

---

## Functions / Modules Required

### New Python code

| Module | Function/Class | Notes |
|---|---|---|
| `agentlint/cli.py` | `demo()` command | Replace stub; resolves demo_repos via `__file__` |
| `tests/integration/test_demo_repos.py` | `test_*` functions | ~7 integration tests |

No new agentlint package modules needed — all analysis logic is complete from Phase 4.

### Helper needed in integration tests

```python
def _run_full_scan(repo_path: Path):
    """Run discover → evidence → rules → findings for repo_path."""
    config = load_config(repo_path)
    sources = discover_sources(repo_path, config)
    evidence = collect_evidence(repo_path)
    rules = extract_rules(sources, repo_path=repo_path)
    findings = run_deterministic_checks(rules, evidence)
    return findings
```

This is a test-local helper, not a production API addition.

---

## Dependencies Required

**No new dependencies.** All work uses:
- `pathlib.Path` — path resolution
- `json` — golden file read/write
- stdlib `importlib.resources` or `__file__`-relative resolution for demo path
- pytest `tmp_path` fixture for write isolation

---

## Tests Required

| Test File | Test Name | Assertion |
|---|---|---|
| `tests/integration/test_demo_repos.py` | `test_inconsistent_js_repo_produces_known_findings` | F01 pm, F01 tf, F02 pm, F02 tf, F03, F04, F05 all present |
| | `test_single_agent_stale_repo_produces_known_findings` | F02 pm, F03 present |
| | `test_clean_repo_no_high_severity` | zero critical/high findings |
| | `test_golden_snapshot_inconsistent` | finding types/count from golden file match |
| | `test_golden_snapshot_single_agent` | same pattern |
| | `test_golden_snapshot_clean` | no_high_severity satisfied |
| | `test_agentlint_demo_command_exits_zero` | exit code 0, stdout mentions all 3 repos |

Minimum 7 new integration tests. All existing 160 unit tests must still pass.

---

## Commands That Must Be Run

```bash
# 1. Run all tests (must still show 160 unit tests + new integration tests)
pytest --tb=short -v

# 2. Verify inconsistent-js-repo produces all expected finding types
agentlint scan demo_repos/inconsistent-js-repo

# 3. Verify single-agent-stale-repo produces F02 + F03
agentlint scan demo_repos/single-agent-stale-repo

# 4. Verify clean-repo produces no high-severity findings
agentlint scan demo_repos/clean-repo

# 5. Verify demo command works
agentlint demo
```

---

## Acceptance Criteria (from §Phase 5 + §25)

| Criterion | Expected |
|---|---|
| `inconsistent-js-repo` → F01 cross-file conflict (package_manager) | AGENTS.md npm vs CLAUDE.md pnpm |
| `inconsistent-js-repo` → F01 cross-file conflict (test_framework) | AGENTS.md jest vs CLAUDE.md vitest |
| `inconsistent-js-repo` → F02 repo mismatch (package_manager) | AGENTS.md npm vs pnpm evidence |
| `inconsistent-js-repo` → F02 repo mismatch (test_framework) | AGENTS.md jest vs vitest evidence |
| `inconsistent-js-repo` → F03 stale path (src/services/) | absent from repo |
| `inconsistent-js-repo` → F04 invalid command (test:unit) | absent from package scripts |
| `inconsistent-js-repo` → F05 duplicate | identical rule in CLAUDE.md + copilot file |
| `single-agent-stale-repo` → F02 (npm vs pnpm) | CLAUDE.md npm vs pnpm evidence |
| `single-agent-stale-repo` → F03 (src/services/) | src/ exists, src/services/ absent |
| `clean-repo` → zero critical/high findings | correct instructions |
| `agentlint demo` exits 0 | all three repos scanned |
| Golden snapshots stored in `tests/golden/` | at least 3 files |
| All 160 existing tests still pass | no regressions |
| New integration tests pass (≥ 7) | `test_demo_repos.py` all green |
| All findings have `deterministic=True` | no Bob findings in Phase 5 |

---

## Risks and Conflicts with Existing Code

### Risk 1 — F05 duplicate detector minimum-length threshold

**Detail:** The F05 detector ignores rules with normalized text shorter than
10 characters. The "identical DoD rule" must be long enough to survive that
filter after punctuation stripping. Keep the duplicated rule text well above
20 characters.

**Mitigation:** Choose a DoD rule like "Always run pnpm lint and pnpm test before
completing a task." (>10 chars normalized).

---

### Risk 2 — F03 conservative root-match logic

**Detail:** The F03 detector in `deterministic_rules.py` does NOT fire if the
root segment of the referenced path exists in evidence. So if `src/` is in
evidence, `src/services/` will NOT produce an F03 finding.
For `single-agent-stale-repo` to produce an F03 on `src/services/`, the repo
must have a `src/` directory (so root `src` is in evidence), but NOT
`src/services/`. This is the intended conservative behavior from the spec.

**Mitigation:** Create `demo_repos/single-agent-stale-repo/src/index.ts` (or
`src/.gitkeep`) so `src/` exists, then add `src/services/` reference to CLAUDE.md.
This exercises the conservative logic correctly.

---

### Risk 3 — `inconsistent-js-repo` AGENTS.md already modified in Phase 4

**Detail:** Phase 4 added a minimal AGENTS.md with npm+Jest to produce golden
F02 findings. Phase 5 needs to extend this same file with `src/services/`
reference. The file must be modified, not replaced.

**Mitigation:** Only add the `src/services/` bullet in the Project Structure
section — do not change npm/Jest references, which are required for F01/F02.

---

### Risk 4 — CLAUDE.md in `inconsistent-js-repo` must produce F01 against AGENTS.md

**Detail:** F01 fires when two *different* source files have different values
for the same `normalized_key`. CLAUDE.md must be normalized to `package_manager=pnpm`
and `test_framework=vitest` to conflict with AGENTS.md's npm/jest.

**Mitigation:** The normalization patterns in `parsing/normalization.py` already
detect pnpm/vitest keywords. Make sure CLAUDE.md uses those exact words prominently
(not inside conditional clauses that the parser might miss).

---

### Risk 5 — Bob rules file location

**Detail:** The discovery module looks for `.bob/rules-code/AGENTS-code.md`.
This directory must be created under `demo_repos/inconsistent-js-repo/` — not
under the project root's `.bob/` directory.

**Mitigation:** Create the directory path explicitly:
`demo_repos/inconsistent-js-repo/.bob/rules-code/AGENTS-code.md`.

---

### Risk 6 — `agentlint demo` path resolution at test time

**Detail:** In tests, `__file__` for `agentlint/cli.py` points to the installed
package. With `pip install -e .`, this is the source tree. The `demo_repos/`
directory is three levels up from `agentlint/cli.py`:
`agentlint/cli.py` → `agentlint/` → project root → `demo_repos/`.
The path must be `Path(__file__).resolve().parent.parent / "demo_repos"`.

**Mitigation:** Add a guard: if `_DEMO_REPOS_DIR` does not exist, print an error
and exit 1 (e.g. when installed from a wheel without `demo_repos/`).

---

### Risk 7 — `pyproject.toml` package data

**Detail:** If `demo_repos/` is not included in the package data, `agentlint demo`
will silently fail to find the repos when installed via wheel. For the hackathon
demo the install is `pip install -e .` so this is not an immediate blocker, but
it should be noted.

**Mitigation:** Check `pyproject.toml` for `[tool.setuptools.package-data]` or
`include-package-data`. Add `demo_repos/**` if missing. Flag in PROGRESS.md if
wheel packaging is deferred.

---

*Ready for implementation.*
