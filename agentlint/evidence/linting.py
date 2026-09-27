"""Lint/format detector.

Detects which lint and format tools the repository uses from package.json
devDependencies, config files, pyproject.toml, and CI workflow commands.
"""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

from agentlint.models import RepositoryEvidence

# JS/TS linting/formatting deps
_JS_LINT_DEPS: dict[str, tuple[str, str]] = {
    # dep_name: (key, value)
    "eslint": ("linter", "eslint"),
    "prettier": ("formatter", "prettier"),
    "biome": ("linter", "biome"),
    "@biomejs/biome": ("linter", "biome"),
    "oxlint": ("linter", "oxlint"),
    "stylelint": ("linter", "stylelint"),
}

# Config file globs → (key, value)
_JS_LINT_CONFIG_GLOBS: list[tuple[str, str, str]] = [
    (".eslintrc*", "linter", "eslint"),
    ("eslint.config.*", "linter", "eslint"),
    (".prettierrc*", "formatter", "prettier"),
    ("prettier.config.*", "formatter", "prettier"),
    (".stylelintrc*", "linter", "stylelint"),
    ("biome.json", "linter", "biome"),
    (".biome.json", "linter", "biome"),
]

# Python lint config file names → (key, value)
_PYTHON_LINT_FILES: list[tuple[str, str, str]] = [
    ("ruff.toml", "linter", "ruff"),
    (".ruff.toml", "linter", "ruff"),
]

# CI patterns → (key, value)
_CI_LINT_PATTERNS: list[tuple[re.Pattern[str], str, str]] = [
    (re.compile(r"\beslint\b"), "linter", "eslint"),
    (re.compile(r"\bprettier\b"), "formatter", "prettier"),
    (re.compile(r"\bruff\b"), "linter", "ruff"),
    (re.compile(r"\bblack\b"), "formatter", "black"),
    (re.compile(r"\bbiome\b"), "linter", "biome"),
    (re.compile(r"\bstylelint\b"), "linter", "stylelint"),
]


def detect_linting(repo_path: Path) -> list[RepositoryEvidence]:
    """Return all lint/format evidence found in *repo_path*.

    Args:
        repo_path: Root directory of the repository.

    Returns:
        A list of :class:`~agentlint.models.RepositoryEvidence` items
        (``category="linting"``).  IDs are left empty.
    """
    repo_path = Path(repo_path).resolve()
    evidence: list[RepositoryEvidence] = []

    evidence.extend(_js_dep_linting_evidence(repo_path))
    evidence.extend(_config_file_linting_evidence(repo_path))
    evidence.extend(_python_linting_evidence(repo_path))
    evidence.extend(_ci_linting_evidence(repo_path))

    return evidence


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _js_dep_linting_evidence(repo_path: Path) -> list[RepositoryEvidence]:
    """Detect lint/format tools from package.json devDependencies."""
    pkg_json = repo_path / "package.json"
    if not pkg_json.is_file():
        return []
    try:
        pkg = json.loads(pkg_json.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    all_deps: dict[str, str] = {}
    all_deps.update(pkg.get("dependencies", {}) or {})
    all_deps.update(pkg.get("devDependencies", {}) or {})

    results: list[RepositoryEvidence] = []
    seen: set[str] = set()  # (key, value) dedup

    for dep_name, (key, value) in _JS_LINT_DEPS.items():
        if dep_name in all_deps and (key, value) not in seen:
            seen.add((key, value))
            results.append(
                RepositoryEvidence(
                    id="",
                    category="linting",
                    key=key,
                    value=value,
                    source_path="package.json",
                    source_locator=f"devDependencies.{dep_name}",
                    strength="strong",
                    explanation=(
                        f'package.json dependency "{dep_name}" indicates '
                        f"{value} is used."
                    ),
                )
            )
    return results


def _config_file_linting_evidence(repo_path: Path) -> list[RepositoryEvidence]:
    """Detect lint/format tools from config files (strong)."""
    results: list[RepositoryEvidence] = []
    seen: set[tuple[str, str]] = set()

    for glob_pattern, key, value in _JS_LINT_CONFIG_GLOBS:
        for config_file in repo_path.glob(glob_pattern):
            if config_file.is_file() and (key, value) not in seen:
                seen.add((key, value))
                rel = config_file.relative_to(repo_path)
                results.append(
                    RepositoryEvidence(
                        id="",
                        category="linting",
                        key=key,
                        value=value,
                        source_path=str(rel),
                        source_locator=None,
                        strength="strong",
                        explanation=f"Config file {str(rel)!r} is present.",
                    )
                )

    for filename, key, value in _PYTHON_LINT_FILES:
        if (repo_path / filename).is_file() and (key, value) not in seen:
            seen.add((key, value))
            results.append(
                RepositoryEvidence(
                    id="",
                    category="linting",
                    key=key,
                    value=value,
                    source_path=filename,
                    source_locator=None,
                    strength="strong",
                    explanation=f"Config file {filename!r} is present.",
                )
            )
    return results


def _python_linting_evidence(repo_path: Path) -> list[RepositoryEvidence]:
    """Detect ruff/black from pyproject.toml (strong)."""
    pyproject = repo_path / "pyproject.toml"
    if not pyproject.is_file():
        return []
    try:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, OSError):
        return []

    results: list[RepositoryEvidence] = []
    tool = data.get("tool", {})

    if "ruff" in tool:
        results.append(
            RepositoryEvidence(
                id="",
                category="linting",
                key="linter",
                value="ruff",
                source_path="pyproject.toml",
                source_locator="[tool.ruff]",
                strength="strong",
                explanation="pyproject.toml contains a [tool.ruff] section.",
            )
        )

    if "black" in tool:
        results.append(
            RepositoryEvidence(
                id="",
                category="linting",
                key="formatter",
                value="black",
                source_path="pyproject.toml",
                source_locator="[tool.black]",
                strength="strong",
                explanation="pyproject.toml contains a [tool.black] section.",
            )
        )

    # Also check dep lists
    for key, dep_name, tool_value in [
        ("linter", "ruff", "ruff"),
        ("formatter", "black", "black"),
    ]:
        if _pyproject_has_dep(data, dep_name) and not any(
            e.value == tool_value for e in results
        ):
            results.append(
                RepositoryEvidence(
                    id="",
                    category="linting",
                    key=key,
                    value=tool_value,
                    source_path="pyproject.toml",
                    source_locator="dependencies",
                    strength="strong",
                    explanation=f"pyproject.toml lists {tool_value} as a dependency.",
                )
            )

    return results


