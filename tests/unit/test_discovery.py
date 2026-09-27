"""Unit tests for agentlint.discovery.instruction_sources (Phase 1).

Tests:
- test_zero_instruction_files — empty dir → 6 built-ins all exists=False
- test_one_file_agents_md — AGENTS.md present → exactly that source exists=True
- test_one_file_claude_md — CLAUDE.md present → claude source exists=True
- test_multiple_files — AGENTS.md + CLAUDE.md → both exist, stable order
- test_bob_mode_files — .bob/rules-* files → discovered
- test_extra_instruction_paths_config — extra path → discovered as "custom"
- test_missing_configured_path — extra path missing → exists=False, no exception
- test_content_hash_set — created file → non-empty SHA-256 hex hash
- test_content_hash_empty_when_missing — missing file → hash is ""
- test_stable_ordering — two calls same result
- test_extra_paths_alphabetical_order — extras sorted alphabetically
- test_copilot_instructions — .github/copilot-instructions.md discovered
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from agentlint.config import AgentLintConfig
from agentlint.discovery.instruction_sources import discover_sources
from agentlint.models import InstructionSource

# Number of built-in candidates (AGENTS.md, CLAUDE.md, copilot, 3 bob modes).
NUM_BUILTINS = 6


def _config(extra: list[str] | None = None) -> AgentLintConfig:
    """Helper: build an AgentLintConfig."""
    return AgentLintConfig(extra_instruction_paths=extra or [])


# ---------------------------------------------------------------------------
# Built-in discovery
# ---------------------------------------------------------------------------

def test_zero_instruction_files(tmp_path: Path) -> None:
    """Empty directory → all 6 built-in sources returned, all exists=False."""
    sources = discover_sources(tmp_path, _config())
    assert len(sources) == NUM_BUILTINS
    assert all(not s.exists for s in sources)


def test_one_file_agents_md(tmp_path: Path) -> None:
    """AGENTS.md present → exactly one source has exists=True."""
    (tmp_path / "AGENTS.md").write_text("# Agent rules\n", encoding="utf-8")
    sources = discover_sources(tmp_path, _config())
    existing = [s for s in sources if s.exists]
    assert len(existing) == 1
    assert existing[0].agent_type == "openai"
    assert "AGENTS.md" in existing[0].path


def test_one_file_claude_md(tmp_path: Path) -> None:
    """CLAUDE.md present → exactly one source has exists=True with agent_type=claude."""
    (tmp_path / "CLAUDE.md").write_text("# Claude rules\n", encoding="utf-8")
    sources = discover_sources(tmp_path, _config())
    existing = [s for s in sources if s.exists]
    assert len(existing) == 1
    assert existing[0].agent_type == "claude"


def test_multiple_files(tmp_path: Path) -> None:
    """AGENTS.md + CLAUDE.md → both exist; AGENTS.md comes before CLAUDE.md."""
    (tmp_path / "AGENTS.md").write_text("# openai\n", encoding="utf-8")
    (tmp_path / "CLAUDE.md").write_text("# claude\n", encoding="utf-8")
    sources = discover_sources(tmp_path, _config())

    # Both must be present.
    existing = [s for s in sources if s.exists]
    assert len(existing) == 2

    # Stable order: AGENTS.md (openai) before CLAUDE.md (claude).
    existing_types = [s.agent_type for s in sources if s.exists]
    assert existing_types.index("openai") < existing_types.index("claude")


def test_bob_mode_files(tmp_path: Path) -> None:
    """Bob mode instruction files are discovered when they exist."""
    rules_code = tmp_path / ".bob" / "rules-code"
    rules_code.mkdir(parents=True)
    (rules_code / "AGENTS-code.md").write_text("# code rules\n", encoding="utf-8")

    rules_plan = tmp_path / ".bob" / "rules-plan"
    rules_plan.mkdir(parents=True)
    (rules_plan / "AGENTS-plan.md").write_text("# plan rules\n", encoding="utf-8")

    sources = discover_sources(tmp_path, _config())
    bob_existing = [s for s in sources if s.exists and s.agent_type == "bob"]
    assert len(bob_existing) == 2  # rules-code and rules-plan exist

    # rules-ask is not present → exists=False
    rules_ask_sources = [
        s for s in sources
        if s.agent_type == "bob" and "rules-ask" in s.path
    ]
    assert len(rules_ask_sources) == 1
    assert not rules_ask_sources[0].exists


def test_copilot_instructions(tmp_path: Path) -> None:
    """GitHub Copilot instructions file is discovered."""
    github_dir = tmp_path / ".github"
    github_dir.mkdir()
    (github_dir / "copilot-instructions.md").write_text(
        "# Copilot\n", encoding="utf-8"
    )
    sources = discover_sources(tmp_path, _config())
    copilot = [s for s in sources if s.agent_type == "copilot"]
    assert len(copilot) == 1
    assert copilot[0].exists is True


# ---------------------------------------------------------------------------
# Extra paths via config
# ---------------------------------------------------------------------------

def test_extra_instruction_paths_config(tmp_path: Path) -> None:
    """Extra path in config is discovered as agent_type='custom'."""
    custom_file = tmp_path / "docs" / "ai-guide.md"
    custom_file.parent.mkdir(parents=True)
    custom_file.write_text("# Custom\n", encoding="utf-8")

    config = _config(extra=["docs/ai-guide.md"])
    sources = discover_sources(tmp_path, config)

    custom = [s for s in sources if s.agent_type == "custom"]
    assert len(custom) == 1
    assert custom[0].exists is True


def test_missing_configured_path(tmp_path: Path) -> None:
    """Non-existent extra path → exists=False, no exception raised."""
    config = _config(extra=["docs/missing.md"])
    sources = discover_sources(tmp_path, config)

    custom = [s for s in sources if s.agent_type == "custom"]
    assert len(custom) == 1
    assert custom[0].exists is False


def test_extra_paths_alphabetical_order(tmp_path: Path) -> None:
    """Extra paths are sorted alphabetically regardless of config order."""
    config = _config(extra=["zzz.md", "aaa.md", "mmm.md"])
    sources = discover_sources(tmp_path, config)

    custom_paths = [s.path for s in sources if s.agent_type == "custom"]
    # casefold sort: aaa < mmm < zzz
    assert custom_paths == sorted(custom_paths, key=str.casefold)


# ---------------------------------------------------------------------------
# Content hash
# ---------------------------------------------------------------------------

def test_content_hash_set(tmp_path: Path) -> None:
    """Existing file has a non-empty SHA-256 hex content_hash."""
    content = b"# Hello AgentLint\n"
    agents_md = tmp_path / "AGENTS.md"
    agents_md.write_bytes(content)

    sources = discover_sources(tmp_path, _config())
    agents_source = next(s for s in sources if "AGENTS.md" in s.path)

    expected_hash = hashlib.sha256(content).hexdigest()
    assert agents_source.content_hash == expected_hash
    assert len(agents_source.content_hash) == 64  # SHA-256 hex is 64 chars


def test_content_hash_empty_when_missing(tmp_path: Path) -> None:
    """Missing file has empty string as content_hash."""
    sources = discover_sources(tmp_path, _config())
    agents_source = next(s for s in sources if "AGENTS.md" in s.path)
    assert agents_source.content_hash == ""
    assert agents_source.exists is False


# ---------------------------------------------------------------------------
# Stable ordering
# ---------------------------------------------------------------------------

def test_stable_ordering(tmp_path: Path) -> None:
    """Calling discover_sources twice returns identical order."""
    (tmp_path / "AGENTS.md").write_text("# rules\n", encoding="utf-8")
    config = _config(extra=["extra-b.md", "extra-a.md"])

    first = [s.path for s in discover_sources(tmp_path, config)]
    second = [s.path for s in discover_sources(tmp_path, config)]
    assert first == second


def test_total_count_with_extras(tmp_path: Path) -> None:
    """With 2 extra paths, total sources = 6 builtins + 2 extras."""
    config = _config(extra=["extra-a.md", "extra-b.md"])
    sources = discover_sources(tmp_path, config)
    assert len(sources) == NUM_BUILTINS + 2


# ---------------------------------------------------------------------------
# to_dict round-trip
# ---------------------------------------------------------------------------

def test_source_to_dict_round_trip(tmp_path: Path) -> None:
    """to_dict() round-trip preserves all fields."""
    (tmp_path / "AGENTS.md").write_text("# rules\n", encoding="utf-8")
    sources = discover_sources(tmp_path, _config())
    agents = next(s for s in sources if "AGENTS.md" in s.path)
    d = agents.to_dict()
    assert d["exists"] is True
    assert d["agent_type"] == "openai"
    assert len(d["content_hash"]) == 64
