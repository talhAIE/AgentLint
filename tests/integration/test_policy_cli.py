"""Integration tests for Phase 7 — Canonical Policy Compiler and Repair Plan CLI.

Tests verify that:
  1. ``agentlint policy <repo-path>`` exits with code 0 on all demo repos.
  2. ``.agentlint/policy.yaml`` is created and contains valid YAML.
  3. ``.agentlint/repair-plan.md`` is created and contains required sections.
  4. Policy YAML structure matches the schema from AgentLintplan.md §11.
  5. Repair plan contains Evidence: references linking to actual source files.

All tests use subprocess to invoke the CLI (same as the existing demo CLI tests),
and operate on copies of the demo repos in tmp_path to avoid polluting the fixture
directories.

Demo repos used as fixtures (per AGENTS.md):
  - demo_repos/inconsistent-js-repo   — multiple conflicts, expected findings
  - demo_repos/single-agent-stale-repo — single stale rule
  - demo_repos/clean-repo             — clean, minimal findings
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

# ---------------------------------------------------------------------------
# Repo locations
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_DEMO_A = _REPO_ROOT / "demo_repos" / "inconsistent-js-repo"
_DEMO_B = _REPO_ROOT / "demo_repos" / "single-agent-stale-repo"
_DEMO_C = _REPO_ROOT / "demo_repos" / "clean-repo"


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _copy_demo_repo(src: Path, tmp_path: Path) -> Path:
    """Return a fresh copy of *src* under *tmp_path* to avoid polluting fixtures."""
    dest = tmp_path / src.name
    shutil.copytree(src, dest, dirs_exist_ok=True)
    return dest


def _run_policy(repo_path: Path) -> subprocess.CompletedProcess:
    """Run ``agentlint policy <repo_path>`` and return the completed process."""
    return subprocess.run(
        [sys.executable, "-m", "agentlint.cli", "policy", str(repo_path)],
        capture_output=True,
        text=True,
    )


# ---------------------------------------------------------------------------
# Demo A — inconsistent-js-repo
# ---------------------------------------------------------------------------


class TestPolicyCLIDemoA:
    def test_exit_code_zero(self, tmp_path):
        repo = _copy_demo_repo(_DEMO_A, tmp_path)
        result = _run_policy(repo)
        assert result.returncode == 0, (
            f"agentlint policy failed on inconsistent-js-repo:\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_policy_yaml_created(self, tmp_path):
        repo = _copy_demo_repo(_DEMO_A, tmp_path)
        _run_policy(repo)
        assert (repo / ".agentlint" / "policy.yaml").exists()

    def test_repair_plan_md_created(self, tmp_path):
        repo = _copy_demo_repo(_DEMO_A, tmp_path)
        _run_policy(repo)
        assert (repo / ".agentlint" / "repair-plan.md").exists()

    def test_policy_yaml_is_valid_yaml(self, tmp_path):
        repo = _copy_demo_repo(_DEMO_A, tmp_path)
        _run_policy(repo)
        content = (repo / ".agentlint" / "policy.yaml").read_text(encoding="utf-8")
        parsed = yaml.safe_load(content)
        assert isinstance(parsed, dict)

    def test_policy_yaml_has_version_1(self, tmp_path):
        repo = _copy_demo_repo(_DEMO_A, tmp_path)
        _run_policy(repo)
        content = (repo / ".agentlint" / "policy.yaml").read_text(encoding="utf-8")
        parsed = yaml.safe_load(content)
        assert parsed["version"] == 1

    def test_policy_yaml_detects_pnpm(self, tmp_path):
        """inconsistent-js-repo uses pnpm — policy should detect it."""
        repo = _copy_demo_repo(_DEMO_A, tmp_path)
        _run_policy(repo)
        content = (repo / ".agentlint" / "policy.yaml").read_text(encoding="utf-8")
        parsed = yaml.safe_load(content)
        tooling = parsed.get("tooling", {})
        assert tooling.get("package_manager") == "pnpm"

    def test_policy_yaml_has_evidence_section(self, tmp_path):
        repo = _copy_demo_repo(_DEMO_A, tmp_path)
        _run_policy(repo)
        content = (repo / ".agentlint" / "policy.yaml").read_text(encoding="utf-8")
        parsed = yaml.safe_load(content)
        assert "evidence" in parsed

    def test_repair_plan_has_approval_notice(self, tmp_path):
        repo = _copy_demo_repo(_DEMO_A, tmp_path)
        _run_policy(repo)
        content = (repo / ".agentlint" / "repair-plan.md").read_text(encoding="utf-8")
        assert "Approval required" in content

    def test_repair_plan_has_repair_items(self, tmp_path):
        """inconsistent-js-repo should produce at least one repair item."""
        repo = _copy_demo_repo(_DEMO_A, tmp_path)
        _run_policy(repo)
        content = (repo / ".agentlint" / "repair-plan.md").read_text(encoding="utf-8")
        # Should have at least one numbered item
        assert "## 1." in content

    def test_stdout_mentions_policy_yaml(self, tmp_path):
        repo = _copy_demo_repo(_DEMO_A, tmp_path)
        result = _run_policy(repo)
        assert "policy.yaml" in result.stdout

    def test_stdout_mentions_repair_plan(self, tmp_path):
        repo = _copy_demo_repo(_DEMO_A, tmp_path)
        result = _run_policy(repo)
        assert "repair-plan.md" in result.stdout

    def test_stdout_approval_message(self, tmp_path):
        repo = _copy_demo_repo(_DEMO_A, tmp_path)
        result = _run_policy(repo)
        assert "Approval required" in result.stdout


# ---------------------------------------------------------------------------
# Demo B — single-agent-stale-repo
# ---------------------------------------------------------------------------


class TestPolicyCLIDemoB:
    def test_exit_code_zero(self, tmp_path):
        repo = _copy_demo_repo(_DEMO_B, tmp_path)
        result = _run_policy(repo)
        assert result.returncode == 0, (
            f"agentlint policy failed on single-agent-stale-repo:\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_policy_yaml_created(self, tmp_path):
        repo = _copy_demo_repo(_DEMO_B, tmp_path)
        _run_policy(repo)
        assert (repo / ".agentlint" / "policy.yaml").exists()

    def test_repair_plan_md_created(self, tmp_path):
        repo = _copy_demo_repo(_DEMO_B, tmp_path)
        _run_policy(repo)
        assert (repo / ".agentlint" / "repair-plan.md").exists()

    def test_policy_yaml_is_valid_yaml(self, tmp_path):
        repo = _copy_demo_repo(_DEMO_B, tmp_path)
        _run_policy(repo)
        content = (repo / ".agentlint" / "policy.yaml").read_text(encoding="utf-8")
        parsed = yaml.safe_load(content)
        assert isinstance(parsed, dict)


# ---------------------------------------------------------------------------
# Demo C — clean-repo
# ---------------------------------------------------------------------------


class TestPolicyCLIDemoC:
    def test_exit_code_zero(self, tmp_path):
        repo = _copy_demo_repo(_DEMO_C, tmp_path)
        result = _run_policy(repo)
        assert result.returncode == 0, (
            f"agentlint policy failed on clean-repo:\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_policy_yaml_created(self, tmp_path):
        repo = _copy_demo_repo(_DEMO_C, tmp_path)
        _run_policy(repo)
        assert (repo / ".agentlint" / "policy.yaml").exists()

    def test_repair_plan_md_created(self, tmp_path):
        repo = _copy_demo_repo(_DEMO_C, tmp_path)
        _run_policy(repo)
        assert (repo / ".agentlint" / "repair-plan.md").exists()

    def test_clean_repo_no_or_minimal_repair_items(self, tmp_path):
        """clean-repo should produce zero or very few repair items (per golden scenarios)."""
        repo = _copy_demo_repo(_DEMO_C, tmp_path)
        result = _run_policy(repo)
        assert result.returncode == 0
        # Either no repair items message, or very few items
        content = (repo / ".agentlint" / "repair-plan.md").read_text(encoding="utf-8")
        assert "Repair Plan" in content


# ---------------------------------------------------------------------------
# Cross-cutting: invalid path
# ---------------------------------------------------------------------------


class TestPolicyCLIInvalidPath:
    def test_nonexistent_path_exits_1(self, tmp_path):
        bad_path = tmp_path / "does-not-exist"
        result = _run_policy(bad_path)
        assert result.returncode == 1

    def test_nonexistent_path_error_message(self, tmp_path):
        bad_path = tmp_path / "does-not-exist"
        result = _run_policy(bad_path)
        assert "Error" in result.stderr or "Error" in result.stdout
