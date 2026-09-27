"""Severity and confidence helpers — Phase 4.

Severity order and helper utilities used across the analysis sub-package.
"""

from __future__ import annotations

SEVERITY_ORDER: dict[str, int] = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
    "info": 4,
}


def severity_rank(severity: str) -> int:
    """Return an integer rank for *severity* (lower = more severe)."""
    return SEVERITY_ORDER.get(severity, 99)
