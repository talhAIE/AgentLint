"""Unit tests for agentlint.config (Phase 1).

Tests:
- test_no_config_file — missing .agentlint/config.yaml returns defaults
- test_extra_paths_loaded — extra paths are read correctly
- test_malformed_yaml_raises — malformed YAML raises AgentLintConfigError
- test_empty_yaml_returns_defaults — empty YAML file returns defaults
- test_non_mapping_yaml_raises — top-level list raises AgentLintConfigError
"""

from __future__ import annotations

import pytest

from agentlint.config import AgentLintConfig, AgentLintConfigError, load_config


def test_no_config_file(tmp_path) -> None:
    """Missing .agentlint/config.yaml returns default config with no extra paths."""
    config = load_config(tmp_path)
    assert isinstance(config, AgentLintConfig)
    assert config.extra_instruction_paths == []


def test_extra_paths_loaded(tmp_path) -> None:
    """Extra paths listed in config.yaml are returned correctly."""
    config_dir = tmp_path / ".agentlint"
    config_dir.mkdir()
    config_file = config_dir / "config.yaml"
    config_file.write_text(
        "extra_instruction_paths:\n  - docs/ai-agent-guidance.md\n  - notes/agent.md\n",
        encoding="utf-8",
    )

    config = load_config(tmp_path)
    assert config.extra_instruction_paths == [
        "docs/ai-agent-guidance.md",
        "notes/agent.md",
    ]


def test_malformed_yaml_raises(tmp_path) -> None:
    """Malformed YAML raises AgentLintConfigError."""
    config_dir = tmp_path / ".agentlint"
    config_dir.mkdir()
    config_file = config_dir / "config.yaml"
    # Indentation error that makes YAML invalid.
    config_file.write_text(
        "extra_instruction_paths:\n  - valid\n  invalid: [\n",
        encoding="utf-8",
    )

    with pytest.raises(AgentLintConfigError, match="Failed to parse"):
        load_config(tmp_path)


def test_empty_yaml_returns_defaults(tmp_path) -> None:
    """An empty config file (None YAML) returns default config."""
    config_dir = tmp_path / ".agentlint"
    config_dir.mkdir()
    config_file = config_dir / "config.yaml"
    config_file.write_text("", encoding="utf-8")

    config = load_config(tmp_path)
    assert config.extra_instruction_paths == []


def test_non_mapping_yaml_raises(tmp_path) -> None:
    """A YAML file whose top level is not a mapping raises AgentLintConfigError."""
    config_dir = tmp_path / ".agentlint"
    config_dir.mkdir()
    config_file = config_dir / "config.yaml"
    config_file.write_text("- item1\n- item2\n", encoding="utf-8")

    with pytest.raises(AgentLintConfigError, match="must be a YAML mapping"):
        load_config(tmp_path)


def test_extra_paths_not_list_raises(tmp_path) -> None:
    """extra_instruction_paths that is not a list raises AgentLintConfigError."""
    config_dir = tmp_path / ".agentlint"
    config_dir.mkdir()
    config_file = config_dir / "config.yaml"
    config_file.write_text("extra_instruction_paths: docs/guide.md\n", encoding="utf-8")

    with pytest.raises(AgentLintConfigError, match="must be a list"):
        load_config(tmp_path)


def test_config_ignores_unknown_keys(tmp_path) -> None:
    """Unknown keys in config.yaml are silently ignored (forward-compatibility)."""
    config_dir = tmp_path / ".agentlint"
    config_dir.mkdir()
    config_file = config_dir / "config.yaml"
    config_file.write_text(
        "extra_instruction_paths:\n  - docs/guide.md\nunknown_future_key: true\n",
        encoding="utf-8",
    )

    config = load_config(tmp_path)
    assert config.extra_instruction_paths == ["docs/guide.md"]
