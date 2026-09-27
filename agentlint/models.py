"""AgentLint domain models.

All six dataclasses that form the shared language for every phase.
Uses only stdlib dataclasses — no external dependencies.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any


def dataclass_to_dict(obj: Any) -> dict[str, Any]:
    """Recursively convert a dataclass instance to a JSON-serialisable plain dict."""
    return dataclasses.asdict(obj)


@dataclass
class InstructionSource:
    """A discovered agent instruction file (may or may not exist on disk)."""

    path: str
    agent_type: str  # "openai" | "claude" | "copilot" | "bob" | "cursor" | "custom"
    content_hash: str  # SHA-256 hex of file bytes; empty string when exists=False
    exists: bool

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable plain dict."""
        return dataclass_to_dict(self)


@dataclass
class InstructionRule:
    """A single rule extracted from an instruction file."""

    id: str
    source_path: str
    source_agent: str
    text: str
    category: str | None
    normalized_key: str | None
    normalized_value: str | None
    line_start: int | None
    line_end: int | None
    extraction_method: str  # "deterministic" | "bob"
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable plain dict."""
        return dataclass_to_dict(self)


@dataclass
class RepositoryEvidence:
    """A single piece of evidence detected from the repository."""

    id: str
    category: str
    key: str
    value: str
    source_path: str
    source_locator: str | None
    strength: str  # "strong" | "medium" | "weak"
    explanation: str

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable plain dict."""
        return dataclass_to_dict(self)


@dataclass
class Finding:
    """A lint finding produced by the deterministic or Bob semantic engine."""

    id: str
    type: str  # F01–F07
    severity: str  # "critical" | "high" | "medium" | "low" | "info"
    title: str
    explanation: str
    instruction_rules: list[str]  # InstructionRule ids
    evidence_ids: list[str]  # RepositoryEvidence ids
    recommended_action: str
    confidence: float
    deterministic: bool
    status: str = field(default="open")  # "open" | "approved" | "repaired" | "ignored"

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable plain dict."""
        return dataclass_to_dict(self)


@dataclass
class CanonicalPolicy:
    """Represents the .agentlint/policy.yaml canonical contract."""

    version: int
    project_name: str | None
    tooling: dict  # package_manager, test_framework, etc.
    runtime: dict
    paths: dict
    definition_of_done: list[str]
    evidence: dict

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable plain dict."""
        return dataclass_to_dict(self)


@dataclass
class ValidationResult:
    """Result of a single verification check."""

    check_id: str
    name: str
    command: str | None
    passed: bool
    duration_ms: int | None
    stdout_excerpt: str | None
    stderr_excerpt: str | None
    evidence: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable plain dict."""
        return dataclass_to_dict(self)
