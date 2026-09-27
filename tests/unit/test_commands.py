"""Unit tests for agentlint.evidence.commands (Phase 2).

Covers detect_commands() for package.json scripts, pyproject.toml
taskipy, Makefile targets, and CI run: steps.
"""

from __future__ import annotations

import json
from pathlib import Path

from agentlint.evidence.commands import detect_commands


def _write_pkg_json(tmp_path: Path, data: dict) -> None:
    (tmp_path / "package.json").write_text(json.dumps(data), encoding="utf-8")


# ---------------------------------------------------------------------------
# package.json scripts
# ---------------------------------------------------------------------------

def test_package_json_scripts(tmp_path: Path) -> None:
    """scripts.test = 'vitest run' → test command strong evidence."""
    _write_pkg_json(tmp_path, {"scripts": {"test": "vitest run"}})
    result = detect_commands(tmp_path)
    test_cmds = [e for e in result if e.key == "test" and e.strength == "strong"]
    assert test_cmds
    assert test_cmds[0].value == "vitest run"


def test_package_json_multiple_scripts(tmp_path: Path) -> None:
    """build + lint + format → multiple command items."""
    _write_pkg_json(
        tmp_path,
        {
            "scripts": {
                "build": "tsc",
                "lint": "eslint src/",
                "format": "prettier --write src/",
            }
        },
    )
    result = detect_commands(tmp_path)
    keys = {e.key for e in result}
    assert "build" in keys
    assert "lint" in keys
    assert "format" in keys


def test_no_scripts(tmp_path: Path) -> None:
    """package.json without scripts → empty list."""
    _write_pkg_json(tmp_path, {"name": "myapp"})
    result = detect_commands(tmp_path)
    assert result == []


# ---------------------------------------------------------------------------
# pyproject.toml taskipy
# ---------------------------------------------------------------------------

def test_pyproject_taskipy(tmp_path: Path) -> None:
    """[tool.taskipy.tasks] → commands extracted (strong)."""
    (tmp_path / "pyproject.toml").write_text(
        "[tool.taskipy.tasks]\ntest = 'pytest'\nlint = 'ruff check .'\n",
        encoding="utf-8",
    )
    result = detect_commands(tmp_path)
    keys = {e.key for e in result if e.strength == "strong"}
    assert "test" in keys
    assert "lint" in keys


# ---------------------------------------------------------------------------
# Makefile
# ---------------------------------------------------------------------------

def test_makefile_targets(tmp_path: Path) -> None:
    """Makefile with 'test:' target → medium evidence."""
    (tmp_path / "Makefile").write_text(
        ".PHONY: test lint\ntest:\n\tpytest\nlint:\n\truff check .\n",
        encoding="utf-8",
    )
    result = detect_commands(tmp_path)
    medium = [e for e in result if e.strength == "medium"]
    keys = {e.key for e in medium}
    assert "test" in keys
