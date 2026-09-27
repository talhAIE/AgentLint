"""Conflict detection helpers — Phase 4.

F01 cross-file conflict detection is implemented in
:mod:`agentlint.analysis.deterministic_rules` as
``detect_f01_cross_file_conflicts``.

This module re-exports it for convenience.
"""

from __future__ import annotations

from agentlint.analysis.deterministic_rules import detect_f01_cross_file_conflicts

__all__ = ["detect_f01_cross_file_conflicts"]
