"""Phase 11 — Unit tests for agentlint.discovery.repo_files.

Covers:
  - Skipped directories (node_modules, .git, __pycache__, .ruff_cache, etc.)
  - Source files included correctly
  - Empty directory returns empty list
  - Accepts both Path and str arguments
  - Max depth limiting
  - Results are sorted and relative
"""

from __future__ import annotations

from pathlib import Path

import pytest

from agentlint.discovery.repo_files import list_repo_files, _SKIP_DIRS


class TestListRepoFiles:
    """Unit tests for list_repo_files."""

    def test_empty_directory(self, tmp_path: Path):
        """Empty directory returns an empty list."""
        result = list_repo_files(tmp_path)
        assert result == []

    def test_single_source_file(self, tmp_path: Path):
        """A single file in src/ is returned."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "main.py").write_text("print('hello')")
        result = list_repo_files(tmp_path)
        assert Path("src/main.py") in result

    def test_git_directory_skipped(self, tmp_path: Path):
        """Contents of .git/ are excluded."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text("[core]")
        (tmp_path / "README.md").write_text("# Hello")
        result = list_repo_files(tmp_path)
        assert Path("README.md") in result
        assert not any(str(p).startswith(".git") for p in result), (
            ".git contents should be excluded"
        )

    def test_node_modules_skipped(self, tmp_path: Path):
        """Contents of node_modules/ are excluded."""
        nm = tmp_path / "node_modules" / "lodash"
        nm.mkdir(parents=True)
        (nm / "index.js").write_text("module.exports = {}")
        (tmp_path / "index.js").write_text("// app")
        result = list_repo_files(tmp_path)
        assert Path("index.js") in result
        assert not any("node_modules" in str(p) for p in result)

    def test_pycache_skipped(self, tmp_path: Path):
        """Contents of __pycache__/ are excluded."""
        cache = tmp_path / "__pycache__"
        cache.mkdir()
        (cache / "module.cpython-312.pyc").write_bytes(b"\x00")
        (tmp_path / "app.py").write_text("pass")
        result = list_repo_files(tmp_path)
        assert Path("app.py") in result
        assert not any("__pycache__" in str(p) for p in result)

    def test_ruff_cache_skipped(self, tmp_path: Path):
        """Contents of .ruff_cache/ are excluded."""
        cache = tmp_path / ".ruff_cache"
        cache.mkdir()
        (cache / "0.6.0" / "data").parent.mkdir(parents=True)
        (cache / "0.6.0" / "data").write_text("")
        (tmp_path / "main.py").write_text("pass")
        result = list_repo_files(tmp_path)
        assert not any(".ruff_cache" in str(p) for p in result)

    def test_results_are_sorted(self, tmp_path: Path):
        """Returned paths are sorted alphabetically."""
        for name in ["c.txt", "a.txt", "b.txt"]:
            (tmp_path / name).write_text(name)
        result = list_repo_files(tmp_path)
        assert result == sorted(result)

    def test_results_are_relative(self, tmp_path: Path):
        """All returned paths are relative to the repo root."""
        (tmp_path / "file.txt").write_text("x")
        result = list_repo_files(tmp_path)
        for p in result:
            assert not p.is_absolute(), f"Path should be relative: {p}"

    def test_accepts_string_path(self, tmp_path: Path):
        """Function accepts str argument (not only Path)."""
        (tmp_path / "hello.txt").write_text("hi")
        result = list_repo_files(str(tmp_path))
        assert len(result) >= 1

    def test_max_depth_limits_traversal(self, tmp_path: Path):
        """Deeply nested files beyond max_depth are excluded."""
        # Create a file at depth 3
        deep = tmp_path / "a" / "b" / "c"
        deep.mkdir(parents=True)
        (deep / "deep.txt").write_text("deep")
        # Also create a file at depth 1
        (tmp_path / "shallow.txt").write_text("shallow")
        result = list_repo_files(tmp_path, max_depth=2)
        assert Path("shallow.txt") in result
        # depth 3 file should be excluded when max_depth=2
        assert Path("a/b/c/deep.txt") not in result

    def test_all_skip_dirs_are_strings(self):
        """_SKIP_DIRS contains only strings (sanity check)."""
        for item in _SKIP_DIRS:
            assert isinstance(item, str)

    def test_skip_dirs_contains_expected_entries(self):
        """_SKIP_DIRS includes the key directories mentioned in the spec."""
        expected = {"node_modules", ".git", "__pycache__", ".ruff_cache", "dist", ".venv"}
        assert expected.issubset(_SKIP_DIRS)
