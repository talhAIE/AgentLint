# Phase 1 Plan — Domain Models and Instruction Discovery

## Overview

Phase 1 implements two things:

1. **`agentlint/models.py`** — all six domain model dataclasses that every later phase depends on.
2. **`agentlint/discovery/instruction_sources.py`** — deterministic discovery of agent instruction files.

It also wires up the first real `agentlint scan` CLI command (enough to run discovery and write `scan.json`)
and adds `agentlint/config.py` (load `.agentlint/config.yaml` for `extra_instruction_paths`).

**Definition of Done (from spec §Phase 1):**

```
agentlint scan demo_repos/single-agent-stale-repo
```

Reports exactly one instruction source and does not fail.

---

## Existing State

| Item | Status |
|---|---|
| `agentlint/models.py` | stub (one comment line) |
| `agentlint/discovery/instruction_sources.py` | stub (one comment line) |
| `agentlint/discovery/repo_files.py` | stub (one comment line) |
| `agentlint/config.py` | stub (one comment line) |
| `agentlint/cli.py` | stub that prints "not implemented" and exits 0 |
| `demo_repos/single-agent-stale-repo/` | empty (`.gitkeep` only) |
| `tests/unit/` | smoke tests only |
| `tests/fixtures/` | empty |

---

## Sub-Tasks

---

### Sub-Task A — Domain Models (`agentlint/models.py`)

**Intent:** Implement all six dataclasses defined in §13 of the spec. These are the shared language
for every phase. Getting them right now means later phases never need to restructure data.

**Expected Outcomes:**
- `from agentlint.models import InstructionSource, InstructionRule, RepositoryEvidence, Finding, CanonicalPolicy, ValidationResult` succeeds.
- Each dataclass has all fields from §13, correct types, and correct defaults.
- `InstructionSource` and `Finding` have a helper method for serialising to a plain dict (for JSON output).
- No Pydantic or external deps — standard library `dataclasses` only.

**Fields to implement (verbatim from §13):**

```python
@dataclass
class InstructionSource:
    path: str
    agent_type: str
    content_hash: str       # hex SHA-256 of file bytes; empty string when exists=False
    exists: bool

@dataclass
class InstructionRule:
    id: str
    source_path: str
    source_agent: str
    text: str
    category: str | None
    normalized_key: str | None
    normalized_value: str | None
    line_start: int | None
    line_end: int | None
    extraction_method: str   # "deterministic" | "bob"
    confidence: float

@dataclass
class RepositoryEvidence:
    id: str
    category: str
    key: str
    value: str
    source_path: str
    source_locator: str | None
    strength: str            # "strong" | "medium" | "weak"
    explanation: str

@dataclass
class Finding:
    id: str
    type: str                # F01–F07
    severity: str            # "critical"|"high"|"medium"|"low"|"info"
    title: str
    explanation: str
    instruction_rules: list[str]    # InstructionRule ids
    evidence_ids: list[str]         # RepositoryEvidence ids
    recommended_action: str
    confidence: float
    deterministic: bool
    status: str              # "open"|"approved"|"repaired"|"ignored"

@dataclass
class CanonicalPolicy:
    version: int
    project_name: str | None
    tooling: dict            # package_manager, test_framework, etc.
    runtime: dict
    paths: dict
    definition_of_done: list[str]
    evidence: dict

@dataclass
class ValidationResult:
    check_id: str
    name: str
    command: str | None
    passed: bool
    duration_ms: int | None
    stdout_excerpt: str | None
    stderr_excerpt: str | None
    evidence: list[str]
```

**Helpers required:**
- `InstructionSource.to_dict()` — returns a JSON-serialisable plain dict.
- `Finding.to_dict()` — same.
- `RepositoryEvidence.to_dict()` — same.
- A module-level `dataclass_to_dict()` utility using `dataclasses.asdict()` to avoid repetition.

**Relevant Context:** §13 Data Models, §14 Output Files (JSON serialisation), §21 Rule 7 (no unnecessary deps).

**Status:** [ ] pending

---

### Sub-Task B — Config Loader (`agentlint/config.py`)

