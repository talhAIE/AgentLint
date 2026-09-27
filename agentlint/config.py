"""AgentLint configuration loader.

Reads `.agentlint/config.yaml` from the target repository and returns
a typed config object. If the file does not exist, returns defaults.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


class AgentLintConfigError(Exception):
    """Raised when the config file cannot be parsed."""


@dataclass
class AgentLintConfig:
    """Configuration loaded from `.agentlint/config.yaml`."""

    extra_instruction_paths: list[str] = field(default_factory=list)


def load_config(repo_path: Path) -> AgentLintConfig:
    """Load `.agentlint/config.yaml` from *repo_path*.

    Returns default config (empty extra paths) when the file does not exist.
    Raises :class:`AgentLintConfigError` when the YAML is malformed or has
    an unexpected structure.

    Args:
        repo_path: Absolute or relative path to the root of the target repo.

    Returns:
        An :class:`AgentLintConfig` instance.
    """
    config_path = Path(repo_path) / ".agentlint" / "config.yaml"

    if not config_path.exists():
        return AgentLintConfig()

    try:
        raw: Any = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise AgentLintConfigError(
            f"Failed to parse config file {config_path}: {exc}"
        ) from exc

    if raw is None:
        # Empty YAML file → use defaults.
        return AgentLintConfig()

    if not isinstance(raw, dict):
        raise AgentLintConfigError(
            f"Config file {config_path} must be a YAML mapping, got {type(raw).__name__}"
        )

    extra_paths: list[str] = []
    if "extra_instruction_paths" in raw:
        value = raw["extra_instruction_paths"]
        if not isinstance(value, list):
            raise AgentLintConfigError(
                f"Config file {config_path}: 'extra_instruction_paths' must be a list"
            )
        extra_paths = [str(p) for p in value]

    return AgentLintConfig(extra_instruction_paths=extra_paths)
