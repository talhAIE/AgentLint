# Phase 3 Plan — Instruction Parsing and Normalization

## Overview

Phase 3 implements **Layer 1** of the two-layer parsing architecture: a purely
deterministic Markdown parser that turns raw instruction files into traceable
`InstructionRule` objects.

**Layer 2** (Bob semantic interpretation) is deferred — it belongs to Phase 6
where Bob slash commands and skills are built.  Phase 3 must leave the door
open for Bob results to be merged in later (the `extraction_method` and
`confidence` fields already support this in the data model).

**Definition of Done (from spec §Phase 3):**

> The UI/CLI can display instruction rules with source file and line location.

Concrete acceptance check:

```
agentlint scan demo_repos/single-agent-stale-repo
```

Must print a rule summary and write `.agentlint/rules.json` containing
`InstructionRule` objects with non-empty `source_path`, `line_start`, and
`text` fields.

Output artifact: `.agentlint/rules.json`

---

## Existing State

| Item | Status |
|---|---|
| `agentlint/parsing/markdown_rules.py` | stub (1 comment line) |
| `agentlint/parsing/normalization.py` | stub (1 comment line) |
| `agentlint/parsing/json_parser.py` | stub — not needed in Phase 3 |
| `agentlint/parsing/yaml_parser.py` | stub — not needed in Phase 3 |
| `agentlint/parsing/__init__.py` | stub |
| `agentlint/models.py` | `InstructionRule` dataclass fully defined |
| `agentlint/cli.py` | Phase 2 complete; `scan` writes scan.json + evidence.json |
| `demo_repos/single-agent-stale-repo/CLAUDE.md` | real file; good parsing test target |
| `demo_repos/inconsistent-js-repo/` | no instruction files yet (Phase 5 adds them) |

---

## Architecture — Layer 1 Deterministic Parser

```
InstructionSource (path + exists)
        │
        ▼
  markdown_rules.py
  parse_instruction_file(source) → list[RawBlock]
        │
        ▼
  normalization.py
  normalize_blocks(blocks, source) → list[InstructionRule]
        │
        ▼
  parsing/__init__.py
  extract_rules(sources) → list[InstructionRule]
  write_rules_json(repo_path, rules) → Path
```

### What a "block" is

The Markdown file is split into these block types:

| Block type | Trigger | Example |
|---|---|---|
| `heading` | Lines starting with `#` | `## Package Manager` |
| `bullet` | Lines starting with `-` or `*` | `- Use pnpm` |
| `numbered` | Lines starting with `1.`, `2.` etc. | `1. Run tests first` |
| `code_block` | Lines between triple-backtick fences | ` ```bash npm install ``` ` |
| `paragraph` | Non-empty prose lines that don't match above | `Node.js 16 is required` |

Each block captures: `block_type`, `text` (stripped), `line_start`, `line_end`.

### Category detection

After block extraction, the normalizer scans each block's text for keyword
signals to assign a `category` and attempt a `normalized_key`/`normalized_value`.

| Keyword signals | category | key |
|---|---|---|
| pnpm, npm, yarn, bun, pip, poetry | `package_manager` | `package_manager` |
| vitest, jest, pytest, mocha, cypress, playwright | `test_framework` | `test_framework` |
| eslint, prettier, ruff, black, biome | `linting` | `linter` / `formatter` |
| `npm run`, `pnpm run`, `yarn`, `make`, `pytest` | `commands` | command type |
| `src/`, `tests/`, `dist/`, path-like strings | `paths` | `path` |
| node, python, version, runtime | `runtime` | `runtime` |
| do not edit, generated, do not modify | `generated` | `generated` |

Rules that don't match any keyword get `category=None`, `normalized_key=None`,
`normalized_value=None` — they are still returned (raw text is preserved for
Bob in Phase 6).

### Confidence

| Scenario | confidence |
|---|---|
| Code block with a single clear command | 0.9 |
| Bullet item with keyword hit | 0.8 |
| Heading with keyword hit | 0.7 |
| Paragraph with keyword hit | 0.6 |
| No keyword hit (raw text only) | 0.4 |

