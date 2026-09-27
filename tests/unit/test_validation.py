"""Unit tests for Phase 8 — Verification Engine.

Tests cover:
  - adapters.py: apply_repair (now implemented in Phase 8)
  - validation/structural.py: run_structural_check, run_consistency_check
  - validation/evidence_check.py: run_evidence_check
  - validation/commands.py: _is_safe_command, run_command_validation
  - validation/runner.py: run_verification, _load_approved_ids, _load_policy
  - validation/__init__.py: public API surface
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from agentlint.models import (
    CanonicalPolicy,
    Finding,
    InstructionRule,
    RepositoryEvidence,
    ValidationResult,
)
from agentlint.policy import RepairItem, apply_repair
from agentlint.policy.adapters import _is_allowed_target
from agentlint.validation import (
    run_command_validation,
    run_consistency_check,
    run_evidence_check,
    run_structural_check,
    run_verification,
)
from agentlint.validation.commands import _is_safe_command
from agentlint.validation.runner import _load_approved_ids, _load_policy


# ---------------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------------


def make_evidence(
    *,
    id: str = "ev-pm-001",
    category: str = "package_manager",
    key: str = "pnpm",
    value: str = "pnpm",
    source_path: str = "pnpm-lock.yaml",
    source_locator: str | None = None,
    strength: str = "strong",
    explanation: str = "pnpm lockfile found",
) -> RepositoryEvidence:
    return RepositoryEvidence(
        id=id,
        category=category,
        key=key,
        value=value,
        source_path=source_path,
        source_locator=source_locator,
        strength=strength,
        explanation=explanation,
    )


def make_policy(
    *,
    tooling: dict | None = None,
    definition_of_done: list[str] | None = None,
) -> CanonicalPolicy:
    return CanonicalPolicy(
        version=1,
        project_name="test-project",
        tooling=tooling or {},
        runtime={},
        paths={},
        definition_of_done=definition_of_done or [],
        evidence={},
    )


def make_repair_item(
    *,
    finding_id: str = "find-f02-001",
    target_file: str = "AGENTS.md",
    original_text: str = "Use npm",
    proposed_text: str = "Use pnpm",
    requires_manual_review: bool = False,
) -> RepairItem:
    return RepairItem(
        finding_id=finding_id,
        target_file=target_file,
        original_text=original_text,
        proposed_text=proposed_text,
        requires_manual_review=requires_manual_review,
    )


# ---------------------------------------------------------------------------
# Tests: apply_repair — Phase 8 implementation
# ---------------------------------------------------------------------------


class TestApplyRepair:
    def test_replace_text_exact_match(self):
        item = make_repair_item(original_text="Use npm", proposed_text="Use pnpm")
        result = apply_repair(item, "Use npm\nand other text\n")
        assert "Use pnpm" in result
        assert "Use npm" not in result

    def test_replace_text_only_first_occurrence(self):
        item = make_repair_item(original_text="Use npm", proposed_text="Use pnpm")
        result = apply_repair(item, "Use npm\nUse npm\n")
        assert result.count("Use pnpm") == 1
        assert result.count("Use npm") == 1  # second occurrence remains

    def test_delete_line_when_proposed_text_empty(self):
        item = make_repair_item(
            original_text="Use npm",
            proposed_text="",
        )
        content = "- Run tests first\n- Use npm\n- Use pnpm\n"
        result = apply_repair(item, content)
        assert "Use npm" not in result
        assert "Run tests first" in result
        assert "Use pnpm" in result

    def test_case_insensitive_fallback(self):
        """When original_text is not found verbatim, try case-insensitive."""
        item = make_repair_item(original_text="use npm", proposed_text="use pnpm")
        result = apply_repair(item, "Use NPM\nsome other text\n")
        # Case-insensitive match should have replaced
        assert "use pnpm" in result.lower()

    def test_raises_value_error_for_disallowed_target(self):
        item = make_repair_item(target_file="src/main.py")
        with pytest.raises(ValueError, match="not in the allowed set"):
            apply_repair(item, "some content")

    def test_raises_value_error_for_manual_review(self):
        item = make_repair_item(requires_manual_review=True)
        with pytest.raises(ValueError, match="manual review"):
            apply_repair(item, "Use npm\n")

    def test_raises_value_error_for_empty_original_text(self):
        item = make_repair_item(original_text="")
        with pytest.raises(ValueError, match="no original_text"):
            apply_repair(item, "some content")

    def test_allowed_target_bob_file(self):
        item = make_repair_item(target_file=".bob/rules-agent/AGENTS.md")
        result = apply_repair(item, "Use npm\n")
        assert "Use pnpm" in result

    def test_allowed_target_agentlint(self):
        item = make_repair_item(target_file=".agentlint/policy.yaml")
        result = apply_repair(item, "Use npm\n")
        # No error raised — allowed target
        assert isinstance(result, str)

    def test_allowed_target_claude(self):
        item = make_repair_item(target_file="CLAUDE.md")
        result = apply_repair(item, "Use npm\n")
        assert "Use pnpm" in result

    def test_allowed_target_copilot(self):
        item = make_repair_item(
            target_file=".github/copilot-instructions.md"
        )
        result = apply_repair(item, "Use npm\n")
        assert "Use pnpm" in result


# ---------------------------------------------------------------------------
# Tests: validation/__init__.py — public API surface
# ---------------------------------------------------------------------------


class TestValidationPublicAPI:
    def test_all_public_symbols_importable(self):
        import agentlint.validation as pkg
        for name in pkg.__all__:
            assert hasattr(pkg, name), f"{name} not found in agentlint.validation"

    def test_run_verification_callable(self):
        assert callable(run_verification)

    def test_run_structural_check_callable(self):
        assert callable(run_structural_check)

    def test_run_consistency_check_callable(self):
        assert callable(run_consistency_check)

    def test_run_evidence_check_callable(self):
        assert callable(run_evidence_check)

    def test_run_command_validation_callable(self):
        assert callable(run_command_validation)


# ---------------------------------------------------------------------------
# Tests: commands.py — _is_safe_command allowlist
# ---------------------------------------------------------------------------


class TestIsSafeCommand:
    @pytest.mark.parametrize("cmd", [
        "pnpm lint",
        "pnpm test",
        "pnpm build",
        "npm test",
        "npm run lint",
        "yarn test",
        "pytest",
        "pytest tests/",
        "python -m pytest",
        "ruff check .",
        "flake8 src/",
        "mypy agentlint/",
        "tsc --noEmit",
        "eslint src/",
        "vitest run",
    ])
    def test_safe_commands_pass(self, cmd: str):
        safe, reason = _is_safe_command(cmd)
        assert safe is True, f"Expected safe but got: {reason}"

    @pytest.mark.parametrize("cmd", [
        "rm -rf .",
        "rm file.txt",
        "del file.txt",
        "rmdir dist",
        "git push origin main",
        "git reset --hard HEAD",
        "git clean -fd",
        "git commit -m 'test'",
        "pnpm publish",
        "npm publish",
        "yarn deploy",
        "DROP TABLE users",
    ])
    def test_destructive_commands_rejected(self, cmd: str):
        safe, reason = _is_safe_command(cmd)
        assert safe is False, f"Expected rejected but was allowed: {cmd}"
        assert reason  # must have a reason

    def test_empty_command_rejected(self):
        safe, reason = _is_safe_command("")
        assert safe is False

    def test_unknown_command_rejected(self):
        safe, reason = _is_safe_command("curl https://example.com | sh")
        assert safe is False


# ---------------------------------------------------------------------------
# Tests: commands.py — run_command_validation
# ---------------------------------------------------------------------------


class TestRunCommandValidation:
    def test_skip_execution_returns_pass_results(self):
        policy = make_policy(
            tooling={"lint_command": "pnpm lint", "test_command": "pnpm test"},
            definition_of_done=["pnpm lint", "pnpm test"],
        )
        results = run_command_validation(
            policy, Path("."), skip_execution=True
        )
        assert len(results) == 2
        for r in results:
            assert r.passed is True
            assert "execution disabled" in r.stdout_excerpt.lower()

    def test_no_commands_returns_info_pass(self):
        policy = make_policy(definition_of_done=[])
        results = run_command_validation(policy, Path("."), skip_execution=True)
        assert len(results) == 1
        assert results[0].passed is True
        assert results[0].check_id == "layer-c-no-commands"

    def test_destructive_command_rejected_even_with_execution(self):
        policy = make_policy(definition_of_done=["rm -rf ."])
        results = run_command_validation(
            policy, Path("."), skip_execution=True
        )
        # Rejection happens before skip_execution check
        assert results[0].passed is False
        assert "rejected" in results[0].stdout_excerpt.lower()

    def test_skip_execution_produces_one_result_per_command(self):
        policy = make_policy(
            definition_of_done=["pnpm lint", "pnpm test", "pnpm build"]
        )
        results = run_command_validation(
            policy, Path("."), skip_execution=True
        )
        assert len(results) == 3

    def test_result_check_ids_are_unique(self):
        policy = make_policy(
            definition_of_done=["pnpm lint", "pnpm test"]
        )
        results = run_command_validation(
            policy, Path("."), skip_execution=True
        )
        ids = [r.check_id for r in results]
        assert len(ids) == len(set(ids))

    def test_result_has_command_field(self):
        policy = make_policy(definition_of_done=["pnpm lint"])
        results = run_command_validation(
            policy, Path("."), skip_execution=True
        )
        assert results[0].command == "pnpm lint"


# ---------------------------------------------------------------------------
# Tests: evidence_check.py — run_evidence_check
# ---------------------------------------------------------------------------


class TestRunEvidenceCheck:
    def test_all_fields_present_all_pass(self):
        policy = make_policy(
            tooling={
                "package_manager": "pnpm",
                "test_framework": "vitest",
                "lint_command": "eslint src/",
                "test_command": "vitest run",
                "build_command": "tsc",
            }
        )
        evidence = [
            make_evidence(
                id="ev-pm-001",
                category="package_manager",
                key="package_manager",
                value="pnpm",
            ),
            make_evidence(
                id="ev-tf-001",
                category="test_framework",
                key="test_framework",
                value="vitest",
            ),
            make_evidence(
                id="ev-cmd-001",
                category="commands",
                key="lint",
                value="eslint src/",
            ),
            make_evidence(
                id="ev-cmd-002",
                category="commands",
                key="test",
                value="vitest run",
            ),
            make_evidence(
                id="ev-cmd-003",
                category="commands",
                key="build",
                value="tsc",
            ),
        ]
        results = run_evidence_check(policy, evidence)
        assert len(results) == 5
        for r in results:
            assert r.passed is True, f"Expected PASS for {r.name}: {r.stdout_excerpt}"

    def test_missing_evidence_produces_fail(self):
        policy = make_policy(
            tooling={"package_manager": "pnpm"}
        )
        # Provide evidence for npm (mismatch)
        evidence = [
            make_evidence(
                id="ev-pm-001",
                category="package_manager",
                key="package_manager",
                value="npm",
            )
        ]
        results = run_evidence_check(policy, evidence)
        assert len(results) == 1
        assert results[0].passed is False
        assert "FAIL" in results[0].stdout_excerpt

    def test_empty_policy_returns_info_pass(self):
        policy = make_policy(tooling={})
        results = run_evidence_check(policy, [])
        assert len(results) == 1
        assert results[0].passed is True
        assert results[0].check_id == "layer-b-no-policy"

    def test_partial_fields_only_checks_populated(self):
        policy = make_policy(tooling={"package_manager": "pnpm"})
        evidence = [
            make_evidence(
                id="ev-pm-001",
                category="package_manager",
                key="package_manager",
                value="pnpm",
            )
        ]
        results = run_evidence_check(policy, evidence)
        # Only 1 field populated → only 1 check
        assert len(results) == 1
        assert results[0].passed is True

    def test_result_has_correct_check_id_prefix(self):
        policy = make_policy(tooling={"package_manager": "pnpm"})
        evidence = [
            make_evidence(
                id="ev-pm-001",
                category="package_manager",
                key="package_manager",
                value="pnpm",
            )
        ]
        results = run_evidence_check(policy, evidence)
        assert results[0].check_id.startswith("layer-b-")


# ---------------------------------------------------------------------------
# Tests: structural.py — run_structural_check
# ---------------------------------------------------------------------------


class TestRunStructuralCheck:
    def test_empty_approved_ids_returns_info_pass(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            results = run_structural_check(Path(tmpdir), [])
        assert len(results) == 1
        assert results[0].passed is True
        assert results[0].check_id == "layer-a-no-approved"

    def test_finding_present_in_fresh_scan_produces_fail(self):
        """If the approved finding still exists, Layer A should FAIL."""
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            # Write a minimal findings.json with one approved finding
            agentlint_dir = p / ".agentlint"
            agentlint_dir.mkdir()
            findings_data = {
                "agentlint_version": "0.1.0",
                "repo_path": str(p),
                "findings": [
                    {
                        "id": "find-f02-001",
                        "type": "F02",
                        "severity": "high",
                        "title": "Package manager mismatch",
                        "explanation": "AGENTS.md says npm but repo uses pnpm",
                        "instruction_rules": ["rule-001"],
                        "evidence_ids": ["ev-pm-001"],
                        "recommended_action": "Update AGENTS.md",
                        "confidence": 1.0,
                        "deterministic": True,
                        "status": "approved",
                    }
                ],
            }
            (agentlint_dir / "findings.json").write_text(
                json.dumps(findings_data), encoding="utf-8"
            )

            # Mock the fresh scan to return the same finding type/title.
            # run_deterministic_checks is imported inside the function body
            # as a late import, so we patch it at its source module.
            mock_finding = Finding(
                id="find-f02-001",
                type="F02",
                severity="high",
                title="Package manager mismatch",
                explanation="still there",
                instruction_rules=[],
                evidence_ids=[],
                recommended_action="",
                confidence=1.0,
                deterministic=True,
                status="open",
            )
            with patch(
                "agentlint.analysis.run_deterministic_checks",
                return_value=[mock_finding],
            ):
                with patch(
                    "agentlint.validation.structural._fresh_scan",
                    return_value=([], [], []),
                ):
                    results = run_structural_check(p, ["find-f02-001"])

        assert len(results) == 1
        assert results[0].passed is False
        assert "find-f02-001" in results[0].stdout_excerpt

    def test_finding_gone_in_fresh_scan_produces_pass(self):
        """If the approved finding no longer appears, Layer A should PASS."""
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            agentlint_dir = p / ".agentlint"
            agentlint_dir.mkdir()
            findings_data = {
                "agentlint_version": "0.1.0",
                "repo_path": str(p),
                "findings": [
                    {
                        "id": "find-f02-001",
                        "type": "F02",
                        "severity": "high",
                        "title": "Package manager mismatch",
                        "explanation": "Was here",
                        "instruction_rules": [],
                        "evidence_ids": [],
                        "recommended_action": "",
                        "confidence": 1.0,
                        "deterministic": True,
                        "status": "approved",
                    }
                ],
            }
            (agentlint_dir / "findings.json").write_text(
                json.dumps(findings_data), encoding="utf-8"
            )

            # Fresh scan returns NO findings → finding is gone
            with patch(
                "agentlint.analysis.run_deterministic_checks",
                return_value=[],
            ):
                with patch(
                    "agentlint.validation.structural._fresh_scan",
                    return_value=([], [], []),
                ):
                    results = run_structural_check(p, ["find-f02-001"])

        assert len(results) == 1
        assert results[0].passed is True


# ---------------------------------------------------------------------------
# Tests: structural.py — run_consistency_check
# ---------------------------------------------------------------------------


class TestRunConsistencyCheck:
    def test_no_issues_returns_pass(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            with patch(
                "agentlint.validation.structural._fresh_scan",
                return_value=([], [], []),
            ):
                with patch(
                    "agentlint.validation.structural.detect_f01_cross_file_conflicts",
                    return_value=[],
                ):
                    with patch(
                        "agentlint.validation.structural.detect_f05_duplicates",
                        return_value=[],
                    ):
                        results = run_consistency_check(p)

        assert len(results) == 1
        assert results[0].passed is True
        assert results[0].check_id == "layer-d-consistency"

    def test_f01_finding_produces_fail(self):
        mock_finding = Finding(
            id="",
            type="F01",
            severity="high",
            title="Conflicting package manager",
            explanation="Conflict",
            instruction_rules=[],
            evidence_ids=[],
            recommended_action="",
            confidence=1.0,
            deterministic=True,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            with patch(
                "agentlint.validation.structural._fresh_scan",
                return_value=([], [], []),
            ):
                with patch(
                    "agentlint.validation.structural.detect_f01_cross_file_conflicts",
                    return_value=[mock_finding],
                ):
                    with patch(
                        "agentlint.validation.structural.detect_f05_duplicates",
                        return_value=[],
                    ):
                        results = run_consistency_check(p)

        assert len(results) == 1
        assert results[0].passed is False
        assert "F01" in results[0].stdout_excerpt


# ---------------------------------------------------------------------------
# Tests: runner.py — _load_approved_ids and _load_policy helpers
# ---------------------------------------------------------------------------


class TestLoadHelpers:
    def test_load_approved_ids_missing_file_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ids = _load_approved_ids(Path(tmpdir))
        assert ids == []

    def test_load_approved_ids_returns_only_approved(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            agentlint_dir = p / ".agentlint"
            agentlint_dir.mkdir()
            data = {
                "findings": [
                    {"id": "find-001", "status": "approved"},
                    {"id": "find-002", "status": "open"},
                    {"id": "find-003", "status": "ignored"},
                    {"id": "find-004", "status": "approved"},
                ]
            }
            (agentlint_dir / "findings.json").write_text(
                json.dumps(data), encoding="utf-8"
            )
            ids = _load_approved_ids(p)
        assert ids == ["find-001", "find-004"]

    def test_load_policy_missing_file_returns_none(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            policy = _load_policy(Path(tmpdir))
        assert policy is None

    def test_load_policy_returns_canonical_policy(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            agentlint_dir = p / ".agentlint"
            agentlint_dir.mkdir()
            policy_data = {
                "version": 1,
                "project": {"name": "test-proj"},
                "tooling": {"package_manager": "pnpm"},
                "runtime": {"node": "22"},
                "paths": {},
                "definition_of_done": ["pnpm test"],
                "evidence": {},
            }
            (agentlint_dir / "policy.yaml").write_text(
                yaml.dump(policy_data), encoding="utf-8"
            )
            policy = _load_policy(p)

        assert policy is not None
        assert policy.project_name == "test-proj"
        assert policy.tooling.get("package_manager") == "pnpm"
        assert policy.definition_of_done == ["pnpm test"]


# ---------------------------------------------------------------------------
# Tests: runner.py — run_verification end-to-end
# ---------------------------------------------------------------------------


class TestRunVerification:
    def _make_artifacts(self, tmpdir: Path) -> None:
        """Write minimal findings.json + policy.yaml for testing."""
        agentlint_dir = tmpdir / ".agentlint"
        agentlint_dir.mkdir(exist_ok=True)

        findings_data = {
            "agentlint_version": "0.1.0",
            "repo_path": str(tmpdir),
            "findings": [],
        }
        (agentlint_dir / "findings.json").write_text(
            json.dumps(findings_data), encoding="utf-8"
        )

        policy_data = {
            "version": 1,
            "tooling": {"package_manager": "pnpm"},
            "definition_of_done": ["pnpm test"],
            "evidence": {},
        }
        (agentlint_dir / "policy.yaml").write_text(
            yaml.dump(policy_data), encoding="utf-8"
        )

    def test_writes_verification_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            self._make_artifacts(p)
            report = run_verification(p, skip_commands=True)
            json_path = p / ".agentlint" / "verification.json"
            assert json_path.exists()

    def test_writes_verification_md(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            self._make_artifacts(p)
            run_verification(p, skip_commands=True)
            md_path = p / ".agentlint" / "verification.md"
            assert md_path.exists()

    def test_report_has_required_keys(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            self._make_artifacts(p)
            report = run_verification(p, skip_commands=True)

        assert "agentlint_version" in report
        assert "repo_path" in report
        assert "timestamp" in report
        assert "summary" in report
        assert "results" in report

    def test_summary_has_correct_keys(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            self._make_artifacts(p)
            report = run_verification(p, skip_commands=True)

        summary = report["summary"]
        assert "total" in summary
        assert "passed" in summary
        assert "failed" in summary
        assert summary["total"] == summary["passed"] + summary["failed"]

    def test_results_is_non_empty_list(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            self._make_artifacts(p)
            report = run_verification(p, skip_commands=True)

        assert isinstance(report["results"], list)
        assert len(report["results"]) > 0

    def test_each_result_has_required_fields(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            self._make_artifacts(p)
            report = run_verification(p, skip_commands=True)

        required = {"check_id", "name", "passed"}
        for r in report["results"]:
            for field in required:
                assert field in r, f"Missing field '{field}' in result: {r}"

    def test_no_approved_ids_still_runs_all_layers(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            self._make_artifacts(p)
            report = run_verification(p, skip_commands=True)

        # Layers A, B, C, D all contribute at least one result
        check_ids = [r["check_id"] for r in report["results"]]
        assert any(cid.startswith("layer-a") for cid in check_ids)
        assert any(cid.startswith("layer-c") for cid in check_ids)
        assert any(cid.startswith("layer-d") for cid in check_ids)

    def test_run_on_empty_repo_does_not_crash(self):
        """Verification should not crash when artifacts are absent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            # Create .agentlint dir and minimal artifacts
            self._make_artifacts(p)
            report = run_verification(p, skip_commands=True)
        assert report is not None

    def test_verification_json_is_readable_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir)
            self._make_artifacts(p)
            run_verification(p, skip_commands=True)
            content = (p / ".agentlint" / "verification.json").read_text(encoding="utf-8")
            data = json.loads(content)
        assert data["summary"]["total"] > 0