**Intent:** Implement a minimal config loader that reads `.agentlint/config.yaml` from a target
repo path and returns `extra_instruction_paths`. This is needed by discovery before instruction
scanning runs.

**Expected Outcomes:**
- `load_config(repo_path: Path) -> AgentLintConfig` works.
- Returns a typed config object (dataclass) with field `extra_instruction_paths: list[str]`.
- If `.agentlint/config.yaml` does not exist, returns defaults (empty extra paths) — no error.
- If the YAML is malformed, raises a clear `AgentLintConfigError` with the file path.
- Uses stdlib `pathlib.Path` + `yaml` (already a dependency).

**Config schema (from §Phase 1 spec):**
```yaml
extra_instruction_paths:
  - docs/ai-agent-guidance.md
```

**Relevant Context:** §Phase 1 Tasks (config file support), §22 Tech Stack (PyYAML already installed).

**Status:** [ ] pending

---

### Sub-Task C — Instruction Source Discovery (`agentlint/discovery/instruction_sources.py`)

**Intent:** Implement the deterministic discovery logic that finds all supported agent instruction
files in a target repository. This is the primary deliverable of Phase 1.

**Expected Outcomes:**
- `discover_sources(repo_path: Path, config: AgentLintConfig) -> list[InstructionSource]` works.
- Returns sources in a **stable, deterministic order** (fixed priority list, then extras alphabetically).
- Each source has a correct `exists` flag — sources that do not exist on disk are **included** (with `exists=False`) so downstream phases know what was checked.
- `content_hash` is set to SHA-256 hex of file bytes when the file exists; `""` otherwise.
- `agent_type` uses a string enum/constant: `"bob"`, `"claude"`, `"copilot"`, `"openai"`, `"cursor"`, `"custom"`.
- Extra paths from `config.extra_instruction_paths` are appended after the built-in set.
- Paths that are absolute are used as-is; relative paths are resolved relative to `repo_path`.

**Discovery priority order (fixed, from §8.1):**
1. `AGENTS.md` — agent_type `"openai"`
2. `CLAUDE.md` — agent_type `"claude"`
3. `.github/copilot-instructions.md` — agent_type `"copilot"`
4. `.bob/rules-code/AGENTS-code.md` — agent_type `"bob"`
5. `.bob/rules-plan/AGENTS-plan.md` — agent_type `"bob"`
6. `.bob/rules-ask/AGENTS-ask.md` — agent_type `"bob"`
7. Extra paths from config — agent_type `"custom"`

**Relevant Context:** §8.1 Supported instruction sources, §Phase 1 Tasks, §13.1 InstructionSource model.

**Status:** [ ] pending

---

### Sub-Task D — Demo Repository B Seed (`demo_repos/single-agent-stale-repo/`)

**Intent:** Create a minimal, realistic repository fixture so the Phase 1 Definition of Done check
(`agentlint scan demo_repos/single-agent-stale-repo` reports exactly one source) can actually run.

Phase 5 populates the full demo content; Phase 1 only needs enough for the acceptance check.

**Expected Outcomes:**
- `demo_repos/single-agent-stale-repo/CLAUDE.md` exists with a few lines of realistic content.
- No `AGENTS.md`, no `.github/`, no `.bob/` in that directory.
- The fixture content references npm (intentionally wrong — Phase 5 adds the full scenario).
- A minimal `package.json` is present (so it looks like a real JS repo).

**Spec description (§Phase 5, Demo B):**
- Only one `CLAUDE.md`
- CLAUDE.md says npm; actual project uses pnpm; stale directory; outdated test command.

The package.json and a minimal stale CLAUDE.md satisfy the Phase 1 check. Full stale scenario is Phase 5.

**Relevant Context:** §Phase 1 Definition of Done, §Phase 5 Demo Repository B.

**Status:** [ ] pending

---

### Sub-Task E — CLI `scan` command (`agentlint/cli.py`)

**Intent:** Replace the Phase 0 stub CLI with a real `agentlint scan <repo-path>` subcommand
that runs discovery, prints the found sources to stdout, and writes `.agentlint/scan.json`.

