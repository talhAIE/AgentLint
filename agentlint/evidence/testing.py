"""Test framework detector.

Detects which test framework the repository uses from package.json
dependencies, config files, pyproject.toml, and CI workflow commands.
All evidence items are returned with strength annotations.
"""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

from agentlint.models import RepositoryEvidence

# ---------------------------------------------------------------------------
# JS/TS test framework signals
# ---------------------------------------------------------------------------

# dep-name → framework name (checked in devDependencies and dependencies)
_JS_DEP_FRAMEWORKS: dict[str, str] = {
    "vitest": "vitest",
    "jest": "jest",
    "@jest/core": "jest",
    "jest-cli": "jest",
    "playwright": "playwright",
    "@playwright/test": "playwright",
    "cypress": "cypress",
    "mocha": "mocha",
    "jasmine": "jasmine",
}

# config file glob patterns → framework name
_JS_CONFIG_PATTERNS: list[tuple[str, str]] = [
    ("vitest.config.*", "vitest"),
    ("jest.config.*", "jest"),
    ("cypress.config.*", "cypress"),
    ("playwright.config.*", "playwright"),
]

# script keyword → framework name (medium strength)
_SCRIPT_KEYWORDS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bvitest\b"), "vitest"),
    (re.compile(r"\bjest\b"), "jest"),
    (re.compile(r"\bplaywright\b"), "playwright"),
    (re.compile(r"\bcypress\b"), "cypress"),
]

# CI run: line keywords (medium strength)
_CI_KEYWORDS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bvitest\b"), "vitest"),
    (re.compile(r"\bjest\b"), "jest"),
    (re.compile(r"\bpytest\b"), "pytest"),
    (re.compile(r"\bplaywright\b"), "playwright"),
    (re.compile(r"\bcypress\b"), "cypress"),
]


