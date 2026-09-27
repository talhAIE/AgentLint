"""Path detector.

Builds a repository path inventory for Phase 4 stale-path validation.
Phase 2 only builds the index; Phase 4 uses it to check instruction-
referenced paths.
"""

from __future__ import annotations

from pathlib import Path

from agentlint.models import RepositoryEvidence

# Well-known nested paths to check explicitly (relative to repo root)
_WELL_KNOWN_PATHS: list[str] = [
    "src",
    "tests",
    "test",
    "lib",
    "app",
    "docs",
    "scripts",
    ".github",
    ".bob",
    "packages",
    "apps",
    "components",
    "pages",
    "public",
    "static",
    "assets",
    "config",
]


def detect_paths(repo_path: Path) -> list[RepositoryEvidence]:
    """Return evidence for notable directories in *repo_path*.

    Emits one :class:`~agentlint.models.RepositoryEvidence` per notable
    directory found.  Only directories are indexed here; individual files
    are indexed by :func:`~agentlint.discovery.repo_files.list_repo_files`.

    Args:
        repo_path: Root directory of the repository.

    Returns:
        A list of :class:`~agentlint.models.RepositoryEvidence` items
        (``category="paths"``).  IDs are left empty.
    """
    repo_path = Path(repo_path).resolve()
    evidence: list[RepositoryEvidence] = []
    seen: set[str] = set()

    # --- All top-level directories ---
    try:
        top_level_dirs = sorted(
            e for e in repo_path.iterdir() if e.is_dir()
        )
    except PermissionError:
        top_level_dirs = []

    for d in top_level_dirs:
        rel = str(d.relative_to(repo_path))
        if rel not in seen:
            seen.add(rel)
            evidence.append(
                RepositoryEvidence(
                    id="",
                    category="paths",
                    key="directory",
                    value=rel,
                    source_path=rel,
                    source_locator=None,
                    strength="strong",
                    explanation=f"Directory {rel!r} exists at repository root.",
                )
            )

    # --- Well-known nested paths not already covered ---
    for known in _WELL_KNOWN_PATHS:
        if (repo_path / known).is_dir() and known not in seen:
            seen.add(known)
            evidence.append(
                RepositoryEvidence(
                    id="",
                    category="paths",
                    key="directory",
                    value=known,
                    source_path=known,
                    source_locator=None,
                    strength="strong",
                    explanation=(
                        f"Well-known directory {known!r} exists in the repository."
                    ),
                )
            )

    return evidence


def path_exists_in_repo(repo_path: Path, query: str) -> bool:
    """Return True if *query* names an existing path inside *repo_path*.

    *query* is a relative path string (e.g. ``"src/services"`` or
    ``"tests/"``).  The check is case-sensitive on POSIX and case-
    insensitive on Windows (i.e. it follows the OS default).

    Args:
        repo_path: Root directory of the repository.
        query:     Relative path to check.

    Returns:
        ``True`` if the path exists (file or directory), ``False`` otherwise.
    """
    target = Path(repo_path).resolve() / query.lstrip("/").lstrip("\\")
    return target.exists()