### ID assignment

`rule-<source_abbrev>-<three_digit_index>` e.g. `rule-claude-001`.
Abbreviation: the stem of the filename lowercased, first 6 chars
(e.g., `CLAUDE.md` → `claude`, `AGENTS.md` → `agents`,
`.github/copilot-instructions.md` → `copilo`).

### extraction_method

Always `"deterministic"` for Phase 3 output.

---

## Sub-Tasks

---

### Sub-Task A — Markdown Block Splitter (`agentlint/parsing/markdown_rules.py`)

**Intent:** Split a Markdown file into typed blocks with line numbers.
This is purely structural — no semantic interpretation here.

**Expected Outcomes:**

- `parse_markdown_blocks(text: str) -> list[dict]` returns a list of block
  dicts, each with keys: `block_type`, `text`, `line_start`, `line_end`.
- Block types: `"heading"`, `"bullet"`, `"numbered"`, `"code_block"`,
  `"paragraph"`.
- Code blocks preserve the language hint if present (e.g. `bash`, `python`).
- Empty files → empty list.
- Multi-line code blocks are captured as a single block with the full interior
  text joined (newline-separated), `line_start` at the opening fence,
  `line_end` at the closing fence.
- Contiguous non-blank prose lines that are not headings/bullets/numbered are
  grouped into one `paragraph` block.
- Blank lines between blocks are not emitted as blocks.
- Pure stdlib — no external Markdown library.

**Relevant Context:** §Phase 3 Layer 1, §13.2 InstructionRule.

**Status:** [ ] pending

---

### Sub-Task B — Rule Normalizer (`agentlint/parsing/normalization.py`)

**Intent:** Convert raw blocks into `InstructionRule` objects, applying
category detection and value extraction where possible.

**Expected Outcomes:**

- `normalize_blocks(blocks: list[dict], source: InstructionSource) -> list[InstructionRule]`
  returns one `InstructionRule` per block.
- For each block, attempts keyword-based category + key + value detection.
- `text` field is set to the block's raw stripped text.
- `line_start` / `line_end` are copied from the block.
- `extraction_method = "deterministic"`, `confidence` set per block type.
- IDs are left as `""` (aggregator assigns them in Sub-Task D).
- `source_path` and `source_agent` are taken from the `InstructionSource`.
- Value extraction rules:
  - For `package_manager` category: value = the detected manager name
    (e.g. `"pnpm"`, `"npm"`).
  - For `test_framework` category: value = the detected framework name.
  - For `linting`: value = tool name; key = `"linter"` or `"formatter"`.
  - For `commands`: value = the command string if inside a code block;
    otherwise the full rule text.
  - For `paths`: value = the path-like substring detected.
  - For `runtime`: value = the version string if detectable; else raw text.
  - `None` when category is undetected or value is ambiguous.

**Relevant Context:** §Phase 3 Normalized examples, §13.2 InstructionRule,
§9 Finding Types (the categories here must align with §9 evidence categories
so Phase 4 can compare them).

**Status:** [ ] pending

---

### Sub-Task C — Parsing Public API (`agentlint/parsing/__init__.py`)

**Intent:** Provide the top-level functions that the CLI and future phases call.
Keeps callers decoupled from internal block structures.

**Expected Outcomes:**

- `extract_rules(sources: list[InstructionSource]) -> list[InstructionRule]`
  — iterates over `sources` where `source.exists=True`, reads the file text,
  calls `parse_markdown_blocks`, calls `normalize_blocks`, assigns sequential
  IDs, and returns the combined list.
- `write_rules_json(repo_path: Path, rules: list[InstructionRule]) -> Path`
  — writes `.agentlint/rules.json` in the same schema as `evidence.json`:
  ```json
  {
    "agentlint_version": "0.1.0",
    "repo_path": "...",
    "rules": [ { ...InstructionRule fields... } ]
  }
  ```
  Returns the path of the written file.
- Re-exports both functions so callers use `from agentlint.parsing import ...`.
- Only Markdown files are parsed in Phase 3. JSON/YAML stubs remain stubs.

