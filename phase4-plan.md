# Phase 4 Plan — Deterministic Finding Engine

## Overview

Phase 4 implements the core lint engine: comparing parsed instruction rules
(Phase 3) against collected repository evidence (Phase 2) to produce a list of
`Finding` objects, written to `.agentlint/findings.json`.

**Every finding produced in this phase must be fully deterministic — no LLM,
no Bob, no network.** Bob's grounded role begins in Phase 6.

**Definition of Done (from spec §Phase 4):**

> The packaged inconsistent repo produces known golden findings with no LLM.

Concrete acceptance check:

```bash
agentlint scan demo_repos/single-agent-stale-repo
# Must write .agentlint/findings.json containing at least:
#   - F02 package_manager mismatch (npm vs pnpm)
```

Output artifact: `.agentlint/findings.json`

---

## Finding Types Implemented in Phase 4

From §9 + §Phase 4:

| ID | Name | Logic |
|---|---|---|
| F01 | Cross-Instruction Conflict | Two instruction files give conflicting normalized_value for same normalized_key |
| F02 | Instruction vs Repository Mismatch | Rule normalized_value ≠ strong evidence value for same category/key |
| F03 | Stale Path | Rule category=paths references a path that does not exist in repo |
| F04 | Invalid/Stale Command | Rule mentions `X run Y` pattern but script `Y` absent from evidence commands |
| F05 | Exact Duplicate Rule | Two rules normalize to same text (case/whitespace/punctuation folded) from any source |

F06 (Missing Context) and F07 (Ambiguous) are Bob-only — deferred to Phase 6.

---

## Architecture

```
list[InstructionRule]  +  list[RepositoryEvidence]
            │
            ▼
   analysis/deterministic_rules.py
   run_deterministic_checks(rules, evidence) → list[Finding]
     ├── detect_f01_cross_file_conflicts(rules)         → list[Finding]
     ├── detect_f02_mismatch(rules, evidence)           → list[Finding]
     ├── detect_f03_stale_paths(rules, evidence)        → list[Finding]
     ├── detect_f04_invalid_commands(rules, evidence)   → list[Finding]
     └── detect_f05_duplicates(rules)                   → list[Finding]
            │
            ▼
   analysis/__init__.py
   write_findings_json(repo_path, findings) → Path
```

All public functions live in `analysis/__init__.py`.
Internal detectors live in `analysis/deterministic_rules.py`.
`conflicts.py`, `duplicates.py`, `scoring.py`, `report_builder.py` are addressed below.

---

## Sub-Tasks

---

### Sub-Task A — F02/F01 Core Detectors (`agentlint/analysis/deterministic_rules.py`)

**Intent:** Implement the two highest-value finding generators:
F02 (rule vs repo mismatch) and F01 (cross-instruction conflict).
These are the most important findings for the demo and the hardest to get right
without false positives.

**Expected Outcomes:**

- `detect_f02_mismatch(rules, evidence) -> list[Finding]`  
  For each rule where `category` ∈ `{package_manager, test_framework, linting}`
  and `normalized_value` is non-None, find strong evidence of the same category.
  If no strong evidence matches the rule's value, emit an F02 Finding.
  - Only fires when evidence strength is `"strong"` (avoids false positives from
    weak/medium CI hints).
  - Confidence = 0.95 when strong evidence conflicts; 0.7 when medium-only evidence conflicts.
  - Severity: `"high"` for package_manager/test_framework; `"medium"` for linting.

- `detect_f01_cross_file_conflicts(rules) -> list[Finding]`  
  Group rules by `(normalized_key, source_path)`. If two *different* source files
  have rules for the same `normalized_key` with *different* `normalized_value`,
  emit an F01 Finding for each conflicting pair.
  - Only fires when both rules have `normalized_value` non-None.
  - Confidence = 0.9 (deterministic text comparison).
  - Severity: `"high"`.

**Key matching invariant:** Category names in `InstructionRule.category` must
exactly match `RepositoryEvidence.category` strings:
`"package_manager"`, `"test_framework"`, `"linting"`, `"commands"`, `"paths"`, `"runtime"`.
This alignment was designed into Phase 3 (see §Phase 3 Risks).

**Finding ID scheme:** `"find-{type_lower}-{index:03d}"` e.g. `"find-f02-001"`.
Each `run_deterministic_checks` call resets the counter per type.

**Relevant Context:** §9 Finding Types, §10 Severity Model, §13.4 Finding dataclass.

**Status:** [ ] pending

---

### Sub-Task B — F03 Stale Path Detector

**Intent:** Check every `category=paths` rule against the actual directory index
from Phase 2 evidence.

