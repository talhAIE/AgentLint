# Phase 7 — Canonical Policy Compiler and Repair Plan

## Top-Level Overview

**Goal:** Convert the deterministic evidence already collected by the scan pipeline into two reviewable artifacts:

1. `.agentlint/policy.yaml` — a candidate canonical contract that maps each tooling choice back to the evidence that justified it.
2. `.agentlint/repair-plan.md` — per-file patch previews (original / proposed change / evidence / reason / expected effect) that require explicit human approval before any file is touched.

Phase 7 implements the four stub modules in `agentlint/policy/`, adds an `agentlint policy` CLI subcommand, and writes the required unit tests. It does **not** apply any repairs (that is Phase 8). It does **not** build the Streamlit UI (that is Phase 9).

---

## Sub-Task 1 — Implement `agentlint/policy/schema.py`

**Intent:** Define the `CanonicalPolicy` dataclass serialization helpers and the YAML schema constants. The `CanonicalPolicy` dataclass already exists in `agentlint/models.py`; this module provides the `to_yaml()` serializer and the schema version constant so all other modules import from one place.

**Expected Outcomes:**
- `policy_to_yaml(policy: CanonicalPolicy) -> str` produces a YAML string matching the example in `AgentLintplan.md §11`.
- `write_policy_yaml(repo_path: Path, policy: CanonicalPolicy) -> Path` writes `.agentlint/policy.yaml` and returns the path.
- Round-trip: a YAML written by `to_yaml` can be loaded back with `pyyaml` and reconstructed.

**Todo List:**
1. Replace the stub in `agentlint/policy/schema.py` with the real implementation.
2. Import `CanonicalPolicy` from `agentlint.models`.
3. Implement `policy_to_yaml(policy)` — use `pyyaml` `yaml.dump()` with `sort_keys=False`, `allow_unicode=True`, and produce the nested structure shown in `AgentLintplan.md §11`.
4. Implement `write_policy_yaml(repo_path, policy)` — ensure `.agentlint/` exists, write `policy.yaml`, return the `Path`.
5. Export both from `agentlint/policy/__init__.py`.

**Relevant Context:**
- [`agentlint/models.py`](agentlint/models.py) — `CanonicalPolicy` fields: `version`, `project_name`, `tooling`, `runtime`, `paths`, `definition_of_done`, `evidence`.
- `AgentLintplan.md §11` (lines 603–658) — exact YAML schema example with `tooling`, `runtime`, `paths`, `definition_of_done`, `evidence` keys.
- `pyyaml>=6.0` is already in `pyproject.toml`.

**Status:** [ ] pending

---

## Sub-Task 2 — Implement `agentlint/policy/compiler.py`

**Intent:** Build the compiler that transforms a list of `RepositoryEvidence` items into a `CanonicalPolicy`. This is the core Phase 7 engine — it picks the highest-strength evidence per category, constructs the tooling/runtime/paths/definition-of-done sections, and records which evidence IDs back each choice.

**Expected Outcomes:**
- `compile_policy(evidence: list[RepositoryEvidence], repo_path: Path) -> CanonicalPolicy` returns a fully populated `CanonicalPolicy`.
- Every tooling field is either populated from strong evidence or left as `None` (never fabricated).
- The `evidence` dict on the policy maps each tooling key to the list of `source_path` strings (and `source_locator` if present) from the backing `RepositoryEvidence` items.
- `definition_of_done` is built from detected commands (test command, lint command, build command) in the order: lint → test → build.
- Project name is inferred from `repo_path.name`.

**Todo List:**
1. Replace the stub in `agentlint/policy/compiler.py` with the real implementation.
2. Add helper `_best_evidence(items, category, key=None)` that returns the single strongest `RepositoryEvidence` for a given category (strong > medium > weak; first-wins within same strength).
3. Implement `_build_tooling(evidence)` — populate `package_manager`, `test_framework`, `test_command`, `lint_command`, `build_command` from evidence categories `package_manager`, `test_framework`, `commands`.
4. Implement `_build_runtime(evidence)` — populate `node`, `python`, or other runtime keys from `runtime` evidence.
5. Implement `_build_paths(evidence)` — populate `generated` and `protected` lists from `paths` evidence with `key in ("generated", "protected")`.
6. Implement `_build_definition_of_done(tooling)` — derive commands list in order: lint → test → build (only include if the command field is non-None).
7. Implement `_build_evidence_map(evidence)` — map each tooling key to the list of evidence source strings.
8. Assemble and return `CanonicalPolicy(version=1, ...)`.
9. Per the architectural constraint: this function generates a **candidate** only — it must never auto-apply or write files itself.