**Relevant Context:** §14 Output Files, §15 `agentlint scan`.

**Status:** [ ] pending

---

### Sub-Task D — CLI Extension (`agentlint/cli.py`)

**Intent:** Extend `agentlint scan` to run parsing after evidence collection
and write `rules.json`.  Add a rule summary to the stdout output.

**Expected Outcomes:**

- After writing `evidence.json`, the `scan` command:
  1. Calls `extract_rules(sources)`.
  2. Prints: `Rules: N rule(s) extracted from M source(s)` plus a
     brief per-source breakdown (e.g. `  CLAUDE.md: 12 rules`).
  3. Writes `.agentlint/rules.json` via `write_rules_json`.
- Phase 1 and Phase 2 outputs (`scan.json`, `evidence.json`) are unaffected.

**Relevant Context:** §15 `agentlint scan`.

**Status:** [ ] pending

---

### Sub-Task E — Tests (`tests/unit/test_parsing.py`)

**Intent:** Cover the deterministic parsing layer thoroughly.
All tests use inline strings — no disk access except for the
`write_rules_json` test which uses `tmp_path`.

**Test cases required:**

| Test | Scenario |
|---|---|
| `test_parse_heading` | `# Heading` → block_type=heading |
| `test_parse_bullet` | `- item` → block_type=bullet |
| `test_parse_numbered` | `1. item` → block_type=numbered |
| `test_parse_code_block` | triple-backtick fence → block_type=code_block |
| `test_parse_paragraph` | plain prose → block_type=paragraph |
| `test_parse_blank_file` | empty string → empty list |
| `test_parse_mixed_content` | headings + bullets + code block together |
| `test_parse_line_numbers_correct` | line_start / line_end match actual line positions |
| `test_normalize_package_manager_pnpm` | "Use pnpm" bullet → category=package_manager, value=pnpm |
| `test_normalize_package_manager_npm` | "npm install" in code block → category=package_manager, value=npm |
| `test_normalize_test_framework_vitest` | "Tests run with Vitest" → category=test_framework, value=vitest |
| `test_normalize_test_framework_pytest` | "Run pytest" in code block → category=test_framework, value=pytest |
| `test_normalize_linting_eslint` | "Use ESLint" → category=linting, value=eslint |
| `test_normalize_path_reference` | "`src/` — source code" → category=paths |
| `test_normalize_no_category` | "Keep things tidy." → category=None |
| `test_normalize_confidence_code_block` | code block rule has confidence=0.9 |
| `test_normalize_confidence_bullet` | bullet rule with keyword has confidence=0.8 |
| `test_extract_rules_skips_nonexistent` | source with exists=False → no rules emitted |
| `test_extract_rules_assigns_ids` | all returned rules have non-empty id |
| `test_write_rules_json_schema` | JSON has agentlint_version + rules array |
| `test_extract_rules_real_claude_md` | parse the fixture CLAUDE.md and check for npm + paths rules |

All existing 87 tests must continue to pass.

**Relevant Context:** §Phase 3 Tests, §21 Rule 2.

**Status:** [ ] pending

---

### Sub-Task F — PROGRESS.md Update

**Intent:** Mark Phase 3 complete after all criteria pass.

**Expected Outcomes:**

- `- [x] Phase 3` in the checklist.
- Phase 3 section with: files created, commands run, test results, acceptance
  criteria status.

**Status:** [ ] pending

---

## Files Created / Modified

| File | Action | Notes |
|---|---|---|
| `agentlint/parsing/markdown_rules.py` | replace stub | `parse_markdown_blocks()` |
| `agentlint/parsing/normalization.py` | replace stub | `normalize_blocks()` |
| `agentlint/parsing/__init__.py` | replace stub | `extract_rules()` + `write_rules_json()` |
| `agentlint/cli.py` | extend | add rule extraction + rules.json output to `scan` |
| `tests/unit/test_parsing.py` | create | ~21 tests |
| `PROGRESS.md` | update | Phase 3 section |

**Not modified in Phase 3:**

