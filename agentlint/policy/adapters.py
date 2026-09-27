"""Policy adapters — Phase 7/8.

File-level text manipulation helpers for repair previews and applying repairs.

This module is intentionally kept free of file I/O: callers pass file
content as strings.  Only the allowed target files may ever be repaired
(matching the custom-mode ``fileRegex`` in ``.bob/custom_modes.yaml``):

* ``AGENTS.md``
* ``CLAUDE.md``
* ``.github/copilot-instructions.md``
* ``.bob/**/*.md``
* ``.cursor/**/*.md``
* ``.agentlint/**``

``apply_repair`` requires explicit human approval before being called:
callers must check ``Finding.status == "approved"`` and verify the target
file is in the allowed set.  Repairs that ``requires_manual_review=True``
cannot be applied programmatically and raise :class:`ValueError`.

Public API:
    build_text_preview(item, file_content)  -> str
    apply_repair(item, file_content)        -> str
"""

from __future__ import annotations

import re
from pathlib import Path

from agentlint.policy.diff import RepairItem

# Allowed target paths — matches the ``fileRegex`` in custom_modes.yaml.
# Enforced by ``_is_allowed_target``; violations raise ``ValueError``.
_ALLOWED_PATTERNS: list[re.Pattern] = [
    re.compile(r"(?:^|[/\\])AGENTS(?:[-_\w]*)\.md$"),
    re.compile(r"(?:^|[/\\])CLAUDE\.md$"),
    re.compile(r"\.github[/\\]copilot-instructions\.md$"),
    re.compile(r"\.bob[/\\]"),
    re.compile(r"\.cursor[/\\]"),
    re.compile(r"\.agentlint[/\\]"),
]


def _is_allowed_target(target_file: str) -> bool:
    """Return ``True`` if *target_file* is within the allowed edit targets.

    This check enforces the hard architectural rule that Phase 7 (and
    future repair phases) may only touch instruction and policy files,
    never production code.
    """
    normalized = target_file.replace("\\", "/")
    for pattern in _ALLOWED_PATTERNS:
        if pattern.search(normalized):
            return True
    return False


def build_text_preview(item: RepairItem, file_content: str) -> str:
    """Return a fenced before/after diff string for display.

    If the ``original_text`` from *item* is found verbatim in *file_content*
    the preview shows a ``--- original`` / ``+++ proposed`` block.

    If ``requires_manual_review`` is ``True`` a ``[MANUAL REVIEW REQUIRED]``
    block is returned instead, describing the change that must be made.

    Args:
        item:         The repair item describing the proposed change.
        file_content: Current text content of the target instruction file.

    Returns:
        A Markdown-formatted preview string.
    """
    if item.requires_manual_review:
        lines: list[str] = [
            "**[MANUAL REVIEW REQUIRED]**",
            "",
            "This repair cannot be expressed as a safe, exact text substitution.",
            "Please review the following guidance and apply the change manually:",
            "",
            f"- **File:** `{item.target_file}`",
            f"- **Finding:** `{item.finding_id}`",
        ]
        if item.original_text:
            lines += [
                "",
                "**Original text to review:**",
                "```",
                item.original_text.strip(),
                "```",
            ]
        if item.reason:
            lines += ["", f"**Reason:** {item.reason}"]
        if item.expected_effect:
            lines += [f"**Expected effect:** {item.expected_effect}"]
        return "\n".join(lines)

    # --- Deterministic preview ---
    if item.original_text and item.original_text in file_content:
        original_block = item.original_text.strip()
        proposed_block = item.proposed_text.strip() if item.proposed_text else "(remove this line)"

        return "\n".join([
            "--- original",
            "```",
            original_block,
            "```",
            "",
            "+++ proposed",
            "```",
            proposed_block,
            "```",
        ])

    # Original text not found in file — cannot produce a precise diff
    header = f"<!-- original_text not found verbatim in {Path(item.target_file).name} -->"
    if item.original_text:
        return "\n".join([
            header,
            "--- original (not found verbatim)",
            "```",
            item.original_text.strip(),
            "```",
            "",
            "+++ proposed",
            "```",
            item.proposed_text.strip() if item.proposed_text else "(remove this line)",
            "```",
        ])
    return header


def apply_repair(item: RepairItem, file_content: str) -> str:
    """Apply *item*'s repair to *file_content* and return the modified content.

    This function performs an in-memory text substitution only.  It never
    writes to disk; the caller is responsible for writing the returned string
    back to the target file.

    Constraints enforced here:

    * Target file must be in the allowed set (``_is_allowed_target``).
    * Items with ``requires_manual_review=True`` cannot be applied
      programmatically and always raise :class:`ValueError`.
    * When ``proposed_text`` is empty, the line containing ``original_text``
      is removed entirely (delete-the-line semantic).
    * When both texts are present, the first occurrence of ``original_text``
      in *file_content* is replaced with ``proposed_text``.

    Args:
        item:         The approved :class:`~agentlint.policy.diff.RepairItem`.
        file_content: Current text content of the target instruction file.

    Returns:
        The modified file content as a string.

    Raises:
        ValueError: If the target file is not in the allowed set, or if
                    ``requires_manual_review`` is ``True``, or if
                    ``original_text`` is empty.
    """
    if not _is_allowed_target(item.target_file):
        raise ValueError(
            f"apply_repair: target file '{item.target_file}' is not in the "
            "allowed set of instruction/policy files. "
            "Repairs may only target AGENTS.md, CLAUDE.md, "
            ".github/copilot-instructions.md, .bob/, .cursor/, or .agentlint/."
        )

    if item.requires_manual_review:
        raise ValueError(
            f"apply_repair: finding '{item.finding_id}' requires manual review "
            "and cannot be applied programmatically. "
            "Please apply the change described in repair-plan.md by hand."
        )

    if not item.original_text:
        raise ValueError(
            f"apply_repair: finding '{item.finding_id}' has no original_text; "
            "cannot determine what to replace."
        )

    # --- Delete-the-line semantic: proposed_text is empty → remove the line ---
    if not item.proposed_text:
        lines = file_content.splitlines(keepends=True)
        new_lines: list[str] = []
        removed = False
        for line in lines:
            if not removed and item.original_text.strip() in line:
                removed = True  # drop this line
                continue
            new_lines.append(line)
        return "".join(new_lines)

    # --- Text-replacement semantic ---
    if item.original_text not in file_content:
        # Try case-insensitive replacement as a fallback
        import re as _re
        new_content = _re.sub(
            _re.escape(item.original_text),
            item.proposed_text,
            file_content,
            count=1,
            flags=_re.IGNORECASE,
        )
        return new_content

    return file_content.replace(item.original_text, item.proposed_text, 1)
