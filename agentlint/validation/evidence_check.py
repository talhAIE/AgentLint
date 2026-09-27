"""Evidence check — Phase 8.

Layer B: Verify that every high-value field in policy.yaml still has current
evidence backing in the repository.

Public API:
    run_evidence_check(policy, evidence) -> list[ValidationResult]
"""

from __future__ import annotations

from agentlint.models import CanonicalPolicy, RepositoryEvidence, ValidationResult

# ---------------------------------------------------------------------------
# High-value fields: maps policy path → (evidence_category, match_on_value)
# match_on_value=True  → compare evidence.value to the policy field value
# match_on_value=False → just confirm evidence of that category exists
# ---------------------------------------------------------------------------

_HIGH_VALUE_FIELDS: list[tuple[str, str, str, bool]] = [
    # (check_id_suffix, policy_display_name, evidence_category, match_on_value)
    ("package_manager", "package_manager", "package_manager", True),
    ("test_framework", "test_framework", "test_framework", True),
    ("lint_command", "lint_command", "commands", False),
    ("test_command", "test_command", "commands", False),
    ("build_command", "build_command", "commands", False),
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_evidence_check(
    policy: CanonicalPolicy,
    evidence: list[RepositoryEvidence],
) -> list[ValidationResult]:
    """Verify each high-value policy field against the current evidence set.

    For each field in ``_HIGH_VALUE_FIELDS``:

    * If the field is not present in the policy, the check is skipped (info
      pass — nothing to verify).
    * If matching evidence exists, the check passes.
    * If no matching evidence exists, the check fails.

    Args:
        policy:   The compiled :class:`~agentlint.models.CanonicalPolicy`.
        evidence: Current repository evidence (from collect_evidence).

    Returns:
        A :class:`~agentlint.models.ValidationResult` list — one entry per
        high-value field that is populated in the policy.
    """
    results: list[ValidationResult] = []

    # Index evidence by category for quick lookup
    by_category: dict[str, list[RepositoryEvidence]] = {}
    for ev in evidence:
        by_category.setdefault(ev.category, []).append(ev)

    for suffix, display, category, match_value in _HIGH_VALUE_FIELDS:
        # Determine the policy value for this field
        policy_value: str | None = policy.tooling.get(display)

        if not policy_value:
            # Field is absent from the policy — nothing to verify
            continue

        candidates = by_category.get(category, [])

        if match_value:
            # Check that evidence value matches the policy value (case-insensitive)
            matching_ev = [
                ev for ev in candidates
                if ev.value.lower() == policy_value.lower()
            ]
        else:
            # For command fields just confirm evidence of that category exists
            # Commands evidence key holds the command type (lint/test/build)
            cmd_key = suffix.replace("_command", "")
            matching_ev = [ev for ev in candidates if ev.key == cmd_key]

        passed = len(matching_ev) > 0
        ev_refs = [
            (f"{ev.source_path}#{ev.source_locator}" if ev.source_locator else ev.source_path)
            for ev in matching_ev
        ]

        if passed:
            excerpt = (
                f"PASS — policy.{display}={policy_value!r} "
                f"— evidence: {', '.join(ev_refs) or 'present'}"
            )
        else:
            excerpt = (
                f"FAIL — policy.{display}={policy_value!r} "
                f"— no supporting evidence found in repository"
            )

        results.append(
            ValidationResult(
                check_id=f"layer-b-{suffix}",
                name=f"Policy Evidence Check: {display}",
                command=None,
                passed=passed,
                duration_ms=None,
                stdout_excerpt=excerpt,
                stderr_excerpt=None,
                evidence=ev_refs,
            )
        )

    if not results:
        # Policy has no high-value fields populated — return a single info pass
        results.append(
            ValidationResult(
                check_id="layer-b-no-policy",
                name="Policy Evidence Check",
                command=None,
                passed=True,
                duration_ms=None,
                stdout_excerpt=(
                    "PASS — no high-value policy fields are set; "
                    "run 'agentlint policy <repo>' to compile a policy first."
                ),
                stderr_excerpt=None,
                evidence=[],
            )
        )

    return results
