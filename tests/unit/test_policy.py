"""Unit tests for Phase 7 — Canonical Policy Compiler and Repair Plan.

Tests cover:
  - schema.py: policy_to_yaml, write_policy_yaml (serialization + round-trip)
  - compiler.py: compile_policy (evidence → CanonicalPolicy)
  - diff.py: RepairItem, generate_repair_items, format_repair_plan, write_repair_plan
  - adapters.py: build_text_preview, apply_repair (Phase 8 implementation)
  - policy/__init__.py: public API surface
"""

from __future__ import annotations

import pytest
import yaml

from agentlint.models import (
    CanonicalPolicy,
    Finding,
    InstructionRule,
    RepositoryEvidence,
)
from agentlint.policy import (
    RepairItem,
    apply_repair,
    build_text_preview,
    compile_policy,
    format_repair_plan,
    generate_repair_items,
    policy_to_yaml,
    write_policy_yaml,
    write_repair_plan,
)
from agentlint.policy.adapters import _is_allowed_target
from agentlint.policy.compiler import (
    _best_evidence,
    _build_definition_of_done,
    _build_evidence_map,
    _build_paths,
    _build_runtime,
    _build_tooling,
)


# ---------------------------------------------------------------------------
# Factories
# ---------------------------------------------------------------------------


def make_evidence(
    *,
    id: str = "ev-pm-001",
    category: str = "package_manager",
    key: str = "pnpm",
    value: str = "pnpm",
    source_path: str = "pnpm-lock.yaml",
    source_locator: str | None = None,
    strength: str = "strong",
    explanation: str = "pnpm lockfile found",
) -> RepositoryEvidence:
    return RepositoryEvidence(
        id=id,
        category=category,
        key=key,
        value=value,
        source_path=source_path,
        source_locator=source_locator,
        strength=strength,
        explanation=explanation,
    )


def make_rule(
    *,
    id: str = "rule-agents-001",
    source_path: str = "AGENTS.md",
    source_agent: str = "openai",
    text: str = "Use npm for all installs.",
    category: str | None = "package_manager",
    normalized_key: str | None = "package_manager",
    normalized_value: str | None = "npm",
    line_start: int = 1,
    line_end: int = 1,
) -> InstructionRule:
    return InstructionRule(
        id=id,
        source_path=source_path,
        source_agent=source_agent,
        text=text,
        category=category,
        normalized_key=normalized_key,
        normalized_value=normalized_value,
        line_start=line_start,
        line_end=line_end,
        extraction_method="deterministic",
        confidence=0.8,
    )


def make_finding(
    *,
    id: str = "find-f02-001",
    type: str = "F02",
    severity: str = "high",
    title: str = "Package manager mismatch",
    explanation: str = "AGENTS.md says npm but repo uses pnpm",
    instruction_rules: list[str] | None = None,
    evidence_ids: list[str] | None = None,
    recommended_action: str = "Replace npm with pnpm",
    confidence: float = 0.95,
    deterministic: bool = True,
    status: str = "open",
) -> Finding:
    return Finding(
        id=id,
        type=type,
        severity=severity,
        title=title,
        explanation=explanation,
        instruction_rules=instruction_rules or ["rule-agents-001"],
        evidence_ids=evidence_ids or ["ev-pm-001"],
        recommended_action=recommended_action,
        confidence=confidence,
        deterministic=deterministic,
        status=status,
    )


def make_policy(
    *,
    version: int = 1,
    project_name: str | None = "my-project",
    tooling: dict | None = None,
    runtime: dict | None = None,
    paths: dict | None = None,
    definition_of_done: list[str] | None = None,
    evidence: dict | None = None,
) -> CanonicalPolicy:
    return CanonicalPolicy(
        version=version,
        project_name=project_name,
        tooling=tooling or {"package_manager": "pnpm", "test_framework": "vitest"},
        runtime=runtime or {"node": "22"},
        paths=paths or {},
        definition_of_done=definition_of_done or ["pnpm lint", "pnpm test"],
        evidence=evidence or {"package_manager": ["pnpm-lock.yaml"]},
    )


# ---------------------------------------------------------------------------
# Tests: schema.py
# ---------------------------------------------------------------------------


