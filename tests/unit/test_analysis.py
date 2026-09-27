"""Phase 4 — Deterministic Finding Engine tests.

Tests cover:
  - F01 cross-file conflict detection
  - F02 instruction vs repository mismatch (package_manager, test_framework, linting)
  - F03 stale path detection
  - F04 invalid command detection
  - F05 duplicate rule detection
  - run_deterministic_checks combined pipeline
  - write_findings_json JSON schema
"""

from __future__ import annotations

import json

import pytest

from agentlint.analysis import run_deterministic_checks, write_findings_json
from agentlint.analysis.deterministic_rules import (
    detect_f01_cross_file_conflicts,
    detect_f02_mismatch,
    detect_f03_stale_paths,
    detect_f04_invalid_commands,
)
from agentlint.analysis.duplicates import detect_f05_duplicates
from agentlint.models import Finding, InstructionRule, RepositoryEvidence


# ---------------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------------


def make_rule(
    *,
    id: str = "rule-agents-001",
    source_path: str = "AGENTS.md",
    source_agent: str = "openai",
    text: str = "Use npm",
    category: str | None = "package_manager",
    normalized_key: str | None = "package_manager",
    normalized_value: str | None = "npm",
    line_start: int = 1,
    line_end: int = 1,
) -> InstructionRule:
    return InstructionRule(
        id=id,
        source_path=source_path,
        source_agent=source_agent,
        text=text,
        category=category,
        normalized_key=normalized_key,
        normalized_value=normalized_value,
        line_start=line_start,
        line_end=line_end,
        extraction_method="deterministic",
        confidence=0.8,
    )


def make_evidence(
    *,
    id: str = "ev-pm-001",
    category: str = "package_manager",
    key: str = "package_manager",
    value: str = "pnpm",
    source_path: str = "package.json",
    strength: str = "strong",
) -> RepositoryEvidence:
    return RepositoryEvidence(
        id=id,
        category=category,
        key=key,
        value=value,
        source_path=source_path,
        source_locator=None,
        strength=strength,
        explanation=f"Evidence: {category}={value}",
    )


# ---------------------------------------------------------------------------
# F02 — Package Manager Mismatch
# ---------------------------------------------------------------------------


class TestF02PackageManagerMismatch:
    def test_f02_pm_mismatch_fires(self):
        """Rule says npm, strong evidence says pnpm → F02 found."""
        rules = [make_rule(normalized_value="npm")]
        evidence = [make_evidence(value="pnpm", strength="strong")]
        findings = detect_f02_mismatch(rules, evidence)
        assert len(findings) == 1
        f = findings[0]
        assert f.type == "F02"
        assert f.severity == "high"
        assert f.deterministic is True
        assert "npm" in f.title
        assert "pnpm" in f.title

    def test_f02_pm_no_mismatch(self):
        """Rule says pnpm, strong evidence says pnpm → no F02."""
        rules = [make_rule(normalized_value="pnpm")]
        evidence = [make_evidence(value="pnpm", strength="strong")]
        findings = detect_f02_mismatch(rules, evidence)
        assert findings == []

    def test_f02_medium_evidence_fires(self):
        """Rule says npm, only medium evidence says pnpm → F02 with lower confidence."""
        rules = [make_rule(normalized_value="npm")]
        evidence = [make_evidence(value="pnpm", strength="medium")]
        findings = detect_f02_mismatch(rules, evidence)
        assert len(findings) == 1
        assert findings[0].confidence == 0.7  # medium confidence
        assert findings[0].type == "F02"

    def test_f02_no_evidence_no_finding(self):
        """Rule says npm, no evidence for package_manager → no F02."""
        rules = [make_rule(normalized_value="npm")]
        evidence = []  # no evidence at all
        findings = detect_f02_mismatch(rules, evidence)
        assert findings == []

    def test_f02_test_framework_mismatch(self):
        """Rule says jest, strong evidence says vitest → F02."""
        rules = [
            make_rule(
                category="test_framework",
                normalized_key="test_framework",
                normalized_value="jest",
                text="Use Jest for testing",
            )
        ]
        evidence = [
            make_evidence(
                id="ev-tf-001",
                category="test_framework",
                key="test_framework",
                value="vitest",
                strength="strong",
            )
        ]
        findings = detect_f02_mismatch(rules, evidence)
        assert len(findings) == 1
        f = findings[0]
        assert f.type == "F02"
        assert f.severity == "high"
        assert "jest" in f.title.lower()
        assert "vitest" in f.title.lower()

    def test_f02_no_value_in_rule_skipped(self):
        """Rule with normalized_value=None is skipped."""
        rules = [make_rule(normalized_value=None)]
        evidence = [make_evidence(value="pnpm", strength="strong")]
        findings = detect_f02_mismatch(rules, evidence)
        assert findings == []

    def test_f02_linting_mismatch_medium_severity(self):
        """Linting mismatch produces severity=medium."""
        rules = [
            make_rule(
                category="linting",
                normalized_key="linter",
                normalized_value="eslint",
                text="Use ESLint",
            )
        ]
        evidence = [
            make_evidence(
                id="ev-lint-001",
                category="linting",
                key="linter",
                value="ruff",
                strength="strong",
            )
        ]
        findings = detect_f02_mismatch(rules, evidence)
        assert len(findings) == 1
        assert findings[0].severity == "medium"
        assert findings[0].confidence == 0.85