**Expected Outcomes:**

- `detect_f03_stale_paths(rules, evidence) -> list[Finding]`  
  For each rule where `category == "paths"` and `normalized_value` is non-None:
  check whether any `RepositoryEvidence` with `category="paths"` and
  `value` equal to the rule's path (or a normalized equivalent) exists.
  If no match, emit an F03 Finding.
  - Path normalization: strip leading/trailing slashes and backticks, lowercase.
  - Conservative matching: a rule referencing `src/services/` does not fail if
    `src/` exists — only fail when the most specific path segment is absent.
    A path fails only if neither the exact path NOR any evidence path starts with
    the same root segment as the rule path.
  - Confidence = 0.8 (conservative per spec §25 Scenario C).
  - Severity: `"medium"`.

**Relevant Context:** §Phase 4 F03, §25 Scenario C, `agentlint/evidence/paths.py`.

**Status:** [ ] pending

---

### Sub-Task C — F04 Invalid Command Detector

**Intent:** Detect instructions that reference `npm run X` / `pnpm X` / `yarn X`
patterns where script `X` is absent from the package scripts evidence.

**Expected Outcomes:**

- `detect_f04_invalid_commands(rules, evidence) -> list[Finding]`  
  For each rule where `category == "commands"` or whose text contains an
  `X run Y` pattern:
  extract the script name `Y` using a regex.
  Look up whether any `RepositoryEvidence` with `category="commands"` has
  `value` containing `Y` as a known script key.
  If script `Y` is absent from evidence, emit an F04 Finding.
  - Only fires when the evidence set contains at least one commands entry
    (avoids false positives on repos with no package.json).
  - Confidence = 0.85.
  - Severity: `"medium"`.

**Relevant Context:** §Phase 4 F04, §25 Scenario D, `agentlint/evidence/commands.py`.

**Status:** [ ] pending

---

### Sub-Task D — F05 Duplicate Rule Detector (`agentlint/analysis/duplicates.py`)

**Intent:** Find exact duplicate rules within or across instruction files after
whitespace/case/punctuation normalization.

**Expected Outcomes:**

- `detect_f05_duplicates(rules) -> list[Finding]`  
  For each rule, compute a fingerprint: lowercase, collapse whitespace, strip
  leading/trailing punctuation.
  Group rules by fingerprint. Groups with ≥ 2 members that share the same
  fingerprint emit one F05 Finding (listing all matching rule IDs).
  - Severity: `"low"`.
  - Confidence = 1.0 (exact text match after normalization).

**Relevant Context:** §9 F05 MVP definition.

**Status:** [ ] pending

---

### Sub-Task E — Public API + findings.json Output (`agentlint/analysis/__init__.py`)

**Intent:** Provide the top-level functions that the CLI calls, following the
same pattern as `agentlint/evidence/__init__.py` and `agentlint/parsing/__init__.py`.

**Expected Outcomes:**

- `run_deterministic_checks(rules, evidence) -> list[Finding]`  
  Calls all five detectors in order (F01 → F02 → F03 → F04 → F05).
  Assigns sequential Finding IDs across all findings.
  Returns the combined list sorted by severity (critical → info).

- `write_findings_json(repo_path: Path, findings: list[Finding]) -> Path`  
  Writes `.agentlint/findings.json` with schema:
  ```json
  {
    "agentlint_version": "0.1.0",
    "repo_path": "...",
    "findings": [ { ...Finding fields... } ]
  }
  ```
  Returns the path of the written file.

- Helper: `_assign_finding_ids(findings: list[Finding]) -> None`  
  Mutates findings in-place; IDs use scheme `"find-{type_lower}-{seq:03d}"`.

**Relevant Context:** §14 Output Files, §15 `agentlint scan`.

**Status:** [ ] pending

---

### Sub-Task F — CLI Extension (`agentlint/cli.py`)

**Intent:** Extend `agentlint scan` to invoke the deterministic finding engine
and write `findings.json`, following the Phase 2 → Phase 3 extension pattern.

**Expected Outcomes:**

- After `write_rules_json`, the `scan` command:
  1. Calls `run_deterministic_checks(rules, evidence)`.
  2. Prints a brief findings summary to stdout:
     `Findings: N finding(s) — K critical, M high, ...`
     plus per-type breakdown (e.g., `  F02 (mismatch): 2`).
  3. Writes `.agentlint/findings.json` via `write_findings_json`.

- Phase 1–3 outputs (scan.json, evidence.json, rules.json) are unaffected.

**Relevant Context:** §15 `agentlint scan`.

**Status:** [ ] pending

---

