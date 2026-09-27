"""Integration tests for Phase 8 — agentlint validate CLI.

Tests verify that the agentlint validate subcommand works end-to-end on
the demo repos and in controlled temp-dir scenarios.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from agentlint.cli import app

runner = CliRunner()

# Demo repos directory (relative to the project root)
_DEMO_REPOS_DIR = Path(__file__).resolve().parent.parent.parent / "demo_repos"

_DEMO_REPOS = [
    "inconsistent-js-repo",
    "single-agent-stale-repo",
    "clean-repo",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _seed_artifacts(repo_path: Path, findings: list | None = None) -> None:
    """Write minimal .agentlint/findings.json and policy.yaml for testing."""
    agentlint_dir = repo_path / ".agentlint"
    agentlint_dir.mkdir(exist_ok=True)

    findings_data = {
        "agentlint_version": "0.1.0",
        "repo_path": str(repo_path),
        "findings": findings or [],
    }
    (agentlint_dir / "findings.json").write_text(
        json.dumps(findings_data), encoding="utf-8"
    )

    policy_data = {
        "version": 1,
        "tooling": {},
        "definition_of_done": [],
        "evidence": {},
    }
    (agentlint_dir / "policy.yaml").write_text(
        yaml.dump(policy_data), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# Tests: missing artifacts produce helpful errors
# ---------------------------------------------------------------------------


class TestValidateMissingArtifacts:
    def test_missing_findings_and_policy_shows_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(
                app, ["validate", tmpdir, "--skip-commands"]
            )
        assert result.exit_code != 0
        output = (result.stdout or "") + (result.output or "")
        assert "missing" in output.lower() or "error" in output.lower()

    def test_missing_findings_json_shows_guidance(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            # Write only policy.yaml, not findings.json
            agentlint_dir = p / ".agentlint"
            agentlint_dir.mkdir()
            (agentlint_dir / "policy.yaml").write_text("version: 1\n", encoding="utf-8")
            result = runner.invoke(app, ["validate", tmpdir, "--skip-commands"])
        assert result.exit_code != 0
        output = result.output or ""
        # Should mention findings.json or agentlint policy
        assert "findings" in output.lower() or "policy" in output.lower()

    def test_nonexistent_path_exits_with_error(self):
        result = runner.invoke(app, ["validate", "/nonexistent/path/xyz"])
        assert result.exit_code != 0

    def test_file_path_exits_with_error(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"content")
            fpath = f.name
        try:
            result = runner.invoke(app, ["validate", fpath])
            assert result.exit_code != 0
        finally:
            Path(fpath).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Tests: validate runs on seeded temp dirs
# ---------------------------------------------------------------------------


class TestValidateWithArtifacts:
    def test_validate_succeeds_with_minimal_artifacts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            _seed_artifacts(p)
            result = runner.invoke(app, ["validate", tmpdir, "--skip-commands"])
        # Should exit 0 (all checks pass when no findings, no commands)
        assert result.exit_code == 0

    def test_validate_writes_verification_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            _seed_artifacts(p)
            runner.invoke(app, ["validate", tmpdir, "--skip-commands"])
            json_path = p / ".agentlint" / "verification.json"
            assert json_path.exists()

    def test_validate_writes_verification_md(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            _seed_artifacts(p)
            runner.invoke(app, ["validate", tmpdir, "--skip-commands"])
            md_path = p / ".agentlint" / "verification.md"
            assert md_path.exists()

    def test_verification_json_has_required_schema(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            _seed_artifacts(p)
            runner.invoke(app, ["validate", tmpdir, "--skip-commands"])
            data = json.loads(
                (p / ".agentlint" / "verification.json").read_text(encoding="utf-8")
            )
        assert "agentlint_version" in data
        assert "repo_path" in data
        assert "timestamp" in data
        assert "summary" in data
        assert "results" in data
        assert "total" in data["summary"]
        assert "passed" in data["summary"]
        assert "failed" in data["summary"]

    def test_summary_counts_are_consistent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            _seed_artifacts(p)
            runner.invoke(app, ["validate", tmpdir, "--skip-commands"])
            data = json.loads(
                (p / ".agentlint" / "verification.json").read_text(encoding="utf-8")
            )
        s = data["summary"]
        assert s["total"] == s["passed"] + s["failed"]
        assert s["total"] == len(data["results"])

    def test_output_contains_pass_or_fail_labels(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            _seed_artifacts(p)
            result = runner.invoke(app, ["validate", tmpdir, "--skip-commands"])
        output = result.output or ""
        assert "[PASS]" in output or "[FAIL]" in output

    def test_output_contains_result_summary_line(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            _seed_artifacts(p)
            result = runner.invoke(app, ["validate", tmpdir, "--skip-commands"])
        output = result.output or ""
        assert "checks passed" in output.lower()

    def test_output_mentions_verification_json_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            _seed_artifacts(p)
            result = runner.invoke(app, ["validate", tmpdir, "--skip-commands"])
        output = result.output or ""
        assert "verification.json" in output

    def test_skip_commands_flag_is_accepted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            _seed_artifacts(p)
            result = runner.invoke(app, ["validate", tmpdir, "--skip-commands"])
        assert result.exit_code == 0

    def test_timeout_option_is_accepted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            _seed_artifacts(p)
            result = runner.invoke(
                app, ["validate", tmpdir, "--skip-commands", "--timeout", "30"]
            )
        assert result.exit_code == 0

    def test_approved_finding_no_longer_present_passes_layer_a(self):
        """When an approved finding is gone from fresh scan, Layer A should pass.

        Uses a synthetic finding type (F99) that will never appear in a real
        scan, so the approved finding is guaranteed to be absent.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            # Approved finding that doesn't match any real finding type
            findings = [
                {
                    "id": "find-f99-001",
                    "type": "F99",
                    "severity": "high",
                    "title": "Synthetic finding for test",
                    "explanation": "test",
                    "instruction_rules": [],
                    "evidence_ids": [],
                    "recommended_action": "",
                    "confidence": 1.0,
                    "deterministic": True,
                    "status": "approved",
                }
            ]
            _seed_artifacts(p, findings)
            # Use mix_stderr=False so stderr doesn't mix into stdout
            runner.invoke(app, ["validate", tmpdir, "--skip-commands"])

            # verification.json is written regardless of exit code
            json_path = p / ".agentlint" / "verification.json"
            assert json_path.exists(), "verification.json should be written even when checks fail"
            data = json.loads(json_path.read_text(encoding="utf-8"))

        # The finding type F99 will not appear in fresh scan →
        # Layer A check passes for this finding
        layer_a_results = [
            r for r in data["results"] if r["check_id"].startswith("layer-a")
        ]
        assert any(r["passed"] for r in layer_a_results)


