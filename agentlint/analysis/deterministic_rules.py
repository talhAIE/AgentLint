"""Deterministic finding detectors — Phase 4.

All public functions are pure, deterministic, and require no LLM or network.

Functions:
    detect_f01_cross_file_conflicts(rules)       → list[Finding]
    detect_f02_mismatch(rules, evidence)          → list[Finding]
    detect_f03_stale_paths(rules, evidence)       → list[Finding]
    detect_f04_invalid_commands(rules, evidence)  → list[Finding]

F05 duplicate detection lives in :mod:`agentlint.analysis.duplicates`.
"""

from __future__ import annotations

import re
from collections import defaultdict

from agentlint.models import Finding, InstructionRule, RepositoryEvidence

# ---------------------------------------------------------------------------
# Categories subject to F02 mismatch checks
# ---------------------------------------------------------------------------

# (category, severity, confidence_strong, confidence_medium)
_F02_CATEGORIES: list[tuple[str, str, float, float]] = [
    ("package_manager", "high", 0.95, 0.7),
    ("test_framework", "high", 0.95, 0.7),
    ("linting", "medium", 0.85, 0.6),
]

# ---------------------------------------------------------------------------
# F01 — Cross-file exact contradictions
# ---------------------------------------------------------------------------


def detect_f01_cross_file_conflicts(
    rules: list[InstructionRule],
) -> list[Finding]:
    """Return F01 findings where two *different* source files give conflicting
    values for the same ``normalized_key``.

    Only fires when both rules have non-None ``normalized_value``.
    Confidence = 0.9 (deterministic text comparison).
    Severity = "high".
    """
    # Group by normalized_key → {source_path: [values]}
    key_sources: dict[str, dict[str, set[str]]] = defaultdict(
        lambda: defaultdict(set)
    )
    for rule in rules:
        if rule.normalized_key is None or rule.normalized_value is None:
            continue
        key_sources[rule.normalized_key][rule.source_path].add(rule.normalized_value)

    findings: list[Finding] = []

    for norm_key, source_map in key_sources.items():
        if len(source_map) < 2:
            continue  # only one source file — no cross-file conflict possible

        # Collect (source_path, value) pairs for all sources
        source_items = sorted(source_map.items())  # stable sort

        # Compare each pair of distinct sources
        for i in range(len(source_items)):
            for j in range(i + 1, len(source_items)):
                path_a, vals_a = source_items[i]
                path_b, vals_b = source_items[j]

                # Conflict if the value sets are disjoint
                if vals_a.isdisjoint(vals_b):
                    # Collect all rule ids involved
                    rule_ids = [
                        r.id
                        for r in rules
                        if r.source_path in (path_a, path_b)
                        and r.normalized_key == norm_key
                        and r.normalized_value is not None
                    ]
                    sorted_a = sorted(vals_a)
                    sorted_b = sorted(vals_b)
                    findings.append(
                        Finding(
                            id="",  # assigned later
                            type="F01",
                            severity="high",
                            title=(
                                f"Cross-instruction conflict: {norm_key} "
                                f"({', '.join(sorted_a)} vs {', '.join(sorted_b)})"
                            ),
                            explanation=(
                                f"{path_a!r} specifies {norm_key}="
                                f"{', '.join(sorted_a)} but {path_b!r} specifies "
                                f"{norm_key}={', '.join(sorted_b)}. "
                                "Agents will receive contradictory guidance."
                            ),
                            instruction_rules=rule_ids,
                            evidence_ids=[],
                            recommended_action=(
                                f"Reconcile {norm_key} across all instruction files "
                                f"to use a single agreed value."
                            ),
                            confidence=0.9,
                            deterministic=True,
                        )
                    )

    return findings


# ---------------------------------------------------------------------------
# F02 — Instruction vs Repository Mismatch
# ---------------------------------------------------------------------------