# ---------------------------------------------------------------------------
# F01 — Cross-file exact contradictions
# ---------------------------------------------------------------------------


class TestF01CrossFileConflicts:
    def test_f01_conflict_two_files(self):
        """AGENTS.md says npm, CLAUDE.md says pnpm → F01."""
        rules = [
            make_rule(
                id="rule-agents-001",
                source_path="AGENTS.md",
                normalized_value="npm",
            ),
            make_rule(
                id="rule-claude-001",
                source_path="CLAUDE.md",
                normalized_value="pnpm",
            ),
        ]
        findings = detect_f01_cross_file_conflicts(rules)
        assert len(findings) == 1
        f = findings[0]
        assert f.type == "F01"
        assert f.severity == "high"
        assert f.confidence == 0.9
        assert f.deterministic is True
        # Both rule IDs should be referenced
        assert "rule-agents-001" in f.instruction_rules
        assert "rule-claude-001" in f.instruction_rules

    def test_f01_no_conflict_same_file(self):
        """Same file says npm twice → no F01."""
        rules = [
            make_rule(id="rule-agents-001", source_path="AGENTS.md", normalized_value="npm"),
            make_rule(id="rule-agents-002", source_path="AGENTS.md", normalized_value="npm"),
        ]
        findings = detect_f01_cross_file_conflicts(rules)
        assert findings == []

    def test_f01_no_conflict_same_value(self):
        """Both files say pnpm → no F01."""
        rules = [
            make_rule(id="rule-agents-001", source_path="AGENTS.md", normalized_value="pnpm"),
            make_rule(id="rule-claude-001", source_path="CLAUDE.md", normalized_value="pnpm"),
        ]
        findings = detect_f01_cross_file_conflicts(rules)
        assert findings == []

    def test_f01_no_conflict_none_value_skipped(self):
        """Rules with None normalized_value are skipped."""
        rules = [
            make_rule(id="rule-agents-001", source_path="AGENTS.md", normalized_value=None),
            make_rule(id="rule-claude-001", source_path="CLAUDE.md", normalized_value="pnpm"),
        ]
        findings = detect_f01_cross_file_conflicts(rules)
        assert findings == []

    def test_f01_different_keys_no_conflict(self):
        """Different normalized_keys in different files → no F01."""
        rules = [
            make_rule(
                id="rule-agents-001",
                source_path="AGENTS.md",
                normalized_key="package_manager",
                normalized_value="npm",
            ),
            make_rule(
                id="rule-claude-001",
                source_path="CLAUDE.md",
                normalized_key="test_framework",
                normalized_value="jest",
            ),
        ]
        findings = detect_f01_cross_file_conflicts(rules)
        assert findings == []


