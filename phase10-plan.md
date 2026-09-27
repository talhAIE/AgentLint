# Phase 10 — GitHub / CI Integration Plan

## Top-Level Overview

**Goal:** Make AgentLint behave as a real developer tool by shipping a GitHub Actions
workflow that runs on pull requests, detects high-severity instruction drift, and fails
the CI check with a human-readable explanation when drift is found.

**Scope (MVP):**

1. Replace the Phase 10 placeholder at `.github/workflows/agentlint.yml` with a fully
   working PR-triggered workflow.
2. Add a `--fail-on-severity` option to `agentlint scan` so the CLI can exit non-zero
   when findings at or above the chosen severity level exist (required for the workflow
   to signal CI failure without coupling the workflow to internal Python logic).
3. Add a `agentlint report` CLI sub-command (or extend `scan`) to print a compact,
   human-readable CI report suitable for GitHub Actions log output.
4. Write integration tests that verify the exit-code behavior end-to-end.
5. Update `PROGRESS.md`.

**Non-goals for Phase 10:**
- GitHub API / PR comment posting (listed as optional stretch — excluded from MVP).
- Any new finding types or evidence detectors.
- Changes to the Streamlit UI.
- Changes to demo repos or golden snapshots.

---

## Sub-Tasks

---

### Sub-Task 1 — Add `--fail-on-severity` flag to `agentlint scan`

**Intent:**
The workflow must fail the CI check when high-severity findings exist.
Currently `agentlint scan` always exits 0 regardless of findings.
A `--fail-on-severity <level>` flag (default: `none`) gives callers explicit control
without breaking existing behaviour for non-CI users.

**Expected Outcomes:**
- `agentlint scan . --fail-on-severity high` exits 1 when any finding has severity
  `critical` or `high`; exits 0 when there are no such findings.
- `agentlint scan .` (no flag) continues to exit 0 as before.
- Printed output includes a `"AgentLint: FAIL"` / `"AgentLint: PASS"` summary line
  when `--fail-on-severity` is set, followed by the drift detail matching the
  spec's example format:

  ```
  AgentLint: FAIL

  High-severity instruction drift detected.

  AGENTS.md says: npm
  Repository evidence: pnpm
  ```

**Todo List:**
1. In `agentlint/cli.py` → `scan()`, add a `fail_on_severity` option:
   ```python
   fail_on_severity: str = typer.Option(
       "none",
       "--fail-on-severity",
       help="Exit 1 if any finding meets or exceeds this severity "
            "(critical|high|medium|low|none). Default: none.",
   )
   ```
2. After `findings` are collected, filter findings whose severity is at or above the
   threshold using the existing `_SEVERITY_ORDER` mapping imported from
   `agentlint.analysis`.
3. If any threshold-breaching findings exist, print a CI-friendly block (see format
   above) and raise `typer.Exit(code=1)`.
4. Export `_SEVERITY_ORDER` from `agentlint/analysis/__init__.py` so `cli.py` can
   import it (currently a module-private name).

**Relevant Context:**
- `agentlint/cli.py:46-168` — `scan()` command
- `agentlint/analysis/__init__.py:24-30` — `_SEVERITY_ORDER` dict
- `agentlint/analysis/report_builder.py:13-52` — `format_findings_summary()`
- Finding model field: `Finding.severity: str` (`"critical"|"high"|"medium"|"low"|"info"`)
- Existing filter pattern already in `_run_scan_for_path` at `cli.py:240-242`

**Status:** [ ] pending

---

### Sub-Task 2 — Implement the GitHub Actions workflow

**Intent:**
Replace the placeholder `.github/workflows/agentlint.yml` with a real workflow
that runs on pull requests touching instruction/config files and fails when
high-severity drift is detected.

