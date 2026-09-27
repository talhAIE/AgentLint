"""Policy schema — Phase 7.

Provides YAML serialization for :class:`~agentlint.models.CanonicalPolicy`.

Public API:
    policy_to_yaml(policy)                -> str
    write_policy_yaml(repo_path, policy)  -> Path
"""

from __future__ import annotations

from pathlib import Path

import yaml

from agentlint.models import CanonicalPolicy

# Schema version — bump when the policy.yaml structure changes in a
# backward-incompatible way.
POLICY_SCHEMA_VERSION = 1


def _policy_to_dict(policy: CanonicalPolicy) -> dict:
    """Convert *policy* to a plain dict suitable for ``yaml.dump``.

    The structure matches the example in AgentLintplan.md §11:

    .. code-block:: yaml

        version: 1
        project:
          name: sample-store
        tooling:
          package_manager: pnpm
          ...
        runtime:
          node: "22"
        paths:
          generated: [...]
          protected: [...]
        definition_of_done:
          - pnpm lint
          ...
        evidence:
          package_manager:
            - package.json#packageManager
            ...
    """
    d: dict = {"version": policy.version}

    # project block — only include if name is set
    if policy.project_name:
        d["project"] = {"name": policy.project_name}

    # tooling block — include all non-None values
    tooling: dict = {}
    for key, val in policy.tooling.items():
        if val is not None:
            tooling[key] = val
    if tooling:
        d["tooling"] = tooling

    # runtime block — include all non-None values
    runtime: dict = {}
    for key, val in policy.runtime.items():
        if val is not None:
            runtime[key] = val
    if runtime:
        d["runtime"] = runtime

    # paths block
    if policy.paths:
        paths: dict = {}
        if policy.paths.get("generated"):
            paths["generated"] = policy.paths["generated"]
        if policy.paths.get("protected"):
            paths["protected"] = policy.paths["protected"]
        if paths:
            d["paths"] = paths

    # definition_of_done
    if policy.definition_of_done:
        d["definition_of_done"] = list(policy.definition_of_done)

    # evidence block
    if policy.evidence:
        ev: dict = {}
        for key, sources in policy.evidence.items():
            if sources:
                ev[key] = list(sources)
        if ev:
            d["evidence"] = ev

    return d


def policy_to_yaml(policy: CanonicalPolicy) -> str:
    """Serialize *policy* to a YAML string.

    Uses ``sort_keys=False`` to preserve the canonical field ordering
    from ``AgentLintplan.md §11``.

    Args:
        policy: The :class:`~agentlint.models.CanonicalPolicy` to serialize.

    Returns:
        A UTF-8 YAML string with a trailing newline.
    """
    return yaml.dump(
        _policy_to_dict(policy),
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    )


def write_policy_yaml(repo_path: Path, policy: CanonicalPolicy) -> Path:
    """Write ``.agentlint/policy.yaml`` inside *repo_path* and return the path.

    Creates ``.agentlint/`` if it does not exist.

    Args:
        repo_path: Root of the scanned repository.
        policy:    The compiled :class:`~agentlint.models.CanonicalPolicy`.

    Returns:
        The :class:`~pathlib.Path` of the written file.
    """
    output_dir = Path(repo_path) / ".agentlint"
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / "policy.yaml"
    output_path.write_text(policy_to_yaml(policy), encoding="utf-8")
    return output_path