def detect_test_framework(repo_path: Path) -> list[RepositoryEvidence]:
    """Return all test-framework evidence found in *repo_path*.

    Args:
        repo_path: Root directory of the repository.

    Returns:
        A list of :class:`~agentlint.models.RepositoryEvidence` items
        (``category="test_framework"``).  IDs are left empty.
    """
    repo_path = Path(repo_path).resolve()
    evidence: list[RepositoryEvidence] = []

    evidence.extend(_js_dep_evidence(repo_path))
    evidence.extend(_js_config_file_evidence(repo_path))
    evidence.extend(_js_script_evidence(repo_path))
    evidence.extend(_python_test_evidence(repo_path))
    evidence.extend(_ci_test_evidence(repo_path))

    return evidence


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _js_dep_evidence(repo_path: Path) -> list[RepositoryEvidence]:
    """Detect test framework from package.json dependencies."""
    pkg_json = repo_path / "package.json"
    if not pkg_json.is_file():
        return []
    try:
        pkg = json.loads(pkg_json.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    results: list[RepositoryEvidence] = []
    all_deps: dict[str, str] = {}
    all_deps.update(pkg.get("dependencies", {}) or {})
    all_deps.update(pkg.get("devDependencies", {}) or {})

    seen: set[str] = set()
    for dep_name, framework in _JS_DEP_FRAMEWORKS.items():
        if dep_name in all_deps and framework not in seen:
            seen.add(framework)
            results.append(
                RepositoryEvidence(
                    id="",
                    category="test_framework",
                    key="test_framework",
                    value=framework,
                    source_path="package.json",
                    source_locator=f"devDependencies.{dep_name}",
                    strength="strong",
                    explanation=(
                        f'package.json dependency "{dep_name}" indicates '
                        f"{framework} is the test framework."
                    ),
                )
            )
    return results


def _js_config_file_evidence(repo_path: Path) -> list[RepositoryEvidence]:
    """Detect test framework from config files."""
    results: list[RepositoryEvidence] = []
    seen: set[str] = set()
    for glob_pattern, framework in _JS_CONFIG_PATTERNS:
        for config_file in repo_path.glob(glob_pattern):
            if config_file.is_file() and framework not in seen:
                seen.add(framework)
                rel = config_file.relative_to(repo_path)
                results.append(
                    RepositoryEvidence(
                        id="",
                        category="test_framework",
                        key="test_framework",
                        value=framework,
                        source_path=str(rel),
                        source_locator=None,
                        strength="strong",
                        explanation=f"Config file {str(rel)!r} is present.",
                    )
                )
    return results


def _js_script_evidence(repo_path: Path) -> list[RepositoryEvidence]:
    """Detect test framework from package.json scripts (medium strength)."""
    pkg_json = repo_path / "package.json"
    if not pkg_json.is_file():
        return []
    try:
        pkg = json.loads(pkg_json.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    scripts: dict[str, str] = pkg.get("scripts", {}) or {}
    script_text = " ".join(str(v) for v in scripts.values())

    results: list[RepositoryEvidence] = []
    seen: set[str] = set()
    for pattern, framework in _SCRIPT_KEYWORDS:
        if pattern.search(script_text) and framework not in seen:
            # Only add as medium if not already covered by dep evidence
            seen.add(framework)
            results.append(
                RepositoryEvidence(
                    id="",
                    category="test_framework",
                    key="test_framework",
                    value=framework,
                    source_path="package.json",
                    source_locator="scripts",
                    strength="medium",
                    explanation=(
                        f'package.json scripts contain "{framework}" command.'
                    ),
                )
            )
    return results


def _python_test_evidence(repo_path: Path) -> list[RepositoryEvidence]:
    """Detect pytest from pyproject.toml or pytest.ini."""
    results: list[RepositoryEvidence] = []

    # pytest.ini
    if (repo_path / "pytest.ini").is_file():
        results.append(
            RepositoryEvidence(
                id="",
                category="test_framework",
                key="test_framework",
                value="pytest",
                source_path="pytest.ini",
                source_locator=None,
                strength="strong",
                explanation="pytest.ini is present.",
            )
        )

    # setup.cfg with [tool:pytest]
    setup_cfg = repo_path / "setup.cfg"
    if setup_cfg.is_file():
        try:
            content = setup_cfg.read_text(encoding="utf-8")
            if "[tool:pytest]" in content:
                results.append(
                    RepositoryEvidence(
                        id="",
                        category="test_framework",
                        key="test_framework",
                        value="pytest",
                        source_path="setup.cfg",
                        source_locator="[tool:pytest]",
                        strength="strong",
                        explanation="setup.cfg contains a [tool:pytest] section.",
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

        # [tool.pytest.*] section
        tool = data.get("tool", {})
        if "pytest" in tool or any(k.startswith("pytest") for k in tool):
            results.append(
                RepositoryEvidence(
                    id="",
                    category="test_framework",
                    key="test_framework",
                    value="pytest",
                    source_path="pyproject.toml",
                    source_locator="[tool.pytest.*]",
                    strength="strong",
                    explanation=(
                        "pyproject.toml contains a [tool.pytest.*] section."
                    ),
                )
            )

        # dependencies / dev dependencies
        deps_found = _pyproject_has_dep(data, "pytest")
        if deps_found and not any(
            e.value == "pytest" and e.source_path == "pyproject.toml"
            for e in results
        ):
            results.append(
                RepositoryEvidence(
                    id="",
                    category="test_framework",
                    key="test_framework",
                    value="pytest",
                    source_path="pyproject.toml",
                    source_locator="dependencies",
                    strength="strong",
                    explanation="pyproject.toml lists pytest as a dependency.",
                )
            )

    return results


def _pyproject_has_dep(data: dict, name: str) -> bool:
    """Return True if *name* appears in pyproject.toml dependencies."""
    # [project] dependencies
    project_deps: list[str] = data.get("project", {}).get("dependencies", []) or []
    for dep in project_deps:
        if isinstance(dep, str) and dep.lower().startswith(name.lower()):
            return True

    # [project.optional-dependencies]
    opt_deps: dict = (
        data.get("project", {}).get("optional-dependencies", {}) or {}
    )
    for deps_list in opt_deps.values():
        for dep in deps_list or []:
            if isinstance(dep, str) and dep.lower().startswith(name.lower()):
                return True

    # [tool.poetry.dependencies]
    poetry_deps: dict = (
        data.get("tool", {}).get("poetry", {}).get("dependencies", {}) or {}
    )
    if any(k.lower() == name.lower() for k in poetry_deps):
        return True

    # [tool.poetry.dev-dependencies]
    dev_deps: dict = (
        data.get("tool", {})
        .get("poetry", {})
        .get("dev-dependencies", {})
        or {}
    )
    if any(k.lower() == name.lower() for k in dev_deps):
        return True

    return False


def _ci_test_evidence(repo_path: Path) -> list[RepositoryEvidence]:
    """Return medium-strength test-framework evidence from CI workflow files."""
    workflows_dir = repo_path / ".github" / "workflows"
    if not workflows_dir.is_dir():
        return []

    found: dict[str, str] = {}  # framework → source_path
    for yml_file in sorted(workflows_dir.glob("*.yml")):
        try:
            text = yml_file.read_text(encoding="utf-8")
        except OSError:
            continue
        rel_path = str(yml_file.relative_to(repo_path))
        for line in text.splitlines():
            for pattern, framework in _CI_KEYWORDS:
                if pattern.search(line) and framework not in found:
                    found[framework] = rel_path

    return [
        RepositoryEvidence(
            id="",
            category="test_framework",
            key="test_framework",
            value=framework,
            source_path=source_path,
            source_locator=None,
            strength="medium",
            explanation=(
                f'CI workflow {source_path!r} contains "{framework}" commands.'
            ),
        )
        for framework, source_path in found.items()
    ]