**Expected Outcomes:**
- Workflow triggers on `pull_request` when paths match:
  - `AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md`, `cursor.rules`,
    `.cursorrules`, `.bob/**`
  - `package.json`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`,
    `pyproject.toml`, `requirements*.txt`, `Pipfile`, `Pipfile.lock`,
    `Cargo.toml`, `Cargo.lock`, `go.mod`, `go.sum`
- Workflow steps:
  1. `actions/checkout@v4`
  2. `actions/setup-python@v5` with Python 3.11
  3. `pip install -e ".[dev]"`
  4. `agentlint scan . --fail-on-severity high`
  5. `agentlint validate . --skip-commands` (runs after scan produces artifacts;
     allowed to fail softly — `continue-on-error: true` since validate requires
     policy.yaml which won't exist until `agentlint policy` is run)
- When `agentlint scan` exits 1, the workflow step fails, the job fails, and
  the human-readable output is visible in the Actions log.
- The job is named `agentlint-check` so it appears clearly in the PR status UI.

**Todo List:**
1. Replace the content of `.github/workflows/agentlint.yml` completely.
2. Use `paths:` filter in the `on.pull_request` trigger to scope the workflow
   to files that could introduce drift.
3. Run `agentlint scan . --fail-on-severity high` as the primary check step.
4. Run `agentlint validate . --skip-commands` with `continue-on-error: true`.
5. Add a final step that echoes a summary line regardless of pass/fail
   (using `if: always()`) so the log always ends cleanly.

**Relevant Context:**
- `.github/workflows/agentlint.yml` (placeholder, lines 1-8)
- `.github/workflows/test.yml` — reference workflow structure to follow
- `agentlint/cli.py:320-414` — `validate` command (requires findings.json + policy.yaml)
- The validate command requires policy.yaml which is only produced by
  `agentlint policy` — so validate must use `continue-on-error: true` in the
  workflow unless the repo has pre-committed policy artifacts.

**Status:** [ ] pending

---

### Sub-Task 3 — Integration tests for `--fail-on-severity` and CI exit-code behavior

**Intent:**
Ensure the new `--fail-on-severity` flag is reliably tested so it cannot regress.
Tests use `typer.testing.CliRunner` following the pattern established in
`tests/integration/test_validate_cli.py`.

**Expected Outcomes:**
- New test file `tests/integration/test_scan_ci.py` passes.
- Tests cover:
  1. `scan . --fail-on-severity high` on `inconsistent-js-repo` → exit code 1
     (the demo repo has known high-severity findings).
  2. `scan . --fail-on-severity high` on `clean-repo` → exit code 0.
  3. `scan .` (no flag) on `inconsistent-js-repo` → exit code 0 (existing behavior
     preserved).
  4. `scan . --fail-on-severity none` → exit code 0 (explicit opt-out works).
  5. `scan . --fail-on-severity high` on a temp dir with an AGENTS.md that mismatches
     the repo evidence → exit 1 and output contains `"AgentLint: FAIL"`.
  6. `scan . --fail-on-severity high` on `clean-repo` → output contains
     `"AgentLint: PASS"`.
  7. Invalid severity value passed to `--fail-on-severity` → exit 1 with an
     informative error message.

**Todo List:**
1. Create `tests/integration/test_scan_ci.py`.
2. Import `CliRunner`, `app` following the exact pattern from `test_validate_cli.py`.
3. Reference `_DEMO_REPOS_DIR` the same way as in existing integration tests.
4. Write the 7 test cases listed above.
5. Run `pytest tests/integration/test_scan_ci.py -v` to confirm all pass.
6. Run full `pytest` suite to confirm no regressions (target: 472+ tests, all passing).

**Relevant Context:**
- `tests/integration/test_validate_cli.py:1-30` — import/setup pattern to replicate
- `tests/integration/test_demo_repos.py` — demo repo path patterns
- `demo_repos/inconsistent-js-repo/` — has known high/critical findings (ground truth
  from PROGRESS.md: 8 high findings)
- `demo_repos/clean-repo/` — has no high/critical findings

**Status:** [ ] pending

---

### Sub-Task 4 — Update `PROGRESS.md`

**Intent:**
Keep `PROGRESS.md` up to date per the project protocol (Rule 3, AgentLintplan.md §21).

**Expected Outcomes:**
- `PROGRESS.md` has a new `## Phase 10 — GitHub / CI Integration` section.
- Phase checklist at the top is updated to mark Phase 10 complete.
- Section documents: files created/modified, commands run, test results, acceptance
  criteria checked off, known issues.

**Todo List:**
1. Add a Phase 10 section to `PROGRESS.md` following the same structure as Phase 9.
2. List all files created/modified (workflow YAML, `cli.py`, test file).
3. Record the `pytest` output confirming the test count and pass rate.
4. Check off each acceptance criterion from `AgentLintplan.md §Phase 10`.
5. Update the phase checklist near the top of `PROGRESS.md`.

**Relevant Context:**
- `PROGRESS.md:5-22` — phase checklist section at the top
- `PROGRESS.md:926-1010` — Phase 9 section as structural template

**Status:** [ ] pending

---

## Files to Create or Modify

| File | Action | Sub-Task |
|------|--------|----------|
| `.github/workflows/agentlint.yml` | **Modify** — replace placeholder with real workflow | 2 |
| `agentlint/cli.py` | **Modify** — add `--fail-on-severity` to `scan()` | 1 |
| `agentlint/analysis/__init__.py` | **Modify** — export `SEVERITY_ORDER` (rename from `_SEVERITY_ORDER`) | 1 |
| `tests/integration/test_scan_ci.py` | **Create** — new integration tests | 3 |
| `PROGRESS.md` | **Modify** — add Phase 10 section | 4 |

---

## Functions / Classes / Modules Required

| Symbol | Location | Change |
|--------|----------|--------|
| `scan()` | `agentlint/cli.py` | Add `fail_on_severity` Typer option; post-findings exit-code block |
| `SEVERITY_ORDER` | `agentlint/analysis/__init__.py` | Rename `_SEVERITY_ORDER` → `SEVERITY_ORDER` and add to `__all__` |
| `format_ci_failure_block()` | `agentlint/analysis/report_builder.py` | **New** — returns the multi-line CI failure message (title + per-finding detail matching spec example) |
| `TestScanCIExitCodes` | `tests/integration/test_scan_ci.py` | **New** test class |

