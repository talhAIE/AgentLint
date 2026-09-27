"""Rule normalizer — Phase 3 Layer 1 deterministic parser.

Converts raw Markdown blocks (from markdown_rules.py) into
``InstructionRule`` objects, applying keyword-based category and value
detection where possible.

Layer 2 (Bob semantic interpretation) is deferred to Phase 6.
"""

from __future__ import annotations

import re
from typing import Any

from agentlint.models import InstructionRule, InstructionSource

# ── Category keyword patterns ────────────────────────────────────────────────

# Each entry: (compiled pattern, category, normalized_key)
# ORDER MATTERS — first match wins, so more-specific patterns come first.
_CATEGORY_PATTERNS: list[tuple[re.Pattern, str, str]] = [
    # Linting / formatting — checked before package_manager so "Use ESLint: npm run lint"
    # resolves to linting rather than package_manager.
    (re.compile(r"\beslint\b", re.IGNORECASE), "linting", "linter"),
    (re.compile(r"\bruff\b", re.IGNORECASE), "linting", "linter"),
    (re.compile(r"\bprettier\b", re.IGNORECASE), "linting", "formatter"),
    (re.compile(r"\bblack\b", re.IGNORECASE), "linting", "formatter"),
    (re.compile(r"\bbiome\b", re.IGNORECASE), "linting", "linter"),
    # Test frameworks — checked before package_manager
    (re.compile(r"\bvitest\b", re.IGNORECASE), "test_framework", "test_framework"),
    (re.compile(r"\bjest\b", re.IGNORECASE), "test_framework", "test_framework"),
    (re.compile(r"\bpytest\b", re.IGNORECASE), "test_framework", "test_framework"),
    (re.compile(r"\bmocha\b", re.IGNORECASE), "test_framework", "test_framework"),
    (re.compile(r"\bcypress\b", re.IGNORECASE), "test_framework", "test_framework"),
    (re.compile(r"\bplaywright\b", re.IGNORECASE), "test_framework", "test_framework"),
    # Package managers
    (re.compile(r"\bpnpm\b", re.IGNORECASE), "package_manager", "package_manager"),
    (re.compile(r"\bnpm\b", re.IGNORECASE), "package_manager", "package_manager"),
    (re.compile(r"\byarn\b", re.IGNORECASE), "package_manager", "package_manager"),
    (re.compile(r"\bbun\b", re.IGNORECASE), "package_manager", "package_manager"),
    (re.compile(r"\bpip\b", re.IGNORECASE), "package_manager", "package_manager"),
    (re.compile(r"\bpoetry\b", re.IGNORECASE), "package_manager", "package_manager"),
    # Paths — common project paths
    (re.compile(r"`?src/`?", re.IGNORECASE), "paths", "path"),
    (re.compile(r"`?tests?/`?", re.IGNORECASE), "paths", "path"),
    (re.compile(r"`?dist/`?", re.IGNORECASE), "paths", "path"),
    (re.compile(r"`?build/`?", re.IGNORECASE), "paths", "path"),
    (re.compile(r"`?lib/`?", re.IGNORECASE), "paths", "path"),
    (re.compile(r"`?docs?/`?", re.IGNORECASE), "paths", "path"),
    # Generated / do-not-edit
    (re.compile(r"\bgenerated\b", re.IGNORECASE), "generated", "generated"),
    (re.compile(r"do not edit", re.IGNORECASE), "generated", "generated"),
    (re.compile(r"do not modify", re.IGNORECASE), "generated", "generated"),
    # Runtime / language
    (re.compile(r"\bnode\.?js\b", re.IGNORECASE), "runtime", "runtime"),
    (re.compile(r"\bpython\b", re.IGNORECASE), "runtime", "runtime"),
    (re.compile(r"\bversion\b.*\d+\.\d+", re.IGNORECASE), "runtime", "runtime"),
    (re.compile(r"\bruntime\b", re.IGNORECASE), "runtime", "runtime"),
]

# ── Value extractors ─────────────────────────────────────────────────────────

