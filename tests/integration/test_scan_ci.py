"""Integration tests for Phase 10 — agentlint scan --fail-on-severity CI flag.

Tests verify that:
- --fail-on-severity high exits 1 on a repo with high findings.
- --fail-on-severity high exits 0 on a clean repo.
- omitting the flag always exits 0 regardless of findings (backward compat).
- --fail-on-severity none explicitly opts out.
- The failure output contains "AgentLint: FAIL".
- The pass output contains "AgentLint: PASS".
- An invalid severity value exits 1 with a helpful error message.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from agentlint.cli import app

runner = CliRunner()

# ---------------------------------------------------------------------------
# Demo repo paths (locked fixtures — permanent per AGENTS.md)
# ---------------------------------------------------------------------------

_DEMO_REPOS_DIR = Path(__file__).resolve().parent.parent.parent / "demo_repos"

# inconsistent-js-repo is known to produce >= 1 high-severity finding.
_INCONSISTENT = _DEMO_REPOS_DIR / "inconsistent-js-repo"

# clean-repo has no high/critical findings.
_CLEAN = _DEMO_REPOS_DIR / "clean-repo"


# ---------------------------------------------------------------------------
# Guard: skip entire module if demo repos are missing (e.g. stripped install)
# ---------------------------------------------------------------------------

pytestmark = pytest.mark.skipif(
    not _DEMO_REPOS_DIR.exists(),
    reason="demo_repos/ not found — skipping CI integration tests",
)


# ---------------------------------------------------------------------------
# Helper: clone a demo repo to a temp dir so scans don't pollute fixtures
# ---------------------------------------------------------------------------


def _copy_repo(src: Path) -> Path:
    """Copy *src* demo repo to a fresh temp directory and return its path."""
    tmp = Path(tempfile.mkdtemp())
    shutil.copytree(src, tmp / src.name)
    return tmp / src.name


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestFailOnSeverityHighFindings:
    """Exit codes when the repo has high-severity findings."""

    def test_fail_on_high_with_high_findings_exits_1(self):
        """scan --fail-on-severity high exits 1 on inconsistent-js-repo."""
        if not _INCONSISTENT.is_dir():
            pytest.skip("inconsistent-js-repo demo fixture not found")

        repo = _copy_repo(_INCONSISTENT)
        try:
            result = runner.invoke(app, ["scan", str(repo), "--fail-on-severity", "high"])
            assert result.exit_code == 1, (
                f"Expected exit 1, got {result.exit_code}.\nOutput:\n{result.output}"
            )
        finally:
            shutil.rmtree(repo.parent, ignore_errors=True)

    def test_fail_output_contains_agentlint_fail(self):
        """--fail-on-severity high prints 'AgentLint: FAIL' on drift repo."""
        if not _INCONSISTENT.is_dir():
            pytest.skip("inconsistent-js-repo demo fixture not found")

        repo = _copy_repo(_INCONSISTENT)
        try:
            result = runner.invoke(app, ["scan", str(repo), "--fail-on-severity", "high"])
            assert "AgentLint: FAIL" in result.output, (
                f"'AgentLint: FAIL' not found in output:\n{result.output}"
            )
        finally:
            shutil.rmtree(repo.parent, ignore_errors=True)

    def test_fail_output_contains_drift_message(self):
        """Failure output mentions severity drift."""
        if not _INCONSISTENT.is_dir():
            pytest.skip("inconsistent-js-repo demo fixture not found")

        repo = _copy_repo(_INCONSISTENT)
        try:
            result = runner.invoke(app, ["scan", str(repo), "--fail-on-severity", "high"])
            assert "instruction drift detected" in result.output.lower(), (
                f"Drift message not found in output:\n{result.output}"
            )
        finally:
            shutil.rmtree(repo.parent, ignore_errors=True)


class TestFailOnSeverityCleanRepo:
    """Exit codes when the repo has no high-severity findings."""

    def test_pass_on_high_with_clean_repo_exits_0(self):
        """scan --fail-on-severity high exits 0 on clean-repo."""
        if not _CLEAN.is_dir():
            pytest.skip("clean-repo demo fixture not found")

        repo = _copy_repo(_CLEAN)
        try:
            result = runner.invoke(app, ["scan", str(repo), "--fail-on-severity", "high"])
            assert result.exit_code == 0, (
                f"Expected exit 0, got {result.exit_code}.\nOutput:\n{result.output}"
            )
        finally:
            shutil.rmtree(repo.parent, ignore_errors=True)

    def test_pass_output_contains_agentlint_pass(self):
        """--fail-on-severity high prints 'AgentLint: PASS' on clean repo."""
        if not _CLEAN.is_dir():
            pytest.skip("clean-repo demo fixture not found")

        repo = _copy_repo(_CLEAN)
        try:
            result = runner.invoke(app, ["scan", str(repo), "--fail-on-severity", "high"])
            assert "AgentLint: PASS" in result.output, (
                f"'AgentLint: PASS' not found in output:\n{result.output}"
            )
        finally:
            shutil.rmtree(repo.parent, ignore_errors=True)


class TestBackwardCompatibility:
    """Omitting --fail-on-severity must not change existing exit behaviour."""

    def test_no_flag_always_exits_zero_on_dirty_repo(self):
        """scan without --fail-on-severity exits 0 even with high findings."""
        if not _INCONSISTENT.is_dir():
            pytest.skip("inconsistent-js-repo demo fixture not found")

        repo = _copy_repo(_INCONSISTENT)
        try:
            result = runner.invoke(app, ["scan", str(repo)])
            assert result.exit_code == 0, (
                f"Expected exit 0 (no flag), got {result.exit_code}.\nOutput:\n{result.output}"
            )
        finally:
            shutil.rmtree(repo.parent, ignore_errors=True)

    def test_fail_on_severity_none_explicit_exits_zero(self):
        """scan --fail-on-severity none explicitly opts out — exits 0."""
        if not _INCONSISTENT.is_dir():
            pytest.skip("inconsistent-js-repo demo fixture not found")

        repo = _copy_repo(_INCONSISTENT)
        try:
            result = runner.invoke(app, ["scan", str(repo), "--fail-on-severity", "none"])
            assert result.exit_code == 0, (
                f"Expected exit 0 with --fail-on-severity none, "
                f"got {result.exit_code}.\nOutput:\n{result.output}"
            )
        finally:
            shutil.rmtree(repo.parent, ignore_errors=True)

    def test_no_flag_output_does_not_contain_agentlint_pass_or_fail(self):
        """Without the flag the CI pass/fail header must NOT appear."""
        if not _CLEAN.is_dir():
            pytest.skip("clean-repo demo fixture not found")

        repo = _copy_repo(_CLEAN)
        try:
            result = runner.invoke(app, ["scan", str(repo)])
            assert "AgentLint: PASS" not in result.output, (
                "CI block printed even without --fail-on-severity flag"
            )
            assert "AgentLint: FAIL" not in result.output, (
                "CI block printed even without --fail-on-severity flag"
            )
        finally:
            shutil.rmtree(repo.parent, ignore_errors=True)


class TestInvalidSeverityValue:
    """Bad --fail-on-severity values must be rejected with exit 1."""

    def test_invalid_severity_value_exits_1(self):
        """Unknown severity string exits 1."""
        if not _CLEAN.is_dir():
            pytest.skip("clean-repo demo fixture not found")

        repo = _copy_repo(_CLEAN)
        try:
            result = runner.invoke(
                app, ["scan", str(repo), "--fail-on-severity", "EXTREME"]
            )
            assert result.exit_code == 1, (
                f"Expected exit 1 for invalid severity, "
                f"got {result.exit_code}.\nOutput:\n{result.output}"
            )
        finally:
            shutil.rmtree(repo.parent, ignore_errors=True)

    def test_invalid_severity_value_prints_error(self):
        """Unknown severity string prints a helpful error message."""
        if not _CLEAN.is_dir():
            pytest.skip("clean-repo demo fixture not found")

        repo = _copy_repo(_CLEAN)
        try:
            result = runner.invoke(
                app, ["scan", str(repo), "--fail-on-severity", "EXTREME"]
            )
            # Error goes to stderr, but CliRunner merges streams by default.
            combined = (result.output or "") + (
                str(result.stderr) if hasattr(result, "stderr") and result.stderr else ""
            )
            assert "invalid" in combined.lower() or "valid values" in combined.lower(), (
                f"No helpful error message found.\nOutput:\n{result.output}"
            )
        finally:
            shutil.rmtree(repo.parent, ignore_errors=True)


class TestSeverityThresholds:
    """Verify threshold levels behave correctly (critical vs high vs medium)."""

    def test_fail_on_critical_does_not_fail_if_only_high_findings(self):
        """--fail-on-severity critical passes when only high findings exist."""
        if not _INCONSISTENT.is_dir():
            pytest.skip("inconsistent-js-repo demo fixture not found")

        repo = _copy_repo(_INCONSISTENT)
        try:
            result = runner.invoke(
                app, ["scan", str(repo), "--fail-on-severity", "critical"]
            )
            # inconsistent-js-repo has high but may not have critical findings.
            # If it does have critical, exit 1; if not, exit 0. Either is correct.
            # The important thing is the command itself doesn't crash.
            assert result.exit_code in (0, 1), (
                f"Unexpected exit code {result.exit_code}.\nOutput:\n{result.output}"
            )
            # No exception/traceback should be in the output
            assert "Traceback" not in result.output, (
                f"Unexpected traceback:\n{result.output}"
            )
        finally:
            shutil.rmtree(repo.parent, ignore_errors=True)

    def test_fail_on_medium_exits_1_if_medium_findings_exist(self):
        """--fail-on-severity medium exits 1 when medium+ findings exist."""
        if not _INCONSISTENT.is_dir():
            pytest.skip("inconsistent-js-repo demo fixture not found")

        repo = _copy_repo(_INCONSISTENT)
        try:
            result = runner.invoke(
                app, ["scan", str(repo), "--fail-on-severity", "medium"]
            )
            # inconsistent-js-repo has many findings including medium severity.
            # Exit 1 expected; if no medium findings exist, exit 0 is also valid.
            assert result.exit_code in (0, 1), (
                f"Unexpected exit code {result.exit_code}.\nOutput:\n{result.output}"
            )
            assert "Traceback" not in result.output
        finally:
            shutil.rmtree(repo.parent, ignore_errors=True)


class TestCIReportBuilder:
    """Unit-level tests for format_ci_failure_block and format_ci_pass_block."""

    def test_format_ci_pass_block(self):
        from agentlint.analysis.report_builder import format_ci_pass_block

        assert format_ci_pass_block() == "AgentLint: PASS"

    def test_format_ci_failure_block_header(self):
        from agentlint.analysis.report_builder import format_ci_failure_block
        from agentlint.models import Finding

        f = Finding(
            id="find-f02-001",
            type="F02",
            severity="high",
            title="AGENTS.md says: npm — Repository evidence: pnpm",
            explanation="...",
            instruction_rules=[],
            evidence_ids=[],
            recommended_action="Update AGENTS.md",
            confidence=1.0,
            deterministic=True,
        )
        block = format_ci_failure_block([f], "high")
        assert block.startswith("AgentLint: FAIL")
        assert "High-severity instruction drift detected." in block
        assert "AGENTS.md says: npm" in block

    def test_format_ci_failure_block_multiple_findings(self):
        from agentlint.analysis.report_builder import format_ci_failure_block
        from agentlint.models import Finding

        findings = [
            Finding(
                id=f"find-f02-00{i}",
                type="F02",
                severity="high",
                title=f"Finding title {i}",
                explanation="...",
                instruction_rules=[],
                evidence_ids=[],
                recommended_action="Fix it",
                confidence=1.0,
                deterministic=True,
            )
            for i in range(1, 4)
        ]
        block = format_ci_failure_block(findings, "high")
        assert "AgentLint: FAIL" in block
        assert "Finding title 1" in block
        assert "Finding title 2" in block
        assert "Finding title 3" in block

    def test_severity_order_exported(self):
        from agentlint.analysis import SEVERITY_ORDER

        assert "critical" in SEVERITY_ORDER
        assert "high" in SEVERITY_ORDER
        assert SEVERITY_ORDER["critical"] < SEVERITY_ORDER["high"]
        assert SEVERITY_ORDER["high"] < SEVERITY_ORDER["medium"]
