"""AgentLint CLI entry point.

Provides the ``agentlint`` command with subcommands.
Phase 1 implements ``agentlint scan <repo-path>``.
Phase 2 extends scan to collect repository evidence and write evidence.json.
Phase 3 extends scan to parse instruction rules and write rules.json.
Phase 4 extends scan to run deterministic finding checks and write findings.json.
Phase 5 adds ``agentlint demo`` to run all three packaged demo repos.
"""

from __future__ import annotations

import json
from pathlib import Path

import typer

import agentlint
from agentlint.analysis import run_deterministic_checks, write_findings_json
from agentlint.analysis.report_builder import format_findings_summary
from agentlint.config import AgentLintConfigError, load_config
from agentlint.discovery.instruction_sources import discover_sources
from agentlint.evidence import collect_evidence, write_evidence_json
from agentlint.parsing import extract_rules, write_rules_json

app = typer.Typer(
    name="agentlint",
    help="Audit AI coding-agent instruction files for drift against the repository.",
    add_completion=False,
    no_args_is_help=True,
)


@app.command("scan")
def scan(
    repo_path: str = typer.Argument(
        ...,
        help="Path to the repository to scan.",
    ),
) -> None:
    """Scan a repository for agent instruction files and report findings.

    Phase 1: discovers instruction sources and writes .agentlint/scan.json.
    Phase 2: collects repository evidence and writes .agentlint/evidence.json.
    Phase 3: extracts instruction rules and writes .agentlint/rules.json.
    Phase 4: runs deterministic finding checks and writes .agentlint/findings.json.
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


# Resolve demo repos relative to this file's location (works for editable install)
_DEMO_REPOS_DIR = Path(__file__).resolve().parent.parent / "demo_repos"

_DEMO_REPOS = [
    "inconsistent-js-repo",
    "single-agent-stale-repo",
    "clean-repo",
]


def _run_scan_for_path(path: Path) -> None:
    """Run the full scan pipeline for *path* and print a brief summary."""
    # Load config
    try:
        config = load_config(path)
    except AgentLintConfigError as exc:
        typer.echo(f"  [config error] {exc}", err=True)
        return

    sources = discover_sources(path, config)
    evidence = collect_evidence(path)
    rules = extract_rules(sources, repo_path=path)
    findings = run_deterministic_checks(rules, evidence)

    existing = [s for s in sources if s.exists]
    high_or_critical = [f for f in findings if f.severity in ("critical", "high")]

    typer.echo(
        f"  Sources: {len(existing)} found | "
        f"Rules: {len(rules)} | "
        f"Findings: {len(findings)} total, {len(high_or_critical)} high/critical"
    )

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


def main() -> None:
    """Entry point called by the ``agentlint`` console script."""
    app()


if __name__ == "__main__":
    main()
