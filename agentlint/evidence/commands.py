"""Commands detector.

Extracts canonical command strings for install, test, lint, build, and
format operations from static project files.  No shell execution occurs.

Sources (in priority):
1. ``package.json`` ``scripts``         (strong)
2. ``pyproject.toml`` ``[tool.taskipy.tasks]`` or ``[project.scripts]``  (strong)
3. ``Makefile`` targets                 (medium)
4. ``.github/workflows/*.yml`` run: steps  (medium)
"""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

from agentlint.models import RepositoryEvidence

# Script names that map to canonical command types.
# Order matters: first match wins for a given script value.
_SCRIPT_TYPE_MAP: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^test(:.+)?$"), "test"),
    (re.compile(r"^lint(:.+)?$"), "lint"),
    (re.compile(r"^build(:.+)?$"), "build"),
    (re.compile(r"^format(:.+)?$"), "format"),
    (re.compile(r"^dev$"), "dev"),
    (re.compile(r"^start$"), "start"),
    (re.compile(r"^install$"), "install"),
    (re.compile(r"^check(:.+)?$"), "check"),
    (re.compile(r"^typecheck(:.+)?$"), "typecheck"),
    (re.compile(r"^type-check(:.+)?$"), "typecheck"),
]


def detect_commands(repo_path: Path) -> list[RepositoryEvidence]:
    """Return all commands evidence found in *repo_path*.

    Args:
        repo_path: Root directory of the repository.

    Returns:
        A list of :class:`~agentlint.models.RepositoryEvidence` items
        (``category="commands"``).  IDs are left empty.
    """
    repo_path = Path(repo_path).resolve()
    evidence: list[RepositoryEvidence] = []

    evidence.extend(_package_json_commands(repo_path))
    evidence.extend(_pyproject_commands(repo_path))
    evidence.extend(_makefile_commands(repo_path))
    evidence.extend(_ci_commands(repo_path))

    return evidence


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _package_json_commands(repo_path: Path) -> list[RepositoryEvidence]:
    """Extract commands from package.json scripts (strong)."""
    pkg_json = repo_path / "package.json"
    if not pkg_json.is_file():
        return []
    try:
        pkg = json.loads(pkg_json.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    scripts: dict[str, str] = pkg.get("scripts", {}) or {}
    results: list[RepositoryEvidence] = []
    seen_types: set[str] = set()

    for script_name, script_value in scripts.items():
        if not isinstance(script_value, str):
            continue
        cmd_type = _classify_script_name(script_name)
        if cmd_type and cmd_type not in seen_types:
            seen_types.add(cmd_type)
            results.append(
                RepositoryEvidence(
                    id="",
                    category="commands",
                    key=cmd_type,
                    value=script_value,
                    source_path="package.json",
                    source_locator=f"scripts.{script_name}",
                    strength="strong",
                    explanation=(
                        f'package.json scripts.{script_name} = "{script_value}".'
                    ),
                )
            )

    return results


def _classify_script_name(name: str) -> str | None:
    """Return the canonical command type for a script *name*, or None."""
    for pattern, cmd_type in _SCRIPT_TYPE_MAP:
        if pattern.match(name.lower()):
            return cmd_type
    return None


def _pyproject_commands(repo_path: Path) -> list[RepositoryEvidence]:
    """Extract commands from pyproject.toml (strong)."""
    pyproject = repo_path / "pyproject.toml"
    if not pyproject.is_file():
        return []
    try:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, OSError):
        return []

    results: list[RepositoryEvidence] = []
    seen_types: set[str] = set()

    # [tool.taskipy.tasks]
    taskipy: dict = (
        data.get("tool", {}).get("taskipy", {}).get("tasks", {}) or {}
    )
    for task_name, task_value in taskipy.items():
        cmd_type = _classify_script_name(task_name)
        if cmd_type and cmd_type not in seen_types:
            seen_types.add(cmd_type)
            cmd_str = (
                task_value
                if isinstance(task_value, str)
                else task_value.get("cmd", str(task_value))
                if isinstance(task_value, dict)
                else str(task_value)
            )
            results.append(
                RepositoryEvidence(
                    id="",
                    category="commands",
                    key=cmd_type,
                    value=cmd_str,
                    source_path="pyproject.toml",
                    source_locator=f"tool.taskipy.tasks.{task_name}",
                    strength="strong",
                    explanation=(
                        f'pyproject.toml [tool.taskipy.tasks].{task_name} '
                        f'= "{cmd_str}".'
                    ),
                )
            )

    # [project.scripts]
    proj_scripts: dict = data.get("project", {}).get("scripts", {}) or {}
    for script_name, entry_point in proj_scripts.items():
        cmd_type = _classify_script_name(script_name)
        if cmd_type and cmd_type not in seen_types:
            seen_types.add(cmd_type)
            results.append(
                RepositoryEvidence(
                    id="",
                    category="commands",
                    key=cmd_type,
                    value=str(entry_point),
                    source_path="pyproject.toml",
                    source_locator=f"project.scripts.{script_name}",
                    strength="strong",
                    explanation=(
                        f'pyproject.toml [project.scripts].{script_name} '
                        f'= "{entry_point}".'
                    ),
                )
            )

    return results


