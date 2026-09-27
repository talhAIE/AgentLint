"""Unit tests for agentlint.evidence.paths (Phase 2).

Covers detect_paths() and path_exists_in_repo().
"""

from __future__ import annotations

from pathlib import Path

from agentlint.evidence.paths import detect_paths, path_exists_in_repo


# ---------------------------------------------------------------------------
# detect_paths
# ---------------------------------------------------------------------------

def test_src_directory_detected(tmp_path: Path) -> None:
    """src/ directory present → evidence item."""
    (tmp_path / "src").mkdir()
    result = detect_paths(tmp_path)
    dirs = [e.value for e in result]
    assert "src" in dirs


def test_tests_directory_detected(tmp_path: Path) -> None:
    """tests/ directory present → evidence item."""
    (tmp_path / "tests").mkdir()
    result = detect_paths(tmp_path)
    dirs = [e.value for e in result]
    assert "tests" in dirs


def test_nested_path_detected(tmp_path: Path) -> None:
    """.github/ directory present → evidence item."""
    (tmp_path / ".github").mkdir()
    result = detect_paths(tmp_path)
    dirs = [e.value for e in result]
    assert ".github" in dirs


def test_all_items_are_strong(tmp_path: Path) -> None:
    """All path evidence items have strength='strong'."""
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    result = detect_paths(tmp_path)
    assert all(e.strength == "strong" for e in result)


def test_no_directories(tmp_path: Path) -> None:
    """Empty directory → empty evidence list."""
    result = detect_paths(tmp_path)
    assert result == []


# ---------------------------------------------------------------------------
# path_exists_in_repo
# ---------------------------------------------------------------------------

def test_path_exists_in_repo_true(tmp_path: Path) -> None:
    """Path that exists → True."""
    (tmp_path / "src").mkdir()
    assert path_exists_in_repo(tmp_path, "src") is True


def test_path_exists_in_repo_false(tmp_path: Path) -> None:
    """Path that does not exist → False."""
    assert path_exists_in_repo(tmp_path, "nonexistent") is False


def test_path_exists_nested(tmp_path: Path) -> None:
    """Nested path that exists → True."""
    nested = tmp_path / "src" / "services"
    nested.mkdir(parents=True)
    assert path_exists_in_repo(tmp_path, "src/services") is True
