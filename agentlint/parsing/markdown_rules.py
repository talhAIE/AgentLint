"""Markdown block splitter — Phase 3 Layer 1 deterministic parser.

Splits a Markdown text into typed blocks with line numbers.
No semantic interpretation; that lives in normalization.py.
"""

from __future__ import annotations

import re

# Regex patterns
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)")
_BULLET_RE = re.compile(r"^[-*]\s+(.*)")
_NUMBERED_RE = re.compile(r"^\d+\.\s+(.*)")
_FENCE_RE = re.compile(r"^(`{3,}|~{3,})(.*)")


def parse_markdown_blocks(text: str) -> list[dict]:
    """Split *text* into typed Markdown blocks with line-number metadata.

    Returns a list of dicts, each with keys:
      - block_type: "heading" | "bullet" | "numbered" | "code_block" | "paragraph"
      - text: stripped content (without fence delimiters)
      - line_start: 1-based line number of the first line
      - line_end: 1-based line number of the last line
      - lang: language hint for code_block blocks (may be empty string); absent for other types

    Empty input → empty list.
    Blank lines between blocks are skipped (not emitted as blocks).
    Contiguous prose lines that are not headings/bullets/numbered are grouped
    into a single paragraph block.
    """
    if not text:
        return []

    lines = text.splitlines()
    blocks: list[dict] = []

    # Paragraph accumulator
    para_lines: list[str] = []
    para_start: int = 0

    def flush_paragraph() -> None:
        """Emit any accumulated paragraph lines as a single block."""
        if para_lines:
            blocks.append(
                {
                    "block_type": "paragraph",
                    "text": " ".join(para_lines),
                    "line_start": para_start,
                    "line_end": para_start + len(para_lines) - 1,
                }
            )
            para_lines.clear()

    i = 0
    while i < len(lines):
        line = lines[i]
        lineno = i + 1  # 1-based

        # ── Code fence ──────────────────────────────────────────────────────
        fence_match = _FENCE_RE.match(line)
        if fence_match:
            flush_paragraph()
            fence_char = fence_match.group(1)
            lang = fence_match.group(2).strip()
            fence_start = lineno
            interior: list[str] = []
            i += 1
            # Collect interior lines until we find a closing fence of same type
            while i < len(lines):
                closing = lines[i]
                if closing.strip() == fence_char or closing.strip().startswith(fence_char):
                    # closing fence found
                    fence_end = i + 1
                    i += 1
                    break
                interior.append(lines[i])
                i += 1
            else:
                # Unclosed fence — treat the rest as code block
                fence_end = len(lines)

            blocks.append(
                {
                    "block_type": "code_block",
                    "text": "\n".join(interior).strip(),
                    "line_start": fence_start,
                    "line_end": fence_end,
                    "lang": lang,
                }
            )
            continue

        # ── Blank line ───────────────────────────────────────────────────────
        if not line.strip():
            flush_paragraph()
            i += 1
            continue

        # ── Heading ──────────────────────────────────────────────────────────
        heading_match = _HEADING_RE.match(line)
        if heading_match:
            flush_paragraph()
            blocks.append(
                {
                    "block_type": "heading",
                    "text": heading_match.group(2).strip(),
                    "line_start": lineno,
                    "line_end": lineno,
                }
            )
            i += 1
            continue

        # ── Bullet ───────────────────────────────────────────────────────────
        bullet_match = _BULLET_RE.match(line)
        if bullet_match:
            flush_paragraph()
            blocks.append(
                {
                    "block_type": "bullet",
                    "text": bullet_match.group(1).strip(),
                    "line_start": lineno,
                    "line_end": lineno,
                }
            )
            i += 1
            continue

        # ── Numbered ─────────────────────────────────────────────────────────
        numbered_match = _NUMBERED_RE.match(line)
        if numbered_match:
            flush_paragraph()
            blocks.append(
                {
                    "block_type": "numbered",
                    "text": numbered_match.group(1).strip(),
                    "line_start": lineno,
                    "line_end": lineno,
                }
            )
            i += 1
            continue

        # ── Paragraph (prose line) ────────────────────────────────────────────
        if not para_lines:
            para_start = lineno
        para_lines.append(line.strip())
        i += 1

    flush_paragraph()
    return blocks