class TestSchema:
    def test_policy_to_yaml_returns_string(self):
        policy = make_policy()
        result = policy_to_yaml(policy)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_policy_to_yaml_has_version(self):
        policy = make_policy(version=1)
        result = policy_to_yaml(policy)
        assert "version: 1" in result

    def test_policy_to_yaml_has_tooling(self):
        policy = make_policy(tooling={"package_manager": "pnpm"})
        result = policy_to_yaml(policy)
        assert "tooling" in result
        assert "pnpm" in result

    def test_policy_to_yaml_has_runtime(self):
        policy = make_policy(runtime={"node": "22"})
        result = policy_to_yaml(policy)
        assert "runtime" in result
        assert "22" in result

    def test_policy_to_yaml_has_evidence(self):
        policy = make_policy(evidence={"package_manager": ["pnpm-lock.yaml"]})
        result = policy_to_yaml(policy)
        assert "evidence" in result
        assert "pnpm-lock.yaml" in result

    def test_policy_to_yaml_omits_none_tooling_values(self):
        policy = make_policy(tooling={"package_manager": "pnpm", "test_framework": None})
        result = policy_to_yaml(policy)
        # test_framework should be absent (None omitted)
        parsed = yaml.safe_load(result)
        assert "test_framework" not in parsed.get("tooling", {})

    def test_policy_to_yaml_omits_empty_tooling_block(self):
        # Construct directly to bypass the factory's `or` default
        policy = CanonicalPolicy(
            version=1,
            project_name="test",
            tooling={},
            runtime={},
            paths={},
            definition_of_done=[],
            evidence={},
        )
        result = policy_to_yaml(policy)
        parsed = yaml.safe_load(result)
        assert "tooling" not in (parsed or {})

    def test_policy_to_yaml_round_trips(self):
        """YAML written by policy_to_yaml can be parsed back and matches."""
        policy = make_policy()
        yaml_str = policy_to_yaml(policy)
        parsed = yaml.safe_load(yaml_str)
        assert parsed["version"] == policy.version
        assert parsed["project"]["name"] == policy.project_name
        assert parsed["tooling"]["package_manager"] == policy.tooling["package_manager"]
        assert parsed["runtime"]["node"] == policy.runtime["node"]
        assert parsed["evidence"]["package_manager"] == policy.evidence["package_manager"]

    def test_policy_to_yaml_definition_of_done(self):
        policy = make_policy(definition_of_done=["pnpm lint", "pnpm test", "pnpm build"])
        yaml_str = policy_to_yaml(policy)
        parsed = yaml.safe_load(yaml_str)
        assert parsed["definition_of_done"] == ["pnpm lint", "pnpm test", "pnpm build"]

    def test_write_policy_yaml_creates_file(self, tmp_path):
        policy = make_policy()
        out = write_policy_yaml(tmp_path, policy)
        assert out.exists()
        assert out.name == "policy.yaml"
        assert out.parent.name == ".agentlint"

    def test_write_policy_yaml_creates_agentlint_dir(self, tmp_path):
        repo = tmp_path / "myrepo"
        repo.mkdir()
        policy = make_policy()
        out = write_policy_yaml(repo, policy)
        assert (repo / ".agentlint").is_dir()
        assert out.exists()

    def test_write_policy_yaml_content_is_valid_yaml(self, tmp_path):
        policy = make_policy()
        out = write_policy_yaml(tmp_path, policy)
        content = out.read_text(encoding="utf-8")
        parsed = yaml.safe_load(content)
        assert parsed["version"] == 1


# ---------------------------------------------------------------------------
# Tests: compiler.py — helpers
# ---------------------------------------------------------------------------