# ---------------------------------------------------------------------------
# Tests: validate on demo repos (uses --skip-commands for CI safety)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not _DEMO_REPOS_DIR.exists(),
    reason="demo_repos/ directory not found",
)
class TestValidateOnDemoRepos:
    @pytest.mark.parametrize("repo_name", _DEMO_REPOS)
    def test_validate_does_not_crash_on_demo_repo(self, repo_name: str, tmp_path: Path):
        """validate should run without unhandled exceptions on all three demo repos.

        Exit code 1 is acceptable — it means findings were detected, which is
        correct behaviour for repos that have genuine issues (e.g.
        inconsistent-js-repo).  We only fail the test on Python exceptions
        (not SystemExit).
        """
        import shutil

        repo_src = _DEMO_REPOS_DIR / repo_name
        if not repo_src.exists():
            pytest.skip(f"demo repo not found: {repo_src}")

        # Copy demo repo to tmp_path to avoid polluting the source
        repo_copy = tmp_path / repo_name
        shutil.copytree(str(repo_src), str(repo_copy))

        # Seed artifacts if not present
        if not (repo_copy / ".agentlint" / "findings.json").exists():
            _seed_artifacts(repo_copy)
        elif not (repo_copy / ".agentlint" / "policy.yaml").exists():
            agentlint_dir = repo_copy / ".agentlint"
            agentlint_dir.mkdir(exist_ok=True)
            policy_data = {
                "version": 1,
                "tooling": {},
                "definition_of_done": [],
                "evidence": {},
            }
            (agentlint_dir / "policy.yaml").write_text(
                yaml.dump(policy_data), encoding="utf-8"
            )

        result = runner.invoke(app, ["validate", str(repo_copy), "--skip-commands"])
        # Only fail on Python exceptions — SystemExit(1) is valid when findings exist
        is_unhandled = (
            result.exception is not None
            and not isinstance(result.exception, SystemExit)
        )
        assert not is_unhandled, (
            f"validate raised an unhandled exception on {repo_name}: "
            f"{result.exception}\nOutput: {result.output}"
        )

    @pytest.mark.parametrize("repo_name", _DEMO_REPOS)
    def test_validate_writes_verification_json_on_demo_repo(
        self, repo_name: str, tmp_path: Path
    ):
        import shutil

        repo_src = _DEMO_REPOS_DIR / repo_name
        if not repo_src.exists():
            pytest.skip(f"demo repo not found: {repo_src}")

        repo_copy = tmp_path / repo_name
        shutil.copytree(str(repo_src), str(repo_copy))
        _seed_artifacts(repo_copy)

        runner.invoke(app, ["validate", str(repo_copy), "--skip-commands"])
        json_path = repo_copy / ".agentlint" / "verification.json"
        assert json_path.exists(), f"verification.json not written for {repo_name}"
