"""Unit tests for agentlint.evidence.package_manager (Phase 2).

Covers detect_package_manager() for all evidence sources.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentlint.evidence.package_manager import detect_package_manager


def _write_pkg_json(tmp_path: Path, data: dict) -> None:
    (tmp_path / "package.json").write_text(json.dumps(data), encoding="utf-8")


# ---------------------------------------------------------------------------
# Lockfile evidence
# ---------------------------------------------------------------------------

def test_pnpm_lock_detected(tmp_path: Path) -> None:
    """pnpm-lock.yaml present → pnpm strong evidence."""
    (tmp_path / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n", encoding="utf-8")
    result = detect_package_manager(tmp_path)
    pm_values = [e.value for e in result if e.strength == "strong"]
    assert "pnpm" in pm_values


def test_npm_lock_detected(tmp_path: Path) -> None:
    """package-lock.json present → npm strong evidence."""
    (tmp_path / "package-lock.json").write_text('{"lockfileVersion": 3}', encoding="utf-8")
    result = detect_package_manager(tmp_path)
    pm_values = [e.value for e in result if e.strength == "strong"]
    assert "npm" in pm_values


def test_yarn_lock_detected(tmp_path: Path) -> None:
    """yarn.lock present → yarn strong evidence."""
    (tmp_path / "yarn.lock").write_text("# yarn lockfile v1\n", encoding="utf-8")
    result = detect_package_manager(tmp_path)
    pm_values = [e.value for e in result if e.strength == "strong"]
    assert "yarn" in pm_values


# ---------------------------------------------------------------------------
# package.json packageManager field
# ---------------------------------------------------------------------------

def test_package_json_package_manager_field(tmp_path: Path) -> None:
    """package.json packageManager: pnpm@9 → pnpm strong evidence."""
    _write_pkg_json(tmp_path, {"packageManager": "pnpm@9.0.0"})
    result = detect_package_manager(tmp_path)
    strong = [e for e in result if e.strength == "strong" and e.source_locator == "packageManager"]
    assert strong
    assert strong[0].value == "pnpm"


def test_package_manager_field_no_version(tmp_path: Path) -> None:
    """packageManager field without version tag is still parsed."""
    _write_pkg_json(tmp_path, {"packageManager": "yarn"})
    result = detect_package_manager(tmp_path)
    values = [e.value for e in result]
    assert "yarn" in values


# ---------------------------------------------------------------------------
# Empty / no evidence
# ---------------------------------------------------------------------------

def test_no_package_manager_evidence(tmp_path: Path) -> None:
    """Empty directory → empty evidence list."""
    result = detect_package_manager(tmp_path)
    assert result == []


# ---------------------------------------------------------------------------
# Conflicting evidence preserved
# ---------------------------------------------------------------------------

def test_conflicting_evidence_both_returned(tmp_path: Path) -> None:
    """packageManager: pnpm + package-lock.json → both evidence items returned."""
    _write_pkg_json(tmp_path, {"packageManager": "pnpm@9.0.0"})
    (tmp_path / "package-lock.json").write_text('{"lockfileVersion": 3}', encoding="utf-8")
    result = detect_package_manager(tmp_path)
    values = [e.value for e in result if e.strength == "strong"]
    assert "pnpm" in values
    assert "npm" in values
    assert len([e for e in result if e.strength == "strong"]) >= 2


# ---------------------------------------------------------------------------
# CI evidence (medium)
# ---------------------------------------------------------------------------

def test_ci_medium_evidence(tmp_path: Path) -> None:
    """CI workflow with 'pnpm install' → medium pnpm evidence."""
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text(
        "steps:\n  - run: pnpm install\n  - run: pnpm test\n",
        encoding="utf-8",
    )
    result = detect_package_manager(tmp_path)
    medium = [e for e in result if e.strength == "medium"]
    assert medium
    assert any(e.value == "pnpm" for e in medium)