This is the minimum CLI needed for the Phase 1 acceptance check. Later phases add evidence,
findings, etc. to the same `scan` command.

**Expected Outcomes:**
- `agentlint scan <path>` runs without error.
- Prints each discovered source (path, exists, agent_type) to stdout.
- Creates `<repo-path>/.agentlint/scan.json` with a JSON object:
  ```json
  {
    "agentlint_version": "0.1.0",
    "repo_path": "...",
    "sources": [ { "path": "...", "agent_type": "...", "exists": true, "content_hash": "..." } ]
  }
  ```
- Uses **Typer** (already installed) for subcommand routing.
- `agentlint` with no args prints help (Typer default behavior).
- `agentlint scan --help` works.
- Exit code 0 on success; non-zero on fatal error (repo path not a directory).

**Implementation note:** The CLI should use a Typer `app = typer.Typer()` with `scan` as a
command. The Phase 0 `main()` function becomes `app()`. This is a **breaking change** to the
stub — but the stub had no real behavior.

**Relevant Context:** §15 CLI, §14 Output Files (scan.json), §22 Tech Stack (Typer).

**Status:** [ ] pending

---

### Sub-Task F — Tests (`tests/unit/test_models.py`, `tests/unit/test_discovery.py`)

**Intent:** Add unit tests for all Phase 1 code. Every test must use only stdlib + the
`agentlint` package — no network, no external files beyond `tmp_path` fixtures.

**Expected Outcomes:**
- `pytest` exits 0 with all existing + new tests passing.
- Tests cover all scenarios listed in §Phase 1 Tests.

**Test file: `tests/unit/test_models.py`**
- `test_instruction_source_fields` — instantiate with all fields, check values.
- `test_instruction_source_to_dict` — round-trips through `to_dict()`.
- `test_finding_defaults` — verify `status` defaults to `"open"` (via `field(default=...)`).
- `test_repository_evidence_to_dict` — serialises cleanly.
- `test_validation_result_fields` — instantiate and check.
- `test_canonical_policy_fields` — instantiate and check.

**Test file: `tests/unit/test_discovery.py`**
- `test_zero_instruction_files` — empty tmp dir → 6 built-in sources all with `exists=False`.
- `test_one_file_agents_md` — create only `AGENTS.md` → exactly that source has `exists=True`.
- `test_multiple_files` — create `AGENTS.md` + `CLAUDE.md` → both exist; stable order preserved.
- `test_bob_mode_files` — create `.bob/rules-code/AGENTS-code.md` etc. → discovered.
- `test_extra_instruction_paths_config` — config with one extra path → discovered as `"custom"`.
- `test_missing_configured_path` — config points to non-existent file → `exists=False`, no exception.
- `test_content_hash_set` — create file, check hash is non-empty SHA-256 hex.
- `test_content_hash_empty_when_missing` — missing file → hash is `""`.
- `test_stable_ordering` — call twice, assert order is identical.

**Test file: `tests/unit/test_config.py`**
- `test_no_config_file` — missing `.agentlint/config.yaml` → returns defaults, no error.
- `test_extra_paths_loaded` — write config YAML, assert extra paths returned.
- `test_malformed_yaml_raises` — malformed YAML → `AgentLintConfigError`.

**Fixtures:** Tests must use `pytest`'s `tmp_path` fixture — no permanent files added to `tests/fixtures/` in Phase 1.

**Relevant Context:** §Phase 1 Tests, §21 Rule 2 (end phase with passing tests).

**Status:** [ ] pending

---

### Sub-Task G — PROGRESS.md Update

**Intent:** Mark Phase 1 complete in `PROGRESS.md` after all acceptance criteria pass.

**Expected Outcomes:**
- `- [x] Phase 1` in the checklist.
- Phase 1 section added with: files created, commands run, test results, acceptance criteria status.

**Status:** [ ] pending

---

## Files Created / Modified