def detect_f02_mismatch(
    rules: list[InstructionRule],
    evidence: list[RepositoryEvidence],
) -> list[Finding]:
    """Return F02 findings where an instruction rule disagrees with repository
    evidence for the same category/key.

    Only fires when strong evidence exists for the category and the rule value
    does not match any strong evidence value.
    When only medium evidence exists and conflicts, a lower-confidence F02 fires.
    No finding fires when there is no evidence for the category.
    """
    findings: list[Finding] = []

    # Build evidence lookup: category → {strength → set[value]}
    ev_by_category: dict[str, dict[str, set[str]]] = defaultdict(
        lambda: defaultdict(set)
    )
    ev_ids_by_category_value: dict[tuple[str, str], list[str]] = defaultdict(list)
    for ev in evidence:
        ev_by_category[ev.category][ev.strength].add(ev.value)
        ev_ids_by_category_value[(ev.category, ev.value)].append(ev.id)

    for cat, severity, conf_strong, conf_medium in _F02_CATEGORIES:
        cat_evidence = ev_by_category.get(cat)
        if not cat_evidence:
            continue  # no evidence for this category → no finding

        strong_values = cat_evidence.get("strong", set())
        medium_values = cat_evidence.get("medium", set())

        for rule in rules:
            if rule.category != cat:
                continue
            if rule.normalized_value is None:
                continue

            rule_val = rule.normalized_value.lower()

            # Gather evidence ids for the conflicting values
            ev_ids: list[str] = []
            for ev in evidence:
                if ev.category == cat and ev.value.lower() != rule_val:
                    ev_ids.append(ev.id)

            if strong_values and rule_val not in {v.lower() for v in strong_values}:
                # Strong conflict
                conflict_vals = sorted(strong_values)
                findings.append(
                    Finding(
                        id="",
                        type="F02",
                        severity=severity,
                        title=(
                            f"Instruction vs repository mismatch: {cat} "
                            f"(instruction={rule.normalized_value}, "
                            f"repo={', '.join(conflict_vals)})"
                        ),
                        explanation=(
                            f"Instruction in {rule.source_path!r} specifies "
                            f"{cat}={rule.normalized_value!r}, but the repository "
                            f"uses {', '.join(conflict_vals)!r} "
                            f"(strong evidence from repository files)."
                        ),
                        instruction_rules=[rule.id],
                        evidence_ids=ev_ids,
                        recommended_action=(
                            f"Update the instruction in {rule.source_path} to "
                            f"use {', '.join(conflict_vals)} instead of "
                            f"{rule.normalized_value}."
                        ),
                        confidence=conf_strong,
                        deterministic=True,
                    )
                )
            elif (
                not strong_values
                and medium_values
                and rule_val not in {v.lower() for v in medium_values}
            ):
                # Medium-only conflict
                conflict_vals = sorted(medium_values)
                findings.append(
                    Finding(
                        id="",
                        type="F02",
                        severity=severity,
                        title=(
                            f"Instruction vs repository mismatch: {cat} "
                            f"(instruction={rule.normalized_value}, "
                            f"repo={', '.join(conflict_vals)})"
                        ),
                        explanation=(
                            f"Instruction in {rule.source_path!r} specifies "
                            f"{cat}={rule.normalized_value!r}, but medium-strength "
                            f"repository evidence suggests "
                            f"{', '.join(conflict_vals)!r}."
                        ),
                        instruction_rules=[rule.id],
                        evidence_ids=ev_ids,
                        recommended_action=(
                            f"Verify that {rule.normalized_value} is the correct "
                            f"{cat} for this repository."
                        ),
                        confidence=conf_medium,
                        deterministic=True,
                    )
                )

    return findings


# ---------------------------------------------------------------------------
# F03 — Stale Paths
# ---------------------------------------------------------------------------

_BACKTICK_QUOTE_RE = re.compile(r"[`'\"]")


def _normalize_path(raw: str) -> str:
    """Strip backticks, quotes, leading/trailing slashes, and lowercase."""
    cleaned = _BACKTICK_QUOTE_RE.sub("", raw).strip()
    cleaned = cleaned.strip("/\\")
    return cleaned.lower()