class TestCompilerHelpers:
    def test_best_evidence_returns_strongest(self):
        strong = make_evidence(id="ev-pm-001", strength="strong", key="pnpm")
        medium = make_evidence(id="ev-pm-002", strength="medium", key="npm")
        result = _best_evidence([medium, strong], "package_manager")
        assert result.key == "pnpm"

    def test_best_evidence_first_wins_same_strength(self):
        ev1 = make_evidence(id="ev-pm-001", strength="strong", key="pnpm")
        ev2 = make_evidence(id="ev-pm-002", strength="strong", key="yarn")
        result = _best_evidence([ev1, ev2], "package_manager")
        assert result.key == "pnpm"

    def test_best_evidence_returns_none_when_no_match(self):
        ev = make_evidence(category="test_framework")
        result = _best_evidence([ev], "package_manager")
        assert result is None

    def test_best_evidence_filters_by_key(self):
        pm_ev = make_evidence(id="ev-pm-001", category="package_manager", key="pnpm")
        result = _best_evidence([pm_ev], "package_manager", key="pnpm")
        assert result is not None
        assert result.key == "pnpm"

    def test_best_evidence_key_filter_no_match(self):
        pm_ev = make_evidence(id="ev-pm-001", category="package_manager", key="pnpm")
        result = _best_evidence([pm_ev], "package_manager", key="yarn")
        assert result is None

    def test_build_tooling_package_manager(self):
        ev = make_evidence(category="package_manager", key="pnpm", strength="strong")
        tooling = _build_tooling([ev])
        assert tooling["package_manager"] == "pnpm"

    def test_build_tooling_test_framework(self):
        ev = make_evidence(
            id="ev-tf-001",
            category="test_framework",
            key="vitest",
            value="vitest",
            source_path="package.json",
            strength="strong",
        )
        tooling = _build_tooling([ev])
        assert tooling["test_framework"] == "vitest"

    def test_build_tooling_commands(self):
        lint_ev = make_evidence(
            id="ev-cmd-001",
            category="commands",
            key="lint",
            value="pnpm lint",
            source_path="package.json",
            strength="strong",
        )
        test_ev = make_evidence(
            id="ev-cmd-002",
            category="commands",
            key="test",
            value="pnpm test",
            source_path="package.json",
            strength="strong",
        )
        tooling = _build_tooling([lint_ev, test_ev])
        assert tooling["lint_command"] == "pnpm lint"
        assert tooling["test_command"] == "pnpm test"

    def test_build_runtime_deduplicates_by_key(self):
        ev1 = make_evidence(
            id="ev-rt-001",
            category="runtime",
            key="node",
            value="22",
            source_path=".nvmrc",
            strength="strong",
        )
        ev2 = make_evidence(
            id="ev-rt-002",
            category="runtime",
            key="node",
            value="18",
            source_path="package.json",
            strength="medium",
        )
        runtime = _build_runtime([ev1, ev2])
        assert runtime["node"] == "22"  # strong wins

    def test_build_paths_only_generated_and_protected(self):
        gen_ev = make_evidence(
            id="ev-path-001",
            category="paths",
            key="generated",
            value="src/generated/**",
            source_path=".",
            strength="medium",
        )
        regular_ev = make_evidence(
            id="ev-path-002",
            category="paths",
            key="src",
            value="src/",
            source_path=".",
            strength="medium",
        )
        paths = _build_paths([gen_ev, regular_ev])
        assert "generated" in paths
        assert "src" not in paths
        assert "src/generated/**" in paths["generated"]

    def test_build_paths_empty_when_no_generated_or_protected(self):
        ev = make_evidence(category="paths", key="src", value="src/")
        paths = _build_paths([ev])
        assert paths == {}

    def test_build_definition_of_done_canonical_order(self):
        tooling = {
            "test_command": "pnpm test",
            "build_command": "pnpm build",
            "lint_command": "pnpm lint",
        }
        dod = _build_definition_of_done(tooling)
        assert dod == ["pnpm lint", "pnpm test", "pnpm build"]

    def test_build_definition_of_done_only_present_commands(self):
        tooling = {"test_command": "pytest"}
        dod = _build_definition_of_done(tooling)
        assert dod == ["pytest"]
        assert "None" not in dod

    def test_build_evidence_map_excludes_paths(self):
        ev_pm = make_evidence(category="package_manager", source_path="pnpm-lock.yaml")
        ev_path = make_evidence(
            id="ev-path-001", category="paths", key="src", value="src/", source_path="."
        )
        ev_map = _build_evidence_map([ev_pm, ev_path])
        assert "package_manager" in ev_map
        assert "paths" not in ev_map

    def test_build_evidence_map_uses_source_locator(self):
        ev = make_evidence(
            source_path="package.json",
            source_locator="devDependencies.vitest",
            category="test_framework",
        )
        ev_map = _build_evidence_map([ev])
        assert "package.json#devDependencies.vitest" in ev_map["test_framework"]

    def test_build_evidence_map_deduplicates(self):
        ev1 = make_evidence(id="ev-pm-001", source_path="pnpm-lock.yaml")
        ev2 = make_evidence(id="ev-pm-002", source_path="pnpm-lock.yaml")
        ev_map = _build_evidence_map([ev1, ev2])
        assert ev_map["package_manager"].count("pnpm-lock.yaml") == 1