| File | Action | Notes |
|---|---|---|
| `agentlint/models.py` | **replace stub** | All 6 dataclasses + to_dict helpers |
| `agentlint/config.py` | **replace stub** | `AgentLintConfig` dataclass + `load_config()` + `AgentLintConfigError` |
| `agentlint/discovery/instruction_sources.py` | **replace stub** | `discover_sources()` |
| `agentlint/cli.py` | **replace stub** | Typer app with `scan` subcommand |
| `demo_repos/single-agent-stale-repo/CLAUDE.md` | **create** | Minimal stale fixture |
| `demo_repos/single-agent-stale-repo/package.json` | **create** | Minimal JS fixture |
| `tests/unit/test_models.py` | **create** | 6 model tests |
| `tests/unit/test_discovery.py` | **create** | 9 discovery tests |
| `tests/unit/test_config.py` | **create** | 3 config tests |
| `PROGRESS.md` | **update** | Phase 1 section |

**Not modified in Phase 1:**
- `agentlint/discovery/repo_files.py` — Phase 2 populates this.
- Any `evidence/`, `parsing/`, `analysis/`, `policy/`, `validation/`, `ui/` stubs — later phases.
- `app.py` — Phase 9.
- `demo_repos/inconsistent-js-repo/` and `demo_repos/clean-repo/` — Phase 5.

---

## Dependencies Required

No new dependencies. All required packages are already installed:
- `pyyaml` — for `.agentlint/config.yaml` loading.
- `typer` — for CLI subcommands.
- `dataclasses` — Python 3.11+ stdlib.
- `hashlib` — Python stdlib (SHA-256 of file content).
- `pathlib` — Python stdlib.

---

## Commands That Must Be Run

```bash
pip install -e ".[dev]"           # re-install after CLI changes (Typer subcommand)
pytest --tb=short -v              # all tests must pass
agentlint scan demo_repos/single-agent-stale-repo
                                  # must print exactly 1 source with exists=True
                                  # must create demo_repos/single-agent-stale-repo/.agentlint/scan.json
agentlint --help                  # Typer help must print cleanly
agentlint scan --help             # subcommand help
```

---

## Acceptance Criteria (from §Phase 1 Definition of Done)

| Criterion | How Verified |
|---|---|
| `agentlint scan demo_repos/single-agent-stale-repo` exits 0 | command run |
| Reports exactly one instruction source | stdout shows 1 `exists=True` source |
| Does not fail | exit code 0, no traceback |
| All Phase 1 tests pass | `pytest` exits 0 |
| Phase 0 smoke tests still pass | `pytest tests/unit/test_smoke.py` |

---

## Risks and Conflicts with Existing Code

| Risk | Detail | Mitigation |
|---|---|---|
| CLI refactor breaks Phase 0 smoke test | Phase 0 smoke test only tests `import agentlint` and `__version__` — it does not call the CLI. No conflict. | None needed. |
| `agentlint/cli.py` was a stub `main()` — Typer replaces it | The `pyproject.toml` entry point `agentlint.cli:main` must still work. With Typer, `main = app` or the entry point calls `app()`. Keep the function name `main`. | Define `app = typer.Typer()` and `def main(): app()`. |
| `discover_sources` must handle `exists=False` gracefully | Downstream phases (3, 4) iterate over sources. They must check `source.exists` before reading file content. | Document this contract in the docstring. Downstream phases are stubs — no conflict yet. |
| `demo_repos/single-agent-stale-repo/` currently has only `.gitkeep` | The Phase 1 acceptance check requires `CLAUDE.md` to exist there. | Sub-Task D creates the minimal fixture. Remove the `.gitkeep` when adding real files. |
| SHA-256 on large files | Phase 1 only reads instruction files — typically small. No performance concern. | No action needed. |
| Config path `.agentlint/config.yaml` inside the target repo | The config is read from the *scanned* repo, not the AgentLint project root. Must resolve relative to `repo_path` argument, not `cwd()`. | Always construct path as `Path(repo_path) / ".agentlint" / "config.yaml"`. |
| Windows path separators in `scan.json` | `Path` objects on Windows produce backslash strings. JSON output must use forward slashes or OS-native but consistent format. | Use `str(path)` — consistency is more important than portability here; document it. |
