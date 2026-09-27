"""Validation runner — Phase 8.

Orchestrates all four verification layers (A → B → C → D) and writes
.agentlint/verification.json.

Public API:
    run_verification(
        repo_path, *, skip_commands=False, command_timeout=60
    ) -> dict
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import agentlint
from agentlint.models import CanonicalPolicy, ValidationResult
from agentlint.validation.commands import run_command_validation
from agentlint.validation.evidence_check import run_evidence_check
from agentlint.validation.structural import run_consistency_check, run_structural_check


# ---------------------------------------------------------------------------
# Internal helpers — artifact loading
# ---------------------------------------------------------------------------


def _load_approved_ids(repo_path: Path) -> list[str]:
    """Load IDs of approved findings from ``.agentlint/findings.json``.

    Returns an empty list when the file does not exist or has no approved
    findings.
    """
    findings_path = repo_path / ".agentlint" / "findings.json"
    if not findings_path.exists():
        return []

    try:
        data = json.loads(findings_path.read_text(encoding="utf-8"))
        return [
            f["id"]
            for f in data.get("findings", [])
            if f.get("status") == "approved"
        ]
    except (json.JSONDecodeError, KeyError):
        return []


def _load_policy(repo_path: Path) -> CanonicalPolicy | None:
    """Load the compiled policy from ``.agentlint/policy.yaml``.

    Returns ``None`` when the file does not exist or cannot be parsed.
    """
    policy_path = repo_path / ".agentlint" / "policy.yaml"
    if not policy_path.exists():
        return None

    try:
        import yaml  # PyYAML is already required by Phase 7

        data = yaml.safe_load(policy_path.read_text(encoding="utf-8")) or {}

        project = data.get("project") or {}
        return CanonicalPolicy(
            version=data.get("version", 1),
            project_name=project.get("name"),
            tooling=data.get("tooling") or {},
            runtime=data.get("runtime") or {},
            paths=data.get("paths") or {},
            definition_of_done=data.get("definition_of_done") or [],
            evidence=data.get("evidence") or {},
        )
    except Exception:  # noqa: BLE001
        return None


def _format_human_report(
    results: list[ValidationResult],
    repo_path: Path,
    summary: dict,
) -> str:
    """Render a Markdown human-readable verification report."""
    lines: list[str] = [
        "# AgentLint Verification Report",
        "",
        f"Repository: `{repo_path}`",
        f"AgentLint version: {agentlint.__version__}",
        "",
        "## Summary",
        "",
        f"- Total checks: {summary['total']}",
        f"- Passed: {summary['passed']}",
        f"- Failed: {summary['failed']}",
        "",
        "## Claim",
        "",
        "> The repaired instruction files are consistent with the evidence "
        "and the configured validation commands passed.",
        ">",
        "> AgentLint does NOT claim that every AI coding agent will now "
        "behave perfectly. Behavioural verification is beyond the scope of "
        "this tool.",
        "",
        "## Results",
        "",
    ]

    for r in results:
        status = "✅ PASS" if r.passed else "❌ FAIL"
        lines.append(f"### {status} — {r.name}")
        if r.command:
            lines.append(f"Command: `{r.command}`")
        if r.stdout_excerpt:
            lines.append("")
            lines.append(f"```\n{r.stdout_excerpt}\n```")
        if r.stderr_excerpt:
            lines.append("")
            lines.append(f"**stderr:** `{r.stderr_excerpt}`")
        if r.duration_ms is not None:
            lines.append(f"Duration: {r.duration_ms} ms")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_verification(
    repo_path: Path | str,
    *,
    skip_commands: bool = False,
    command_timeout: int = 60,
) -> dict:
    """Run all four verification layers and write ``.agentlint/verification.json``.

    Layer A — Structural Re-scan: confirm approved findings are gone.
    Layer B — Policy Evidence Check: confirm policy fields still have evidence.
    Layer C — Command Validation: run safe commands, capture exit codes.
    Layer D — Instruction Consistency: no remaining conflicts or duplicates.

    Args:
        repo_path:       Root of the repository to verify.
        skip_commands:   When ``True``, Layer C skips subprocess execution.
        command_timeout: Per-command timeout in seconds (default 60).

    Returns:
        The verification report dict (also written to
        ``.agentlint/verification.json`` and ``.agentlint/verification.md``).

    Raises:
        FileNotFoundError: When neither ``findings.json`` nor ``policy.yaml``
                           exists — the caller should produce a helpful error
                           rather than letting this propagate.
    """
    repo_path = Path(repo_path)
    output_dir = repo_path / ".agentlint"
    output_dir.mkdir(exist_ok=True)

    # Load artifacts
    approved_ids = _load_approved_ids(repo_path)
    policy = _load_policy(repo_path)

    # If no policy, build an empty one so layers B/C still run meaningfully
    if policy is None:
        policy = CanonicalPolicy(
            version=1,
            project_name=None,
            tooling={},
            runtime={},
            paths={},
            definition_of_done=[],
            evidence={},
        )

    # Collect fresh evidence for Layer B
    try:
        from agentlint.evidence import collect_evidence

        fresh_evidence = collect_evidence(repo_path)
    except Exception:  # noqa: BLE001
        fresh_evidence = []

    # -------------------------------------------------------------------
    # Run layers
    # -------------------------------------------------------------------
    all_results: list[ValidationResult] = []

    # Layer A — Structural Re-scan
    all_results.extend(run_structural_check(repo_path, approved_ids))

    # Layer B — Policy Evidence Check
    all_results.extend(run_evidence_check(policy, fresh_evidence))

    # Layer C — Command Validation
    all_results.extend(
        run_command_validation(
            policy,
            repo_path,
            timeout_sec=command_timeout,
            skip_execution=skip_commands,
        )
    )

    # Layer D — Instruction Consistency
    all_results.extend(run_consistency_check(repo_path))

    # -------------------------------------------------------------------
    # Build report
    # -------------------------------------------------------------------
    passed_count = sum(1 for r in all_results if r.passed)
    failed_count = sum(1 for r in all_results if not r.passed)

    summary = {
        "total": len(all_results),
        "passed": passed_count,
        "failed": failed_count,
    }

    report = {
        "agentlint_version": agentlint.__version__,
        "repo_path": str(repo_path.resolve()),
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "summary": summary,
        "results": [r.to_dict() for r in all_results],
    }

    # Write JSON
    json_path = output_dir / "verification.json"
    json_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Write human-readable Markdown report
    md_path = output_dir / "verification.md"
    md_path.write_text(
        _format_human_report(all_results, repo_path, summary),
        encoding="utf-8",
    )

    return report