# ---------------------------------------------------------------------------
# Tests: compiler.py — compile_policy
# ---------------------------------------------------------------------------


class TestCompilePolicy:
    def test_compile_policy_empty_evidence(self, tmp_path):
        policy = compile_policy([], tmp_path)
        assert isinstance(policy, CanonicalPolicy)
        assert policy.version == 1
        assert policy.tooling == {}
        assert policy.runtime == {}

    def test_compile_policy_project_name_from_repo_path(self, tmp_path):
        repo = tmp_path / "my-project"
        repo.mkdir()
        policy = compile_policy([], repo)
        assert policy.project_name == "my-project"

    def test_compile_policy_detects_package_manager(self, tmp_path):
        ev = make_evidence(
            category="package_manager", key="pnpm", strength="strong"
        )
        policy = compile_policy([ev], tmp_path)
        assert policy.tooling["package_manager"] == "pnpm"

    def test_compile_policy_prefers_strong_over_medium(self, tmp_path):
        strong = make_evidence(
            id="ev-pm-001", category="package_manager", key="pnpm", strength="strong"
        )
        medium = make_evidence(
            id="ev-pm-002", category="package_manager", key="npm", strength="medium"
        )
        policy = compile_policy([medium, strong], tmp_path)
        assert policy.tooling["package_manager"] == "pnpm"

    def test_compile_policy_definition_of_done_ordered(self, tmp_path):
        """lint command comes before test command in definition_of_done."""
        test_ev = make_evidence(
            id="ev-cmd-001",
            category="commands",
            key="test",
            value="pnpm test",
            source_path="package.json",
            strength="strong",
        )
        lint_ev = make_evidence(
            id="ev-cmd-002",
            category="commands",
            key="lint",
            value="pnpm lint",
            source_path="package.json",
            strength="strong",
        )
        policy = compile_policy([test_ev, lint_ev], tmp_path)
        dod = policy.definition_of_done
        assert dod.index("pnpm lint") < dod.index("pnpm test")

    def test_compile_policy_evidence_map_populated(self, tmp_path):
        ev = make_evidence(
            category="package_manager", key="pnpm", source_path="pnpm-lock.yaml"
        )
        policy = compile_policy([ev], tmp_path)
        assert "package_manager" in policy.evidence
        assert "pnpm-lock.yaml" in policy.evidence["package_manager"]

    def test_compile_policy_returns_canonical_policy_instance(self, tmp_path):
        policy = compile_policy([], tmp_path)
        assert isinstance(policy, CanonicalPolicy)

    def test_compile_policy_version_is_1(self, tmp_path):
        policy = compile_policy([], tmp_path)
        assert policy.version == 1

    def test_compile_policy_does_not_write_files(self, tmp_path):
        """compile_policy must not write to disk — candidate only."""
        compile_policy([], tmp_path)
        agentlint_dir = tmp_path / ".agentlint"
        # Either no .agentlint dir, or policy.yaml specifically absent
        if agentlint_dir.exists():
            assert not (agentlint_dir / "policy.yaml").exists()


# ---------------------------------------------------------------------------
# Tests: diff.py — RepairItem
# ---------------------------------------------------------------------------


class TestRepairItem:
    def test_repair_item_to_dict(self):
        item = RepairItem(
            finding_id="find-f02-001",
            target_file="AGENTS.md",
            original_text="Use npm",
            proposed_text="Use pnpm",
            evidence_sources=["pnpm-lock.yaml"],
            reason="npm not detected, pnpm is",
            expected_effect="Agent will use pnpm",
            requires_manual_review=False,
        )
        d = item.to_dict()
        assert d["finding_id"] == "find-f02-001"
        assert d["original_text"] == "Use npm"
        assert d["proposed_text"] == "Use pnpm"
        assert d["requires_manual_review"] is False

    def test_repair_item_defaults(self):
        item = RepairItem(
            finding_id="x",
            target_file="AGENTS.md",
            original_text="",
            proposed_text="",
        )
        assert item.evidence_sources == []
        assert item.reason == ""
        assert item.requires_manual_review is False


