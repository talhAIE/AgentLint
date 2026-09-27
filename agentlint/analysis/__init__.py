"""Analysis sub-package public API — Phase 4.

Public entry points:
    run_deterministic_checks(rules, evidence)   → list[Finding]
    write_findings_json(repo_path, findings)    → Path

Phase 10 adds:
    SEVERITY_ORDER  — exported dict used by the CI exit-code logic in cli.py
"""

from __future__ import annotations

import json
from pathlib import Path

import agentlint
from agentlint.analysis.deterministic_rules import (
    detect_f01_cross_file_conflicts,
    detect_f02_mismatch,
    detect_f03_stale_paths,
    detect_f04_invalid_commands,
)
from agentlint.analysis.duplicates import detect_f05_duplicates
from agentlint.models import Finding, InstructionRule, RepositoryEvidence

# Severity sort order (lower = more severe → sort ascending for highest first).
# Exported as SEVERITY_ORDER so callers (cli.py, report_builder.py) can import it.
SEVERITY_ORDER: dict[str, int] = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
    "info": 4,
}


def _assign_finding_ids(findings: list[Finding]) -> None:
    """Assign sequential IDs to *findings* in-place.

    ID scheme: ``"find-{type_lower}-{seq:03d}"`` where *seq* restarts per type.
    e.g. ``"find-f02-001"``, ``"find-f02-002"``, ``"find-f01-001"``.
    """
    counters: dict[str, int] = {}
    for finding in findings:
        type_key = finding.type.lower()
        n = counters.get(type_key, 0) + 1
        counters[type_key] = n
        finding.id = f"find-{type_key}-{n:03d}"


def run_deterministic_checks(
    rules: list[InstructionRule],
    evidence: list[RepositoryEvidence],
) -> list[Finding]:
    """Run all deterministic finding detectors and return sorted findings.

    Detectors run in order: F01 → F02 → F03 → F04 → F05.
    Finding IDs are assigned sequentially per type after all detectors complete.
    Results are sorted by severity (critical → info) then by finding ID.

    Args:
        rules:    Parsed instruction rules from Phase 3.
        evidence: Repository evidence items from Phase 2.

    Returns:
        Combined list of :class:`~agentlint.models.Finding` objects with IDs
        assigned.  Always deterministic for the same inputs.
    """
    all_findings: list[Finding] = []

    all_findings.extend(detect_f01_cross_file_conflicts(rules))
    all_findings.extend(detect_f02_mismatch(rules, evidence))
    all_findings.extend(detect_f03_stale_paths(rules, evidence))
    all_findings.extend(detect_f04_invalid_commands(rules, evidence))
    all_findings.extend(detect_f05_duplicates(rules))

    # Sort by severity (most severe first), then by finding type for stability.
    all_findings.sort(
        key=lambda f: (SEVERITY_ORDER.get(f.severity, 99), f.type)
    )

    _assign_finding_ids(all_findings)

    return all_findings


def write_findings_json(
    repo_path: Path,
    findings: list[Finding],
) -> Path:
    """Write ``.agentlint/findings.json`` inside *repo_path*.

    Schema::

        {
          "agentlint_version": "0.1.0",
          "repo_path": "...",
          "findings": [ { ...Finding fields... } ]
        }

    Returns the path of the written file.
    """
    output_dir = Path(repo_path) / ".agentlint"
    output_dir.mkdir(exist_ok=True)

    payload = {
        "agentlint_version": agentlint.__version__,
        "repo_path": str(Path(repo_path).resolve()),
        "findings": [f.to_dict() for f in findings],
    }

    findings_json_path = output_dir / "findings.json"
    findings_json_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return findings_json_path


__all__ = ["run_deterministic_checks", "write_findings_json", "SEVERITY_ORDER"]
