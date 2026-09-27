"""Policy diff — Phase 7.

Generates per-finding repair items and the human-readable ``repair-plan.md``
file.  This module operates at the *logical* level: it decides *what* to
change.  Actual text manipulation is in :mod:`agentlint.policy.adapters`.

No repairs are applied here.  Every item requires explicit human approval
(see AgentLintplan.md §4.2 and §Phase 7).

Public API:
    RepairItem                                               — dataclass
    generate_repair_items(findings, rules, evidence)         -> list[RepairItem]
    format_repair_plan(items)                                -> str
    write_repair_plan(repo_path, items)                      -> Path
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agentlint.models import Finding, InstructionRule, RepositoryEvidence


# ---------------------------------------------------------------------------
# RepairItem dataclass
# ---------------------------------------------------------------------------


@dataclass
class RepairItem:
    """A single proposed repair action for one finding.

    Attributes:
        finding_id:           ID of the :class:`~agentlint.models.Finding` this
                              repair addresses.
        target_file:          Path of the instruction file to modify.
        original_text:        The exact text to replace (empty string if not
                              safely determinable).
        proposed_text:        The replacement text (empty string if
                              ``requires_manual_review`` is ``True``).
        evidence_sources:     Human-readable list of evidence references that
                              justify this repair (e.g. ``"pnpm-lock.yaml"``).
        reason:               Short explanation of why this repair is needed.
        expected_effect:      What the repair will fix for agents.
        requires_manual_review: ``True`` when the repair cannot be expressed as
                              a safe, exact text substitution.
    """

    finding_id: str
    target_file: str
    original_text: str
    proposed_text: str
    evidence_sources: list[str] = field(default_factory=list)
    reason: str = ""
    expected_effect: str = ""
    requires_manual_review: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable plain dict."""
        return dataclasses.asdict(self)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _rules_by_id(rules: list[InstructionRule]) -> dict[str, InstructionRule]:
    return {r.id: r for r in rules}


def _evidence_by_id(evidence: list[RepositoryEvidence]) -> dict[str, RepositoryEvidence]:
    return {e.id: e for e in evidence}


def _evidence_sources_for_ids(
    ev_ids: list[str],
    ev_index: dict[str, RepositoryEvidence],
) -> list[str]:
    """Build a deduplicated list of human-readable evidence source strings."""
    seen: list[str] = []
    for eid in ev_ids:
        ev = ev_index.get(eid)
        if ev is None:
            continue
        ref = ev.source_path
        if ev.source_locator:
            ref = f"{ref}#{ev.source_locator}"
        if ref not in seen:
            seen.append(ref)
    return seen


def _best_evidence_value(
    category: str,
    ev_ids: list[str],
    ev_index: dict[str, RepositoryEvidence],
) -> str | None:
    """Return the *value* field of the strongest evidence for *category* from
    the given evidence ID list.

    For package_manager evidence the ``key`` field is ``"package_manager"``
    and the ``value`` field is the detected tool (e.g. ``"pnpm"``).
    We always want the human-readable tool name, so we use ``.value``.

    Returns ``None`` when no matching evidence is found.
    """
    _RANK = {"strong": 0, "medium": 1, "weak": 2}
    candidates = [
        ev_index[eid]
        for eid in ev_ids
        if eid in ev_index and ev_index[eid].category == category
    ]
    if not candidates:
        return None
    best = min(candidates, key=lambda e: _RANK.get(e.strength, 99))
    return best.value


# ---------------------------------------------------------------------------
# Finding-type handlers — each returns a RepairItem or None
# ---------------------------------------------------------------------------


