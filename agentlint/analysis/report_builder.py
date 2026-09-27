"""Report builder — Phase 4.

Formats findings for human-readable CLI output.
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
