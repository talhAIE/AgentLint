"""AgentLint CLI entry point.

Provides the ``agentlint`` command with subcommands.
Phase 1 implements ``agentlint scan <repo-path>``.
Phase 2 extends scan to collect repository evidence and write evidence.json.
Phase 3 extends scan to parse instruction rules and write rules.json.
Phase 4 extends scan to run deterministic finding checks and write findings.json.
Phase 5 adds ``agentlint demo`` to run all three packaged demo repos.
Phase 7 adds ``agentlint policy <repo-path>`` to compile canonical policy.yaml
         and repair-plan.md from repository evidence.
Phase 8 adds ``agentlint validate <repo-path>`` to run the verification engine.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import NamedTuple

import typer

import agentlint
from agentlint.analysis import SEVERITY_ORDER, run_deterministic_checks, write_findings_json
from agentlint.analysis.report_builder import (
    format_ci_failure_block,
    format_ci_pass_block,
    format_findings_summary,
)
from agentlint.config import AgentLintConfigError, load_config
from agentlint.discovery.instruction_sources import discover_sources
from agentlint.evidence import collect_evidence, write_evidence_json
from agentlint.models import Finding, InstructionRule, RepositoryEvidence
from agentlint.parsing import extract_rules, write_rules_json
from agentlint.policy import (
    compile_policy,
    generate_repair_items,
    write_policy_yaml,
    write_repair_plan,
)
from agentlint.validation import run_verification

app = typer.Typer(
    name="agentlint",
    help="Audit AI coding-agent instruction files for drift against the repository.",
    add_completion=False,
    no_args_is_help=True,
)


# Valid severity levels accepted by --fail-on-severity (plus "none" to disable).
_VALID_SEVERITY_LEVELS = ("critical", "high", "medium", "low", "info", "none")


@app.command("scan")
def scan(
    repo_path: str = typer.Argument(
        ...,
        help="Path to the repository to scan.",
    ),
    fail_on_severity: str = typer.Option(
        "none",
        "--fail-on-severity",
        help=(
            "Exit 1 if any finding meets or exceeds this severity level "
            "(critical|high|medium|low|info|none). "
            "Default: none (never fail on findings). "
            "Example: --fail-on-severity high"
        ),
    ),
) -> None:
    """Scan a repository for agent instruction files and report findings.

    Phase 1: discovers instruction sources and writes .agentlint/scan.json.
    Phase 2: collects repository evidence and writes .agentlint/evidence.json.
    Phase 3: extracts instruction rules and writes .agentlint/rules.json.
    Phase 4: runs deterministic finding checks and writes .agentlint/findings.json.
    Phase 10: --fail-on-severity exits 1 when qualifying findings are found.
    """
    path = Path(repo_path)

    if not path.exists():
        typer.echo(f"Error: path does not exist: {repo_path}", err=True)
        raise typer.Exit(code=1)

    if not path.is_dir():
        typer.echo(f"Error: path is not a directory: {repo_path}", err=True)
        raise typer.Exit(code=1)

    # Load config (returns defaults if .agentlint/config.yaml is missing).
    try:
        config = load_config(path)
    except AgentLintConfigError as exc:
        typer.echo(f"Error loading config: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    # Discover instruction sources.
    sources = discover_sources(path, config)

    # Print summary to stdout.
    existing = [s for s in sources if s.exists]
    typer.echo(
        f"AgentLint {agentlint.__version__} - scanning {path.resolve()}"
    )
    typer.echo(
        f"Found {len(existing)} instruction source(s) "
        f"(checked {len(sources)} candidate location(s)):"
    )
    for src in sources:
        mark = "+" if src.exists else "-"
        typer.echo(f"  [{mark}] {src.path}  (agent_type={src.agent_type})")

    # Write .agentlint/scan.json inside the scanned repo.
    output_dir = path / ".agentlint"
    output_dir.mkdir(exist_ok=True)
    scan_output = {
        "agentlint_version": agentlint.__version__,
        "repo_path": str(path.resolve()),
        "sources": [s.to_dict() for s in sources],
    }
    scan_json_path = output_dir / "scan.json"
    scan_json_path.write_text(
        json.dumps(scan_output, indent=2),
        encoding="utf-8",
    )
    typer.echo(f"\nWrote {scan_json_path}")

    # --- Phase 2: Collect repository evidence ---
    evidence = collect_evidence(path)

    # Print brief evidence summary.
    if evidence:
        # Build a condensed view: category → distinct values
        category_values: dict[str, list[str]] = {}
        for ev in evidence:
            category_values.setdefault(ev.category, [])
            if ev.value not in category_values[ev.category]:
                category_values[ev.category].append(ev.value)

        summary_parts = [
            f"{cat}: {', '.join(vals)}"
            for cat, vals in category_values.items()
            if cat not in ("paths",)  # paths list can be long — omit from summary
        ]
        path_count = sum(1 for ev in evidence if ev.category == "paths")
        if path_count:
            summary_parts.append(f"paths: {path_count} director(ies) indexed")

        typer.echo(
            f"Evidence: {len(evidence)} item(s) collected -- "
            + "; ".join(summary_parts)
        )
    else:
        typer.echo("Evidence: 0 items collected (no recognised project files found).")

    # Write .agentlint/evidence.json
    evidence_json_path = write_evidence_json(path, evidence)
    typer.echo(f"Wrote {evidence_json_path}")

    # --- Phase 3: Parse instruction rules ---
    rules = extract_rules(sources, repo_path=path)

    # Print per-source rule count breakdown
    source_counts: dict[str, int] = {}
    for rule in rules:
        source_counts[rule.source_path] = source_counts.get(rule.source_path, 0) + 1

    existing_source_count = len([s for s in sources if s.exists])
    typer.echo(
        f"Rules: {len(rules)} rule(s) extracted from {existing_source_count} source(s)"
    )
    for src_path, count in source_counts.items():
        typer.echo(f"  {Path(src_path).name}: {count} rules")

    # Write .agentlint/rules.json
    rules_json_path = write_rules_json(path, rules)
    typer.echo(f"Wrote {rules_json_path}")

    # --- Phase 4: Run deterministic finding checks ---
    findings = run_deterministic_checks(rules, evidence)

    # Print findings summary
    summary = format_findings_summary(findings)
    typer.echo(summary)

    # Write .agentlint/findings.json
    findings_json_path = write_findings_json(path, findings)
    typer.echo(f"Wrote {findings_json_path}")

    # --- Phase 10: CI exit-code enforcement ---
    threshold = fail_on_severity.strip().lower()
    if threshold != "none":
        if threshold not in SEVERITY_ORDER:
            typer.echo(
                f"Error: invalid --fail-on-severity value '{fail_on_severity}'. "
                f"Valid values: {', '.join(_VALID_SEVERITY_LEVELS)}",
                err=True,
            )
            raise typer.Exit(code=1)

        threshold_rank = SEVERITY_ORDER[threshold]
        breaching = [
            f for f in findings
            if SEVERITY_ORDER.get(f.severity, 99) <= threshold_rank
        ]

        if breaching:
            typer.echo("")
            typer.echo(format_ci_failure_block(breaching, threshold))
            raise typer.Exit(code=1)
        else:
            typer.echo("")
            typer.echo(format_ci_pass_block())


# Resolve demo repos relative to this file's location (works for editable install)
_DEMO_REPOS_DIR = Path(__file__).resolve().parent.parent / "demo_repos"

_DEMO_REPOS = [
    "inconsistent-js-repo",
    "single-agent-stale-repo",
    "clean-repo",
]


class _PipelineResult(NamedTuple):
    """Return type for :func:`_run_pipeline`."""

    evidence: list[RepositoryEvidence]
    rules: list[InstructionRule]
    findings: list[Finding]


def _run_pipeline(path: Path) -> _PipelineResult | None:
    """Run the full scan pipeline for *path*, write outputs, and return results.

    Returns ``None`` when the config cannot be loaded (error already printed).
    """
    try:
        config = load_config(path)
    except AgentLintConfigError as exc:
        typer.echo(f"  [config error] {exc}", err=True)
        return None

    sources = discover_sources(path, config)
    evidence = collect_evidence(path)
    rules = extract_rules(sources, repo_path=path)
    findings = run_deterministic_checks(rules, evidence)

    # Write outputs
    output_dir = path / ".agentlint"
    output_dir.mkdir(exist_ok=True)

    scan_output = {
        "agentlint_version": agentlint.__version__,
        "repo_path": str(path.resolve()),
        "sources": [s.to_dict() for s in sources],
    }
    (output_dir / "scan.json").write_text(
        json.dumps(scan_output, indent=2), encoding="utf-8"
    )
    write_evidence_json(path, evidence)
    write_rules_json(path, rules)
    write_findings_json(path, findings)

    return _PipelineResult(evidence=evidence, rules=rules, findings=findings)


def _run_scan_for_path(path: Path) -> None:
    """Run the full scan pipeline for *path* and print a brief summary.

    Delegates to :func:`_run_pipeline`; kept for ``demo`` command compatibility.
    """
    result = _run_pipeline(path)
    if result is None:
        return

    existing_count = len(
        [
            line
            for line in (path / ".agentlint" / "scan.json").read_text(encoding="utf-8").splitlines()
            if '"exists": true' in line
        ]
    )
    high_or_critical = [
        f for f in result.findings if f.severity in ("critical", "high")
    ]
    typer.echo(
        f"  Rules: {len(result.rules)} | "
        f"Findings: {len(result.findings)} total, {len(high_or_critical)} high/critical"
    )


@app.command("policy")
def policy(
    repo_path: str = typer.Argument(
        ...,
        help="Path to the repository to compile policy for.",
    ),
) -> None:
    """Compile a candidate canonical policy from repository evidence.

    Produces:

    * ``.agentlint/policy.yaml``  — traceable tooling contract
    * ``.agentlint/repair-plan.md`` — per-finding patch previews

    No changes are applied.  Human approval is required before any instruction
    file is modified.
    """
    path = Path(repo_path)

    if not path.exists():
        typer.echo(f"Error: path does not exist: {repo_path}", err=True)
        raise typer.Exit(code=1)

    if not path.is_dir():
        typer.echo(f"Error: path is not a directory: {repo_path}", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"AgentLint {agentlint.__version__} - compiling policy for {path.resolve()}")

    # --- Run the full scan pipeline to get fresh evidence/rules/findings ---
    result = _run_pipeline(path)
    if result is None:
        raise typer.Exit(code=1)

    evidence, rules, findings = result

    # --- Compile candidate policy from evidence ---
    policy_obj = compile_policy(evidence, path)
    policy_path = write_policy_yaml(path, policy_obj)
    typer.echo(f"\nWrote {policy_path}")

    # Print tooling summary
    tooling = policy_obj.tooling
    if tooling:
        typer.echo("\nDetected tooling:")
        for key, val in tooling.items():
            if val is not None:
                typer.echo(f"  {key}: {val}")
    else:
        typer.echo("\nNo tooling detected from repository evidence.")

    if policy_obj.definition_of_done:
        typer.echo("\nDefinition of done:")
        for cmd in policy_obj.definition_of_done:
            typer.echo(f"  - {cmd}")

    # --- Generate repair items from findings ---
    repair_items = generate_repair_items(findings, rules, evidence)
    repair_path = write_repair_plan(path, repair_items)
    typer.echo(f"\nWrote {repair_path}")

    if repair_items:
        typer.echo(f"\n{len(repair_items)} repair item(s) proposed.")
        typer.echo("Approval required before changes are applied.")
        typer.echo(
            "Review repair-plan.md and mark findings as 'approved' in findings.json."
        )
    else:
        typer.echo("\nNo repair items generated. No instruction changes required.")


@app.command("validate")
def validate(
    repo_path: str = typer.Argument(
        ...,
        help="Path to the repository to verify.",
    ),
    skip_commands: bool = typer.Option(
        False,
        "--skip-commands",
        help="Skip subprocess command execution (safe for CI and demo mode).",
    ),
    timeout: int = typer.Option(
        60,
        "--timeout",
        help="Per-command timeout in seconds (default: 60).",
    ),
) -> None:
    """Verify that repairs are consistent with repository evidence.

    Runs all four verification layers:

    * Layer A — Structural Re-scan: approved findings disappeared.
    * Layer B — Policy Evidence Check: policy fields still backed by evidence.
    * Layer C — Command Validation: safe commands pass (use --skip-commands to skip).
    * Layer D — Instruction Consistency: no remaining conflicts or duplicates.

    Requires ``.agentlint/findings.json`` and ``.agentlint/policy.yaml`` to exist.
    Run ``agentlint policy <repo>`` first if they do not.
    """
    path = Path(repo_path)

    if not path.exists():
        typer.echo(f"Error: path does not exist: {repo_path}", err=True)
        raise typer.Exit(code=1)

    if not path.is_dir():
        typer.echo(f"Error: path is not a directory: {repo_path}", err=True)
        raise typer.Exit(code=1)

    # Verify prerequisite artifacts exist — provide helpful guidance if not
    findings_json = path / ".agentlint" / "findings.json"
    policy_yaml = path / ".agentlint" / "policy.yaml"

    missing: list[str] = []
    if not findings_json.exists():
        missing.append("findings.json")
    if not policy_yaml.exists():
        missing.append("policy.yaml")

    if missing:
        typer.echo(
            f"Error: missing required artifact(s): {', '.join(missing)}", err=True
        )
        typer.echo(
            f"Run 'agentlint policy {repo_path}' first to generate these files.",
            err=True,
        )
        raise typer.Exit(code=1)

    typer.echo(
        f"AgentLint {agentlint.__version__} - verifying {path.resolve()}"
    )
    if skip_commands:
        typer.echo("  (command execution disabled via --skip-commands)")

    report = run_verification(
        path,
        skip_commands=skip_commands,
        command_timeout=timeout,
    )

    summary = report["summary"]
    results = report["results"]

    typer.echo("")
    for r in results:
        status = "[PASS]" if r["passed"] else "[FAIL]"
        typer.echo(f"  {status} {r['name']}")
        if r.get("stdout_excerpt"):
            # Print first line of excerpt only for brevity
            first_line = r["stdout_excerpt"].splitlines()[0]
            typer.echo(f"         {first_line}")

    typer.echo("")
    typer.echo(
        f"Result: {summary['passed']}/{summary['total']} checks passed"
        + (f", {summary['failed']} failed" if summary["failed"] else "")
    )

    # Write paths
    typer.echo(f"\nWrote {path / '.agentlint' / 'verification.json'}")
    typer.echo(f"Wrote {path / '.agentlint' / 'verification.md'}")

    if summary["failed"] > 0:
        raise typer.Exit(code=1)


@app.command("demo")
def demo() -> None:
    """Run AgentLint against the three bundled demo repositories."""
    if not _DEMO_REPOS_DIR.exists():
        typer.echo(
            f"Error: demo_repos/ not found at {_DEMO_REPOS_DIR}. "
            "Ensure you are running from an editable install (pip install -e .).",
            err=True,
        )
        raise typer.Exit(code=1)

    typer.echo(
        f"AgentLint {agentlint.__version__} — demo mode "
        f"({len(_DEMO_REPOS)} repositories)"
    )
    typer.echo("")

    for repo_name in _DEMO_REPOS:
        repo_path = _DEMO_REPOS_DIR / repo_name
        typer.echo(f"[{repo_name}]")
        if not repo_path.is_dir():
            typer.echo(f"  Warning: directory not found: {repo_path}", err=True)
            continue
        _run_scan_for_path(repo_path)
        typer.echo("")

    typer.echo("Demo complete.")


@app.command("ui")
def ui(
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind the server to."),
    port: int = typer.Option(8000, "--port", help="Port to bind the server to."),
) -> None:
    """Launch the AgentLint UI (FastAPI backend + React frontend)."""
    import uvicorn
    import webbrowser
    import threading
    import time
    import subprocess
    
    frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
    dist_dir = frontend_dir / "dist"
    
    if frontend_dir.exists() and not (dist_dir / "index.html").exists():
        typer.echo("Building frontend UI...")
        subprocess.run(["npm", "install"], cwd=frontend_dir, check=True, shell=True)
        subprocess.run(["npm", "run", "build"], cwd=frontend_dir, check=True, shell=True)
    
    url = f"http://{host}:{port}"
    typer.echo(f"Starting AgentLint UI at {url}")
    
    def open_browser() -> None:
        time.sleep(1)
        webbrowser.open(url)
        
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("agentlint.server.app:create_app", host=host, port=port, factory=True)


def main() -> None:
    """Entry point called by the ``agentlint`` console script."""
    app()


if __name__ == "__main__":
    main()
