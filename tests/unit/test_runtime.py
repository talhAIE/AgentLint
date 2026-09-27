"""Unit tests for agentlint.evidence.runtime (Phase 2).

Covers detect_runtime() for Node.js and Python version detection.
"""

from __future__ import annotations

import json
from pathlib import Path

from agentlint.evidence.runtime import detect_runtime


def _write_pkg_json(tmp_path: Path, data: dict) -> None:
    (tmp_path / "package.json").write_text(json.dumps(data), encoding="utf-8")


# ---------------------------------------------------------------------------
# Node version
# ---------------------------------------------------------------------------

def test_nvmrc_detected(tmp_path: Path) -> None:
    """.nvmrc with '20' → node_version strong evidence."""
    (tmp_path / ".nvmrc").write_text("20\n", encoding="utf-8")
    result = detect_runtime(tmp_path)
    strong = [
        e for e in result
        if e.key == "node_version" and e.strength == "strong"
    ]
    assert strong
    assert strong[0].value == "20"


def test_node_version_file(tmp_path: Path) -> None:
    """.node-version file → node_version strong evidence."""
    (tmp_path / ".node-version").write_text("20.11.0\n", encoding="utf-8")
    result = detect_runtime(tmp_path)
    strong = [
        e for e in result
        if e.key == "node_version" and e.strength == "strong"
        and e.source_path == ".node-version"
    ]
    assert strong
    assert strong[0].value == "20.11.0"


def test_package_engines_node(tmp_path: Path) -> None:
    """package.json engines.node → node_version strong evidence."""
    _write_pkg_json(tmp_path, {"engines": {"node": ">=18"}})
    result = detect_runtime(tmp_path)
    strong = [
        e for e in result
        if e.key == "node_version" and e.source_locator == "engines.node"
    ]
    assert strong
    assert strong[0].value == ">=18"


# ---------------------------------------------------------------------------
# Python version
# ---------------------------------------------------------------------------

def test_python_version_file(tmp_path: Path) -> None:
    """.python-version with '3.11' → python_version strong evidence."""
    (tmp_path / ".python-version").write_text("3.11\n", encoding="utf-8")
    result = detect_runtime(tmp_path)
    strong = [e for e in result if e.key == "python_version" and e.strength == "strong"]
    assert strong
    assert strong[0].value == "3.11"


def test_pyproject_requires_python(tmp_path: Path) -> None:
    """pyproject.toml requires-python → python_version strong evidence."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "myapp"\nrequires-python = ">=3.11"\n',
        encoding="utf-8",
    )
    result = detect_runtime(tmp_path)
    strong = [
        e for e in result
        if e.key == "python_version" and e.source_locator == "project.requires-python"
    ]
    assert strong
    assert strong[0].value == ">=3.11"


# ---------------------------------------------------------------------------
# Empty repo
# ---------------------------------------------------------------------------

def test_no_runtime_evidence(tmp_path: Path) -> None:
    """Empty directory → empty evidence list."""
    result = detect_runtime(tmp_path)
    assert result == []
