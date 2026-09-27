"""Unit tests for agentlint.evidence.linting (Phase 2).

Covers detect_linting() for ESLint, Prettier, Ruff, Black evidence.
"""

from __future__ import annotations

import json
from pathlib import Path

from agentlint.evidence.linting import detect_linting


def _write_pkg_json(tmp_path: Path, data: dict) -> None:
    (tmp_path / "package.json").write_text(json.dumps(data), encoding="utf-8")


# ---------------------------------------------------------------------------
# JS/TS devDependencies
# ---------------------------------------------------------------------------

def test_eslint_in_devdeps(tmp_path: Path) -> None:
    """devDependencies.eslint → eslint linter strong evidence."""
    _write_pkg_json(tmp_path, {"devDependencies": {"eslint": "^9.0.0"}})
    result = detect_linting(tmp_path)
    strong = [e for e in result if e.value == "eslint" and e.strength == "strong"]
    assert strong


def test_prettier_in_devdeps(tmp_path: Path) -> None:
    """devDependencies.prettier → prettier formatter strong evidence."""
    _write_pkg_json(tmp_path, {"devDependencies": {"prettier": "^3.0.0"}})
    result = detect_linting(tmp_path)
    strong = [e for e in result if e.value == "prettier" and e.strength == "strong"]
    assert strong


# ---------------------------------------------------------------------------
# Config files
# ---------------------------------------------------------------------------

def test_prettier_config_file(tmp_path: Path) -> None:
    """.prettierrc present → prettier strong evidence."""
    (tmp_path / ".prettierrc").write_text('{"semi": false}', encoding="utf-8")
    result = detect_linting(tmp_path)
    strong = [e for e in result if e.value == "prettier" and e.strength == "strong"]
    assert strong


# ---------------------------------------------------------------------------
# Python
# ---------------------------------------------------------------------------

def test_ruff_in_pyproject(tmp_path: Path) -> None:
    """[tool.ruff] section → ruff linter strong evidence."""
    (tmp_path / "pyproject.toml").write_text(
        "[tool.ruff]\nline-length = 88\n",
        encoding="utf-8",
    )
    result = detect_linting(tmp_path)
    strong = [e for e in result if e.value == "ruff" and e.strength == "strong"]
    assert strong


def test_black_in_pyproject(tmp_path: Path) -> None:
    """[tool.black] section → black formatter strong evidence."""
    (tmp_path / "pyproject.toml").write_text(
        "[tool.black]\nline-length = 88\n",
        encoding="utf-8",
    )
    result = detect_linting(tmp_path)
    strong = [e for e in result if e.value == "black" and e.strength == "strong"]
    assert strong


# ---------------------------------------------------------------------------
# Empty repo
# ---------------------------------------------------------------------------

def test_no_linting_evidence(tmp_path: Path) -> None:
    """Empty directory → empty evidence list."""
    result = detect_linting(tmp_path)
    assert result == []
