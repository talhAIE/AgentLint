"""Instruction source discovery.

Deterministically finds all supported agent instruction files in a target
repository and returns them in a stable, fixed order.

Contract:
- Sources that do not exist on disk are **included** with ``exists=False``
  so downstream phases know what was checked.
- ``content_hash`` is SHA-256 hex of file bytes when the file exists; ``""``
  otherwise.
- Extra paths from config are appended after the built-in set, sorted
  alphabetically for stable ordering.
- Absolute extra paths are used as-is; relative paths are resolved relative
  to *repo_path*.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from agentlint.config import AgentLintConfig
from agentlint.models import InstructionSource

# ---------------------------------------------------------------------------
# Built-in discovery candidates in fixed priority order (§8.1 + §Phase 1).
# Each tuple: (relative_path, agent_type)
# ---------------------------------------------------------------------------
_BUILTIN_SOURCES: list[tuple[str, str]] = [
    ("AGENTS.md", "openai"),
    ("CLAUDE.md", "claude"),
    (".github/copilot-instructions.md", "copilot"),
    (".bob/rules-code/AGENTS-code.md", "bob"),
    (".bob/rules-plan/AGENTS-plan.md", "bob"),
    (".bob/rules-ask/AGENTS-ask.md", "bob"),
]


def _sha256_hex(path: Path) -> str:
    """Return the SHA-256 hex digest of *path*'s bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _build_source(abs_path: Path, agent_type: str, repo_path: Path) -> InstructionSource:
    """Build an :class:`InstructionSource` for *abs_path*.

    The ``path`` field is stored as a string using the OS-native representation.
    It is relative to *repo_path* when possible so that scan.json output is
    portable across machines.
    """
    try:
        display_path = str(abs_path.relative_to(repo_path))
    except ValueError:
        # Absolute extra path that is outside repo_path — store as-is.
        display_path = str(abs_path)

    exists = abs_path.exists() and abs_path.is_file()
    content_hash = _sha256_hex(abs_path) if exists else ""

    return InstructionSource(
        path=display_path,
        agent_type=agent_type,
        content_hash=content_hash,
        exists=exists,
    )


def discover_sources(
    repo_path: Path,
    config: AgentLintConfig,
) -> list[InstructionSource]:
    """Return all instruction sources for *repo_path* in stable order.

    Built-in sources come first in their fixed priority order.  Extra paths
    from *config* are appended in alphabetical order (case-insensitive on
    Windows, case-sensitive on POSIX) for determinism.

    Args:
        repo_path: Root directory of the repository to scan.
        config:    Loaded :class:`AgentLintConfig` (may have extra paths).

    Returns:
        A list of :class:`InstructionSource` instances, always in the same
        order for the same inputs.
    """
    repo_path = Path(repo_path).resolve()
    sources: list[InstructionSource] = []

    # --- Built-in candidates (fixed order) ---
    for rel, agent_type in _BUILTIN_SOURCES:
        abs_path = repo_path / rel
        sources.append(_build_source(abs_path, agent_type, repo_path))

    # --- Extra paths from config (alphabetical for stable ordering) ---
    sorted_extras = sorted(config.extra_instruction_paths, key=str.casefold)
    for extra in sorted_extras:
        extra_path = Path(extra)
        if not extra_path.is_absolute():
            extra_path = repo_path / extra_path
        sources.append(_build_source(extra_path, "custom", repo_path))

    return sources
