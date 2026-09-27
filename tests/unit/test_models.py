"""Unit tests for agentlint.models (Phase 1).

Covers all six domain model dataclasses:
- InstructionSource
- InstructionRule
- RepositoryEvidence
- Finding
- CanonicalPolicy
- ValidationResult
"""

from __future__ import annotations

from agentlint.models import (
    CanonicalPolicy,
    Finding,
    InstructionRule,
    InstructionSource,
    RepositoryEvidence,
    ValidationResult,
    dataclass_to_dict,
)


# ---------------------------------------------------------------------------
# InstructionSource
# ---------------------------------------------------------------------------

def test_instruction_source_fields() -> None:
    """InstructionSource stores all fields correctly."""
    src = InstructionSource(
        path="AGENTS.md",
        agent_type="openai",
        content_hash="abc123",
        exists=True,
    )
    assert src.path == "AGENTS.md"
    assert src.agent_type == "openai"
    assert src.content_hash == "abc123"
    assert src.exists is True


def test_instruction_source_to_dict() -> None:
    """InstructionSource.to_dict() returns a plain dict with correct values."""
    src = InstructionSource(
        path="CLAUDE.md",
        agent_type="claude",
        content_hash="deadbeef",
        exists=True,
    )
    d = src.to_dict()
    assert isinstance(d, dict)
    assert d["path"] == "CLAUDE.md"
    assert d["agent_type"] == "claude"
    assert d["content_hash"] == "deadbeef"
    assert d["exists"] is True


def test_instruction_source_exists_false_empty_hash() -> None:
    """A missing source has empty content_hash and exists=False."""
    src = InstructionSource(
        path="AGENTS.md",
        agent_type="openai",
        content_hash="",
        exists=False,
    )
    assert src.exists is False
    assert src.content_hash == ""


# ---------------------------------------------------------------------------
# InstructionRule
# ---------------------------------------------------------------------------

def test_instruction_rule_fields() -> None:
    """InstructionRule stores all fields correctly."""
    rule = InstructionRule(
        id="rule-001",
        source_path="AGENTS.md",
        source_agent="openai",
        text="Use npm for all package operations.",
        category="tooling",
        normalized_key="package_manager",
        normalized_value="npm",
        line_start=5,
        line_end=5,
        extraction_method="deterministic",
        confidence=1.0,
    )
    assert rule.id == "rule-001"
    assert rule.extraction_method == "deterministic"
    assert rule.confidence == 1.0
    assert rule.normalized_key == "package_manager"


def test_instruction_rule_nullable_fields() -> None:
    """InstructionRule accepts None for optional fields."""
    rule = InstructionRule(
        id="rule-002",
        source_path="CLAUDE.md",
        source_agent="claude",
        text="Keep commits small.",
        category=None,
        normalized_key=None,
        normalized_value=None,
        line_start=None,
        line_end=None,
        extraction_method="bob",
        confidence=0.7,
    )
    assert rule.category is None
    assert rule.normalized_key is None
    assert rule.line_start is None


# ---------------------------------------------------------------------------
# RepositoryEvidence
# ---------------------------------------------------------------------------

def test_repository_evidence_to_dict() -> None:
    """RepositoryEvidence.to_dict() serialises all fields."""
    ev = RepositoryEvidence(
        id="ev-001",
        category="package_manager",
        key="package_manager",
        value="pnpm",
        source_path="pnpm-lock.yaml",
        source_locator=None,
        strength="strong",
        explanation="pnpm-lock.yaml exists at repository root.",
    )
    d = ev.to_dict()
    assert isinstance(d, dict)
    assert d["id"] == "ev-001"
    assert d["strength"] == "strong"
    assert d["source_locator"] is None
    assert d["value"] == "pnpm"


def test_repository_evidence_strength_values() -> None:
    """RepositoryEvidence.strength accepts strong/medium/weak."""
    for strength in ("strong", "medium", "weak"):
        ev = RepositoryEvidence(
            id="ev-x",
            category="test_framework",
            key="test_framework",
            value="vitest",
            source_path="package.json",
            source_locator="devDependencies.vitest",
            strength=strength,
            explanation="Found vitest in devDependencies.",
        )
        assert ev.strength == strength


# ---------------------------------------------------------------------------
# Finding
# ---------------------------------------------------------------------------

def test_finding_defaults() -> None:
    """Finding.status defaults to 'open'."""
    f = Finding(
        id="F02-001",
        type="F02",
        severity="high",
        title="Package manager mismatch",
        explanation="AGENTS.md says npm but pnpm-lock.yaml exists.",
        instruction_rules=["rule-001"],
        evidence_ids=["ev-001"],
        recommended_action="Update AGENTS.md to reference pnpm.",
        confidence=1.0,
        deterministic=True,
    )
    assert f.status == "open"