- `agentlint/parsing/json_parser.py` — remains a stub; JSON instruction sources are not used in Phase 3
- `agentlint/parsing/yaml_parser.py` — remains a stub
- `agentlint/models.py` — `InstructionRule` dataclass already complete
- All `evidence/` modules — Phase 2 complete, no changes needed
- `demo_repos/` fixtures — Phase 5 adds instruction files to `inconsistent-js-repo`
- `app.py` — Phase 9

---

## Dependencies Required

No new dependencies.  All parsing is pure Python stdlib:

- `re` — keyword pattern matching
- `pathlib` — file reading
- `json` — writing rules.json

The `json_parser.py` and `yaml_parser.py` stubs remain stubs. They are
not needed to parse `.md` instruction files.

---

## Commands That Must Be Run

```bash
pytest --tb=short -v
# Must show: 87 existing + ~21 new = ~108 tests, all passed

agentlint scan demo_repos/single-agent-stale-repo
# Must print: "Rules: N rule(s) extracted from 1 source(s)"
# Must print: "  CLAUDE.md: N rules"
# Must create: demo_repos/single-agent-stale-repo/.agentlint/rules.json

agentlint --help
# Must still work
```

---

## Acceptance Criteria (from §Phase 3 Definition of Done)

| Criterion | Expected |
|---|---|
| `agentlint scan demo_repos/single-agent-stale-repo` exits 0 | ✅ no traceback |
| At least 1 rule extracted from CLAUDE.md | rule with `source_path=CLAUDE.md`, `line_start` ≥ 1 |
| `npm` detected as package manager rule | `category=package_manager`, `value=npm` |
| `src/` detected as path reference | `category=paths`, `value` contains `src` |
| All rules have `extraction_method="deterministic"` | no `"bob"` entries in Phase 3 |
| `rules.json` written to `.agentlint/rules.json` | file exists with correct schema |
| `rules.json` schema: `agentlint_version`, `repo_path`, `rules` | top-level keys present |
| Phase 1+2 tests still pass (87) | no regressions |
| New Phase 3 tests pass (~21) | `test_parsing.py` all green |

---

## Risks and Conflicts

| Risk | Detail | Mitigation |
|---|---|---|
| **Paragraph grouping ambiguity** | Contiguous prose lines that aren't clearly a "rule" inflate the rule count. | Only emit paragraph blocks when they contain at least one keyword signal, OR keep all but rely on `confidence=0.4` to let Phase 4 ignore them. Keep all for now — Bob in Phase 6 can filter. |
| **Code block content vs fence** | Triple-backtick fences may themselves contain a command (e.g., `npm install`). The fence delimiter lines must be excluded from the text; only interior lines matter. | Strip opening/closing fence lines; join interior lines. Capture language hint separately. |
| **Multi-agent sources** | `demo_repos/inconsistent-js-repo` has no instruction files in Phase 3. The acceptance check runs against `single-agent-stale-repo` only. | The parser must not crash on empty source lists. |
| **Windows path separators in rules.json** | `source_path` from `InstructionSource.path` uses OS-native separators on Windows. | Store `source_path` as received from `InstructionSource.path` (already uses backslashes on Windows — consistent with scan.json). |
| **ID namespace collision** | Multiple instruction files produce rules with the same abbreviation stem. | Use per-source counter, not global counter. `rule-claude-001`, `rule-agents-001` etc. stay in separate namespaces. |
| **json_parser.py / yaml_parser.py stubs** | Phases 1–2 did not import them. Nothing in Phase 3 imports them either. | Leave as stubs. No action needed. |
| **`exists=False` sources** | `discover_sources` returns all 6 built-in candidates, most with `exists=False`. The parser must silently skip these. | Guard with `if source.exists:` in `extract_rules`. |
| **Phase 4 dependency** | Phase 4 compares `InstructionRule.normalized_key`/`normalized_value` against `RepositoryEvidence.key`/`value`. The category names MUST align: `"package_manager"`, `"test_framework"`, `"linting"`, `"commands"`, `"paths"`, `"runtime"`. | Use identical category strings as the evidence detectors. |

---

*Ready for implementation.*