# ---------------------------------------------------------------------------
# F03 — Stale Paths
# ---------------------------------------------------------------------------


class TestF03StalePaths:
    def _path_evidence(self, value: str, id: str = "ev-path-001") -> RepositoryEvidence:
        return make_evidence(
            id=id,
            category="paths",
            key="directory",
            value=value,
            source_path=value,
            strength="strong",
        )

    def test_f03_stale_path_fires(self):
        """Rule refs src/services/, no evidence for that root → F03."""
        rules = [
            make_rule(
                category="paths",
                normalized_key="path",
                normalized_value="src/services/",
                text="Add files in `src/services/`",
            )
        ]
        # Only 'lib/' in evidence — not 'src/'
        evidence = [self._path_evidence("lib")]
        findings = detect_f03_stale_paths(rules, evidence)
        assert len(findings) == 1
        f = findings[0]
        assert f.type == "F03"
        assert f.severity == "medium"
        assert f.confidence == 0.8
        assert f.deterministic is True

    def test_f03_valid_path_no_finding(self):
        """Rule refs src/, evidence has src/ → no F03."""
        rules = [
            make_rule(
                category="paths",
                normalized_key="path",
                normalized_value="src/",
                text="Source code in `src/`",
            )
        ]
        evidence = [self._path_evidence("src")]
        findings = detect_f03_stale_paths(rules, evidence)
        assert findings == []

    def test_f03_root_match_fires_with_lower_confidence(self):
        """Rule refs src/services/ but only src/ exists — conservative F03 with confidence=0.6."""
        rules = [
            make_rule(
                category="paths",
                normalized_key="path",
                normalized_value="src/services/",
                text="Add files in `src/services/`",
            )
        ]
        evidence = [self._path_evidence("src")]  # 'src' root exists, services/ absent
        findings = detect_f03_stale_paths(rules, evidence)
        assert len(findings) == 1
        f = findings[0]
        assert f.type == "F03"
        assert f.confidence == 0.6  # lower confidence due to root match
        assert f.deterministic is True

    def test_f03_no_path_evidence_skipped(self):
        """No path evidence → no F03 (avoid false positives)."""
        rules = [
            make_rule(
                category="paths",
                normalized_key="path",
                normalized_value="src/",
                text="Source code in `src/`",
            )
        ]
        findings = detect_f03_stale_paths(rules, evidence=[])
        assert findings == []

    def test_f03_non_path_rule_skipped(self):
        """Rules with category != 'paths' are ignored."""
        rules = [
            make_rule(
                category="package_manager",
                normalized_key="package_manager",
                normalized_value="npm",
            )
        ]
        evidence = [self._path_evidence("src")]
        findings = detect_f03_stale_paths(rules, evidence)
        assert findings == []


# ---------------------------------------------------------------------------
# F04 — Invalid/Stale Commands
# ---------------------------------------------------------------------------