def test_finding_explicit_status() -> None:
    """Finding.status can be set to other valid values."""
    for status in ("open", "approved", "repaired", "ignored"):
        f = Finding(
            id="F02-002",
            type="F02",
            severity="medium",
            title="Stale path",
            explanation="Path dist/ does not exist.",
            instruction_rules=[],
            evidence_ids=[],
            recommended_action="Remove or update the path reference.",
            confidence=1.0,
            deterministic=True,
            status=status,
        )
        assert f.status == status


def test_finding_to_dict() -> None:
    """Finding.to_dict() includes all fields including status."""
    f = Finding(
        id="F05-001",
        type="F05",
        severity="low",
        title="Duplicate rule",
        explanation="Same rule appears twice.",
        instruction_rules=["rule-001", "rule-002"],
        evidence_ids=[],
        recommended_action="Remove one copy.",
        confidence=1.0,
        deterministic=True,
        status="open",
    )
    d = f.to_dict()
    assert d["status"] == "open"
    assert d["deterministic"] is True
    assert d["instruction_rules"] == ["rule-001", "rule-002"]


def test_finding_deterministic_flag() -> None:
    """Finding.deterministic distinguishes engine-produced from Bob-inferred."""
    f_det = Finding(
        id="F02-003",
        type="F02",
        severity="high",
        title="Mismatch",
        explanation="...",
        instruction_rules=[],
        evidence_ids=[],
        recommended_action="...",
        confidence=1.0,
        deterministic=True,
    )
    f_bob = Finding(
        id="F07-001",
        type="F07",
        severity="info",
        title="Ambiguous",
        explanation="...",
        instruction_rules=[],
        evidence_ids=[],
        recommended_action="...",
        confidence=0.6,
        deterministic=False,
    )
    assert f_det.deterministic is True
    assert f_bob.deterministic is False


# ---------------------------------------------------------------------------
# CanonicalPolicy
# ---------------------------------------------------------------------------

def test_canonical_policy_fields() -> None:
    """CanonicalPolicy stores all fields correctly."""
    policy = CanonicalPolicy(
        version=1,
        project_name="my-project",
        tooling={"package_manager": "pnpm", "test_framework": "vitest"},
        runtime={"language": "typescript", "node_version": "20"},
        paths={"src": "src/", "tests": "tests/"},
        definition_of_done=["All tests pass", "Lint passes"],
        evidence={"package_manager": ["ev-001"]},
    )
    assert policy.version == 1
    assert policy.project_name == "my-project"
    assert policy.tooling["package_manager"] == "pnpm"
    assert len(policy.definition_of_done) == 2


def test_canonical_policy_to_dict() -> None:
    """CanonicalPolicy.to_dict() serialises correctly."""
    policy = CanonicalPolicy(
        version=1,
        project_name=None,
        tooling={},
        runtime={},
        paths={},
        definition_of_done=[],
        evidence={},
    )
    d = policy.to_dict()
    assert isinstance(d, dict)
    assert d["version"] == 1
    assert d["project_name"] is None


# ---------------------------------------------------------------------------
# ValidationResult
# ---------------------------------------------------------------------------

def test_validation_result_fields() -> None:
    """ValidationResult stores all fields correctly."""
    vr = ValidationResult(
        check_id="check-001",
        name="pytest passes",
        command="pytest",
        passed=True,
        duration_ms=1234,
        stdout_excerpt="3 passed",
        stderr_excerpt=None,
        evidence=["ev-001"],
    )
    assert vr.check_id == "check-001"
    assert vr.passed is True
    assert vr.duration_ms == 1234
    assert vr.stderr_excerpt is None


def test_validation_result_nullable_command() -> None:
    """ValidationResult.command can be None for non-command checks."""
    vr = ValidationResult(
        check_id="check-002",
        name="file exists",
        command=None,
        passed=False,
        duration_ms=None,
        stdout_excerpt=None,
        stderr_excerpt=None,
        evidence=[],
    )
    assert vr.command is None
    assert vr.passed is False


def test_validation_result_to_dict() -> None:
    """ValidationResult.to_dict() serialises all fields."""
    vr = ValidationResult(
        check_id="check-003",
        name="lint",
        command="ruff check .",
        passed=True,
        duration_ms=500,
        stdout_excerpt="No issues",
        stderr_excerpt=None,
        evidence=["ev-002"],
    )
    d = vr.to_dict()
    assert isinstance(d, dict)
    assert d["check_id"] == "check-003"
    assert d["passed"] is True


# ---------------------------------------------------------------------------
# dataclass_to_dict utility
# ---------------------------------------------------------------------------

def test_dataclass_to_dict_utility() -> None:
    """dataclass_to_dict works for any dataclass."""
    src = InstructionSource(
        path="AGENTS.md",
        agent_type="openai",
        content_hash="abc",
        exists=True,
    )
    d = dataclass_to_dict(src)
    assert isinstance(d, dict)
    assert d["path"] == "AGENTS.md"
