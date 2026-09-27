"""Duplicate rule detector — Phase 4 (F05).

Finds exact duplicate rules within or across instruction files after
whitespace/case/punctuation normalization and hashing.
"""

from __future__ import annotations

import re
from collections import defaultdict

from agentlint.models import Finding, InstructionRule

# Characters to strip when computing a rule fingerprint.
_PUNCT_STRIP_RE = re.compile(r"[^\w\s]")
_WHITESPACE_RE = re.compile(r"\s+")

# Minimum rule text length to bother comparing (suppress heading noise).
_MIN_TEXT_LENGTH = 10


def _fingerprint(text: str) -> str:
    """Return a normalized fingerprint for *text*.

    Steps:
    1. Lowercase.
    2. Strip non-word, non-whitespace characters (punctuation).
    3. Collapse whitespace.
    4. Strip leading/trailing whitespace.
    """
    lowered = text.lower()
    no_punct = _PUNCT_STRIP_RE.sub(" ", lowered)
    collapsed = _WHITESPACE_RE.sub(" ", no_punct).strip()
    return collapsed


def detect_f05_duplicates(rules: list[InstructionRule]) -> list[Finding]:
    """Return F05 findings for rules that are exact duplicates after
    normalization.

    Groups rules by fingerprint.  Any group with ≥ 2 members whose
    text is longer than ``_MIN_TEXT_LENGTH`` after normalization emits
    one F05 Finding listing all duplicated rule IDs.

    Severity = "low".
    Confidence = 1.0 (exact normalized match).
    """
    # Group rules by fingerprint
    groups: dict[str, list[InstructionRule]] = defaultdict(list)
    for rule in rules:
        fp = _fingerprint(rule.text)
        if len(fp) >= _MIN_TEXT_LENGTH:
            groups[fp].append(rule)

    findings: list[Finding] = []
    for fp, dupes in groups.items():
        if len(dupes) < 2:
            continue

        rule_ids = [r.id for r in dupes]
        source_paths = sorted({r.source_path for r in dupes})
        # Use the shared normalized text as the title excerpt (first 60 chars).
        excerpt = fp[:60] + ("..." if len(fp) > 60 else "")

        findings.append(
            Finding(
                id="",  # assigned by aggregator
                type="F05",
                severity="low",
                title=f"Duplicate instruction: {len(dupes)} identical rules found",
                explanation=(
                    f"The following rules contain identical content "
                    f"(after normalization): {rule_ids}. "
                    f"Sources: {', '.join(source_paths)}. "
                    f"Normalized text: \"{excerpt}\"."
                ),
                instruction_rules=rule_ids,
                evidence_ids=[],
                recommended_action=(
                    "Remove or consolidate duplicate instructions to reduce "
                    "maintenance burden and avoid conflicting updates."
                ),
                confidence=1.0,
                deterministic=True,
            )
        )

    return findings
