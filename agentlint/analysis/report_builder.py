"""Report builder — Phase 4.

Formats findings for human-readable CLI output.

Phase 10 adds:
    format_ci_failure_block(findings, threshold_severity)
        Produces the machine-friendly block printed to stdout when
        ``agentlint scan --fail-on-severity <level>`` detects drift.
"""

from __future__ import annotations

from collections import Counter

from agentlint.models import Finding


def format_findings_summary(findings: list[Finding]) -> str:
    """Return a multi-line human-readable summary of *findings*.

    Example output::

        Findings: 3 finding(s) -- 0 critical, 2 high, 1 medium, 0 low, 0 info
          F02 (mismatch): 2
          F03 (stale path): 1

    Args:
        findings: The list of :class:`~agentlint.models.Finding` objects.

    Returns:
        A formatted string ready for ``typer.echo``.
    """
    if not findings:
        return "Findings: 0 finding(s) -- clean"

    sev_counts: Counter[str] = Counter(f.severity for f in findings)
    type_counts: Counter[str] = Counter(f.type for f in findings)

    sev_parts = [
        f"{sev_counts.get(s, 0)} {s}"
        for s in ("critical", "high", "medium", "low", "info")
    ]
    header = f"Findings: {len(findings)} finding(s) -- {', '.join(sev_parts)}"

    type_labels = {
        "F01": "cross-file conflict",
        "F02": "mismatch",
        "F03": "stale path",
        "F04": "invalid command",
        "F05": "duplicate",
    }
    lines = [header]
    for ftype, count in sorted(type_counts.items()):
        label = type_labels.get(ftype, ftype.lower())
        lines.append(f"  {ftype} ({label}): {count}")

    return "\n".join(lines)


def format_ci_failure_block(
    findings: list[Finding],
    threshold_severity: str,
) -> str:
    """Return a human-readable CI failure block for high-severity findings.

    Only findings whose severity is at or above *threshold_severity* are
    included.  The output format matches the spec example::

        AgentLint: FAIL

        High-severity instruction drift detected.

        AGENTS.md says: npm
        Repository evidence: pnpm

    One detail line is emitted per qualifying finding using the finding's
    ``title`` field (which is always a concise, human-readable sentence).

    Args:
        findings:           All findings at or above the threshold (pre-filtered).
        threshold_severity: The severity level used (e.g. ``"high"``).

    Returns:
        A formatted multi-line string ready for ``typer.echo``.
    """
    lines: list[str] = [
        "AgentLint: FAIL",
        "",
        f"{threshold_severity.capitalize()}-severity instruction drift detected.",
    ]
    for f in findings:
        lines.append("")
        lines.append(f.title)

    return "\n".join(lines)


def format_ci_pass_block() -> str:
    """Return a one-line CI pass message.

    Printed by ``agentlint scan --fail-on-severity`` when no qualifying
    findings are present::

        AgentLint: PASS

    Returns:
        A single-line string ready for ``typer.echo``.
    """
    return "AgentLint: PASS"
