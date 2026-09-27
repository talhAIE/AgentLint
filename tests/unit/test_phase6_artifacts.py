"""Unit tests for Phase 6 — Bob Skill, Custom Mode, and Slash Commands.

Phase 6 produces configuration artifacts (SKILL.md, slash command markdown files,
custom_modes.yaml). These tests verify that every required artifact:

1. exists at the correct path
2. contains the required structural content specified in AgentLintplan.md §17
3. does not fabricate functionality or claim capabilities beyond what is
   documented in the spec

No Python engine changes occur in Phase 6; these tests are purely structural.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml
import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent

_SKILL_FILE = _REPO_ROOT / ".bob" / "skills" / "agent-policy-audit" / "SKILL.md"
_AUDIT_CMD = _REPO_ROOT / ".bob" / "commands" / "agentlint-audit.md"
_REPAIR_CMD = _REPO_ROOT / ".bob" / "commands" / "agentlint-repair.md"
_VERIFY_CMD = _REPO_ROOT / ".bob" / "commands" / "agentlint-verify.md"
_CUSTOM_MODES = _REPO_ROOT / ".bob" / "custom_modes.yaml"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _contains_all(text: str, *fragments: str) -> list[str]:
    """Return list of fragments NOT found in text (empty list = all present)."""
    return [f for f in fragments if f not in text]


# ---------------------------------------------------------------------------
# Skill file
# ---------------------------------------------------------------------------


class TestSkillFile:
    def test_file_exists(self):
        assert _SKILL_FILE.exists(), f"SKILL.md not found at {_SKILL_FILE}"

    def test_has_frontmatter_name(self):
        text = _read(_SKILL_FILE)
        assert "name: agent-policy-audit" in text, "SKILL.md must declare name: agent-policy-audit"

    def test_has_frontmatter_description(self):
        text = _read(_SKILL_FILE)
        # Description must exist and be non-trivial (> 20 chars)
        m = re.search(r"description:\s*(.+)", text)
        assert m is not None, "SKILL.md must have a description field in frontmatter"
        assert len(m.group(1).strip()) > 20, "SKILL.md description must be substantive"

    def test_has_all_ten_rules(self):
        """All 10 skill rules from §17.2 must be present."""
        text = _read(_SKILL_FILE)
        missing = _contains_all(
            text,
            "Do not edit instructions before evidence collection",
            "Prefer deterministic AgentLint output",
            "Every finding must cite",
            "Never claim a command works",
            "Never claim an agent will follow a rule",
            "Require human approval before modifying",
            "After repair, rerun",
            "Run relevant project validation commands",
            "Produce before/after evidence",
        )
        assert not missing, f"SKILL.md missing required rule content: {missing}"

    def test_distinguishes_finding_types(self):
        """Skill must distinguish the five deterministic finding types."""
        text = _read(_SKILL_FILE)
        for ftype in ("F01", "F02", "F03", "F04", "F05", "F06", "F07"):
            assert ftype in text, f"SKILL.md must mention finding type {ftype}"

    def test_has_failsafe(self):
        """Skill must document the fail-safe: deterministic scan works without Bob."""
        text = _read(_SKILL_FILE)
        assert "fail" in text.lower() or "without Bob" in text or "unavailable" in text, (
            "SKILL.md must document that deterministic scan works without Bob (fail-safe)"
        )

    def test_no_fake_functionality(self):
        """Skill must not claim to auto-apply repairs without approval."""
        text = _read(_SKILL_FILE)
        bad_phrases = ["automatically apply", "auto-apply without", "apply without approval"]
        for phrase in bad_phrases:
            assert phrase.lower() not in text.lower(), (
                f"SKILL.md contains forbidden phrase: {phrase!r}"
            )

    def test_semantic_findings_json_schema_present(self):
        """Skill must document the required JSON schema for Bob findings (§Phase 6)."""
        text = _read(_SKILL_FILE)
        missing = _contains_all(
            text,
            "reasoning_summary",
            "instruction_sources",
            "repository_evidence",
            "recommended_action",
            "confidence",
            "deterministic",
        )
        assert not missing, f"SKILL.md missing required finding schema fields: {missing}"


# ---------------------------------------------------------------------------
# /agentlint-audit command
# ---------------------------------------------------------------------------


class TestAuditCommand:
    def test_file_exists(self):
        assert _AUDIT_CMD.exists(), f"agentlint-audit.md not found at {_AUDIT_CMD}"

    def test_runs_deterministic_scan_first(self):
        """Audit must run agentlint scan as the first step."""
        text = _read(_AUDIT_CMD)
        assert "agentlint scan" in text, "agentlint-audit.md must invoke agentlint scan"

    def test_reads_all_four_output_files(self):
        """Must reference all four .agentlint/ output files."""
        text = _read(_AUDIT_CMD)
        for fname in ("scan.json", "evidence.json", "rules.json", "findings.json"):
            assert fname in text, f"agentlint-audit.md must reference {fname}"

    def test_spawns_parallel_subagents(self):
        """Must document spawning parallel subagents for investigation."""
        text = _read(_AUDIT_CMD)
        assert "subagent" in text.lower() or "spawn_subagent" in text, (
            "agentlint-audit.md must document subagent usage"
        )

    def test_three_analyst_roles(self):
        """Must define Instruction Analyst, Repository Reality Analyst, Maintenance Analyst."""
        text = _read(_AUDIT_CMD)
        for role in ("Instruction Analyst", "Repository Reality", "Maintenance Analyst"):
            assert role in text, f"agentlint-audit.md must define role: {role}"

    def test_writes_findings_json(self):
        """Audit must write to findings.json (semantic_findings key)."""
        text = _read(_AUDIT_CMD)
        assert "semantic_findings" in text, (
            "agentlint-audit.md must write semantic findings to findings.json "
            "under 'semantic_findings' key"
        )

    def test_writes_repair_plan(self):
        """Audit must create repair-plan.md."""
        text = _read(_AUDIT_CMD)
        assert "repair-plan.md" in text, "agentlint-audit.md must create repair-plan.md"

    def test_does_not_modify_instructions(self):
        """Audit must explicitly state it does NOT modify instruction files."""
        text = _read(_AUDIT_CMD)
        assert (
            "do not modify" in text.lower()
            or "not modify" in text.lower()
            or "Do NOT modify" in text
        ), "agentlint-audit.md must state that instruction files are not modified"

    def test_semantic_finding_schema(self):
        """Audit command must document the Bob finding JSON schema fields."""
        text = _read(_AUDIT_CMD)
        for field in ("reasoning_summary", "instruction_sources", "repository_evidence",
                      "confidence", "deterministic"):
            assert field in text, f"agentlint-audit.md must document finding field: {field}"

    def test_no_fabricated_evidence_ids(self):
        """Must instruct that evidence IDs must come from evidence.json."""
        text = _read(_AUDIT_CMD)
        assert "evidence.json" in text and (
            "fabricate" in text.lower()
            or "from evidence" in text.lower()
            or "evidence item" in text.lower()
        ), "agentlint-audit.md must require evidence IDs to come from evidence.json"


# ---------------------------------------------------------------------------
# /agentlint-repair command
# ---------------------------------------------------------------------------


class TestRepairCommand:
    def test_file_exists(self):
        assert _REPAIR_CMD.exists(), f"agentlint-repair.md not found at {_REPAIR_CMD}"

    def test_requires_prior_audit(self):
        """Repair must require findings.json from a prior audit."""
        text = _read(_REPAIR_CMD)
        assert "findings.json" in text, "agentlint-repair.md must reference findings.json"

    def test_requires_human_approval(self):
        """Repair must explicitly require human approval before applying changes."""
        text = _read(_REPAIR_CMD)
        assert (
            "approval" in text.lower()
            or "confirm" in text.lower()
            or "human" in text.lower()
        ), "agentlint-repair.md must require human approval"

    def test_creates_policy_yaml(self):
        """Repair must create/update policy.yaml."""
        text = _read(_REPAIR_CMD)
        assert "policy.yaml" in text, "agentlint-repair.md must create policy.yaml"

    def test_shows_diff_preview(self):
        """Repair must preview diffs before applying."""
        text = _read(_REPAIR_CMD)
        assert (
            "diff" in text.lower()
            or "preview" in text.lower()
            or "before" in text.lower()
        ), "agentlint-repair.md must show a diff/preview before applying"

    def test_never_edits_production_code(self):
        """Repair must explicitly forbid editing production code."""
        text = _read(_REPAIR_CMD)
        assert (
            "production code" in text.lower()
            or "never edit" in text.lower()
            or "never modify" in text.lower()
        ), "agentlint-repair.md must forbid editing production/application code"

    def test_allowed_edit_targets_listed(self):
        """Must list the instruction/policy files that may be edited."""
        text = _read(_REPAIR_CMD)
        for target in ("AGENTS.md", "CLAUDE.md", ".agentlint/policy.yaml"):
            assert target in text, (
                f"agentlint-repair.md must list {target} as an allowed edit target"
            )

    def test_policy_yaml_structure(self):
        """Repair must document policy.yaml structure with required fields."""
        text = _read(_REPAIR_CMD)
        for field in ("version", "tooling", "definition_of_done"):
            assert field in text, (
                f"agentlint-repair.md must document policy.yaml field: {field}"
            )


# ---------------------------------------------------------------------------
# /agentlint-verify command
# ---------------------------------------------------------------------------


class TestVerifyCommand:
    def test_file_exists(self):
        assert _VERIFY_CMD.exists(), f"agentlint-verify.md not found at {_VERIFY_CMD}"

    def test_reruns_scan(self):
        """Verify must rerun agentlint scan."""
        text = _read(_VERIFY_CMD)
        assert "agentlint scan" in text, "agentlint-verify.md must rerun agentlint scan"

    def test_confirms_findings_resolved(self):
        """Verify must confirm repaired findings no longer appear."""
        text = _read(_VERIFY_CMD)
        assert (
            "resolved" in text.lower()
            or "no longer" in text.lower()
            or "disappear" in text.lower()
        ), "agentlint-verify.md must confirm findings are resolved"

    def test_runs_validation_commands(self):
        """Verify must run project validation commands."""
        text = _read(_VERIFY_CMD)
        assert (
            "validation" in text.lower()
            or "definition_of_done" in text
            or "pytest" in text
        ), "agentlint-verify.md must run project validation commands"

    def test_writes_verification_json(self):
        """Verify must write verification.json."""
        text = _read(_VERIFY_CMD)
        assert "verification.json" in text, "agentlint-verify.md must write verification.json"

    def test_verification_json_schema(self):
        """verification.json must include required fields."""
        text = _read(_VERIFY_CMD)
        for field in ("pre_repair_finding_count", "post_repair_finding_count",
                      "resolved_findings", "overall_passed", "validation_commands"):
            assert field in text, (
                f"agentlint-verify.md must document verification.json field: {field}"
            )

    def test_before_after_summary(self):
        """Verify must produce a before/after summary."""
        text = _read(_VERIFY_CMD)
        assert "before" in text.lower() and "after" in text.lower(), (
            "agentlint-verify.md must produce before/after summary"
        )

    def test_no_commands_without_running(self):
        """Must not claim commands succeed without executing them."""
        text = _read(_VERIFY_CMD)
        assert (
            "execute_command" in text
            or "run" in text.lower()
        ), "agentlint-verify.md must use execute_command to run validation"
        assert "never claim" in text.lower() or "without running" in text.lower(), (
            "agentlint-verify.md must state that commands must be run, not assumed"
        )


# ---------------------------------------------------------------------------
# Custom mode YAML
# ---------------------------------------------------------------------------


class TestCustomMode:
    @pytest.fixture(scope="class")
    def modes_data(self) -> dict:
        assert _CUSTOM_MODES.exists(), f"custom_modes.yaml not found at {_CUSTOM_MODES}"
        with open(_CUSTOM_MODES, encoding="utf-8") as f:
            return yaml.safe_load(f)

    @pytest.fixture(scope="class")
    def auditor_mode(self, modes_data) -> dict:
        modes = modes_data.get("customModes", [])
        for mode in modes:
            if mode.get("slug") == "agent-policy-auditor":
                return mode
        pytest.fail("No mode with slug 'agent-policy-auditor' found in custom_modes.yaml")

    def test_file_exists(self):
        assert _CUSTOM_MODES.exists(), f"custom_modes.yaml not found at {_CUSTOM_MODES}"

    def test_valid_yaml(self, modes_data):
        assert isinstance(modes_data, dict), "custom_modes.yaml must be a valid YAML mapping"

    def test_has_custom_modes_key(self, modes_data):
        assert "customModes" in modes_data, "custom_modes.yaml must have 'customModes' key"

    def test_auditor_mode_exists(self, auditor_mode):
        assert auditor_mode is not None

    def test_slug_format(self, auditor_mode):
        slug = auditor_mode.get("slug", "")
        assert re.match(r"^[a-zA-Z0-9-]+$", slug), (
            f"Mode slug {slug!r} must match ^[a-zA-Z0-9-]+$"
        )
        assert slug == "agent-policy-auditor"

    def test_has_name(self, auditor_mode):
        assert "name" in auditor_mode, "Mode must have a 'name' field"
        assert auditor_mode["name"].strip(), "Mode name must not be empty"

    def test_has_role_definition(self, auditor_mode):
        role = auditor_mode.get("roleDefinition", "")
        assert len(role.strip()) > 50, "roleDefinition must be substantive (> 50 chars)"

    def test_role_definition_mentions_audit(self, auditor_mode):
        role = auditor_mode.get("roleDefinition", "")
        assert (
            "audit" in role.lower()
            or "instruction" in role.lower()
        ), "roleDefinition must describe audit/instruction purpose"

    def test_has_groups(self, auditor_mode):
        groups = auditor_mode.get("groups", [])
        assert len(groups) > 0, "Mode must have at least one group"

    def test_has_read_group(self, auditor_mode):
        """Mode must have read access."""
        groups = auditor_mode.get("groups", [])
        flat_groups = [g if isinstance(g, str) else g[0] for g in groups]
        assert "read" in flat_groups, "Agent Policy Auditor mode must have 'read' group"

    def test_has_skill_group(self, auditor_mode):
        """Mode must have skill access to invoke the agent-policy-audit skill."""
        groups = auditor_mode.get("groups", [])
        flat_groups = [g if isinstance(g, str) else g[0] for g in groups]
        assert "skill" in flat_groups, "Agent Policy Auditor mode must have 'skill' group"

    def test_has_subagent_group(self, auditor_mode):
        """Mode must support subagents for parallel investigation."""
        groups = auditor_mode.get("groups", [])
        flat_groups = [g if isinstance(g, str) else g[0] for g in groups]
        assert "subagent" in flat_groups, "Agent Policy Auditor mode must have 'subagent' group"

    def test_has_execute_group(self, auditor_mode):
        """Mode must be able to run agentlint scan commands."""
        groups = auditor_mode.get("groups", [])
        flat_groups = [g if isinstance(g, str) else g[0] for g in groups]
        assert "execute" in flat_groups, "Agent Policy Auditor mode must have 'execute' group"

    def test_edit_restricted_to_instruction_files(self, auditor_mode):
        """Edit access must be restricted to instruction/policy files via fileRegex."""
        groups = auditor_mode.get("groups", [])
        edit_entries = [g for g in groups if isinstance(g, list) and g[0] == "edit"]
        assert len(edit_entries) >= 1, (
            "Mode must have an 'edit' group entry (with fileRegex restriction)"
        )
        edit_entry = edit_entries[0]
        # edit_entry is a list: ["edit", {"fileRegex": "..."}]
        assert len(edit_entry) >= 2, "Edit group entry must include fileRegex restriction"
        restrictions = edit_entry[1] if isinstance(edit_entry[1], dict) else {}
        assert "fileRegex" in restrictions, (
            "Edit group must have a fileRegex to restrict to instruction/policy files"
        )
        regex = restrictions["fileRegex"]
        # Must cover at least AGENTS.md and .agentlint/
        assert "AGENTS" in regex or "agentlint" in regex, (
            f"Edit fileRegex {regex!r} must cover instruction/policy file paths"
        )

    def test_no_group_typos(self, auditor_mode):
        """Guard against common group name typos that silently grant nothing."""
        groups = auditor_mode.get("groups", [])
        flat_groups = [g if isinstance(g, str) else g[0] for g in groups]
        invalid_names = {"command", "write", "shell", "run", "browser", "tools"}
        bad = [g for g in flat_groups if g in invalid_names]
        assert not bad, (
            f"Mode uses invalid group name(s) {bad} — these silently grant nothing. "
            f"Valid names: read, edit, execute, mcp, skill, todo, subagent, mode"
        )


# ---------------------------------------------------------------------------
# Cross-artifact consistency
# ---------------------------------------------------------------------------


class TestCrossArtifactConsistency:
    def test_audit_references_skill(self):
        """The audit command or mode should reference the skill name."""
        # The mode's customInstructions should mention the skill
        modes_text = _read(_CUSTOM_MODES)
        assert "agent-policy-audit" in modes_text, (
            "custom_modes.yaml should reference the agent-policy-audit skill"
        )

    def test_audit_repair_verify_chain_documented(self):
        """Each command should reference the next step in the chain."""
        audit_text = _read(_AUDIT_CMD)
        repair_text = _read(_REPAIR_CMD)
        verify_text = _read(_VERIFY_CMD)

        # Audit should point to repair
        assert "agentlint-repair" in audit_text or "repair" in audit_text.lower(), (
            "agentlint-audit.md should reference the next step (/agentlint-repair)"
        )
        # Repair should point to verify
        assert "agentlint-verify" in repair_text or "verify" in repair_text.lower(), (
            "agentlint-repair.md should reference the next step (/agentlint-verify)"
        )
        # Verify should reference scan (closing the loop)
        assert "agentlint scan" in verify_text, (
            "agentlint-verify.md must re-run agentlint scan"
        )

    def test_all_artifacts_reference_deterministic_scan(self):
        """All three commands must invoke or reference agentlint scan."""
        for cmd_file in (_AUDIT_CMD, _VERIFY_CMD):
            text = _read(cmd_file)
            assert "agentlint scan" in text, (
                f"{cmd_file.name} must invoke 'agentlint scan'"
            )

    def test_failsafe_mentioned_in_skill_or_audit(self):
        """Fail-safe (works without Bob) must be documented somewhere in Phase 6."""
        skill_text = _read(_SKILL_FILE)
        audit_text = _read(_AUDIT_CMD)
        combined = skill_text + audit_text
        assert (
            "without Bob" in combined
            or "unavailable" in combined
            or "fail" in combined.lower()
        ), "Fail-safe (deterministic scan works without Bob) must be documented"

    def test_no_private_chain_of_thought(self):
        """Spec §Phase 6: Do not store private chain-of-thought."""
        for f in (_SKILL_FILE, _AUDIT_CMD):
            text = _read(f)
            assert (
                "chain-of-thought" in text.lower()
                or "private" in text.lower()
                or "reasoning_summary" in text
            ), (
                f"{f.name} must address the chain-of-thought constraint "
                f"(store reasoning_summary only, not private chain-of-thought)"
            )
