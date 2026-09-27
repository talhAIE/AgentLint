# Phase 8 — Verification Engine Plan

## Top-Level Overview

Phase 8 implements the Verification Engine: after a human has approved repairs in
`findings.json`, AgentLint re-scans the repository, checks every policy field still
has evidence backing, optionally runs safe commands from `definition_of_done`, checks
instruction consistency, and writes `.agentlint/verification.json` plus a
human-readable report.

It also implements `apply_repair()` in `agentlint/policy/adapters.py` (currently a
`NotImplementedError` stub placed in Phase 7 precisely for this phase) and adds the
`agentlint validate` CLI subcommand.

All four verification layers come from AgentLintplan.md §Phase 8:

| Layer | Name                    | What it does |
|-------|-------------------------|--------------|
| A     | Structural Re-scan      | Re-run the full scan; confirm approved findings disappeared |
| B     | Policy Evidence Check   | Every high-value policy field must have current evidence |
| C     | Command Validation      | Run safe commands; capture exit code + output excerpt |
| D     | Instruction Consistency | Confirm no remaining cross-instruction contradictions |

---

## Sub-Task 1 — Implement `apply_repair()` in `agentlint/policy/adapters.py`

**Intent**  
Replace the `NotImplementedError` stub with real text-substitution logic. This is the
only place in the codebase that mutates instruction file content. The allowlist guard
`_is_allowed_target()` already exists and must remain in place.

**Expected Outcomes**  
- `apply_repair(item, file_content)` returns the new file content with `original_text`
  replaced by `proposed_text`.
- When `proposed_text` is empty (delete-the-line case) the original line is removed.
- When `requires_manual_review=True` a `ValueError` is raised (cannot apply
  programmatically).
- `_is_allowed_target(item.target_file)` is checked before any mutation; raises
  `ValueError` on a disallowed path.
- All existing Phase 7 tests for `apply_repair` (currently asserting
  `NotImplementedError`) are updated to match the new behaviour.

**Todo List**  
1. Read existing `apply_repair` stub and its Phase 7 tests.
2. Implement line-deletion path (empty `proposed_text`): find the line containing
   `original_text`, strip that line.
3. Implement text-replacement path: `file_content.replace(original_text, proposed_text, 1)`.
4. Add `_is_allowed_target` guard at the top of the function.
5. Raise `ValueError` when `requires_manual_review=True`.
6. Update the Phase 7 tests that previously expected `NotImplementedError` —
   replace with tests for the correct new behaviours.

**Relevant Context**  
- [`agentlint/policy/adapters.py`](agentlint/policy/adapters.py) — `apply_repair` stub, `_is_allowed_target`.
- [`tests/unit/test_policy.py`](tests/unit/test_policy.py) — existing `apply_repair` tests (look for `NotImplementedError`).

**Status:** [ ] pending

---

## Sub-Task 2 — Implement `agentlint/validation/structural.py` — Layer A

**Intent**  
Layer A re-runs the full deterministic scan and checks that any findings whose
`status="approved"` in `findings.json` are no longer present in the fresh scan
results. This proves structural repairs actually landed in the instruction files.

**Expected Outcomes**  
- `run_structural_check(repo_path, approved_finding_ids) -> list[ValidationResult]`
  is the public function.
- Returns one `ValidationResult` per approved finding: `passed=True` when the finding
  is absent from the re-scan, `passed=False` when it is still present.
- Uses `run_deterministic_checks()` from `agentlint/analysis/__init__.py` (no new
  scan orchestration — reuse `_run_pipeline` from `cli.py` is *not* required here;
  calling the analysis function directly is sufficient).
- Does not write any files; the caller (runner) writes `verification.json`.

**Todo List**  
1. Replace stub content of `structural.py`.
2. Import `collect_evidence`, `discover_sources`, `extract_rules`,
   `run_deterministic_checks`, `load_config`.
3. Implement `run_structural_check(repo_path, approved_finding_ids)`.
4. Fresh findings from re-scan compared against `approved_finding_ids`:
   a finding is "resolved" if no fresh finding has the same `type`, `title`, and
   the same `instruction_rules` (IDs reset after re-scan, so match on content).
5. Return `ValidationResult` list — one entry per approved ID.

**Relevant Context**  
- [`agentlint/validation/structural.py`](agentlint/validation/structural.py) — stub.
- [`agentlint/analysis/__init__.py`](agentlint/analysis/__init__.py) — `run_deterministic_checks`.
- [`agentlint/models.py`](agentlint/models.py) — `ValidationResult` dataclass.