### Sub-Task G — Tests (`tests/unit/test_analysis.py`)

**Intent:** Cover the deterministic finding engine thoroughly.
All tests use inline fixtures — no disk access except `write_findings_json`
which uses `tmp_path`.

**Test cases required:**

| Test | Scenario |
|---|---|
| `test_f02_pm_mismatch_fires` | Rule says npm, strong evidence says pnpm → F02 found |
| `test_f02_pm_no_mismatch` | Rule says pnpm, strong evidence says pnpm → no F02 |
| `test_f02_medium_evidence_fires` | Rule says npm, only medium evidence says pnpm → F02 with lower confidence |
| `test_f02_no_evidence_no_finding` | Rule says npm, no evidence for package_manager → no F02 |
| `test_f02_test_framework_mismatch` | Rule says jest, strong evidence says vitest → F02 |
| `test_f01_conflict_two_files` | AGENTS.md says npm, CLAUDE.md says pnpm → F01 |
| `test_f01_no_conflict_same_file` | Same file says npm twice → no F01 |
| `test_f01_no_conflict_same_value` | Both files say pnpm → no F01 |
| `test_f03_stale_path_fires` | Rule refs `src/services/`, no evidence for that path → F03 |
| `test_f03_valid_path_no_finding` | Rule refs `src/`, evidence has `src/` → no F03 |
| `test_f04_invalid_command_fires` | Rule says `npm run test:unit`, scripts have no `test:unit` → F04 |
| `test_f04_valid_command_no_finding` | Rule says `npm run test`, scripts have `test` → no F04 |
| `test_f04_no_commands_evidence_skipped` | No commands evidence → no F04 |
| `test_f05_exact_duplicate` | Same text in two files → F05 |
| `test_f05_no_duplicate` | All unique rules → no F05 |
| `test_f05_case_insensitive` | "Use pnpm" and "use pnpm" → F05 |
| `test_run_deterministic_checks_combined` | Full pipeline with multiple finding types |
| `test_findings_ids_assigned` | All returned findings have non-empty IDs |
| `test_findings_deterministic_flag` | All Phase 4 findings have deterministic=True |
| `test_write_findings_json_schema` | JSON has agentlint_version + findings array |
| `test_write_findings_json_empty` | Empty findings list writes valid JSON |

All existing 125 tests must continue to pass.

**Status:** [ ] pending

---

### Sub-Task H — Add AGENTS.md to `inconsistent-js-repo` for F01 golden scenario

**Intent:** Phase 4's Definition of Done requires the inconsistent-js-repo to
produce known golden findings. The repo currently has no instruction files.
Add a minimal AGENTS.md that conflicts with the pnpm/Vitest reality so Scenario A
from §25 is testable.

**Expected Outcomes:**

- `demo_repos/inconsistent-js-repo/AGENTS.md` — created with npm + Jest
  contradicting the repo's pnpm + Vitest reality.
- Running `agentlint scan demo_repos/inconsistent-js-repo` produces:
  - F02 package_manager mismatch (AGENTS.md says npm, repo says pnpm)
  - F02 test_framework mismatch (AGENTS.md says jest, repo says vitest)

**Relevant Context:** §25 Scenario A, §Phase 5 (full demo repo content is Phase 5 —
Phase 4 only needs a minimal file to exercise finding detection).

**Status:** [ ] pending

---

### Sub-Task I — PROGRESS.md Update

**Intent:** Mark Phase 4 complete after all criteria pass.

**Expected Outcomes:**

- `- [x] Phase 4` in the checklist.
- Phase 4 section with: files created, commands run, test results, acceptance
  criteria status.

**Status:** [ ] pending

---

## Files Created / Modified

| File | Action | Notes |
|---|---|---|
| `agentlint/analysis/deterministic_rules.py` | replace stub | F01, F02, F03, F04 detectors |
| `agentlint/analysis/duplicates.py` | replace stub | F05 duplicate detector |
| `agentlint/analysis/__init__.py` | replace stub | `run_deterministic_checks()` + `write_findings_json()` |
| `agentlint/analysis/conflicts.py` | may fold into deterministic_rules.py | F01 logic |
| `agentlint/analysis/scoring.py` | replace stub | severity/confidence helpers (used by detectors) |
| `agentlint/analysis/report_builder.py` | replace stub | `format_findings_summary()` for CLI stdout |
| `agentlint/cli.py` | extend | add findings phase + findings.json output to `scan` |
| `tests/unit/test_analysis.py` | create | ~21 tests |
| `demo_repos/inconsistent-js-repo/AGENTS.md` | create | minimal instruction file for golden scenario |
| `PROGRESS.md` | update | Phase 4 section |

