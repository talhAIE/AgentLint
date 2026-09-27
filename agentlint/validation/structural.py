"""Structural validation — Phase 8.

Layer A: Re-scan the repository after repairs and verify that approved findings
are no longer present.

Layer D: Run only the cross-instruction conflict (F01) and duplicate (F05)
detectors to confirm no remaining contradictions exist in instruction files.

Public API:
    run_structural_check(repo_path, approved_finding_ids) -> list[ValidationResult]
    run_consistency_check(repo_path)                      -> list[ValidationResult]
"""

from __future__ import annotations

from pathlib import Path

from agentlint.analysis.deterministic_rules import (
    detect_f01_cross_file_conflicts,
    detect_f04_invalid_commands,
)
from agentlint.analysis.duplicates import detect_f05_duplicates
from agentlint.config import AgentLintConfigError, load_config
from agentlint.discovery.instruction_sources import discover_sources
from agentlint.evidence import collect_evidence
from agentlint.models import ValidationResult
from agentlint.parsing import extract_rules


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _fresh_scan(repo_path: Path) -> tuple[list, list, list]:
    """Run a fresh pipeline scan for *repo_path*.

    Returns (sources, evidence, rules) without writing any files.
    Returns empty lists when config cannot be loaded.
    """
    try:
        config = load_config(repo_path)
    except AgentLintConfigError:
        return [], [], []

    sources = discover_sources(repo_path, config)
    evidence = collect_evidence(repo_path)
    rules = extract_rules(sources, repo_path=repo_path)
    return sources, evidence, rules


def _finding_fingerprint(finding) -> str:
    """Return a stable content-based fingerprint for a finding.

    IDs are re-assigned on every scan so we match on (type, title, first
    instruction_rule text).  This avoids false positives when IDs shift.
    """
    return f"{finding.type}|{finding.title}"


# ---------------------------------------------------------------------------
# Layer A — Structural Re-scan
# ---------------------------------------------------------------------------


def run_structural_check(
    repo_path: Path | str,
    approved_finding_ids: list[str],
) -> list[ValidationResult]:
    """Re-scan *repo_path* and verify approved findings are gone.

    For each ID in *approved_finding_ids* the check passes when no fresh
    finding with the same ``(type, title)`` fingerprint exists.

    If *approved_finding_ids* is empty, a single informational pass result
    is returned explaining there are no approved findings to verify.

    Args:
        repo_path:             Root of the repository.
        approved_finding_ids:  IDs from ``findings.json`` with status="approved".

    Returns:
        A :class:`~agentlint.models.ValidationResult` list.
    """
    repo_path = Path(repo_path)

    if not approved_finding_ids:
        return [
            ValidationResult(
                check_id="layer-a-no-approved",
                name="Structural Re-scan",
                command=None,
                passed=True,
                duration_ms=None,
                stdout_excerpt=(
                    "No approved findings to verify. "
                    "Mark findings as 'approved' in findings.json "
                    "after reviewing repair-plan.md."
                ),
                stderr_excerpt=None,
                evidence=[],
            )
        ]

    # Load original findings to get their fingerprints
    findings_path = repo_path / ".agentlint" / "findings.json"
    original_fingerprints: dict[str, str] = {}
    if findings_path.exists():
        import json

        data = json.loads(findings_path.read_text(encoding="utf-8"))
        for f in data.get("findings", []):
            if f.get("id") in approved_finding_ids:
                fingerprint = f"{f['type']}|{f['title']}"
                original_fingerprints[f["id"]] = fingerprint

    # Run a fresh scan
    from agentlint.analysis import run_deterministic_checks

    _, evidence, rules = _fresh_scan(repo_path)
    fresh_findings = run_deterministic_checks(rules, evidence)
    fresh_fingerprints = {_finding_fingerprint(f) for f in fresh_findings}

    results: list[ValidationResult] = []
    for fid in approved_finding_ids:
        fingerprint = original_fingerprints.get(fid, f"unknown|{fid}")
        still_present = fingerprint in fresh_fingerprints
        results.append(
            ValidationResult(
                check_id=f"layer-a-{fid}",
                name=f"Structural Re-scan: {fid}",
                command=None,
                passed=not still_present,
                duration_ms=None,
                stdout_excerpt=(
                    f"PASS — finding '{fid}' no longer detected after repair."
                    if not still_present
                    else f"FAIL — finding '{fid}' is still present after repair."
                ),
                stderr_excerpt=None,
                evidence=[],
            )
        )

    return results


# ---------------------------------------------------------------------------
# Layer D — Instruction Consistency
# ---------------------------------------------------------------------------


def run_consistency_check(repo_path: Path | str) -> list[ValidationResult]:
    """Check for remaining cross-instruction conflicts and duplicates.

    Runs only F01 and F05 detectors on the current state of instruction files.

    Args:
        repo_path: Root of the repository.

    Returns:
        A :class:`~agentlint.models.ValidationResult` list — one per remaining
        conflict/duplicate finding, or a single passing result when none remain.
    """
    repo_path = Path(repo_path)

    _, evidence, rules = _fresh_scan(repo_path)

    f01_findings = detect_f01_cross_file_conflicts(rules)
    f05_findings = detect_f05_duplicates(rules)
    all_issues = f01_findings + f05_findings

    if not all_issues:
        return [
            ValidationResult(
                check_id="layer-d-consistency",
                name="Instruction Consistency",
                command=None,
                passed=True,
                duration_ms=None,
                stdout_excerpt=(
                    "PASS — no cross-instruction conflicts or duplicates detected."
                ),
                stderr_excerpt=None,
                evidence=[],
            )
        ]

    results: list[ValidationResult] = []
    for i, finding in enumerate(all_issues, start=1):
        results.append(
            ValidationResult(
                check_id=f"layer-d-issue-{i:03d}",
                name=f"Instruction Consistency: {finding.type}",
                command=None,
                passed=False,
                duration_ms=None,
                stdout_excerpt=(
                    f"FAIL — {finding.type}: {finding.title}"
                ),
                stderr_excerpt=None,
                evidence=list(finding.evidence_ids),
            )
        )

    return results