class TestF04InvalidCommands:
    def _cmd_evidence(self, key: str, value: str, id: str = "ev-cmd-001") -> RepositoryEvidence:
        return make_evidence(
            id=id,
            category="commands",
            key=key,
            value=value,
            source_path="package.json",
            strength="strong",
        )

    def test_f04_invalid_command_fires(self):
        """Rule says npm run test:unit, scripts have no test:unit → F04."""
        rules = [
            make_rule(
                category=None,
                normalized_key=None,
                normalized_value=None,
                text="Run tests with `npm run test:unit`",
            )
        ]
        evidence = [self._cmd_evidence("test", "vitest run")]
        findings = detect_f04_invalid_commands(rules, evidence)
        assert len(findings) == 1
        f = findings[0]
        assert f.type == "F04"
        assert f.severity == "medium"
        assert "test:unit" in f.title
        assert f.deterministic is True

    def test_f04_valid_command_no_finding(self):
        """Rule says npm run test, scripts have test → no F04."""
        rules = [
            make_rule(
                category=None,
                normalized_key=None,
                normalized_value=None,
                text="Run tests with `npm run test`",
            )
        ]
        evidence = [self._cmd_evidence("test", "vitest run")]
        findings = detect_f04_invalid_commands(rules, evidence)
        assert findings == []

    def test_f04_no_commands_evidence_skipped(self):
        """No commands evidence → no F04 (guard for Python-only repos)."""
        rules = [
            make_rule(
                category=None,
                normalized_key=None,
                normalized_value=None,
                text="Run tests with `npm run test:unit`",
            )
        ]
        findings = detect_f04_invalid_commands(rules, evidence=[])
        assert findings == []

    def test_f04_pnpm_run_pattern_detected(self):
        """pnpm run X patterns also trigger F04 for unknown scripts."""
        rules = [
            make_rule(
                category=None,
                normalized_key=None,
                normalized_value=None,
                text="Use `pnpm run check:types` to type check",
            )
        ]
        evidence = [self._cmd_evidence("build", "tsc")]
        findings = detect_f04_invalid_commands(rules, evidence)
        assert len(findings) == 1
        assert "check:types" in findings[0].title

    def test_f04_known_build_command_no_finding(self):
        """npm run build where build script exists → no F04."""
        rules = [
            make_rule(
                category=None,
                normalized_key=None,
                normalized_value=None,
                text="Build with `npm run build`",
            )
        ]
        evidence = [self._cmd_evidence("build", "tsc")]
        findings = detect_f04_invalid_commands(rules, evidence)
        assert findings == []


# ---------------------------------------------------------------------------
# F05 — Exact Duplicate Rules
# ---------------------------------------------------------------------------


class TestF05Duplicates:
    def test_f05_exact_duplicate(self):
        """Same text in two files → F05."""
        rules = [
            make_rule(
                id="rule-agents-001",
                source_path="AGENTS.md",
                text="Always run pnpm install before making changes.",
            ),
            make_rule(
                id="rule-claude-001",
                source_path="CLAUDE.md",
                text="Always run pnpm install before making changes.",
            ),
        ]
        findings = detect_f05_duplicates(rules)
        assert len(findings) == 1
        f = findings[0]
        assert f.type == "F05"
        assert f.severity == "low"
        assert f.confidence == 1.0
        assert "rule-agents-001" in f.instruction_rules
        assert "rule-claude-001" in f.instruction_rules

    def test_f05_no_duplicate(self):
        """All unique rules → no F05."""
        rules = [
            make_rule(id="rule-agents-001", source_path="AGENTS.md", text="Use pnpm for package management."),
            make_rule(id="rule-agents-002", source_path="AGENTS.md", text="Run vitest for tests."),
        ]
        findings = detect_f05_duplicates(rules)
        assert findings == []

    def test_f05_case_insensitive(self):
        """'Use pnpm' and 'use pnpm' → F05 (case-folded match)."""
        rules = [
            make_rule(id="rule-agents-001", source_path="AGENTS.md", text="Use pnpm to install."),
            make_rule(id="rule-claude-001", source_path="CLAUDE.md", text="use pnpm to install."),
        ]
        findings = detect_f05_duplicates(rules)
        assert len(findings) == 1

    def test_f05_short_text_skipped(self):
        """Short rules (< 10 chars after normalization) are skipped."""
        rules = [
            make_rule(id="rule-agents-001", source_path="AGENTS.md", text="Use npm"),
            make_rule(id="rule-claude-001", source_path="CLAUDE.md", text="use npm"),
        ]
        # "use npm" normalizes to "use npm" = 7 chars — below threshold
        findings = detect_f05_duplicates(rules)
        assert findings == []

    def test_f05_deterministic_flag(self):
        """F05 findings have deterministic=True."""
        rules = [
            make_rule(id="r1", source_path="A.md", text="Always run pnpm install before changes."),
            make_rule(id="r2", source_path="B.md", text="Always run pnpm install before changes."),
        ]
        findings = detect_f05_duplicates(rules)
        assert findings[0].deterministic is True


# ---------------------------------------------------------------------------
# Combined pipeline
# ---------------------------------------------------------------------------