# ---------------------------------------------------------------------------
# Tests: diff.py — generate_repair_items
# ---------------------------------------------------------------------------


class TestGenerateRepairItems:
    def test_empty_findings_returns_empty(self):
        items = generate_repair_items([], [], [])
        assert items == []

    def test_f02_produces_repair_item(self):
        rule = make_rule(id="rule-agents-001", text="Use npm for all installs.", normalized_value="npm")
        ev = make_evidence(
            id="ev-pm-001", category="package_manager", key="pnpm", strength="strong"
        )
        finding = make_finding(
            id="find-f02-001",
            type="F02",
            instruction_rules=["rule-agents-001"],
            evidence_ids=["ev-pm-001"],
        )
        items = generate_repair_items([finding], [rule], [ev])
        assert len(items) == 1
        assert items[0].finding_id == "find-f02-001"
        assert items[0].target_file == "AGENTS.md"

    def test_f02_proposes_correct_replacement(self):
        rule = make_rule(text="Use npm for all installs.", normalized_value="npm")
        ev = make_evidence(
            id="ev-pm-001", category="package_manager", key="pnpm", strength="strong"
        )
        finding = make_finding(
            type="F02",
            instruction_rules=[rule.id],
            evidence_ids=["ev-pm-001"],
        )
        items = generate_repair_items([finding], [rule], [ev])
        assert len(items) == 1
        assert "pnpm" in items[0].proposed_text

    def test_f05_produces_repair_item(self):
        rule1 = make_rule(id="rule-agents-001", text="Run pnpm lint before finishing.", source_path="AGENTS.md")
        rule2 = make_rule(id="rule-claude-001", text="Run pnpm lint before finishing.", source_path="CLAUDE.md")
        finding = Finding(
            id="find-f05-001",
            type="F05",
            severity="low",
            title="Duplicate rule",
            explanation="Same rule in both files",
            instruction_rules=["rule-agents-001", "rule-claude-001"],
            evidence_ids=[],
            recommended_action="Remove duplicate",
            confidence=0.95,
            deterministic=True,
        )
        items = generate_repair_items([finding], [rule1, rule2], [])
        assert len(items) == 1
        assert items[0].requires_manual_review is False
        assert items[0].target_file == "CLAUDE.md"  # remove the later occurrence

    def test_f01_requires_manual_review(self):
        rule = make_rule(id="rule-agents-001", text="Use npm.")
        finding = Finding(
            id="find-f01-001",
            type="F01",
            severity="high",
            title="Conflict",
            explanation="Two files disagree",
            instruction_rules=["rule-agents-001"],
            evidence_ids=[],
            recommended_action="Reconcile",
            confidence=0.9,
            deterministic=True,
        )
        items = generate_repair_items([finding], [rule], [])
        assert len(items) == 1
        assert items[0].requires_manual_review is True

    def test_ignored_findings_are_skipped(self):
        finding = make_finding(status="ignored")
        items = generate_repair_items([finding], [], [])
        assert items == []

    def test_f06_and_f07_produce_no_items(self):
        """F06/F07 semantic findings have no deterministic repair."""
        finding = Finding(
            id="find-f06-001",
            type="F06",
            severity="medium",
            title="Missing context",
            explanation="Missing high-value context",
            instruction_rules=[],
            evidence_ids=[],
            recommended_action="Add context",
            confidence=0.6,
            deterministic=False,
        )
        items = generate_repair_items([finding], [], [])
        assert items == []

    def test_evidence_sources_populated_in_item(self):
        rule = make_rule(normalized_value="npm")
        ev = make_evidence(
            id="ev-pm-001", source_path="pnpm-lock.yaml"
        )
        finding = make_finding(
            instruction_rules=[rule.id],
            evidence_ids=["ev-pm-001"],
        )
        items = generate_repair_items([finding], [rule], [ev])
        assert "pnpm-lock.yaml" in items[0].evidence_sources


# ---------------------------------------------------------------------------
# Tests: diff.py — format_repair_plan
# ---------------------------------------------------------------------------


