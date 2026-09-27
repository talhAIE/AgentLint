"""Package manager detector.

Determines which package manager a repository uses by inspecting file-system
evidence in priority order.  All evidence items are returned so Phase 4 can
detect instruction-vs-repository mismatches.

Evidence priority:
1. ``package.json`` → ``packageManager`` field  (strong)
2. ``pnpm-lock.yaml`` exists                     (strong)
3. ``yarn.lock`` exists                          (strong)
4. ``package-lock.json`` exists                  (npm, strong)
5. ``bun.lock`` / ``bun.lockb`` exists           (strong)
6. CI workflow commands mentioning a manager      (medium)

Conflicting evidence is **preserved**, never discarded.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from agentlint.models import RepositoryEvidence


def detect_package_manager(repo_path: Path) -> list[RepositoryEvidence]:
    """Return all package-manager evidence found in *repo_path*.

    Args:
        repo_path: Root directory of the repository.

    Returns:
        A list of :class:`~agentlint.models.RepositoryEvidence` items
        (``category="package_manager"``).  May be empty if no evidence is
        found.  IDs are left empty — the aggregator in
        :mod:`agentlint.evidence.repository_truth` assigns them.
    """
    repo_path = Path(repo_path).resolve()
    evidence: list[RepositoryEvidence] = []

    # --- 1. package.json packageManager field ---
    pkg_json_path = repo_path / "package.json"
    if pkg_json_path.is_file():
        try:
            pkg = json.loads(pkg_json_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pkg = {}

        pm_field = pkg.get("packageManager", "")
        if isinstance(pm_field, str) and pm_field:
            # e.g. "pnpm@8.15.0" → "pnpm"
            manager_name = pm_field.split("@")[0].strip().lower()
            if manager_name:
                evidence.append(
                    RepositoryEvidence(
                        id="",
                        category="package_manager",
                        key="package_manager",
                        value=manager_name,
                        source_path="package.json",
                        source_locator="packageManager",
                        strength="strong",
                        explanation=(
                            f'package.json "packageManager" field is "{pm_field}".'
                        ),
                    )
                )

    # --- 2–5. Lockfiles ---
    lockfile_map: list[tuple[str, str]] = [
        ("pnpm-lock.yaml", "pnpm"),
        ("yarn.lock", "yarn"),
        ("package-lock.json", "npm"),
        ("bun.lock", "bun"),
        ("bun.lockb", "bun"),
    ]
    for lockfile, manager in lockfile_map:
        if (repo_path / lockfile).is_file():
            evidence.append(
                RepositoryEvidence(
                    id="",
                    category="package_manager",
                    key="package_manager",
                    value=manager,
                    source_path=lockfile,
                    source_locator=None,
                    strength="strong",
                    explanation=f"Lockfile {lockfile!r} is present.",
                )
            )

    # --- 6. CI workflow commands ---
    evidence.extend(_ci_package_manager_evidence(repo_path))

    return evidence


# ---------------------------------------------------------------------------
# CI helper
# ---------------------------------------------------------------------------

_CI_MANAGER_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bpnpm\b"), "pnpm"),
    (re.compile(r"\byarn\b"), "yarn"),
    (re.compile(r"\bnpm\b"), "npm"),
    (re.compile(r"\bbun\b"), "bun"),
]


def _ci_package_manager_evidence(repo_path: Path) -> list[RepositoryEvidence]:
    """Return medium-strength package-manager evidence from CI workflow files."""
    workflows_dir = repo_path / ".github" / "workflows"
    if not workflows_dir.is_dir():
        return []

    found: dict[str, str] = {}  # manager → first source_path seen
    for yml_file in sorted(workflows_dir.glob("*.yml")):
        try:
            text = yml_file.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines():
            for pattern, manager in _CI_MANAGER_PATTERNS:
                if pattern.search(line) and manager not in found:
                    rel_path = str(yml_file.relative_to(repo_path))
                    found[manager] = rel_path

    return [
        RepositoryEvidence(
            id="",
            category="package_manager",
            key="package_manager",
            value=manager,
            source_path=source_path,
            source_locator=None,
            strength="medium",
            explanation=(
                f'CI workflow {source_path!r} contains "{manager}" commands.'
            ),
        )
        for manager, source_path in found.items()
    ]