**Relevant Context:**
- [`agentlint/models.py`](agentlint/models.py) — `RepositoryEvidence` fields and `CanonicalPolicy` fields.
- [`agentlint/evidence/repository_truth.py`](agentlint/evidence/repository_truth.py) — `_CATEGORY_ABBREV` and evidence categories used.
- `AgentLintplan.md §11` — canonical policy YAML example showing which fields map to which evidence.
- AGENTS.md architectural constraint: "compiler.py generates a candidate only — it must never auto-apply."

**Status:** [ ] pending

---

## Sub-Task 3 — Implement `agentlint/policy/diff.py`

**Intent:** Generate per-finding patch previews showing original text, proposed replacement, evidence, reason, and expected effect. This is the "repair plan" content generator. Each finding that has a clear, safe deterministic fix gets a structured `RepairItem`; ambiguous findings get a manual-review block.

**Expected Outcomes:**
- `RepairItem` dataclass with fields: `finding_id`, `target_file`, `original_text`, `proposed_text`, `evidence_sources`, `reason`, `expected_effect`, `requires_manual_review: bool`.
- `generate_repair_items(findings, rules, evidence) -> list[RepairItem]` produces one `RepairItem` per actionable finding.
- `format_repair_plan(items) -> str` renders the Markdown repair plan matching the example in `AgentLintplan.md §Phase 7 Example Repair Plan`.
- `write_repair_plan(repo_path, items) -> Path` writes `.agentlint/repair-plan.md`.

**Todo List:**
1. Replace the stub in `agentlint/policy/diff.py`.
2. Define `RepairItem` as a `dataclass` with the fields listed above plus a `to_dict()` method.
3. Implement `generate_repair_items(findings, rules, evidence)`:
   - For F02 findings: propose replacing the stale tool name with the evidence-backed name (e.g., `"Use npm"` → `"Use pnpm"`).
   - For F01 findings: propose removing or reconciling conflicting lines.
   - For F03 findings: propose removing stale path references.
   - For F04 findings: propose correcting invalid commands.
   - For F05 findings: propose removing the duplicate rule (keep first occurrence).
   - If the original text cannot be determined safely, set `requires_manual_review=True` and leave `proposed_text` as an empty string.
4. Implement `format_repair_plan(items)` — numbered Markdown list matching the spec example format: file, action, evidence line.
5. Implement `write_repair_plan(repo_path, items)` — write to `.agentlint/repair-plan.md`.
6. The adapter strategy from the spec must be followed: preserve unrelated content, modify only identified stale/conflicting lines, prefer minimal diff.

**Relevant Context:**
- `AgentLintplan.md §Phase 7` lines 1725–1739 — example repair plan format.
- `AgentLintplan.md §Phase 7` lines 1713–1723 — Adapter Strategy rules.
- `AgentLintplan.md §Phase 7 Definition of Done` lines 1741–1749 — user must see: original, proposed change, evidence, reason, expected effect.
- [`agentlint/models.py`](agentlint/models.py) — `Finding`, `InstructionRule`, `RepositoryEvidence` fields.

**Status:** [ ] pending

---

## Sub-Task 4 — Implement `agentlint/policy/adapters.py`

**Intent:** Provide file-level adapter helpers that, given a `RepairItem`, locate the exact line(s) to change in a target instruction file and return a structured diff preview (not yet applied). This keeps `diff.py` at the logical level and `adapters.py` at the text-manipulation level.

**Expected Outcomes:**
- `build_text_preview(item: RepairItem, file_content: str) -> str` returns a fenced before/after diff string for display.
- `apply_repair(item: RepairItem, file_content: str) -> str` returns the new file content with the single repair applied (for use later in Phase 8 after approval — stubbed in Phase 7 to raise `NotImplementedError`).
- Supported targets: `AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md`, `.bob/**/*.md` — matches the mode's `fileRegex`.

**Todo List:**
1. Replace the stub in `agentlint/policy/adapters.py`.
2. Implement `build_text_preview(item, file_content)`:
   - Locate `item.original_text` in `file_content` (exact substring match).
   - Return a fenced block:
     ```
     --- original
     <original_text>
     +++ proposed
     <proposed_text>
     ```
   - If `item.requires_manual_review` is `True`, return a `[MANUAL REVIEW REQUIRED]` block instead.
3. Stub `apply_repair(item, file_content)` with `raise NotImplementedError("apply_repair is Phase 8")` — this is the architectural guard that enforces human approval comes before file mutation.
4. Keep `adapters.py` free of file I/O — callers pass file content as strings.

**Relevant Context:**
- `AgentLintplan.md §Phase 7 Adapter Strategy` lines 1713–1723 — "preserve unrelated content; modify only identified stale/conflicting lines where safe; otherwise propose manual replacement block; prefer minimal diff."
- `AgentLintplan.md §4.2` (lines 196–205) — "Human approval is a hard architectural requirement."
- `.bob/custom_modes.yaml` — `fileRegex` defines the allowed edit targets.

