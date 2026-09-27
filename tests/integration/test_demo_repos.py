"""Integration tests for Phase 5 — Sample Repositories and Golden Scenarios.

Tests run the full scanner pipeline against the three packaged demo repos and
assert deterministic, known expected outputs.  No LLM or network is involved.

Helper ``_run_full_scan`` drives the pipeline directly (no subprocess) to
avoid OS-path and entry-point complications.  The ``agentlint demo`` CLI test
uses subprocess to verify the command-level contract.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from agentlint.analysis import run_deterministic_checks
from agentlint.config import load_config
from agentlint.discovery.instruction_sources import discover_sources
from agentlint.evidence import collect_evidence
from agentlint.models import Finding
from agentlint.parsing import extract_rules

# ---------------------------------------------------------------------------
# Paths to the three demo repos (resolved relative to this package root)
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_DEMO_A = _REPO_ROOT / "demo_repos" / "inconsistent-js-repo"
_DEMO_B = _REPO_ROOT / "demo_repos" / "single-agent-stale-repo"
_DEMO_C = _REPO_ROOT / "demo_repos" / "clean-repo"
_GOLDEN_DIR = _REPO_ROOT / "tests" / "golden"


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _run_full_scan(repo_path: Path) -> list[Finding]:
    """Run discover → evidence → rules → findings for *repo_path*.

    Does NOT write any output files — purely in-memory pipeline.
    """
    config = load_config(repo_path)
    sources = discover_sources(repo_path, config)
    evidence = collect_evidence(repo_path)
    rules = extract_rules(sources, repo_path=repo_path)
    findings = run_deterministic_checks(rules, evidence)
    return findings


# ---------------------------------------------------------------------------
# Demo A — inconsistent-js-repo
# ---------------------------------------------------------------------------


class TestInconsistentJsRepo:
    @pytest.fixture(scope="class")
    def findings(self) -> list[Finding]:
        return _run_full_scan(_DEMO_A)

    def test_has_f01_package_manager_conflict(self, findings):
        """AGENTS.md (npm) vs CLAUDE.md (pnpm) → at least one F01 for package_manager."""
        f01_pm = [
            f for f in findings
            if f.type == "F01" and "package_manager" in f.title
        ]
        assert len(f01_pm) >= 1, "Expected F01 package_manager conflict"

    def test_has_f01_test_framework_conflict(self, findings):
        """AGENTS.md (jest) vs CLAUDE.md (vitest) → at least one F01 for test_framework."""
        f01_tf = [
            f for f in findings
            if f.type == "F01" and "test_framework" in f.title
        ]
        assert len(f01_tf) >= 1, "Expected F01 test_framework conflict"

    def test_has_f02_package_manager_mismatch(self, findings):
        """AGENTS.md npm vs repo pnpm → at least one F02 for package_manager."""
        f02_pm = [
            f for f in findings
            if f.type == "F02" and "package_manager" in f.title
        ]
        assert len(f02_pm) >= 1, "Expected F02 package_manager mismatch"

    def test_has_f02_test_framework_mismatch(self, findings):
        """AGENTS.md jest vs repo vitest → at least one F02 for test_framework."""
        f02_tf = [
            f for f in findings
            if f.type == "F02" and "test_framework" in f.title
        ]
        assert len(f02_tf) >= 1, "Expected F02 test_framework mismatch"

    def test_has_f03_stale_path(self, findings):
        """AGENTS.md references src/services/ or absent path → at least one F03."""
        f03 = [f for f in findings if f.type == "F03"]
        assert len(f03) >= 1, "Expected at least one F03 stale path"

    def test_has_f04_invalid_command_test_unit(self, findings):
        """Copilot instructions reference npm run test:unit → F04."""
        f04_tu = [
            f for f in findings
            if f.type == "F04" and "test:unit" in f.title
        ]
        assert len(f04_tu) >= 1, "Expected F04 for test:unit absent script"

    def test_has_f04_invalid_command_deploy(self, findings):
        """Bob rules reference npm run deploy → F04."""
        f04_dep = [
            f for f in findings
            if f.type == "F04" and "deploy" in f.title
        ]
        assert len(f04_dep) >= 1, "Expected F04 for deploy absent script"

    def test_has_f05_duplicate(self, findings):
        """CLAUDE.md and copilot instructions share DoD rule → at least one F05."""
        f05 = [f for f in findings if f.type == "F05"]
        assert len(f05) >= 1, "Expected at least one F05 duplicate"

    def test_all_findings_deterministic(self, findings):
        """All findings from Phase 4/5 must have deterministic=True."""
        for f in findings:
            assert f.deterministic is True, f"Finding {f.id} has deterministic=False"

    def test_minimum_finding_count(self, findings):
        """At least 7 findings total."""
        assert len(findings) >= 7, f"Expected >= 7 findings, got {len(findings)}"


# ---------------------------------------------------------------------------
# Demo B — single-agent-stale-repo
# ---------------------------------------------------------------------------


class TestSingleAgentStaleRepo:
    @pytest.fixture(scope="class")
    def findings(self) -> list[Finding]:
        return _run_full_scan(_DEMO_B)

    def test_has_f02_package_manager_mismatch(self, findings):
        """CLAUDE.md npm vs pnpm repo → at least one F02 package_manager."""
        f02_pm = [
            f for f in findings
            if f.type == "F02" and "package_manager" in f.title
        ]
        assert len(f02_pm) >= 1, "Expected F02 package_manager mismatch"

    def test_has_f03_stale_services_path(self, findings):
        """CLAUDE.md references src/services/ which does not exist → F03."""
        f03_svc = [
            f for f in findings
            if f.type == "F03" and "src/services/" in f.title
        ]
        assert len(f03_svc) >= 1, "Expected F03 for src/services/ stale path"

    def test_all_findings_deterministic(self, findings):
        """All findings have deterministic=True."""
        for f in findings:
            assert f.deterministic is True, f"Finding {f.id} has deterministic=False"

    def test_minimum_finding_count(self, findings):
        """At least 2 findings (F02 + F03)."""
        assert len(findings) >= 2, f"Expected >= 2 findings, got {len(findings)}"


# ---------------------------------------------------------------------------
# Demo C — clean-repo
# ---------------------------------------------------------------------------


class TestCleanRepo:
    @pytest.fixture(scope="class")
    def findings(self) -> list[Finding]:
        return _run_full_scan(_DEMO_C)

    def test_no_high_severity_findings(self, findings):
        """Clean repo must produce zero critical or high severity findings."""
        high_or_critical = [
            f for f in findings
            if f.severity in ("critical", "high")
        ]
        assert high_or_critical == [], (
            f"Expected no critical/high findings, got: "
            + ", ".join(f"{f.type}:{f.severity} — {f.title}" for f in high_or_critical)
        )

    def test_all_findings_deterministic(self, findings):
        """All findings (if any) have deterministic=True."""
        for f in findings:
            assert f.deterministic is True


# ---------------------------------------------------------------------------
# Golden snapshot tests
# ---------------------------------------------------------------------------


class TestGoldenSnapshotInconsistent:
    @pytest.fixture(scope="class")
    def golden(self) -> dict:
        return json.loads((_GOLDEN_DIR / "inconsistent-js-repo.json").read_text(encoding="utf-8"))

    @pytest.fixture(scope="class")
    def findings(self) -> list[Finding]:
        return _run_full_scan(_DEMO_A)

    def test_minimum_count_met(self, golden, findings):
        """Actual finding count meets golden minimum."""
        assert len(findings) >= golden["minimum_finding_count"], (
            f"Expected >= {golden['minimum_finding_count']} findings, got {len(findings)}"
        )

    def test_required_types_present(self, golden, findings):
        """All required finding types from golden file are present."""
        actual_types = {f.type for f in findings}
        for req_type in golden["required_types"]:
            assert req_type in actual_types, (
                f"Required type {req_type!r} not found in actual findings"
            )

    def test_golden_finding_entries_matched(self, golden, findings):
        """Each entry in golden 'findings' has at least one match in actual output."""
        for entry in golden["findings"]:
            f_type = entry["type"]
            title_contains = entry.get("title_contains", "")
            severity = entry.get("severity")
            matches = [
                f for f in findings
                if f.type == f_type
                and (not title_contains or title_contains in f.title)
                and (not severity or f.severity == severity)
            ]
            assert len(matches) >= 1, (
                f"No match for golden entry: type={f_type!r}, "
                f"title_contains={title_contains!r}, severity={severity!r}"
            )


class TestGoldenSnapshotSingleAgent:
    @pytest.fixture(scope="class")
    def golden(self) -> dict:
        return json.loads((_GOLDEN_DIR / "single-agent-stale-repo.json").read_text(encoding="utf-8"))

    @pytest.fixture(scope="class")
    def findings(self) -> list[Finding]:
        return _run_full_scan(_DEMO_B)

    def test_minimum_count_met(self, golden, findings):
        assert len(findings) >= golden["minimum_finding_count"]

    def test_required_types_present(self, golden, findings):
        actual_types = {f.type for f in findings}
        for req_type in golden["required_types"]:
            assert req_type in actual_types, (
                f"Required type {req_type!r} not found in actual findings"
            )

    def test_golden_finding_entries_matched(self, golden, findings):
        for entry in golden["findings"]:
            f_type = entry["type"]
            title_contains = entry.get("title_contains", "")
            severity = entry.get("severity")
            matches = [
                f for f in findings
                if f.type == f_type
                and (not title_contains or title_contains in f.title)
                and (not severity or f.severity == severity)
            ]
            assert len(matches) >= 1, (
                f"No match for golden entry: type={f_type!r}, "
                f"title_contains={title_contains!r}, severity={severity!r}"
            )


class TestGoldenSnapshotClean:
    @pytest.fixture(scope="class")
    def golden(self) -> dict:
        return json.loads((_GOLDEN_DIR / "clean-repo.json").read_text(encoding="utf-8"))

    @pytest.fixture(scope="class")
    def findings(self) -> list[Finding]:
        return _run_full_scan(_DEMO_C)

    def test_no_high_severity_from_golden(self, golden, findings):
        """Golden no_high_severity=true means no critical/high findings."""
        if golden["no_high_severity"]:
            high = [f for f in findings if f.severity in ("critical", "high")]
            assert high == [], (
                "Golden requires no high-severity, got: "
                + ", ".join(f.title for f in high)
            )


# ---------------------------------------------------------------------------
# agentlint demo command
# ---------------------------------------------------------------------------


class TestAgentlintDemoCommand:
    def test_demo_command_exits_zero(self):
        """``agentlint demo`` must exit with code 0."""
        result = subprocess.run(
            [sys.executable, "-m", "agentlint.cli", "demo"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"agentlint demo exited {result.returncode}.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_demo_command_mentions_all_repos(self):
        """``agentlint demo`` stdout mentions all three demo repo names."""
        result = subprocess.run(
            [sys.executable, "-m", "agentlint.cli", "demo"],
            capture_output=True,
            text=True,
        )
        output = result.stdout + result.stderr
        for repo_name in ["inconsistent-js-repo", "single-agent-stale-repo", "clean-repo"]:
            assert repo_name in output, (
                f"Demo output should mention {repo_name!r}.\n"
                f"stdout: {result.stdout}\nstderr: {result.stderr}"
            )