def _repair_f02(
    finding: Finding,
    rule_index: dict[str, InstructionRule],
    ev_index: dict[str, RepositoryEvidence],
) -> RepairItem | None:
    """F02 — Instruction vs repository mismatch.

    Propose replacing the stale tool name in each affected rule with the
    evidence-backed name.
    """
    if not finding.instruction_rules:
        return None

    rule_id = finding.instruction_rules[0]
    rule = rule_index.get(rule_id)
    if rule is None or rule.normalized_value is None:
        return None

    # Determine what the repo actually uses
    repo_value = _best_evidence_value(
        rule.category or "", finding.evidence_ids, ev_index
    )
    # Fall back: try all categories in the finding's evidence — use .value for
    # human-readable tool name (e.g. "pnpm"), not .key (e.g. "package_manager")
    if repo_value is None:
        all_ev = [ev_index[eid] for eid in finding.evidence_ids if eid in ev_index]
        if all_ev:
            _RANK = {"strong": 0, "medium": 1, "weak": 2}
            best = min(all_ev, key=lambda e: _RANK.get(e.strength, 99))
            repo_value = best.value

    if repo_value is None:
        # Cannot determine the correct value — flag for manual review
        return RepairItem(
            finding_id=finding.id,
            target_file=rule.source_path,
            original_text=rule.text,
            proposed_text="",
            evidence_sources=_evidence_sources_for_ids(finding.evidence_ids, ev_index),
            reason=finding.explanation,
            expected_effect=(
                f"Instruction will match the repository's actual {rule.category}."
            ),
            requires_manual_review=True,
        )

    stale_value = rule.normalized_value
    proposed_text = rule.text.replace(stale_value, repo_value)
    if proposed_text == rule.text:
        # Case-insensitive replacement
        import re
        proposed_text = re.sub(
            re.escape(stale_value),
            repo_value,
            rule.text,
            flags=re.IGNORECASE,
        )

    return RepairItem(
        finding_id=finding.id,
        target_file=rule.source_path,
        original_text=rule.text,
        proposed_text=proposed_text,
        evidence_sources=_evidence_sources_for_ids(finding.evidence_ids, ev_index),
        reason=finding.explanation,
        expected_effect=(
            f"Instruction will reference '{repo_value}' instead of "
            f"'{stale_value}', matching repository evidence."
        ),
        requires_manual_review=(proposed_text == rule.text),
    )


def _repair_f01(
    finding: Finding,
    rule_index: dict[str, InstructionRule],
    ev_index: dict[str, RepositoryEvidence],
) -> RepairItem | None:
    """F01 — Cross-instruction conflict.

    These almost always require manual review because there is no single
    authoritative source to prefer without additional human input.
    """
    if not finding.instruction_rules:
        return None

    rule_id = finding.instruction_rules[0]
    rule = rule_index.get(rule_id)
    if rule is None:
        return None

    return RepairItem(
        finding_id=finding.id,
        target_file=rule.source_path,
        original_text=rule.text,
        proposed_text="",
        evidence_sources=_evidence_sources_for_ids(finding.evidence_ids, ev_index),
        reason=finding.explanation,
        expected_effect=(
            "Conflicting instructions will be reconciled so agents receive "
            "consistent guidance."
        ),
        requires_manual_review=True,
    )


def _repair_f03(
    finding: Finding,
    rule_index: dict[str, InstructionRule],
    ev_index: dict[str, RepositoryEvidence],
) -> RepairItem | None:
    """F03 — Stale path reference.

    Propose removing the stale path reference from the rule.
    """
    if not finding.instruction_rules:
        return None

    rule_id = finding.instruction_rules[0]
    rule = rule_index.get(rule_id)
    if rule is None:
        return None

    return RepairItem(
        finding_id=finding.id,
        target_file=rule.source_path,
        original_text=rule.text,
        proposed_text="",
        evidence_sources=_evidence_sources_for_ids(finding.evidence_ids, ev_index),
        reason=finding.explanation,
        expected_effect=(
            "Stale path reference will be removed or updated so agents are not "
            "misled by non-existent directories."
        ),
        requires_manual_review=True,
    )


def _repair_f04(
    finding: Finding,
    rule_index: dict[str, InstructionRule],
    ev_index: dict[str, RepositoryEvidence],
) -> RepairItem | None:
    """F04 — Invalid/stale command.

    Propose correcting the command referenced in the rule.
    """
    if not finding.instruction_rules:
        return None

    rule_id = finding.instruction_rules[0]
    rule = rule_index.get(rule_id)
    if rule is None:
        return None

    return RepairItem(
        finding_id=finding.id,
        target_file=rule.source_path,
        original_text=rule.text,
        proposed_text="",
        evidence_sources=_evidence_sources_for_ids(finding.evidence_ids, ev_index),
        reason=finding.explanation,
        expected_effect=(
            "Invalid command reference will be corrected so agents run the "
            "right commands."
        ),
        requires_manual_review=True,
    )