**Status:** [ ] pending

---

## Sub-Task 5 — Wire `agentlint/policy/__init__.py` and add `agentlint policy` CLI subcommand

**Intent:** Expose the Phase 7 engine through the public package API and add the `agentlint policy <repo-path>` CLI subcommand that reads an existing `.agentlint/` scan output (or runs a fresh scan), compiles the policy, generates repair items, and writes `policy.yaml` + `repair-plan.md`.

**Expected Outcomes:**
- `agentlint policy <repo-path>` runs, reads scan artifacts from `.agentlint/` (or re-scans if missing), calls `compile_policy()` and `generate_repair_items()`, writes both output files, and prints a summary to stdout.
- Output includes: path to `policy.yaml`, summary of tooling discovered, count of repair items generated, path to `repair-plan.md`.
- The command exits 0 on success even when there are findings (findings are advisory, not errors).

**Todo List:**
1. Update `agentlint/policy/__init__.py` to export `compile_policy`, `write_policy_yaml`, `generate_repair_items`, `write_repair_plan`, `RepairItem`.
2. Add `@app.command("policy")` to `agentlint/cli.py`:
   - Accept `repo_path: str` argument.
   - Validate path exists and is a directory.
   - Load config.
   - Re-run the full scan pipeline (same as `scan` command) to get fresh `evidence`, `rules`, `findings`.
   - Call `compile_policy(evidence, path)` to get a `CanonicalPolicy`.
   - Call `write_policy_yaml(path, policy)` and print the output path.
   - Call `generate_repair_items(findings, rules, evidence)` to get `RepairItem` list.
   - Call `write_repair_plan(path, items)` and print the output path.
   - Print tooling summary (package_manager, test_framework, definition_of_done).
   - Print count of repair items and "Approval required before changes are applied."
3. Import new policy symbols in `cli.py`.

**Relevant Context:**
- [`agentlint/cli.py`](agentlint/cli.py) — existing `scan` and `demo` commands; follow the same pattern (validate path → load config → pipeline → write outputs → print summary).
- `AgentLintplan.md §15` lines 903–906 — `agentlint policy` behavior spec.
- AGENTS.md: "Never auto-apply. Human approval is a hard architectural requirement."

**Status:** [ ] pending

---

## Sub-Task 6 — Write Tests

**Intent:** Achieve passing tests for all Phase 7 code. Tests must cover: policy compilation from evidence, repair item generation from findings, YAML serialization, repair plan Markdown format, and CLI integration.

**Expected Outcomes:**
- New test file `tests/unit/test_policy.py` with all unit tests passing.
- `pytest tests/unit/test_policy.py` exits 0.
- `pytest` (full suite) still exits 0 with no regressions.

**Todo List:**
1. Create `tests/unit/test_policy.py`.
2. **Schema tests:** `test_write_policy_yaml_creates_file`, `test_policy_yaml_contains_required_keys` (version, tooling, runtime, evidence), `test_policy_to_yaml_round_trips` (write + parse back == original fields).
3. **Compiler tests:** `test_compile_policy_empty_evidence` (returns `CanonicalPolicy` with empty tooling), `test_compile_policy_strong_pm_evidence` (pnpm lockfile → `package_manager: pnpm`), `test_compile_policy_prefers_strong_over_medium`, `test_compile_policy_evidence_map_populated`, `test_compile_policy_definition_of_done_ordered` (lint before test before build), `test_compile_policy_project_name_from_repo_path`.
4. **Diff tests:** `test_generate_repair_items_empty` (no findings → empty list), `test_generate_repair_items_f02_produces_item`, `test_generate_repair_items_f05_flags_duplicate`, `test_format_repair_plan_structure` (numbered list, contains evidence string), `test_write_repair_plan_creates_file`.
5. **Adapters tests:** `test_build_text_preview_shows_original_and_proposed`, `test_build_text_preview_manual_review_block`, `test_apply_repair_raises_not_implemented`.
6. **CLI integration test:** Add `test_policy_command` to `tests/integration/test_demo_repos.py` or a new `tests/integration/test_policy_cli.py` — run `agentlint policy demo_repos/inconsistent-js-repo`, assert exit code 0, assert `policy.yaml` and `repair-plan.md` are created.

**Relevant Context:**
- Existing test patterns in [`tests/unit/test_analysis.py`](tests/unit/test_analysis.py) and [`tests/unit/test_phase6_artifacts.py`](tests/unit/test_phase6_artifacts.py) — use `tmp_path` fixtures, construct test data with model constructors.
- [`agentlint/models.py`](agentlint/models.py) — `RepositoryEvidence`, `Finding`, `InstructionRule` constructors for building test fixtures.
- `pytest` is already installed as a dev dependency.

