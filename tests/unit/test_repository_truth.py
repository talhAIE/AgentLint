"""Unit tests for agentlint.evidence.repository_truth (Phase 2).

Covers collect_evidence() and write_evidence_json().
"""

from __future__ import annotations

import json
from pathlib import Path

from agentlint.evidence.repository_truth import collect_evidence, write_evidence_json


# ---------------------------------------------------------------------------
# collect_evidence
# ---------------------------------------------------------------------------

def test_collect_evidence_empty_repo(tmp_path: Path) -> None:
    """Empty directory → collect_evidence returns empty list without raising."""
    result = collect_evidence(tmp_path)
    assert isinstance(result, list)
    assert result == []


def test_collect_evidence_js_repo(tmp_path: Path) -> None:
    """package.json with pnpm + vitest → both are detected."""
    (tmp_path / "package.json").write_text(
        json.dumps(
            {
                "packageManager": "pnpm@9.0.0",
                "devDependencies": {"vitest": "^1.0.0"},
                "scripts": {"test": "vitest run"},
            }
        ),
        encoding="utf-8",
    )
    result = collect_evidence(tmp_path)
    values = [e.value for e in result]
    assert "pnpm" in values
    assert "vitest" in values


def test_ids_are_assigned(tmp_path: Path) -> None:
    """Every evidence item has a non-empty id after collect_evidence."""
    (tmp_path / "package.json").write_text(
        json.dumps({"packageManager": "npm@10", "scripts": {"test": "jest"}}),
        encoding="utf-8",
    )
    result = collect_evidence(tmp_path)
    assert result  # must have at least some items
    for item in result:
        assert item.id, f"Evidence item has empty id: {item}"


# ---------------------------------------------------------------------------
# write_evidence_json
# ---------------------------------------------------------------------------

def test_write_evidence_json_creates_file(tmp_path: Path) -> None:
    """write_evidence_json creates .agentlint/evidence.json."""
    evidence = collect_evidence(tmp_path)
    out_path = write_evidence_json(tmp_path, evidence)
    assert out_path.exists()
    assert out_path.name == "evidence.json"
    assert out_path.parent.name == ".agentlint"


def test_write_evidence_json_schema(tmp_path: Path) -> None:
    """evidence.json has required top-level keys."""
    evidence = collect_evidence(tmp_path)
    write_evidence_json(tmp_path, evidence)
    data = json.loads((tmp_path / ".agentlint" / "evidence.json").read_text(encoding="utf-8"))
    assert "agentlint_version" in data
    assert "evidence" in data
    assert isinstance(data["evidence"], list)


def test_collect_evidence_returns_all_categories(tmp_path: Path) -> None:
    """Full fixture → multiple evidence categories in result."""
    # Create a JS project with multiple signals
    (tmp_path / "package.json").write_text(
        json.dumps(
            {
                "packageManager": "pnpm@9.0.0",
                "devDependencies": {
                    "vitest": "^1.0.0",
                    "eslint": "^9.0.0",
                    "prettier": "^3.0.0",
                },
                "scripts": {
                    "test": "vitest run",
                    "lint": "eslint src/",
                    "build": "tsc",
                },
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n", encoding="utf-8")
    (tmp_path / "src").mkdir()

    result = collect_evidence(tmp_path)
    categories = {e.category for e in result}
    # Expect at least package_manager, test_framework, commands, linting, paths
    assert "package_manager" in categories
    assert "test_framework" in categories
    assert "commands" in categories
    assert "linting" in categories
    assert "paths" in categories
