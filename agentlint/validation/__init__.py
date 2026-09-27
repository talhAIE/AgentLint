"""Validation sub-package — Phase 8.

Provides the verification engine that runs all four post-repair verification
layers and produces .agentlint/verification.json.

Public API:
    run_verification(repo_path, *, skip_commands=False, command_timeout=60) -> dict
    run_structural_check(repo_path, approved_finding_ids) -> list[ValidationResult]
    run_consistency_check(repo_path)                      -> list[ValidationResult]
    run_evidence_check(policy, evidence)                  -> list[ValidationResult]
    run_command_validation(policy, repo_path, ...)        -> list[ValidationResult]
"""

from __future__ import annotations

from agentlint.validation.commands import run_command_validation
from agentlint.validation.evidence_check import run_evidence_check
from agentlint.validation.runner import run_verification
from agentlint.validation.structural import run_consistency_check, run_structural_check

__all__ = [
    "run_verification",
    "run_structural_check",
    "run_consistency_check",
    "run_evidence_check",
    "run_command_validation",
]
