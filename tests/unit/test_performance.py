"""Phase 11 — Performance smoke test.

AgentLintplan.md §Phase 11 Performance:
    "For hackathon-sized repos, target quick deterministic scan."

This test runs the full deterministic scan pipeline against each demo repo
and asserts it completes in under 10 seconds (wall-clock).  This is a
smoke-level guard against accidentally quadratic code paths, not a benchmark.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from agentlint.analysis import run_deterministic_checks
from agentlint.config import load_config
from agentlint.discovery.instruction_sources import discover_sources
from agentlint.evidence import collect_evidence
from agentlint.parsing import extract_rules

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_DEMO_REPOS = [
    _REPO_ROOT / "demo_repos" / "inconsistent-js-repo",
    _REPO_ROOT / "demo_repos" / "single-agent-stale-repo",
    _REPO_ROOT / "demo_repos" / "clean-repo",
]


@pytest.mark.parametrize("repo_path", _DEMO_REPOS, ids=lambda p: p.name)
def test_deterministic_scan_completes_quickly(repo_path: Path):
    """Full deterministic scan completes in < 10 seconds.

    Pipeline: discover → evidence → parse rules → deterministic checks.
    No file I/O (no JSON writes), no network, no LLM.
    """
    if not repo_path.exists():
        pytest.skip(f"Demo repo not found: {repo_path}")

    start = time.monotonic()

    config = load_config(repo_path)
    sources = discover_sources(repo_path, config)
    evidence = collect_evidence(repo_path)
    rules = extract_rules(sources, repo_path=repo_path)
    findings = run_deterministic_checks(rules, evidence)

    elapsed = time.monotonic() - start

    assert elapsed < 10.0, (
        f"Scan of {repo_path.name} took {elapsed:.2f}s (limit: 10s). "
        f"Found {len(findings)} findings from {len(sources)} sources."
    )