class TestFormatRepairPlan:
    def test_empty_items_returns_no_items_message(self):
        result = format_repair_plan([])
        assert "No repair items" in result
        assert "Approval required" in result

    def test_numbered_items(self):
        items = [
            RepairItem(
                finding_id="find-f02-001",
                target_file="AGENTS.md",
                original_text="Use npm",
                proposed_text="Use pnpm",
                evidence_sources=["pnpm-lock.yaml"],
                reason="pnpm is the actual package manager",
                expected_effect="Consistent tooling",
            ),
            RepairItem(
                finding_id="find-f05-001",
                target_file="CLAUDE.md",
                original_text="Run pnpm lint",
                proposed_text="",
                evidence_sources=["AGENTS.md"],
                reason="Duplicate",
                expected_effect="No duplication",
            ),
        ]
        result = format_repair_plan(items)
        assert "## 1." in result
        assert "## 2." in result

    def test_contains_evidence_line(self):
        items = [
            RepairItem(
                finding_id="find-f02-001",
                target_file="AGENTS.md",
                original_text="Use npm",
                proposed_text="Use pnpm",
                evidence_sources=["pnpm-lock.yaml"],
                reason="test",
                expected_effect="test",
            )
        ]
        result = format_repair_plan(items)
        assert "Evidence:" in result
        assert "pnpm-lock.yaml" in result

    def test_contains_reason_and_expected_effect(self):
        items = [
            RepairItem(
                finding_id="find-f02-001",
                target_file="AGENTS.md",
                original_text="Use npm",
                proposed_text="Use pnpm",
                evidence_sources=[],
                reason="Mismatched tooling",
                expected_effect="Agents use correct package manager",
            )
        ]
        result = format_repair_plan(items)
        assert "Reason:" in result
        assert "Mismatched tooling" in result
        assert "Expected effect:" in result
        assert "Agents use correct package manager" in result

    def test_manual_review_flag_shown(self):
        items = [
            RepairItem(
                finding_id="find-f01-001",
                target_file="AGENTS.md",
                original_text="Use npm",
                proposed_text="",
                evidence_sources=[],
                reason="Conflict",
                expected_effect="Reconciled",
                requires_manual_review=True,
            )
        ]
        result = format_repair_plan(items)
        assert "MANUAL REVIEW REQUIRED" in result

    def test_approval_notice_always_present(self):
        result = format_repair_plan([])
        assert "Approval required" in result

        items = [RepairItem(
            finding_id="find-f02-001",
            target_file="AGENTS.md",
            original_text="x",
            proposed_text="y",
        )]
        result2 = format_repair_plan(items)
        assert "Approval required" in result2


# ---------------------------------------------------------------------------
# Tests: diff.py — write_repair_plan
# ---------------------------------------------------------------------------


class TestWriteRepairPlan:
    def test_write_repair_plan_creates_file(self, tmp_path):
        out = write_repair_plan(tmp_path, [])
        assert out.exists()
        assert out.name == "repair-plan.md"
        assert out.parent.name == ".agentlint"

    def test_write_repair_plan_content_readable(self, tmp_path):
        out = write_repair_plan(tmp_path, [])
        content = out.read_text(encoding="utf-8")
        assert "Repair Plan" in content

    def test_write_repair_plan_with_items(self, tmp_path):
        items = [
            RepairItem(
                finding_id="find-f02-001",
                target_file="AGENTS.md",
                original_text="Use npm",
                proposed_text="Use pnpm",
                evidence_sources=["pnpm-lock.yaml"],
                reason="mismatch",
                expected_effect="fixed",
            )
        ]
        out = write_repair_plan(tmp_path, items)
        content = out.read_text(encoding="utf-8")
        assert "find-f02-001" in content
        assert "pnpm-lock.yaml" in content


# ---------------------------------------------------------------------------
# Tests: adapters.py — _is_allowed_target
# ---------------------------------------------------------------------------


class TestIsAllowedTarget:
    def test_agents_md_allowed(self):
        assert _is_allowed_target("AGENTS.md") is True

    def test_claude_md_allowed(self):
        assert _is_allowed_target("CLAUDE.md") is True

    def test_copilot_allowed(self):
        assert _is_allowed_target(".github/copilot-instructions.md") is True

    def test_bob_rules_allowed(self):
        assert _is_allowed_target(".bob/rules-agent/AGENTS.md") is True

    def test_cursor_allowed(self):
        assert _is_allowed_target(".cursor/rules.md") is True

    def test_agentlint_allowed(self):
        assert _is_allowed_target(".agentlint/policy.yaml") is True

    def test_src_py_not_allowed(self):
        assert _is_allowed_target("src/main.py") is False

    def test_setup_py_not_allowed(self):
        assert _is_allowed_target("setup.py") is False