class TestRunDeterministicChecks:
    def test_run_deterministic_checks_combined(self):
        """Full pipeline with multiple finding types returns all findings."""
        rules = [
            # F02: npm vs pnpm mismatch
            make_rule(
                id="rule-claude-001",
                source_path="CLAUDE.md",
                category="package_manager",
                normalized_key="package_manager",
                normalized_value="npm",
                text="Use npm to install dependencies.",
            ),
        ]
        evidence = [
            make_evidence(id="ev-pm-001", value="pnpm", strength="strong"),
        ]
        findings = run_deterministic_checks(rules, evidence)
        assert len(findings) >= 1
        types = [f.type for f in findings]
        assert "F02" in types

    def test_findings_ids_assigned(self):
        """All returned findings have non-empty IDs."""
        rules = [make_rule(normalized_value="npm")]
        evidence = [make_evidence(value="pnpm", strength="strong")]
        findings = run_deterministic_checks(rules, evidence)
        for f in findings:
            assert f.id != ""
            assert f.id.startswith("find-")

    def test_findings_deterministic_flag(self):
        """All Phase 4 findings have deterministic=True."""
        rules = [make_rule(normalized_value="npm")]
        evidence = [make_evidence(value="pnpm", strength="strong")]
        findings = run_deterministic_checks(rules, evidence)
        for f in findings:
            assert f.deterministic is True

    def test_empty_inputs_returns_empty(self):
        """No rules + no evidence → no findings."""
        assert run_deterministic_checks([], []) == []

    def test_findings_sorted_by_severity(self):
        """Findings are sorted most-severe-first."""
        rules = [
            # F02 high
            make_rule(
                id="rule-claude-001",
                source_path="CLAUDE.md",
                category="package_manager",
                normalized_key="package_manager",
                normalized_value="npm",
                text="Use npm to install. Always run pnpm install before changes.",
            ),
            make_rule(
                id="rule-agents-001",
                source_path="AGENTS.md",
                category="package_manager",
                normalized_key="package_manager",
                normalized_value="npm",
                text="Always run pnpm install before changes.",
            ),
        ]
        evidence = [
            make_evidence(id="ev-pm-001", value="pnpm", strength="strong"),
        ]
        findings = run_deterministic_checks(rules, evidence)
        sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        for i in range(len(findings) - 1):
            assert sev_order.get(findings[i].severity, 99) <= sev_order.get(
                findings[i + 1].severity, 99
            )


# ---------------------------------------------------------------------------
# write_findings_json
# ---------------------------------------------------------------------------


class TestWriteFindingsJson:
    def test_write_findings_json_schema(self, tmp_path):
        """JSON file has agentlint_version, repo_path, and findings array."""
        findings = [
            Finding(
                id="find-f02-001",
                type="F02",
                severity="high",
                title="Test finding",
                explanation="Test explanation.",
                instruction_rules=["rule-001"],
                evidence_ids=["ev-001"],
                recommended_action="Fix it.",
                confidence=0.95,
                deterministic=True,
            )
        ]
        out_path = write_findings_json(tmp_path, findings)
        assert out_path.exists()
        data = json.loads(out_path.read_text(encoding="utf-8"))
        assert "agentlint_version" in data
        assert "repo_path" in data
        assert "findings" in data
        assert isinstance(data["findings"], list)
        assert len(data["findings"]) == 1
        assert data["findings"][0]["type"] == "F02"

    def test_write_findings_json_empty(self, tmp_path):
        """Empty findings list writes valid JSON with empty array."""
        out_path = write_findings_json(tmp_path, [])
        data = json.loads(out_path.read_text(encoding="utf-8"))
        assert data["findings"] == []

    def test_write_findings_json_creates_agentlint_dir(self, tmp_path):
        """Creates .agentlint/ directory if it doesn't exist."""
        repo = tmp_path / "myrepo"
        repo.mkdir()
        out_path = write_findings_json(repo, [])
        assert out_path.parent.name == ".agentlint"
        assert out_path.parent.is_dir()
