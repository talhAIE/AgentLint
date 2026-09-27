"""Unit tests for agentlint.evidence.testing (Phase 2).

Covers detect_test_framework() for JS/Python test framework detection.
"""

from __future__ import annotations

import json
from pathlib import Path

from agentlint.evidence.testing import detect_test_framework


def _write_pkg_json(tmp_path: Path, data: dict) -> None:
    (tmp_path / "package.json").write_text(json.dumps(data), encoding="utf-8")


# ---------------------------------------------------------------------------
# JS devDependencies
# ---------------------------------------------------------------------------

def test_vitest_in_devdeps(tmp_path: Path) -> None:
    """devDependencies.vitest → vitest strong evidence."""
    _write_pkg_json(tmp_path, {"devDependencies": {"vitest": "^1.0.0"}})
    result = detect_test_framework(tmp_path)
    strong = [e for e in result if e.strength == "strong" and e.value == "vitest"]
    assert strong, "Expected vitest strong evidence"


def test_jest_in_devdeps(tmp_path: Path) -> None:
    """devDependencies.jest → jest strong evidence."""
    _write_pkg_json(tmp_path, {"devDependencies": {"jest": "^29.0.0"}})
    result = detect_test_framework(tmp_path)
    strong = [e for e in result if e.strength == "strong" and e.value == "jest"]
    assert strong, "Expected jest strong evidence"


# ---------------------------------------------------------------------------
# Config files
# ---------------------------------------------------------------------------

def test_vitest_config_file(tmp_path: Path) -> None:
    """vitest.config.ts exists → vitest strong evidence."""
    (tmp_path / "vitest.config.ts").write_text("export default {}", encoding="utf-8")
    result = detect_test_framework(tmp_path)
    strong = [e for e in result if e.strength == "strong" and e.value == "vitest"]
    assert strong, "Expected vitest strong evidence from config file"


def test_jest_config_file(tmp_path: Path) -> None:
    """jest.config.js exists → jest strong evidence."""
    (tmp_path / "jest.config.js").write_text("module.exports = {}", encoding="utf-8")
    result = detect_test_framework(tmp_path)
    strong = [e for e in result if e.strength == "strong" and e.value == "jest"]
    assert strong, "Expected jest strong evidence from config file"


# ---------------------------------------------------------------------------
# Python (pytest)
# ---------------------------------------------------------------------------

def test_pytest_in_pyproject(tmp_path: Path) -> None:
    """pyproject.toml with pytest in dependencies → strong evidence."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "myapp"\ndependencies = ["pytest>=7"]\n',
        encoding="utf-8",
    )
    result = detect_test_framework(tmp_path)
    strong = [e for e in result if e.value == "pytest" and e.strength == "strong"]
    assert strong, "Expected pytest strong evidence from pyproject.toml"


def test_pytest_ini_exists(tmp_path: Path) -> None:
    """pytest.ini present → pytest strong evidence."""
    (tmp_path / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    result = detect_test_framework(tmp_path)
    strong = [e for e in result if e.value == "pytest" and e.strength == "strong"]
    assert strong, "Expected pytest strong evidence from pytest.ini"


# ---------------------------------------------------------------------------
# Empty repo
# ---------------------------------------------------------------------------

def test_no_test_framework(tmp_path: Path) -> None:
    """Empty directory → empty evidence list."""
    result = detect_test_framework(tmp_path)
    assert result == []