def _repair_f05(
    finding: Finding,
    rule_index: dict[str, InstructionRule],
    ev_index: dict[str, RepositoryEvidence],
) -> RepairItem | None:
    """F05 — Exact duplicate rule.

    Propose removing the second occurrence (keep the first).
    The duplicate is the last rule_id in the finding (deterministic from Phase 4).
    """
    if len(finding.instruction_rules) < 2:
        return None

    # The duplicate is the second (or later) occurrence
    dup_rule_id = finding.instruction_rules[-1]
    rule = rule_index.get(dup_rule_id)
    if rule is None:
        return None

    first_rule_id = finding.instruction_rules[0]
    first_rule = rule_index.get(first_rule_id)
    first_source = first_rule.source_path if first_rule else "another file"

    return RepairItem(
        finding_id=finding.id,
        target_file=rule.source_path,
        original_text=rule.text,
        proposed_text="",  # remove the line
        evidence_sources=[first_source],
        reason=(
            f"Rule is an exact duplicate of a rule in {first_source!r}. "
            f"Duplicate rules cause confusion for agents."
        ),
        expected_effect=(
            "Duplicate instruction will be removed; the canonical version "
            f"remains in {first_source!r}."
        ),
        requires_manual_review=False,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


_REPAIR_HANDLERS = {
    "F01": _repair_f01,
    "F02": _repair_f02,
    "F03": _repair_f03,
    "F04": _repair_f04,
    "F05": _repair_f05,
}


def generate_repair_items(
    findings: list[Finding],
    rules: list[InstructionRule],
    evidence: list[RepositoryEvidence],
) -> list[RepairItem]:
    """Generate one :class:`RepairItem` per actionable finding.

    Only findings of types F01–F05 produce repair items.  F06/F07 semantic
    findings (from Bob) are excluded because they lack the deterministic rule
    linkage needed for safe automated repair proposals.

    Findings with ``status="ignored"`` are skipped.

    Args:
        findings: All findings (deterministic + semantic).
        rules:    Parsed instruction rules.
        evidence: Repository evidence.

    Returns:
        List of :class:`RepairItem` objects, one per actionable finding.
        Items preserve the ordering of *findings*.
    """
    rule_index = _rules_by_id(rules)
    ev_index = _evidence_by_id(evidence)

    items: list[RepairItem] = []
    for finding in findings:
        if finding.status == "ignored":
            continue
        handler = _REPAIR_HANDLERS.get(finding.type)
        if handler is None:
            continue
        item = handler(finding, rule_index, ev_index)
        if item is not None:
            items.append(item)

    return items


def format_repair_plan(items: list[RepairItem]) -> str:
    """Render *items* as a human-readable Markdown repair plan.

    Matches the example format in AgentLintplan.md §Phase 7::

        1. AGENTS.md
           Replace "Use npm" with "Use pnpm".
           Evidence: pnpm-lock.yaml
           Reason: ...
           Expected effect: ...

    Each item also carries an ``[APPROVAL REQUIRED]`` notice, and manual-review
    items are clearly flagged.

    Args:
        items: Repair items from :func:`generate_repair_items`.

    Returns:
        A Markdown string ready to write to ``repair-plan.md``.
    """
    if not items:
        return (
            "# Repair Plan\n\n"
            "No repair items generated. "
            "All findings are clean or require no instruction changes.\n\n"
            "> **Approval required before any changes are applied.**\n"
        )

    lines: list[str] = [
        "# Repair Plan",
        "",
        "> **Approval required before any changes are applied.**",
        "> Review each item and mark findings as `approved` in `findings.json`",
        "> before running `agentlint validate`.",
        "",
    ]

    for i, item in enumerate(items, start=1):
        target_name = Path(item.target_file).name
        lines.append(f"## {i}. {target_name}  (finding: `{item.finding_id}`)")
        lines.append("")

        if item.requires_manual_review:
            lines.append("**[MANUAL REVIEW REQUIRED]**")
            lines.append("")

        if item.original_text:
            lines.append("**Original:**")
            lines.append("")
            lines.append("```")
            lines.append(item.original_text.strip())
            lines.append("```")
            lines.append("")

        if item.proposed_text:
            lines.append("**Proposed:**")
            lines.append("")
            lines.append("```")
            lines.append(item.proposed_text.strip())
            lines.append("```")
            lines.append("")
        elif not item.requires_manual_review:
            lines.append("**Proposed:** *(remove this line)*")
            lines.append("")

        if item.evidence_sources:
            lines.append(f"Evidence: {', '.join(item.evidence_sources)}")
            lines.append("")

        if item.reason:
            lines.append(f"Reason: {item.reason}")
            lines.append("")

        if item.expected_effect:
            lines.append(f"Expected effect: {item.expected_effect}")
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def write_repair_plan(
    repo_path: Path,
    items: list[RepairItem],
) -> Path:
    """Write ``.agentlint/repair-plan.md`` inside *repo_path*.

    Args:
        repo_path: Root of the scanned repository.
        items:     Repair items from :func:`generate_repair_items`.

    Returns:
        The :class:`~pathlib.Path` of the written file.
    """
    output_dir = Path(repo_path) / ".agentlint"
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / "repair-plan.md"
    output_path.write_text(format_repair_plan(items), encoding="utf-8")
    return output_path