# Simple Makefile target pattern: line starts with word chars, ends with ':'
# optionally followed by prerequisites.
_MAKEFILE_TARGET_RE = re.compile(r"^([A-Za-z0-9_.-]+)\s*:(?:[^=]|$)")


def _makefile_commands(repo_path: Path) -> list[RepositoryEvidence]:
    """Extract targets from Makefile (medium)."""
    makefile = repo_path / "Makefile"
    if not makefile.is_file():
        return []
    try:
        lines = makefile.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []

    results: list[RepositoryEvidence] = []
    seen_types: set[str] = set()

    for line in lines:
        m = _MAKEFILE_TARGET_RE.match(line)
        if not m:
            continue
        target = m.group(1)
        cmd_type = _classify_script_name(target)
        if cmd_type and cmd_type not in seen_types:
            seen_types.add(cmd_type)
            results.append(
                RepositoryEvidence(
                    id="",
                    category="commands",
                    key=cmd_type,
                    value=f"make {target}",
                    source_path="Makefile",
                    source_locator=target,
                    strength="medium",
                    explanation=f'Makefile target "{target}" maps to {cmd_type} command.',
                )
            )

    return results


# Match run: values in GitHub Actions YAML (line-level, not full parse)
_CI_RUN_RE = re.compile(r"^\s+run:\s+(.+)$")


def _ci_commands(repo_path: Path) -> list[RepositoryEvidence]:
    """Extract run: commands from CI workflows (medium)."""
    workflows_dir = repo_path / ".github" / "workflows"
    if not workflows_dir.is_dir():
        return []

    results: list[RepositoryEvidence] = []
    seen_types: set[str] = set()

    for yml_file in sorted(workflows_dir.glob("*.yml")):
        try:
            lines = yml_file.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        rel_path = str(yml_file.relative_to(repo_path))
        for line in lines:
            m = _CI_RUN_RE.match(line)
            if not m:
                continue
            cmd = m.group(1).strip()
            # Determine command type by inspecting the command text
            cmd_type = _classify_ci_command(cmd)
            if cmd_type and cmd_type not in seen_types:
                seen_types.add(cmd_type)
                results.append(
                    RepositoryEvidence(
                        id="",
                        category="commands",
                        key=cmd_type,
                        value=cmd,
                        source_path=rel_path,
                        source_locator="run",
                        strength="medium",
                        explanation=(
                            f'CI workflow {rel_path!r} runs "{cmd}" '
                            f'({cmd_type}).'
                        ),
                    )
                )

    return results


_CI_CMD_TYPE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\btest\b|\bvitest\b|\bjest\b|\bpytest\b"), "test"),
    (re.compile(r"\blint\b|\beslint\b|\bruff\b"), "lint"),
    (re.compile(r"\bbuild\b|\btsc\b"), "build"),
    (re.compile(r"\bformat\b|\bprettier\b|\bblack\b"), "format"),
    (re.compile(r"\binstall\b"), "install"),
]


def _classify_ci_command(cmd: str) -> str | None:
    """Return a canonical command type for a CI run: step value."""
    for pattern, cmd_type in _CI_CMD_TYPE_PATTERNS:
        if pattern.search(cmd):
            return cmd_type
    return None
