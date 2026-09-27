"""Unit tests for Phase 3 — Instruction Parsing and Normalization.

Covers:
  - agentlint.parsing.markdown_rules.parse_markdown_blocks
  - agentlint.parsing.normalization.normalize_blocks
  - agentlint.parsing.extract_rules
  - agentlint.parsing.write_rules_json

All tests use inline strings except where tmp_path / real fixture is needed.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentlint.models import InstructionSource
from agentlint.parsing import extract_rules, write_rules_json
from agentlint.parsing.markdown_rules import parse_markdown_blocks
from agentlint.parsing.normalization import normalize_blocks


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_source(path: str, exists: bool = True) -> InstructionSource:
    return InstructionSource(
        path=path,
        agent_type="claude",
        content_hash="abc123",
        exists=exists,
    )


# ============================================================================
# parse_markdown_blocks — block splitter
# ============================================================================


class TestParseMarkdownBlocks:

    def test_parse_heading(self):
        blocks = parse_markdown_blocks("# My Heading")
        assert len(blocks) == 1
        b = blocks[0]
        assert b["block_type"] == "heading"
        assert b["text"] == "My Heading"
        assert b["line_start"] == 1
        assert b["line_end"] == 1

    def test_parse_heading_levels(self):
        blocks = parse_markdown_blocks("## Level Two\n### Level Three")
        types = [b["block_type"] for b in blocks]
        assert types == ["heading", "heading"]

    def test_parse_bullet_dash(self):
        blocks = parse_markdown_blocks("- Use pnpm")
        assert len(blocks) == 1
        b = blocks[0]
        assert b["block_type"] == "bullet"
        assert b["text"] == "Use pnpm"

    def test_parse_bullet_asterisk(self):
        blocks = parse_markdown_blocks("* Use npm")
        assert len(blocks) == 1
        assert blocks[0]["block_type"] == "bullet"
        assert blocks[0]["text"] == "Use npm"

    def test_parse_numbered(self):
        blocks = parse_markdown_blocks("1. Run tests first")
        assert len(blocks) == 1
        b = blocks[0]
        assert b["block_type"] == "numbered"
        assert b["text"] == "Run tests first"

    def test_parse_code_block(self):
        md = "```bash\nnpm install\n```"
        blocks = parse_markdown_blocks(md)
        assert len(blocks) == 1
        b = blocks[0]
        assert b["block_type"] == "code_block"
        assert "npm install" in b["text"]
        assert b["lang"] == "bash"

    def test_parse_code_block_no_lang(self):
        md = "```\npnpm test\n```"
        blocks = parse_markdown_blocks(md)
        assert blocks[0]["block_type"] == "code_block"
        assert blocks[0]["lang"] == ""

    def test_parse_paragraph(self):
        blocks = parse_markdown_blocks("Node.js 16 is required.")
        assert len(blocks) == 1
        b = blocks[0]
        assert b["block_type"] == "paragraph"
        assert "Node.js 16 is required" in b["text"]

    def test_parse_blank_file(self):
        assert parse_markdown_blocks("") == []

    def test_parse_whitespace_only(self):
        assert parse_markdown_blocks("   \n\n  \n") == []

    def test_parse_mixed_content(self):
        md = "# Heading\n\n- bullet item\n\n```bash\necho hi\n```"
        blocks = parse_markdown_blocks(md)
        types = [b["block_type"] for b in blocks]
        assert "heading" in types
        assert "bullet" in types
        assert "code_block" in types

    def test_parse_line_numbers_correct(self):
        md = "# Title\n\n- item one\n- item two"
        blocks = parse_markdown_blocks(md)
        heading = next(b for b in blocks if b["block_type"] == "heading")
        assert heading["line_start"] == 1

        bullets = [b for b in blocks if b["block_type"] == "bullet"]
        assert bullets[0]["line_start"] == 3
        assert bullets[1]["line_start"] == 4

    def test_parse_code_block_line_numbers(self):
        md = "intro\n```bash\nnpm install\n```\nend"
        blocks = parse_markdown_blocks(md)
        code = next(b for b in blocks if b["block_type"] == "code_block")
        assert code["line_start"] == 2
        assert code["line_end"] == 4

    def test_blank_lines_not_emitted(self):
        md = "\n\n# Heading\n\n"
        blocks = parse_markdown_blocks(md)
        # Only the heading; blank lines are not blocks
        assert all(b["block_type"] != "paragraph" for b in blocks if not b["text"].strip())

    def test_contiguous_prose_grouped(self):
        md = "Line one.\nLine two.\nLine three."
        blocks = parse_markdown_blocks(md)
        # All three lines → one paragraph block
        paragraphs = [b for b in blocks if b["block_type"] == "paragraph"]
        assert len(paragraphs) == 1
        assert "Line one" in paragraphs[0]["text"]
        assert "Line three" in paragraphs[0]["text"]


# ============================================================================
# normalize_blocks — category + value detection
# ============================================================================


class TestNormalizeBlocks:

    def _source(self) -> InstructionSource:
        return _make_source("CLAUDE.md")

    def _bullet_block(self, text: str) -> dict:
        return {"block_type": "bullet", "text": text, "line_start": 1, "line_end": 1}

    def _code_block(self, text: str) -> dict:
        return {"block_type": "code_block", "text": text, "line_start": 1, "line_end": 3, "lang": "bash"}

    def _para_block(self, text: str) -> dict:
        return {"block_type": "paragraph", "text": text, "line_start": 1, "line_end": 1}

    def test_normalize_package_manager_pnpm(self):
        blocks = [self._bullet_block("Use pnpm for all dependencies")]
        rules = normalize_blocks(blocks, self._source())
        assert rules[0].category == "package_manager"
        assert rules[0].normalized_value == "pnpm"

    def test_normalize_package_manager_npm(self):
        blocks = [self._code_block("npm install")]
        rules = normalize_blocks(blocks, self._source())
        assert rules[0].category == "package_manager"
        assert rules[0].normalized_value == "npm"

    def test_normalize_test_framework_vitest(self):
        blocks = [self._bullet_block("Tests run with Vitest")]
        rules = normalize_blocks(blocks, self._source())
        assert rules[0].category == "test_framework"
        assert rules[0].normalized_value == "vitest"

    def test_normalize_test_framework_pytest(self):
        blocks = [self._code_block("pytest tests/")]
        rules = normalize_blocks(blocks, self._source())
        assert rules[0].category == "test_framework"
        assert rules[0].normalized_value == "pytest"

    def test_normalize_linting_eslint(self):
        blocks = [self._bullet_block("Use ESLint for linting")]
        rules = normalize_blocks(blocks, self._source())
        assert rules[0].category == "linting"
        assert rules[0].normalized_value == "eslint"

    def test_normalize_linting_prettier(self):
        blocks = [self._bullet_block("Use Prettier for formatting")]
        rules = normalize_blocks(blocks, self._source())
        assert rules[0].category == "linting"
        assert rules[0].normalized_value == "prettier"

    def test_normalize_path_reference(self):
        blocks = [self._bullet_block("`src/` — application source code")]
        rules = normalize_blocks(blocks, self._source())
        assert rules[0].category == "paths"
        # value should contain "src/"
        assert rules[0].normalized_value is not None
        assert "src" in rules[0].normalized_value

    def test_normalize_no_category(self):
        blocks = [self._bullet_block("Keep things tidy.")]
        rules = normalize_blocks(blocks, self._source())
        assert rules[0].category is None
        assert rules[0].normalized_key is None
        assert rules[0].normalized_value is None

    def test_normalize_confidence_code_block(self):
        blocks = [self._code_block("npm install")]
        rules = normalize_blocks(blocks, self._source())
        assert rules[0].confidence == pytest.approx(0.9)

    def test_normalize_confidence_bullet_with_keyword(self):
        blocks = [self._bullet_block("Use pnpm")]
        rules = normalize_blocks(blocks, self._source())
        assert rules[0].confidence == pytest.approx(0.8)

    def test_normalize_confidence_no_keyword(self):
        blocks = [self._bullet_block("Keep things tidy.")]
        rules = normalize_blocks(blocks, self._source())
        assert rules[0].confidence == pytest.approx(0.4)

    def test_normalize_extraction_method_always_deterministic(self):
        blocks = [self._bullet_block("Use pnpm"), self._para_block("Some note.")]
        rules = normalize_blocks(blocks, self._source())
        assert all(r.extraction_method == "deterministic" for r in rules)

    def test_normalize_preserves_source_fields(self):
        src = _make_source("path/to/AGENTS.md")
        blocks = [self._bullet_block("Use npm")]
        rules = normalize_blocks(blocks, src)
        assert rules[0].source_path == "path/to/AGENTS.md"
        assert rules[0].source_agent == "claude"

    def test_normalize_ids_empty(self):
        """IDs should be blank — assigned by extract_rules."""
        blocks = [self._bullet_block("Use pnpm")]
        rules = normalize_blocks(blocks, self._source())
        assert rules[0].id == ""

    def test_normalize_empty_blocks(self):
        assert normalize_blocks([], self._source()) == []


# ============================================================================
# extract_rules — public aggregator
# ============================================================================


class TestExtractRules:

    def test_extract_rules_skips_nonexistent(self, tmp_path: Path):
        missing = InstructionSource(
            path=str(tmp_path / "MISSING.md"),
            agent_type="openai",
            content_hash="",
            exists=False,
        )
        rules = extract_rules([missing])
        assert rules == []

    def test_extract_rules_assigns_ids(self, tmp_path: Path):
        md_file = tmp_path / "AGENTS.md"
        md_file.write_text("# Title\n\n- Use npm\n- Run pytest\n", encoding="utf-8")
        src = InstructionSource(
            path=str(md_file),
            agent_type="openai",
            content_hash="abc",
            exists=True,
        )
        rules = extract_rules([src])
        assert all(r.id != "" for r in rules)
        # IDs should start with "rule-agents-"
        assert all(r.id.startswith("rule-agents-") for r in rules)

    def test_extract_rules_id_format(self, tmp_path: Path):
        md_file = tmp_path / "CLAUDE.md"
        md_file.write_text("- Use npm\n", encoding="utf-8")
        src = InstructionSource(path=str(md_file), agent_type="claude", content_hash="x", exists=True)
        rules = extract_rules([src])
        assert rules[0].id == "rule-claude-001"

    def test_extract_rules_multiple_sources_separate_counters(self, tmp_path: Path):
        f1 = tmp_path / "CLAUDE.md"
        f2 = tmp_path / "AGENTS.md"
        f1.write_text("- Use npm\n", encoding="utf-8")
        f2.write_text("- Use pytest\n", encoding="utf-8")
        src1 = InstructionSource(path=str(f1), agent_type="claude", content_hash="a", exists=True)
        src2 = InstructionSource(path=str(f2), agent_type="openai", content_hash="b", exists=True)
        rules = extract_rules([src1, src2])
        ids = [r.id for r in rules]
        assert "rule-claude-001" in ids
        assert "rule-agents-001" in ids


# ============================================================================
# write_rules_json — output file
# ============================================================================


class TestWriteRulesJson:

    def test_write_rules_json_schema(self, tmp_path: Path):
        md_file = tmp_path / "AGENTS.md"
        md_file.write_text("- Use pnpm\n- Run vitest\n", encoding="utf-8")
        src = InstructionSource(path=str(md_file), agent_type="openai", content_hash="x", exists=True)
        rules = extract_rules([src])

        out_path = write_rules_json(tmp_path, rules)
        assert out_path.exists()

        data = json.loads(out_path.read_text(encoding="utf-8"))
        assert "agentlint_version" in data
        assert "repo_path" in data
        assert "rules" in data
        assert isinstance(data["rules"], list)

    def test_write_rules_json_rule_fields(self, tmp_path: Path):
        md_file = tmp_path / "AGENTS.md"
        md_file.write_text("- Use pnpm\n", encoding="utf-8")
        src = InstructionSource(path=str(md_file), agent_type="openai", content_hash="x", exists=True)
        rules = extract_rules([src])

        out_path = write_rules_json(tmp_path, rules)
        data = json.loads(out_path.read_text(encoding="utf-8"))
        rule = data["rules"][0]

        # All required InstructionRule fields must be present
        for field in ("id", "source_path", "source_agent", "text",
                      "category", "normalized_key", "normalized_value",
                      "line_start", "line_end", "extraction_method", "confidence"):
            assert field in rule, f"Missing field: {field}"

    def test_write_rules_json_returns_path(self, tmp_path: Path):
        out_path = write_rules_json(tmp_path, [])
        assert out_path.name == "rules.json"
        assert out_path.parent.name == ".agentlint"


# ============================================================================
# Integration — parse real CLAUDE.md fixture
# ============================================================================


class TestExtractRulesRealFixture:

    def test_extract_rules_real_claude_md(self):
        """Parse the bundled single-agent-stale-repo CLAUDE.md fixture."""
        fixture = Path("demo_repos/single-agent-stale-repo/CLAUDE.md")
        if not fixture.exists():
            pytest.skip("Fixture not found")

        src = InstructionSource(
            path=str(fixture),
            agent_type="claude",
            content_hash="any",
            exists=True,
        )
        rules = extract_rules([src])

        assert len(rules) > 0

        categories = [r.category for r in rules]
        values = [r.normalized_value for r in rules if r.normalized_value]
        values_lower = [v.lower() for v in values]

        # npm should be detected as package manager
        assert "package_manager" in categories
        pm_rules = [r for r in rules if r.category == "package_manager"]
        pm_values = [r.normalized_value for r in pm_rules if r.normalized_value]
        assert any("npm" in v for v in pm_values), f"npm not found in {pm_values}"

        # src/ or tests/ path should be detected
        assert "paths" in categories

        # All rules have extraction_method="deterministic"
        assert all(r.extraction_method == "deterministic" for r in rules)

        # All rules have non-empty source_path and line_start >= 1
        for r in rules:
            assert r.source_path != ""
            assert r.line_start is not None and r.line_start >= 1