# Package manager names — ordered longest first to avoid partial matches
_PM_VALUES = ["pnpm", "npm", "yarn", "bun", "poetry", "pip"]
_TF_VALUES = ["vitest", "jest", "pytest", "mocha", "cypress", "playwright"]
_LINTER_VALUES = ["eslint", "ruff", "prettier", "black", "biome"]

# Path-like pattern (token ending with /)
_PATH_LIKE_RE = re.compile(r"`?([a-zA-Z0-9_.\-]+/[a-zA-Z0-9_./\-]*)`?")

# Version pattern
_VERSION_RE = re.compile(r"\b(\d+\.\d+(?:\.\d+)?)\b")


def _extract_pm_value(text: str) -> str | None:
    lower = text.lower()
    for pm in _PM_VALUES:
        if pm in lower:
            return pm
    return None


def _extract_tf_value(text: str) -> str | None:
    lower = text.lower()
    for tf in _TF_VALUES:
        if tf in lower:
            return tf
    return None


def _extract_linting_value(text: str) -> str | None:
    lower = text.lower()
    for lnt in _LINTER_VALUES:
        if lnt in lower:
            return lnt
    return None


def _extract_path_value(text: str) -> str | None:
    m = _PATH_LIKE_RE.search(text)
    return m.group(1) if m else None


def _extract_runtime_value(text: str) -> str | None:
    m = _VERSION_RE.search(text)
    return m.group(1) if m else None


# ── Confidence table ─────────────────────────────────────────────────────────

_CONFIDENCE_MAP: dict[str, float] = {
    "code_block": 0.9,
    "bullet": 0.8,
    "numbered": 0.8,
    "heading": 0.7,
    "paragraph": 0.6,
}

_NO_KEYWORD_CONFIDENCE = 0.4


def _detect_category_and_key(
    text: str,
) -> tuple[str | None, str | None]:
    """Return (category, normalized_key) for the first matching pattern."""
    for pattern, category, key in _CATEGORY_PATTERNS:
        if pattern.search(text):
            return category, key
    return None, None


def _extract_value(
    category: str | None,
    key: str | None,
    text: str,
    block_type: str,
) -> str | None:
    """Attempt to extract a normalized value from the block text."""
    if category is None:
        return None
    if category == "package_manager":
        return _extract_pm_value(text)
    if category == "test_framework":
        return _extract_tf_value(text)
    if category == "linting":
        return _extract_linting_value(text)
    if category == "paths":
        return _extract_path_value(text)
    if category == "runtime":
        return _extract_runtime_value(text)
    if category == "generated":
        return None  # boolean-style — no value needed
    if category == "commands":
        # For code blocks, return the full interior; otherwise return the text
        if block_type == "code_block":
            # Return the first non-empty line as the "command"
            for line in text.splitlines():
                stripped = line.strip()
                if stripped:
                    return stripped
        return text
    return None


def normalize_blocks(
    blocks: list[dict[str, Any]],
    source: InstructionSource,
) -> list[InstructionRule]:
    """Convert raw Markdown blocks into ``InstructionRule`` objects.

    IDs are left as ``""`` — the aggregator (``extract_rules``) assigns them.
    """
    rules: list[InstructionRule] = []

    for block in blocks:
        block_type: str = block["block_type"]
        text: str = block["text"]
        line_start: int = block["line_start"]
        line_end: int = block["line_end"]

        category, key = _detect_category_and_key(text)

        # Confidence depends on block type; lower if no keyword was matched
        if category is not None:
            confidence = _CONFIDENCE_MAP.get(block_type, 0.6)
        else:
            confidence = _NO_KEYWORD_CONFIDENCE

        value = _extract_value(category, key, text, block_type)

        rules.append(
            InstructionRule(
                id="",  # assigned by aggregator
                source_path=str(source.path),
                source_agent=source.agent_type,
                text=text,
                category=category,
                normalized_key=key,
                normalized_value=value,
                line_start=line_start,
                line_end=line_end,
                extraction_method="deterministic",
                confidence=confidence,
            )
        )

    return rules