def _pyproject_has_dep(data: dict, name: str) -> bool:
    """Return True if *name* appears in pyproject.toml dependencies."""
    project_deps = data.get("project", {}).get("dependencies", []) or []
    for dep in project_deps:
        if isinstance(dep, str) and dep.lower().startswith(name.lower()):
            return True

    opt_deps = data.get("project", {}).get("optional-dependencies", {}) or {}
    for deps_list in opt_deps.values():
        for dep in deps_list or []:
            if isinstance(dep, str) and dep.lower().startswith(name.lower()):
                return True

    poetry_deps = (
        data.get("tool", {}).get("poetry", {}).get("dependencies", {}) or {}
    )
    if any(k.lower() == name.lower() for k in poetry_deps):
        return True

    dev_deps = (
        data.get("tool", {})
        .get("poetry", {})
        .get("dev-dependencies", {})
        or {}
    )
    if any(k.lower() == name.lower() for k in dev_deps):
        return True

    return False


def _ci_linting_evidence(repo_path: Path) -> list[RepositoryEvidence]:
    """Return medium-strength lint/format evidence from CI workflow files."""
    workflows_dir = repo_path / ".github" / "workflows"
    if not workflows_dir.is_dir():
        return []

    found: dict[tuple[str, str], str] = {}  # (key, value) → source_path
    for yml_file in sorted(workflows_dir.glob("*.yml")):
        try:
            text = yml_file.read_text(encoding="utf-8")
        except OSError:
            continue
        rel_path = str(yml_file.relative_to(repo_path))
        for line in text.splitlines():
            for pattern, key, value in _CI_LINT_PATTERNS:
                pair = (key, value)
                if pattern.search(line) and pair not in found:
                    found[pair] = rel_path

    return [
        RepositoryEvidence(
            id="",
            category="linting",
            key=key,
            value=value,
            source_path=source_path,
            source_locator=None,
            strength="medium",
            explanation=(
                f'CI workflow {source_path!r} contains "{value}" commands.'
            ),
        )
        for (key, value), source_path in found.items()
    ]
