"""Policy sub-package — Phase 7.

Converts repository evidence into a candidate canonical policy and repair plan.

Public API:
    compile_policy(evidence, repo_path)             -> CanonicalPolicy
    policy_to_yaml(policy)                          -> str
    write_policy_yaml(repo_path, policy)            -> Path
    RepairItem                                      — dataclass
    generate_repair_items(findings, rules, evidence)-> list[RepairItem]
    format_repair_plan(items)                       -> str
    write_repair_plan(repo_path, items)             -> Path
    build_text_preview(item, file_content)          -> str
    apply_repair(item, file_content)                -> str  (Phase 8 stub)
"""

from __future__ import annotations

from agentlint.policy.adapters import apply_repair, build_text_preview
from agentlint.policy.compiler import compile_policy
from agentlint.policy.diff import (
    RepairItem,
    format_repair_plan,
    generate_repair_items,
    write_repair_plan,
)
from agentlint.policy.schema import policy_to_yaml, write_policy_yaml

__all__ = [
    "compile_policy",
    "policy_to_yaml",
    "write_policy_yaml",
    "RepairItem",
    "generate_repair_items",
    "format_repair_plan",
    "write_repair_plan",
    "build_text_preview",
    "apply_repair",
]