def detect_f03_stale_paths(
    rules: list[InstructionRule],
    evidence: list[RepositoryEvidence],
) -> list[Finding]:
    """Return F03 findings for instruction path references that have no
    matching repository evidence.

    Conservative matching:
    - If neither the path nor its root segment exist in evidence → F03, confidence=0.8.
    - If the root segment exists but the exact sub-path does not → F03, confidence=0.6
      (lower confidence because the path may have been reorganised under the same root).
    - Exact match → no finding.
    """
    # Build a set of normalized path values from evidence
    path_evidence_values: set[str] = set()
    path_ev_ids: list[str] = []
    for ev in evidence:
        if ev.category == "paths":
            path_evidence_values.add(_normalize_path(ev.value))
            if ev.id:
                path_ev_ids.append(ev.id)

    if not path_evidence_values:
        # No path evidence indexed — skip to avoid false positives
        return []

    findings: list[Finding] = []

    for rule in rules:
        if rule.category != "paths":
            continue
        if rule.normalized_value is None:
            continue

        norm_val = _normalize_path(rule.normalized_value)
        if not norm_val:
            continue

        # Exact match → path exists; no finding.
        if norm_val in path_evidence_values:
            continue

        # Root segment is the first component of the path
        root_segment = norm_val.split("/")[0]

        # If norm_val has no "/" it's a top-level dir (e.g. "dist") — treat as
        # no root match needed; check directly against evidence.
        has_sub_path = "/" in norm_val

        if has_sub_path:
            root_match = any(
                ev_path == root_segment or ev_path.startswith(root_segment + "/")
                for ev_path in path_evidence_values
            )
        else:
            root_match = False

        if root_match:
            # Root exists but exact sub-path does not — conservative low-confidence F03
            confidence = 0.6
            explanation = (
                f"Instruction in {rule.source_path!r} references "
                f"path {rule.normalized_value!r}, but this exact sub-path was not "
                f"found in the repository index (root directory "
                f"{root_segment!r} exists)."
            )
        else:
            confidence = 0.8
            explanation = (
                f"Instruction in {rule.source_path!r} references "
                f"path {rule.normalized_value!r}, but no matching "
                f"directory was found in the repository index."
            )

        findings.append(
            Finding(
                id="",
                type="F03",
                severity="medium",
                title=(
                    f"Stale path reference: {rule.normalized_value!r} "
                    f"not found in repository"
                ),
                explanation=explanation,
                instruction_rules=[rule.id],
                evidence_ids=path_ev_ids,
                recommended_action=(
                    f"Verify that {rule.normalized_value!r} exists or update "
                    f"the instruction to reference the correct path."
                ),
                confidence=confidence,
                deterministic=True,
            )
        )

    return findings


# ---------------------------------------------------------------------------
# F04 — Invalid/Stale Commands
# ---------------------------------------------------------------------------

# Matches patterns like: npm run test:unit  /  pnpm run build  /  yarn run dev
# Group 1: manager (npm/pnpm/yarn/bun)
# Group 2: script name
_RUN_SCRIPT_RE = re.compile(
    r"\b(?:npm|pnpm|yarn|bun)\s+run\s+([A-Za-z0-9:_.-]+)",
    re.IGNORECASE,
)


def detect_f04_invalid_commands(
    rules: list[InstructionRule],
    evidence: list[RepositoryEvidence],
) -> list[Finding]:
    """Return F04 findings for instruction commands referencing scripts that
    are absent from repository evidence.

    Only fires when at least one ``commands`` evidence item exists (guard
    against Python-only repos with no package.json).
    """
    cmd_evidence = [ev for ev in evidence if ev.category == "commands"]
    if not cmd_evidence:
        return []

    # Build a set of known script names from evidence values.
    # Evidence value for package.json scripts is the full command string
    # (e.g., "vitest run"), so we extract the base script trigger from the
    # evidence key (e.g., "test", "build", "lint") and the command values.
    known_scripts: set[str] = set()
    cmd_ev_ids: list[str] = []
    for ev in cmd_evidence:
        known_scripts.add(ev.key.lower())  # e.g. "test", "build", "lint"
        cmd_ev_ids.append(ev.id)
        # Also try to extract the first word of the command value as a script name
        # This handles aliased scripts like "vitest run" → "vitest"
        first_word = ev.value.split()[0].lower() if ev.value.strip() else ""
        if first_word:
            known_scripts.add(first_word)

    findings: list[Finding] = []

    for rule in rules:
        # Search the full rule text for run-script patterns
        matches = _RUN_SCRIPT_RE.findall(rule.text)
        for script_name in matches:
            script_lower = script_name.lower()
            if script_lower not in known_scripts:
                findings.append(
                    Finding(
                        id="",
                        type="F04",
                        severity="medium",
                        title=(
                            f"Invalid/stale command: script {script_name!r} "
                            f"not found in repository"
                        ),
                        explanation=(
                            f"Instruction in {rule.source_path!r} references "
                            f"script {script_name!r} (via `run {script_name}`), "
                            f"but this script is absent from the repository's "
                            f"known commands."
                        ),
                        instruction_rules=[rule.id],
                        evidence_ids=cmd_ev_ids,
                        recommended_action=(
                            f"Verify that script {script_name!r} exists or update "
                            f"the instruction to reference a valid script."
                        ),
                        confidence=0.85,
                        deterministic=True,
                    )
                )

    return findings