**Status:** [ ] pending

---

## Sub-Task 3 — Implement `agentlint/validation/evidence_check.py` — Layer B

**Intent**  
Layer B verifies that every high-value field in `policy.yaml` still has current
evidence in the repository. If the policy says `package_manager: pnpm` but the
lockfile has disappeared, that is a regression.

**Expected Outcomes**  
- `run_evidence_check(policy, evidence) -> list[ValidationResult]` is the public
  function.
- One `ValidationResult` per high-value policy field (`package_manager`,
  `test_framework`, `lint_command`, `test_command`, `build_command`).
- `passed=True` when matching evidence still exists; `passed=False` when evidence
  is gone or contradicts the policy value.
- `evidence` field on the result lists the matching `RepositoryEvidence` ids.
- No subprocess calls; purely data-driven.

**Todo List**  
1. Replace stub content of `evidence_check.py`.
2. Define `_HIGH_VALUE_FIELDS` mapping policy field → evidence category + key.
3. Implement `run_evidence_check(policy: CanonicalPolicy, evidence: list[RepositoryEvidence])`.
4. For each high-value field: look up the policy value, find matching evidence,
   set `passed` accordingly.
5. Populate `stdout_excerpt` with a short human-readable result line
   (e.g. `"policy.package_manager=pnpm — evidence: pnpm-lock.yaml PASS"`).

**Relevant Context**  
- [`agentlint/validation/evidence_check.py`](agentlint/validation/evidence_check.py) — stub.
- [`agentlint/models.py`](agentlint/models.py) — `ValidationResult`, `CanonicalPolicy`, `RepositoryEvidence`.
- AgentLintplan.md §Phase 8 Layer B example output.

**Status:** [ ] pending

---

## Sub-Task 4 — Implement `agentlint/validation/commands.py` — Layer C

**Intent**  
Layer C runs the safe commands from `definition_of_done` with a timeout, capturing
exit code and output excerpt. This is the key differentiator AgentLintplan.md calls
out: "Can the recommended commands actually run successfully?"

This layer has a hard-safety contract:
- Only commands in `definition_of_done` may be executed.
- The command allowlist prevents `rm`, `del`, `git push`, destructive operations.
- Execution can be disabled entirely by the caller (for CI / demo mode).
- Timeout per command (default 60 s; configurable).

**Expected Outcomes**  
- `run_command_validation(policy, repo_path, *, timeout_sec=60, skip_execution=False) -> list[ValidationResult]`
  is the public function.
- When `skip_execution=True`: returns results with `passed=None` (cannot determine)
  and `stdout_excerpt="[execution disabled]"`.
- When a command fails the allowlist check: `passed=False`, `stdout_excerpt`
  contains the rejection reason; command is not run.
- When execution is enabled: runs each command in `repo_path`, captures
  stdout/stderr (first 500 chars), records `duration_ms` and exit code.
- `passed=True` when exit code is 0.

**Todo List**  
1. Replace stub content of `commands.py`.
2. Define `_ALLOWLIST_REJECT` regex patterns (reject any command containing
   `rm`, `del`, `rmdir`, `git push`, `git reset --hard`, `git clean`,
   `format`, `DROP`, etc.).
3. Implement `_is_safe_command(cmd: str) -> bool`.
4. Implement `_run_command(cmd, cwd, timeout_sec) -> tuple[int, str, str, int]`
   (exit_code, stdout_excerpt, stderr_excerpt, duration_ms).
