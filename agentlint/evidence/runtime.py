"""Runtime/language detector.

Detects the language and runtime version the repository targets from
.nvmrc, .node-version, package.json engines, .python-version,
pyproject.toml, and the presence of language-specific source files.
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

from agentlint.models import RepositoryEvidence


def detect_runtime(repo_path: Path) -> list[RepositoryEvidence]:
    """Return all runtime/language evidence found in *repo_path*.

    Args:
        repo_path: Root directory of the repository.

    Returns:
        A list of :class:`~agentlint.models.RepositoryEvidence` items
        (``category="runtime"``).  IDs are left empty.
    """
    repo_path = Path(repo_path).resolve()
    evidence: list[RepositoryEvidence] = []

    evidence.extend(_node_version_evidence(repo_path))
    evidence.extend(_python_version_evidence(repo_path))
    evidence.extend(_language_hint_evidence(repo_path))

    return evidence


# ---------------------------------------------------------------------------
# Node version
# ---------------------------------------------------------------------------

def _node_version_evidence(repo_path: Path) -> list[RepositoryEvidence]:
    """Detect Node.js version from .nvmrc, .node-version, or package.json."""
    results: list[RepositoryEvidence] = []

    # .nvmrc
    nvmrc = repo_path / ".nvmrc"
    if nvmrc.is_file():
        try:
            version = nvmrc.read_text(encoding="utf-8").strip()
            if version:
                results.append(
                    RepositoryEvidence(
                        id="",
                        category="runtime",
                        key="node_version",
                        value=version,
                        source_path=".nvmrc",
                        source_locator=None,
                        strength="strong",
                        explanation=f".nvmrc specifies Node.js version {version!r}.",
                    )
                )
        except OSError:
            pass

    # .node-version
    node_ver_file = repo_path / ".node-version"
    if node_ver_file.is_file():
        try:
            version = node_ver_file.read_text(encoding="utf-8").strip()
            if version:
                results.append(
                    RepositoryEvidence(
                        id="",
                        category="runtime",
                        key="node_version",
                        value=version,
                        source_path=".node-version",
                        source_locator=None,
                        strength="strong",
                        explanation=(
                            f".node-version specifies Node.js version {version!r}."
                        ),
                    )
                )
        except OSError:
            pass

    # package.json engines.node
    pkg_json = repo_path / "package.json"
    if pkg_json.is_file():
        try:
            pkg = json.loads(pkg_json.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pkg = {}
        engines_node = (pkg.get("engines") or {}).get("node")
        if isinstance(engines_node, str) and engines_node:
            results.append(
                RepositoryEvidence(
                    id="",
                    category="runtime",
                    key="node_version",
                    value=engines_node,
                    source_path="package.json",
                    source_locator="engines.node",
                    strength="strong",
                    explanation=(
                        f'package.json engines.node = "{engines_node}".'
                    ),
                )
            )

    return results


# ---------------------------------------------------------------------------
# Python version
# ---------------------------------------------------------------------------

def _python_version_evidence(repo_path: Path) -> list[RepositoryEvidence]:
    """Detect Python version from .python-version or pyproject.toml."""
    results: list[RepositoryEvidence] = []

    # .python-version
    py_ver_file = repo_path / ".python-version"
    if py_ver_file.is_file():
        try:
            version = py_ver_file.read_text(encoding="utf-8").strip()
            if version:
                results.append(
                    RepositoryEvidence(
                        id="",
                        category="runtime",
                        key="python_version",
                        value=version,
                        source_path=".python-version",
                        source_locator=None,
                        strength="strong",
                        explanation=(
                            f".python-version specifies Python {version!r}."
                        ),
                    )
                )
        except OSError:
            pass

    # pyproject.toml
    pyproject = repo_path / "pyproject.toml"
    if pyproject.is_file():
        try:
            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        except (tomllib.TOMLDecodeError, OSError):
            data = {}

        # [project] requires-python
        req_python = (data.get("project") or {}).get("requires-python")
        if isinstance(req_python, str) and req_python:
            results.append(
                RepositoryEvidence(
                    id="",
                    category="runtime",
                    key="python_version",
                    value=req_python,
                    source_path="pyproject.toml",
                    source_locator="project.requires-python",
                    strength="strong",
                    explanation=(
                        f'pyproject.toml requires-python = "{req_python}".'
                    ),
                )
            )

        # [tool.poetry.dependencies].python
        poetry_python = (
            data.get("tool", {})
            .get("poetry", {})
            .get("dependencies", {})
            .get("python")
        )
        if isinstance(poetry_python, str) and poetry_python:
            results.append(
                RepositoryEvidence(
                    id="",
                    category="runtime",
                    key="python_version",
                    value=poetry_python,
                    source_path="pyproject.toml",
                    source_locator="tool.poetry.dependencies.python",
                    strength="strong",
                    explanation=(
                        f'pyproject.toml [tool.poetry.dependencies].python'
                        f' = "{poetry_python}".'
                    ),
                )
            )

    return results


# ---------------------------------------------------------------------------
# Language hint
# ---------------------------------------------------------------------------

def _language_hint_evidence(repo_path: Path) -> list[RepositoryEvidence]:
    """Return weak language hints based on file presence."""
    results: list[RepositoryEvidence] = []

    has_package_json = (repo_path / "package.json").is_file()

    if has_package_json:
        # Check for TypeScript files
        has_ts = _any_file_with_extension(repo_path, ".ts")
        if has_ts:
            results.append(
                RepositoryEvidence(
                    id="",
                    category="runtime",
                    key="language",
                    value="typescript",
                    source_path="package.json",
                    source_locator=None,
                    strength="weak",
                    explanation=(
                        "package.json is present and .ts files were found."
                    ),
                )
            )
        else:
            has_js = _any_file_with_extension(repo_path, ".js")
            if has_js:
                results.append(
                    RepositoryEvidence(
                        id="",
                        category="runtime",
                        key="language",
                        value="javascript",
                        source_path="package.json",
                        source_locator=None,
                        strength="weak",
                        explanation=(
                            "package.json is present and .js files were found."
                        ),
                    )
                )

    has_pyproject = (repo_path / "pyproject.toml").is_file()
    has_setup_py = (repo_path / "setup.py").is_file()
    has_py = _any_file_with_extension(repo_path, ".py")

    if has_pyproject or has_setup_py or has_py:
        hint_source = (
            "pyproject.toml"
            if has_pyproject
            else "setup.py"
            if has_setup_py
            else "*.py"
        )
        results.append(
            RepositoryEvidence(
                id="",
                category="runtime",
                key="language",
                value="python",
                source_path=hint_source,
                source_locator=None,
                strength="weak",
                explanation="Python project files are present.",
            )
        )

    return results


def _any_file_with_extension(repo_path: Path, ext: str) -> bool:
    """Return True if any file with *ext* exists in the top two levels."""
    # Check top-level
    for f in repo_path.iterdir():
        if f.is_file() and f.suffix == ext:
            return True
    # Check one level down (src/, lib/, etc.) — stay shallow for speed
    for d in repo_path.iterdir():
        if d.is_dir() and d.name not in {".git", "node_modules", "__pycache__"}:
            for f in d.iterdir():
                if f.is_file() and f.suffix == ext:
                    return True
    return False