**Status:** [ ] pending

---

## Sub-Task 7 — Update `PROGRESS.md`

**Intent:** Keep `PROGRESS.md` as the source of truth per the project convention.

**Expected Outcomes:**
- `PROGRESS.md` has a new `## Phase 7` section with: goal, files created/modified, commands run, test results, acceptance criteria met.

**Todo List:**
1. Add `## Phase 7 — Canonical Policy Compiler and Repair Plan` section to `PROGRESS.md`.
2. Mark the phase checklist entry as complete.
3. Record test count and `pytest` invocation.
4. Record acceptance criteria status against each point in `AgentLintplan.md §Phase 7 Definition of Done`.

**Relevant Context:**
- [`PROGRESS.md`](PROGRESS.md) — existing phase sections as templates.

**Status:** [ ] pending

---

## Files To Create or Modify

| File | Action |
|------|--------|
| `agentlint/policy/schema.py` | Replace stub — implement `policy_to_yaml`, `write_policy_yaml` |
| `agentlint/policy/compiler.py` | Replace stub — implement `compile_policy` |
| `agentlint/policy/diff.py` | Replace stub — implement `RepairItem`, `generate_repair_items`, `format_repair_plan`, `write_repair_plan` |
| `agentlint/policy/adapters.py` | Replace stub — implement `build_text_preview`, stub `apply_repair` |
| `agentlint/policy/__init__.py` | Replace stub — export public API |
| `agentlint/cli.py` | Add `agentlint policy` subcommand |
| `tests/unit/test_policy.py` | Create — all unit tests for Phase 7 |
| `tests/integration/test_policy_cli.py` | Create — CLI integration test |
| `PROGRESS.md` | Add Phase 7 section |

No new Python package dependencies are required. `pyyaml` (already listed) handles YAML writing.

---

## Acceptance Criteria (from `AgentLintplan.md §Phase 7 Definition of Done`)

> User can see: original; proposed change; evidence; reason; expected effect.

Mapping to implementation:

| Criterion | Satisfied by |
|-----------|-------------|
| User can see the **original** text | `RepairItem.original_text` + `build_text_preview()` before block |
| User can see the **proposed change** | `RepairItem.proposed_text` + `build_text_preview()` after block |
| User can see the **evidence** | `RepairItem.evidence_sources` listed in repair-plan.md |
| User can see the **reason** | `RepairItem.reason` field in repair-plan.md |
| User can see the **expected effect** | `RepairItem.expected_effect` field in repair-plan.md |
| Policy is **candidate only** — no auto-apply | `apply_repair` raises `NotImplementedError`; CLI prints approval message |
| **`policy.yaml` traceable to evidence** | `CanonicalPolicy.evidence` dict maps each field to its source paths |
| **`repair-plan.md` exists** | `write_repair_plan()` writes it |

---

## Risks and Conflicts With Existing Code

1. **`agentlint/policy/__init__.py` is currently a stub with no exports.** Any import of policy symbols will fail until Sub-Task 5 is complete. Order: implement schema → compiler → diff → adapters → `__init__` → CLI.

2. **`CanonicalPolicy` is already defined in `agentlint/models.py`** — the schema module must import it from there, not redefine it. The `evidence` field type is `dict` (plain), so the YAML serializer must handle nested dicts.

3. **`cli.py` scan command re-runs the full pipeline.** The `agentlint policy` command should call the same `_run_scan_for_path` logic rather than duplicating it — but `_run_scan_for_path` currently doesn't return values. A small refactor of that helper (or a new one) is needed to return `(evidence, rules, findings)` so the policy command can consume them. This is a minimal internal refactor, not a scope change.

4. **`repair-plan.md` is an artifact read by the `/agentlint-repair` Bob slash command** (see `.bob/commands/agentlint-repair.md`). The Markdown format must include the word "Evidence:" on each item so the existing slash command can parse it correctly.

5. **`apply_repair` stubbed with `NotImplementedError`** — this is intentional and architecturally required. Tests must assert it raises `NotImplementedError`, not that it works.

6. **Path detection evidence contains many entries** — `compile_policy()` must filter path evidence carefully (only `generated`/`protected` key items contribute to `paths` section) to avoid polluting the policy with every directory in the repo.

7. **Windows encoding** — `write_policy_yaml` and `write_repair_plan` must explicitly use `encoding="utf-8"` when writing files, consistent with the existing convention in `cli.py` and `evidence/repository_truth.py`.

8. **`definition_of_done` ordering** — the spec shows `pnpm lint` before `pnpm test` before `pnpm build`. The compiler must enforce this canonical order (lint → test → build) regardless of evidence insertion order.