**Not modified in Phase 4:**
- `agentlint/models.py` — `Finding` dataclass already complete
- `agentlint/parsing/` — Phase 3 complete, no changes needed
- `agentlint/evidence/` — Phase 2 complete, no changes needed
- `agentlint/policy/` — Phase 7
- `agentlint/validation/` — Phase 8
- `app.py` — Phase 9

---

## Severity & Confidence Rules

| Finding | Default Severity | Confidence (strong evidence) | Confidence (medium evidence) |
|---|---|---|---|
| F01 Cross-file conflict | high | 0.9 | 0.9 (rules are text, not evidence-strength-dependent) |
| F02 Mismatch (pm, tf) | high | 0.95 | 0.7 |
| F02 Mismatch (linting) | medium | 0.85 | 0.6 |
| F03 Stale path | medium | 0.8 | 0.8 |
| F04 Invalid command | medium | 0.85 | — |
| F05 Duplicate | low | 1.0 | — |

---

## Dependencies Required

No new dependencies. All analysis is pure Python stdlib:
- `re` — command pattern matching
- `json` — writing findings.json
- `collections` — Counter/defaultdict for grouping

---

## Commands That Must Be Run

```bash
pytest --tb=short -v
# Must show: 125 existing + ~21 new = ~146 tests, all passed

agentlint scan demo_repos/single-agent-stale-repo
# Must print: "Findings: N finding(s)"
# Must create: demo_repos/single-agent-stale-repo/.agentlint/findings.json
# findings.json must contain at least one F02 finding (npm vs pnpm mismatch)

agentlint scan demo_repos/inconsistent-js-repo
# Must produce: F02 package_manager mismatch, F02 test_framework mismatch

agentlint --help
# Must still work
```

---

## Acceptance Criteria (from §Phase 4 Definition of Done + §25)

| Criterion | Expected |
|---|---|
| `inconsistent-js-repo` produces known F02 package_manager finding | AGENTS.md npm vs pnpm evidence |
| `inconsistent-js-repo` produces known F02 test_framework finding | AGENTS.md jest vs vitest evidence |
| `single-agent-stale-repo` produces F02 package_manager finding | CLAUDE.md npm vs pnpm evidence |
| All findings have `deterministic=True` | no Bob entries in Phase 4 |
| `findings.json` schema: `agentlint_version`, `repo_path`, `findings` | top-level keys present |
| Phase 1–3 tests still pass (125) | no regressions |
| New Phase 4 tests pass (~21) | `test_analysis.py` all green |
| `agentlint scan` exits 0 for both demo repos | no traceback |

---

## Risks and Conflicts

| Risk | Detail | Mitigation |
|---|---|---|
| **Category alignment** | `InstructionRule.category` must exactly match `RepositoryEvidence.category` strings. Phase 3 was designed to match Phase 2 category strings, but cross-check at implementation. | Assert category strings at the start of `detect_f02_mismatch`; document the contract. |
| **Relative paths in rules** | `InstructionRule.source_path` is relative (e.g., `"CLAUDE.md"`). F01 compares source_path across rules — this comparison is string equality, which works correctly for relative paths. | No action needed, but note this. |
| **Path normalization for F03** | Rule text may say `` `src/services/` `` with backticks. The normalizer may not strip these. | Apply explicit backtick + quote stripping in the F03 detector, separate from the Phase 3 normalizer. |
| **Command pattern extraction for F04** | The rule text (not `normalized_value`) must be scanned for `run X` patterns. The Phase 3 normalizer does not reliably capture the script name `X` as `normalized_value` — it captures the full command string. | Use a regex in `detect_f04_invalid_commands` to extract the script name from `rule.text`. |
| **Evidence commands key format** | Phase 2 commands evidence uses key=`"test"`, value=`"vitest run"` (not key=script-name). F04 must match against evidence `value` strings, not `key`. | Parse script names from evidence `value` (split on spaces, take first token after `run`). |
| **F05 inflates rule count** | Every heading and paragraph block produces a rule. Many will have identical text (e.g. headings like "## Package Manager" appearing in two files). | F05 should only fire when rules have non-trivial content (text length > 10 chars). |
| **`inconsistent-js-repo` has no instruction file** | Phase 4's golden scenario requires it. | Sub-Task H adds a minimal AGENTS.md. Full demo repo content is Phase 5 — keep Phase 4 fixture minimal. |
| **F04 false positives on non-JS repos** | Python repos have no `npm run` commands. | F04 only fires when at least one `commands` evidence item exists (Sub-Task C guard). |

---

*Ready for implementation.*