The `format_ci_failure_block(findings)` function lives in `report_builder.py` alongside
`format_findings_summary()` and produces output like:

```
AgentLint: FAIL

High-severity instruction drift detected.

AGENTS.md says: npm
Repository evidence: pnpm
```

It is used by `scan()` when `--fail-on-severity` threshold is breached. This keeps
formatting logic out of the CLI module.

---

## Dependencies Required

**No new Python packages.** All dependencies (typer, existing stdlib) already satisfy
Phase 10 needs. The GitHub Actions workflow uses only:
- `actions/checkout@v4` (already used in `test.yml`)
- `actions/setup-python@v5` (already used in `test.yml`)
- `pip install -e ".[dev]"` (existing install command)

---

## Tests Required

| Test File | Test Name | Assertion |
|-----------|-----------|-----------|
| `tests/integration/test_scan_ci.py` | `test_fail_on_high_with_high_findings` | exit 1 on `inconsistent-js-repo` |
| `tests/integration/test_scan_ci.py` | `test_pass_on_high_with_clean_repo` | exit 0 on `clean-repo` |
| `tests/integration/test_scan_ci.py` | `test_no_flag_always_exits_zero` | exit 0 on `inconsistent-js-repo` (no flag) |
| `tests/integration/test_scan_ci.py` | `test_fail_on_severity_none_explicit` | exit 0 even with findings |
| `tests/integration/test_scan_ci.py` | `test_fail_output_contains_agentlint_fail` | stdout includes `"AgentLint: FAIL"` |
| `tests/integration/test_scan_ci.py` | `test_pass_output_contains_agentlint_pass` | stdout includes `"AgentLint: PASS"` |
| `tests/integration/test_scan_ci.py` | `test_invalid_severity_value` | exit 1, error message in output |

---

## Commands That Must Be Run

```bash
# Install (already done, but required for any fresh environment)
pip install -e ".[dev]"

# Run only the new integration tests first
pytest tests/integration/test_scan_ci.py -v

# Run full suite to verify no regressions
pytest --tb=short -q

# Manually verify the workflow YAML is valid (no Python tooling needed):
# Push a branch that modifies AGENTS.md and open a PR — the workflow should trigger.
# Alternatively, use `act` (local GitHub Actions runner) if available:
# act pull_request -W .github/workflows/agentlint.yml
```

---

## Acceptance Criteria (from AgentLintplan.md §Phase 10)

> **Definition of Done:** A sample pull request or local workflow run demonstrates
> that changing an instruction to a stale value causes CI to fail.

Operationally this means:

- [ ] `.github/workflows/agentlint.yml` is a valid GitHub Actions workflow that
      triggers on pull requests touching instruction/config files.
- [ ] `agentlint scan . --fail-on-severity high` exits 1 when the scanned repo
      has high-severity findings.
- [ ] `agentlint scan . --fail-on-severity high` exits 0 on a clean repo.
- [ ] The failure output matches the spec format:
      `"AgentLint: FAIL\n\nHigh-severity instruction drift detected.\n..."`.
- [ ] `agentlint scan .` (no flag) still exits 0 — existing behaviour preserved.
- [ ] All existing 472 tests continue to pass.
- [ ] New integration tests in `test_scan_ci.py` all pass.

---

## Risks and Conflicts with Existing Code

| Risk | Detail | Mitigation |
|------|--------|------------|
| **`_SEVERITY_ORDER` rename** | `_SEVERITY_ORDER` is used in `agentlint/analysis/__init__.py:47-60` internally. Renaming to `SEVERITY_ORDER` for export must not break the internal sort. | Keep the same dict; just remove the leading underscore and add to `__all__`. Run full pytest suite to catch any shadowing. |
| **`validate` step in workflow needs policy.yaml** | `agentlint validate` requires both `findings.json` and `policy.yaml` to exist. The workflow does not call `agentlint policy` first, so the validate step will always fail in a clean checkout. | Use `continue-on-error: true` on the validate step. The primary CI gate is the `scan` step. The validate step is informational only at this phase. |
| **Demo repo findings count** | Tests assert exit 1 on `inconsistent-js-repo`. If a future scan run produces zero high findings (e.g., evidence detectors change), the test fails. | Tests assert `exit_code == 1` only for known-good fixtures; add a guard that checks the fixture's `.agentlint/findings.json` exists before running the live scan, or run the scan fresh and rely on the deterministic engine. The demo repo files are permanent test fixtures (per AGENTS.md). |
| **`validate` exit-code change in workflow** | If `continue-on-error` is not set on the validate step and policy.yaml is absent, the entire workflow job will fail at that step even when the scan passed — masking the real result. | Use `continue-on-error: true` explicitly. |
| **Invalid severity string** | A user might pass `--fail-on-severity CRITICAL` (uppercase). | Normalise the input to lowercase and validate against known values before use; exit 1 with a clear message for unknowns. |