# ---------------------------------------------------------------------------
# Tests: adapters.py — build_text_preview
# ---------------------------------------------------------------------------


class TestBuildTextPreview:
    def _make_item(self, **kwargs) -> RepairItem:
        defaults = dict(
            finding_id="find-f02-001",
            target_file="AGENTS.md",
            original_text="Use npm",
            proposed_text="Use pnpm",
            evidence_sources=["pnpm-lock.yaml"],
            reason="mismatch",
            expected_effect="fixed",
            requires_manual_review=False,
        )
        defaults.update(kwargs)
        return RepairItem(**defaults)

    def test_shows_original_block(self):
        item = self._make_item()
        file_content = "Some text.\nUse npm\nMore text."
        preview = build_text_preview(item, file_content)
        assert "Use npm" in preview
        assert "--- original" in preview

    def test_shows_proposed_block(self):
        item = self._make_item()
        file_content = "Some text.\nUse npm\nMore text."
        preview = build_text_preview(item, file_content)
        assert "Use pnpm" in preview
        assert "+++ proposed" in preview

    def test_manual_review_shows_flag(self):
        item = self._make_item(
            requires_manual_review=True,
            proposed_text="",
        )
        file_content = "Use npm\n"
        preview = build_text_preview(item, file_content)
        assert "MANUAL REVIEW REQUIRED" in preview

    def test_manual_review_no_proposed_block(self):
        item = self._make_item(
            requires_manual_review=True,
            proposed_text="",
        )
        file_content = "Use npm\n"
        preview = build_text_preview(item, file_content)
        # Should not show a "+++ proposed" block for manual review
        assert "+++ proposed" not in preview

    def test_original_not_found_shows_header(self):
        item = self._make_item(original_text="Does not exist in file")
        file_content = "Completely different content."
        preview = build_text_preview(item, file_content)
        # Should gracefully handle not finding the text
        assert "Does not exist in file" in preview


# ---------------------------------------------------------------------------
# Tests: adapters.py — apply_repair (Phase 8 implementation)
# ---------------------------------------------------------------------------


class TestApplyRepair:
    def test_apply_repair_replaces_text(self):
        """apply_repair replaces original_text with proposed_text."""
        item = RepairItem(
            finding_id="find-f02-001",
            target_file="AGENTS.md",
            original_text="Use npm",
            proposed_text="Use pnpm",
        )
        result = apply_repair(item, "Use npm\n")
        assert "Use pnpm" in result
        assert "Use npm" not in result

    def test_apply_repair_raises_value_error_for_manual_review(self):
        """Items requiring manual review cannot be applied programmatically."""
        item = RepairItem(
            finding_id="find-f02-001",
            target_file="AGENTS.md",
            original_text="Use npm",
            proposed_text="",
            requires_manual_review=True,
        )
        with pytest.raises(ValueError, match="manual review"):
            apply_repair(item, "Use npm\n")

    def test_apply_repair_raises_value_error_for_disallowed_target(self):
        """Target files outside the allowed set raise ValueError."""
        item = RepairItem(
            finding_id="find-f02-001",
            target_file="src/production_code.py",
            original_text="Use npm",
            proposed_text="Use pnpm",
        )
        with pytest.raises(ValueError, match="not in the allowed set"):
            apply_repair(item, "Use npm\n")


# ---------------------------------------------------------------------------
# Tests: policy/__init__.py — public API surface
# ---------------------------------------------------------------------------


class TestPublicAPI:
    def test_all_symbols_importable(self):
        """Every symbol listed in __all__ must be importable from agentlint.policy."""
        import agentlint.policy as pkg
        for name in pkg.__all__:
            assert hasattr(pkg, name), f"{name} not found in agentlint.policy"

    def test_compile_policy_callable(self):
        assert callable(compile_policy)

    def test_write_policy_yaml_callable(self):
        assert callable(write_policy_yaml)

    def test_generate_repair_items_callable(self):
        assert callable(generate_repair_items)

    def test_write_repair_plan_callable(self):
        assert callable(write_repair_plan)

    def test_apply_repair_callable(self):
        assert callable(apply_repair)
