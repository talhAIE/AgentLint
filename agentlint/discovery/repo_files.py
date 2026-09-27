"""Repository file index.

Provides a lightweight enumeration of files present in a repository,
used by the evidence detectors to check file presence quickly.
"""

from __future__ import annotations

from pathlib import Path

# Directories to skip during traversal — noise / large trees.
_SKIP_DIRS: frozenset[str] = frozenset(
    {
        ".git",
        "node_modules",
        "__pycache__",
        ".venv",
        "venv",
        ".env",
        "dist",
        "build",
        ".agentlint",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "coverage",
        ".next",
        ".nuxt",
        "out",
    }
)


def list_repo_files(
    repo_path: Path,
    max_depth: int = 6,
) -> list[Path]:
    """Return a sorted list of regular files under *repo_path*.

    Args:
        repo_path:  Root directory to search.
        max_depth:  Maximum directory nesting depth to traverse (default 6).

    Returns:
        Sorted list of :class:`~pathlib.Path` objects **relative** to
        *repo_path*.  Only regular files are included (no symlinks, no dirs).
        Unreadable entries are silently skipped.
    """
    repo_path = Path(repo_path).resolve()
    results: list[Path] = []
    _walk(repo_path, repo_path, 0, max_depth, results)
    results.sort()
    return results


def _walk(
    root: Path,
    current: Path,
    depth: int,
    max_depth: int,
    results: list[Path],
) -> None:
    """Recursive helper for :func:`list_repo_files`."""
    if depth > max_depth:
        return
    try:
        for entry in current.iterdir():
            if entry.is_dir():
                if entry.name in _SKIP_DIRS:
                    continue
                _walk(root, entry, depth + 1, max_depth, results)
            elif entry.is_file():
                try:
                    results.append(entry.relative_to(root))
                except ValueError:
                    pass
    except PermissionError:
        pass