5. Implement `run_command_validation(policy, repo_path, ...)`.
6. Log each command to stdout before running (per spec: "show command before
   execution").

**Relevant Context**  
- [`agentlint/validation/commands.py`](agentlint/validation/commands.py) — stub.
- AgentLintplan.md §Phase 8 Layer C rules.
- AGENTS.md — "Command runner must have a timeout and an allowlist".
- [`agentlint/models.py`](agentlint/models.py) — `ValidationResult`.

**Status:** [ ] pending

---

## Sub-Task 5 — Implement `agentlint/validation/evidence_check.py` Layer D (instruction consistency check)

> **Note:** Layer D is logically part of `structural.py` or can be a dedicated
> function in `evidence_check.py`. Given the spec says "confirm supported instruction
> files no longer contain known contradictions", the cleanest approach is a new
> function in `structural.py` that runs F01/F05 detectors only.

**Intent**  
Layer D runs only the cross-instruction conflict and duplicate detectors (F01, F05)
on the post-repair instruction state and reports whether any remain.

**Expected Outcomes**  
- `run_consistency_check(repo_path) -> list[ValidationResult]` is the public function
  (added to `structural.py`).
- Returns one `ValidationResult` per detected remaining contradiction or duplicate;
  or one passing result when none are found.
- `passed=True` when no F01/F05 findings remain; `passed=False` per finding that
  persists.

**Todo List**  
1. Add `run_consistency_check(repo_path)` to `structural.py`.
2. Re-run discovery + parsing + F01 + F05 only.
3. For each remaining finding: add a `ValidationResult` with `passed=False`.
4. If none: add a single `ValidationResult(passed=True, name="Instruction Consistency")`.

**Relevant Context**  
- [`agentlint/analysis/deterministic_rules.py`](agentlint/analysis/deterministic_rules.py) — `detect_f01_cross_file_conflicts`.
- [`agentlint/analysis/duplicates.py`](agentlint/analysis/duplicates.py) — `detect_f05_duplicates`.

**Status:** [ ] pending

---

## Sub-Task 6 — Implement `agentlint/validation/runner.py` — orchestration

**Intent**  
`runner.py` is the single orchestration point for verification. It loads
`findings.json` and `policy.yaml`, calls all four layers in order (A → B → C → D),
aggregates results into a `VerificationReport` dict, and writes
`.agentlint/verification.json`.

**Expected Outcomes**  
- `run_verification(repo_path, *, skip_commands=False, command_timeout=60) -> dict`
  is the public function (returns the report dict, also written to disk).
- Reads `findings.json` to get approved finding IDs.
- Reads `policy.yaml` (via `agentlint/policy/schema.py` or direct yaml load) to
  get the compiled policy.
- Aggregates all `ValidationResult` objects from layers A–D.
- Writes `.agentlint/verification.json` with schema:
  ```json
  {
    "agentlint_version": "0.1.0",
    "repo_path": "...",
    "timestamp": "...",
    "summary": { "total": N, "passed": N, "failed": N },
    "results": [ ...ValidationResult dicts... ]
  }
  ```
- Returns the dict.

**Todo List**  
1. Replace stub content of `runner.py`.
2. Implement `_load_approved_ids(repo_path) -> list[str]` (reads `findings.json`,
   returns IDs with `status="approved"`).
3. Implement `_load_policy(repo_path) -> CanonicalPolicy | None` (reads
   `policy.yaml`, returns None if not found).
4. Implement `run_verification(repo_path, *, skip_commands, command_timeout)`.
5. Aggregate results, compute summary counts, write `verification.json`.
6. Return the report dict.

**Relevant Context**  
- [`agentlint/validation/runner.py`](agentlint/validation/runner.py) — stub.
- [`agentlint/models.py`](agentlint/models.py) — `ValidationResult`.
- [`agentlint/policy/schema.py`](agentlint/policy/schema.py) — `POLICY_SCHEMA_VERSION`.

**Status:** [ ] pending

---

## Sub-Task 7 — Update `agentlint/validation/__init__.py`

**Intent**  
Expose the public API of the validation sub-package so callers can import from
`agentlint.validation` without knowing internal module names.

**Expected Outcomes**  
- `from agentlint.validation import run_verification` works.
- `__all__` is defined.

**Todo List**  
1. Replace stub `__init__.py` with proper imports from `runner`, `structural`,
   `evidence_check`, `commands`.
2. Export `run_verification` as the primary entry point.

**Relevant Context**  
- [`agentlint/validation/__init__.py`](agentlint/validation/__init__.py) — one-line stub.

**Status:** [ ] pending

---

## Sub-Task 8 — Add `agentlint validate` CLI subcommand to `agentlint/cli.py`

**Intent**  
Add the `agentlint validate <repo-path>` command that calls `run_verification`,
prints per-check results, and exits with code 1 if any checks failed.

**Expected Outcomes**  
- `agentlint validate <repo-path>` runs verification and prints a summary table.
- `--skip-commands` flag disables subprocess execution (for CI / demo use).
- `--timeout` option (default 60) sets per-command timeout seconds.
- Exit code 0 when all checks pass; exit code 1 on any failure.
- Prints: "Wrote .agentlint/verification.json" on success.
- Works on all three demo repos (even if policy/findings artifacts do not exist yet,
  it should print a meaningful error rather than crash).

**Todo List**  
1. Add `validate` command to `cli.py` using `@app.command("validate")`.
2. Accept `repo_path`, `--skip-commands` bool flag, `--timeout` int option.
3. Call `run_verification(path, skip_commands=..., command_timeout=...)`.
4. Print per-result status lines: `[PASS]` / `[FAIL]` with check name.
5. Print summary line: `N/M checks passed`.
6. Exit 1 if any result has `passed=False`.
7. Handle missing `findings.json` / `policy.yaml` gracefully (print guidance,
   exit 1).

**Relevant Context**  
- [`agentlint/cli.py`](agentlint/cli.py) — existing pattern for commands.
- [`agentlint/validation/__init__.py`](agentlint/validation/__init__.py).

**Status:** [ ] pending

---

## Sub-Task 9 — Unit tests for `agentlint/validation/`

**Intent**  
Full unit test coverage for each validation module, following existing test patterns.

**Expected Outcomes**  
- `tests/unit/test_validation.py` created.
- Tests cover: `apply_repair` success paths, `run_structural_check`,
  `run_evidence_check`, `run_command_validation` (with `skip_execution=True`),
  `run_consistency_check`, `run_verification` (with mocked sub-layers).
- Each function has at least one passing and one failing scenario.
- All existing 338 tests continue to pass.

**Todo List**  
1. Create `tests/unit/test_validation.py`.
2. Test `apply_repair`: replace path, delete path, manual-review `ValueError`,
   disallowed-target `ValueError`.
3. Test `run_evidence_check`: all fields present → all pass; missing evidence → fail.
4. Test `run_command_validation` with `skip_execution=True` (no subprocess).
5. Test `run_command_validation` allowlist rejection.
6. Test `run_structural_check` with a fake re-scan (mock `run_deterministic_checks`).
7. Test `run_verification` end-to-end using a temp dir with pre-written artifacts.

**Relevant Context**  
- [`tests/unit/test_policy.py`](tests/unit/test_policy.py) — existing test patterns.
- [`tests/unit/test_analysis.py`](tests/unit/test_analysis.py) — fixture patterns.

**Status:** [ ] pending

---

## Sub-Task 10 — Integration tests for `agentlint validate` CLI

**Intent**  
Verify the `agentlint validate` CLI command works end-to-end on the demo repos with
pre-seeded artifacts.

**Expected Outcomes**  
- `tests/integration/test_validate_cli.py` created.
- At minimum: test that `agentlint validate <demo-repo> --skip-commands` runs
  without crashing on all three demo repos.
- Test that `verification.json` is written and contains expected keys.
- Test that missing `findings.json` prints a useful error (not a stack trace).

**Todo List**  
1. Create `tests/integration/test_validate_cli.py`.
2. Use Typer's `CliRunner` (same pattern as `test_policy_cli.py`).
3. Pre-seed `.agentlint/findings.json` and `policy.yaml` in temp dirs.
4. Run `agentlint validate --skip-commands` and assert exit code.
5. Assert `verification.json` written with correct schema.
6. Test missing-artifacts error path.

**Relevant Context**  
- [`tests/integration/test_policy_cli.py`](tests/integration/test_policy_cli.py) — pattern for CLI integration tests.

**Status:** [ ] pending

---

## Sub-Task 11 — Update `PROGRESS.md`

**Intent**  
Document Phase 8 completion per the spec's "Rule 3 — Keep PROGRESS.md" requirement.

**Expected Outcomes**  
- Phase 8 section added to `PROGRESS.md` with file list, commands run, test results,
  acceptance criteria, and known issues.
- Phase checklist at top of `PROGRESS.md` updated.

**Todo List**  
1. Add Phase 8 entry to PROGRESS.md phase checklist.
2. Add full Phase 8 section with all required fields after the Phase 7 section.

**Status:** [ ] pending

---

## Files to Create

| File | Action |
|------|--------|
| `agentlint/validation/structural.py` | Implement (replace stub) |
| `agentlint/validation/evidence_check.py` | Implement (replace stub) |
| `agentlint/validation/commands.py` | Implement (replace stub) |
| `agentlint/validation/runner.py` | Implement (replace stub) |
| `agentlint/validation/__init__.py` | Implement (replace stub) |
| `tests/unit/test_validation.py` | Create new |
| `tests/integration/test_validate_cli.py` | Create new |

## Files to Modify

| File | Change |
|------|--------|
| `agentlint/policy/adapters.py` | Implement `apply_repair()` (remove `NotImplementedError` stub) |
| `agentlint/cli.py` | Add `agentlint validate` subcommand |
| `tests/unit/test_policy.py` | Update `apply_repair` tests that expected `NotImplementedError` |
| `PROGRESS.md` | Add Phase 8 section |

---

## Dependencies Required

No new third-party packages. All required stdlib modules:

- `subprocess` — for Layer C command execution.
- `datetime` — for timestamp in `verification.json`.
- `json` — already used.
- `pathlib` — already used.
- `re` — already used.
- `time` — for `duration_ms` measurement.

`PyYAML` is already installed (used in Phase 7 `policy/schema.py`).

---

## Commands That Must Be Run

```bash
# After implementation — run full test suite
python -m pytest tests/unit/test_validation.py -v
python -m pytest tests/integration/test_validate_cli.py -v
python -m pytest -v  # all 338+ tests must pass

# Manual acceptance check
python -m agentlint.cli validate demo_repos/inconsistent-js-repo --skip-commands
python -m agentlint.cli validate demo_repos/single-agent-stale-repo --skip-commands
python -m agentlint.cli validate demo_repos/clean-repo --skip-commands
```

---

## Acceptance Criteria (from AgentLintplan.md §Phase 8)

| Criterion | Check |
|-----------|-------|
| Layer A: re-scan confirms approved findings disappeared | `run_structural_check` returns `passed=True` for findings that were fixed |
| Layer B: every high-value policy field has evidence | `run_evidence_check` passes for each field with matching evidence |
| Layer C: safe commands run with timeout; exit code captured | `run_command_validation` runs commands, records duration_ms and exit code |
| Layer C: destructive commands are rejected | `_is_safe_command` blocks `rm`, `del`, `git push`, etc. |
| Layer C: execution can be disabled | `skip_execution=True` returns non-crashing results |
| Layer D: no remaining contradictions | `run_consistency_check` returns `passed=True` for clean repos |
| `verification.json` written to `.agentlint/` | File exists with `summary`, `results` keys |
| `agentlint validate` CLI subcommand exists | `agentlint validate <repo>` runs without error |
| Exit code 1 when checks fail | CLI exits 1 on any `passed=False` result |
| Claim discipline: no over-claiming | AgentLint only claims "repaired files are consistent with evidence and commands passed" |

---

## Risks and Conflicts with Existing Code

### Risk 1 — `apply_repair` test update
The test in `tests/unit/test_policy.py` that currently asserts `NotImplementedError`
on `apply_repair` **must** be updated. If missed, those tests will fail. Action: 
identify all tests calling `apply_repair` and update them in Sub-Task 1.

### Risk 2 — Re-scan finding ID instability in Layer A
Fresh scan IDs are re-assigned sequentially (see `_assign_finding_ids` in
`agentlint/analysis/__init__.py`). A finding's `id` field changes between scans.
Layer A must match on content (type + title + instruction_rules text), not on ID.
Action: document and implement content-based matching in Sub-Task 2.

### Risk 3 — Command execution on Windows
The project's dev environment is Windows (`powershell.exe`). `subprocess` with
`shell=True` behaves differently. Commands like `pnpm lint` may not be in PATH.
Action: wrap subprocess calls with `shell=True` on Windows; catch `FileNotFoundError`
and treat it as `passed=False` with a descriptive message.

### Risk 4 — Demo repos do not have approved findings
The demo repos' `.agentlint/findings.json` files may not have any findings with
`status="approved"`. Layer A will have no approved IDs to check. The runner must
handle an empty approved-ID list gracefully (return a single info-level result:
"No approved findings to verify").

### Risk 5 — Missing `policy.yaml` or `findings.json` in validate command
If the user runs `agentlint validate` before `agentlint policy`, those files won't
exist. The CLI must detect this and print clear guidance: "Run 'agentlint policy
<repo>' first." rather than crashing on a `FileNotFoundError`.

### Risk 6 — Scope creep into Phase 9
Phase 8 does NOT implement Streamlit UI changes. The `agentlint/ui/` module must not
be touched. The `view_models.py` may reference `ValidationResult` in the future but
that is Phase 9 work.
