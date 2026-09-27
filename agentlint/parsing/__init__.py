"""Parsing sub-package public API — Phase 3.

Public entry points:
  extract_rules(sources)           → list[InstructionRule]
  write_rules_json(repo_path, rules) → Path
"""

from __future__ import annotations

import json
from pathlib import Path

import agentlint
from agentlint.models import InstructionRule, InstructionSource
from agentlint.parsing.markdown_rules import parse_markdown_blocks
from agentlint.parsing.normalization import normalize_blocks


def _source_abbrev(source: InstructionSource) -> str:
    """Return a short stable abbreviation of the instruction source filename.

    e.g.  CLAUDE.md           → "claude"
          AGENTS.md           → "agents"
          copilot-instructions.md → "copilo"
    """
    stem = Path(source.path).stem.lower()  # e.g. "CLAUDE" → "claude"
    return stem[:6]


def extract_rules(
    sources: list[InstructionSource],
    repo_path: Path | None = None,
) -> list[InstructionRule]:
    """Parse all existing instruction sources and return ``InstructionRule`` objects.

    Rules are processed in source order.  Each source uses its own counter
    so that IDs stay stable regardless of how many sources exist.

    Non-existent sources are silently skipped.

    Args:
        sources:   The discovered instruction sources (from ``discover_sources``).
        repo_path: Optional base directory used to resolve relative paths stored
                   in ``InstructionSource.path``.  When ``None``, paths are used
                   as-is and must already be absolute or resolvable from the CWD.
    """
    all_rules: list[InstructionRule] = []

    for source in sources:
        if not source.exists:
            continue

        raw_path = Path(source.path)
        if repo_path is not None and not raw_path.is_absolute():
            file_path = repo_path / raw_path
        else:
            file_path = raw_path

        try:
            text = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            # Unreadable file — skip without crashing
            continue

        blocks = parse_markdown_blocks(text)
        rules = normalize_blocks(blocks, source)

        abbrev = _source_abbrev(source)
        for idx, rule in enumerate(rules, start=1):
            rule.id = f"rule-{abbrev}-{idx:03d}"

        all_rules.extend(rules)

    return all_rules


def write_rules_json(repo_path: Path, rules: list[InstructionRule]) -> Path:
    """Write ``.agentlint/rules.json`` inside *repo_path*.

    Schema::

        {
          "agentlint_version": "0.1.0",
          "repo_path": "...",
          "rules": [ { ...InstructionRule fields... } ]
        }

    Returns the path of the written file.
    """
    output_dir = repo_path / ".agentlint"
    output_dir.mkdir(exist_ok=True)

    payload = {
        "agentlint_version": agentlint.__version__,
        "repo_path": str(repo_path.resolve()),
        "rules": [r.to_dict() for r in rules],
    }

    rules_json_path = output_dir / "rules.json"
    rules_json_path.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )
    return rules_json_path


__all__ = ["extract_rules", "write_rules_json"]
