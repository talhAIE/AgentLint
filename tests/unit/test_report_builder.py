"""Phase 11 — Unit tests for agentlint.analysis.report_builder.

Covers:
  - format_findings_summary (zero, single, mixed, unknown-type findings)
  - format_ci_failure_block (header, per-finding detail)
  - format_ci_pass_block (static output)
"""

from __future__ import annotations

import pytest

from agentlint.analysis.report_builder import (
    format_ci_failure_block,
    format_ci_pass_block,
    format_findings_summary,
)
from agentlint.models import Finding


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def _make_finding(
    *,
    id: str = "find-f02-001",
    type: str = "F02",
    severity: str = "high",
    title: str = "Package manager mismatch",
    explanation: str = "test",
    confidence: float = 0.95,
    deterministic: bool = True,
    status: str = "open",
) -> Finding:
    return Finding(
        id=id,
        type=type,
        severity=severity,
        title=title,
        explanation=explanation,
        instruction_rules=[],
        evidence_ids=[],
        recommended_action="Fix it",
        confidence=confidence,
        deterministic=deterministic,
        status=status,
    )


# ---------------------------------------------------------------------------
# format_findings_summary
# ---------------------------------------------------------------------------

class TestFormatFindingsSummary:
    """Unit tests for format_findings_summary."""

    def test_empty_list_returns_clean(self):
        """Zero findings → clean message."""
        result = format_findings_summary([])
        assert result == "Findings: 0 finding(s) -- clean"

    def test_single_high_f02(self):
        """Single high-severity F02 finding."""
        findings = [_make_finding()]
        result = format_findings_summary(findings)
        assert "1 finding(s)" in result
        assert "1 high" in result
        assert "0 critical" in result
        assert "F02 (mismatch): 1" in result

    def test_mixed_severities(self):
        """Correct counts for multiple severity levels."""
        findings = [
            _make_finding(id="a", severity="critical", type="F01"),
            _make_finding(id="b", severity="high", type="F02"),
            _make_finding(id="c", severity="high", type="F02"),
            _make_finding(id="d", severity="medium", type="F03"),
            _make_finding(id="e", severity="low", type="F05"),
            _make_finding(id="f", severity="info", type="F05"),
        ]
        result = format_findings_summary(findings)
        assert "6 finding(s)" in result
        assert "1 critical" in result
        assert "2 high" in result
        assert "1 medium" in result
        assert "1 low" in result
        assert "1 info" in result

    def test_type_breakdown_lines_present(self):
        """Per-type breakdown lines appear in the output."""
        findings = [
            _make_finding(id="a", type="F01"),
            _make_finding(id="b", type="F03"),
            _make_finding(id="c", type="F05"),
        ]
        result = format_findings_summary(findings)
        assert "F01 (cross-file conflict): 1" in result
        assert "F03 (stale path): 1" in result
        assert "F05 (duplicate): 1" in result

    def test_unknown_type_uses_lowercase(self):
        """Unknown finding type falls back to type.lower() label."""
        findings = [_make_finding(type="F99")]
        result = format_findings_summary(findings)
        assert "F99 (f99): 1" in result

    def test_all_five_severity_levels_in_header(self):
        """Header always contains all 5 severity labels, even if count is 0."""
        findings = [_make_finding(severity="medium")]
        result = format_findings_summary(findings)
        header = result.split("\n")[0]
        for sev in ("critical", "high", "medium", "low", "info"):
            assert sev in header


# ---------------------------------------------------------------------------
# format_ci_failure_block
# ---------------------------------------------------------------------------

class TestFormatCiFailureBlock:
    """Unit tests for format_ci_failure_block."""

    def test_header_contains_fail(self):
        result = format_ci_failure_block([], "high")
        assert "AgentLint: FAIL" in result

    def test_severity_label_capitalized(self):
        result = format_ci_failure_block([], "high")
        assert "High-severity instruction drift detected." in result

    def test_finding_titles_included(self):
        findings = [
            _make_finding(title="AGENTS.md says npm but repository evidence shows pnpm"),
            _make_finding(title="Test framework mismatch: jest vs vitest"),
        ]
        result = format_ci_failure_block(findings, "high")
        assert "AGENTS.md says npm but repository evidence shows pnpm" in result
        assert "Test framework mismatch: jest vs vitest" in result


# ---------------------------------------------------------------------------
# format_ci_pass_block
# ---------------------------------------------------------------------------

class TestFormatCiPassBlock:
    """Unit tests for format_ci_pass_block."""

    def test_returns_pass(self):
        assert format_ci_pass_block() == "AgentLint: PASS"
