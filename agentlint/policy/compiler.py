"""Policy compiler — Phase 7.

Transforms collected :class:`~agentlint.models.RepositoryEvidence` items into
a candidate :class:`~agentlint.models.CanonicalPolicy`.

The compiled policy is a *candidate only* — it must never be auto-applied.
Human approval is required before it becomes the canonical contract.

Public API:
    compile_policy(evidence, repo_path) -> CanonicalPolicy
"""

from __future__ import annotations

from pathlib import Path

from agentlint.models import CanonicalPolicy, RepositoryEvidence

# Strength ordering for _best_evidence selection (lower = stronger).
_STRENGTH_RANK: dict[str, int] = {
    "strong": 0,
    "medium": 1,
    "weak": 2,
}

# Commands evidence keys that map to the tooling command fields.
# Order matters: lint → test → build for definition_of_done.
_COMMAND_KEYS: list[tuple[str, str]] = [
    ("lint", "lint_command"),
    ("test", "test_command"),
    ("build", "build_command"),
]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _best_evidence(
    items: list[RepositoryEvidence],
    category: str,
    key: str | None = None,
) -> RepositoryEvidence | None:
    """Return the single strongest :class:`~agentlint.models.RepositoryEvidence`
    for *category* (and optionally *key*).

    Strength order: strong > medium > weak.  First item wins within the same
    strength tier (collection order is deterministic from Phase 2).

    Args:
        items:    Full evidence list.
        category: Evidence category to filter on.
        key:      Optional evidence key for finer filtering (e.g. ``"pnpm"``).

    Returns:
        The best matching evidence item, or ``None`` if none found.
    """
    candidates = [e for e in items if e.category == category]
    if key is not None:
        candidates = [e for e in candidates if e.key == key]
    if not candidates:
        return None
    return min(candidates, key=lambda e: _STRENGTH_RANK.get(e.strength, 99))


def _all_evidence_for(
    items: list[RepositoryEvidence],
    category: str,
) -> list[RepositoryEvidence]:
    """Return all evidence items for *category*, strongest-first."""
    candidates = [e for e in items if e.category == category]
    return sorted(candidates, key=lambda e: _STRENGTH_RANK.get(e.strength, 99))


def _build_tooling(evidence: list[RepositoryEvidence]) -> dict:
    """Build the ``tooling`` section from evidence.

    Fields:
        package_manager  — from package_manager evidence (best by strength)
        test_framework   — from test_framework evidence (best by strength)
        test_command     — from commands evidence with key "test"
        lint_command     — from commands evidence with key "lint"
        build_command    — from commands evidence with key "build"
    """
    tooling: dict = {}

    pm = _best_evidence(evidence, "package_manager")
    if pm is not None:
        tooling["package_manager"] = pm.value

    tf = _best_evidence(evidence, "test_framework")
    if tf is not None:
        tooling["test_framework"] = tf.value

    for cmd_key, tooling_field in _COMMAND_KEYS:
        cmd_ev = _best_evidence(evidence, "commands", key=cmd_key)
        if cmd_ev is not None:
            tooling[tooling_field] = cmd_ev.value

    return tooling


def _build_runtime(evidence: list[RepositoryEvidence]) -> dict:
    """Build the ``runtime`` section from evidence.

    Each runtime evidence item contributes a ``{key: value}`` pair
    (e.g. ``{"node": "22"}``, ``{"python": "3.11"}``).
    Only the strongest item per key is included.
    """
    runtime: dict = {}
    seen_keys: set[str] = set()
    for ev in _all_evidence_for(evidence, "runtime"):
        if ev.key not in seen_keys:
            runtime[ev.key] = ev.value
            seen_keys.add(ev.key)
    return runtime


def _build_paths(evidence: list[RepositoryEvidence]) -> dict:
    """Build the ``paths`` section from evidence.

    Only includes evidence items with key ``"generated"`` or ``"protected"``.
    Regular indexed-directory evidence is excluded to avoid polluting the
    policy with every directory in the repo.
    """
    generated: list[str] = []
    protected: list[str] = []

    for ev in evidence:
        if ev.category != "paths":
            continue
        if ev.key == "generated":
            generated.append(ev.value)
        elif ev.key == "protected":
            protected.append(ev.value)

    result: dict = {}
    if generated:
        result["generated"] = generated
    if protected:
        result["protected"] = protected
    return result


def _build_definition_of_done(tooling: dict) -> list[str]:
    """Derive the ``definition_of_done`` list from *tooling* commands.

    Canonical order (per spec): lint → test → build.
    Only includes commands that were detected.
    """
    dod: list[str] = []
    for _, field in _COMMAND_KEYS:  # already in lint/test/build order
        cmd = tooling.get(field)
        if cmd:
            dod.append(cmd)
    return dod


def _build_evidence_map(evidence: list[RepositoryEvidence]) -> dict:
    """Build the ``evidence`` section that maps each tooling key to its
    evidence source paths.

    Only includes sources for: package_manager, test_framework, linting,
    commands, runtime.
    Paths evidence is excluded (too noisy).

    Returns a dict like::

        {
            "package_manager": ["package.json#packageManager", "pnpm-lock.yaml"],
            "test_framework":  ["package.json#devDependencies.vitest"],
        }
    """
    _EVIDENCE_CATEGORIES = {
        "package_manager",
        "test_framework",
        "linting",
        "commands",
        "runtime",
    }

    ev_map: dict[str, list[str]] = {}

    for ev in evidence:
        if ev.category not in _EVIDENCE_CATEGORIES:
            continue

        source_ref = ev.source_path
        if ev.source_locator:
            source_ref = f"{source_ref}#{ev.source_locator}"

        bucket = ev_map.setdefault(ev.category, [])
        if source_ref not in bucket:
            bucket.append(source_ref)

    return ev_map


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compile_policy(
    evidence: list[RepositoryEvidence],
    repo_path: Path,
) -> CanonicalPolicy:
    """Compile a candidate :class:`~agentlint.models.CanonicalPolicy` from
    *evidence*.

    Every field is populated from the strongest available evidence, or left
    empty if no evidence exists.  This function never fabricates values and
    never writes to disk.

    The returned policy is a *candidate* — it must not be auto-applied.
    Human approval is required before it becomes the canonical contract
    (see AgentLintplan.md §4.2 and §11).

    Args:
        evidence:  Evidence list from :func:`~agentlint.evidence.collect_evidence`.
        repo_path: Root of the repository (used for ``project_name``).

    Returns:
        A :class:`~agentlint.models.CanonicalPolicy` populated from evidence.
    """
    repo_path = Path(repo_path)

    tooling = _build_tooling(evidence)
    runtime = _build_runtime(evidence)
    paths = _build_paths(evidence)
    definition_of_done = _build_definition_of_done(tooling)
    evidence_map = _build_evidence_map(evidence)

    return CanonicalPolicy(
        version=1,
        project_name=repo_path.name or None,
        tooling=tooling,
        runtime=runtime,
        paths=paths,
        definition_of_done=definition_of_done,
        evidence=evidence_map,
    )
