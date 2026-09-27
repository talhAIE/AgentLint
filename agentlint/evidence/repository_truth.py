"""Repository truth aggregator.

Single entry point that runs all evidence detectors and returns the
consolidated list of :class:`~agentlint.models.RepositoryEvidence`
items.  Also writes ``.agentlint/evidence.json``.
"""

from __future__ import annotations

import json
from pathlib import Path

import agentlint
from agentlint.evidence.commands import detect_commands
from agentlint.evidence.linting import detect_linting
from agentlint.evidence.package_manager import detect_package_manager
from agentlint.evidence.paths import detect_paths
from agentlint.evidence.runtime import detect_runtime
from agentlint.evidence.testing import detect_test_framework
from agentlint.models import RepositoryEvidence

# Short category abbreviations used in evidence IDs.
_CATEGORY_ABBREV: dict[str, str] = {
    "package_manager": "pm",
    "test_framework": "tf",
    "commands": "cmd",
    "linting": "lint",
    "runtime": "rt",
    "paths": "path",
}


def collect_evidence(repo_path: Path) -> list[RepositoryEvidence]:
    """Run all detectors and return the combined evidence list.

    Evidence IDs are auto-assigned after collection in the form
    ``ev-<abbrev>-<three_digit_index>`` e.g. ``ev-pm-001``.

    Args:
        repo_path: Root directory of the repository to analyse.

    Returns:
        All evidence items from every detector, in detector order.
        IDs are populated on every returned item.
    """
    repo_path = Path(repo_path).resolve()

    # Run detectors in specification order.
    raw: list[RepositoryEvidence] = []
    raw.extend(detect_package_manager(repo_path))
    raw.extend(detect_test_framework(repo_path))
    raw.extend(detect_commands(repo_path))
    raw.extend(detect_linting(repo_path))
    raw.extend(detect_runtime(repo_path))
    raw.extend(detect_paths(repo_path))

    # Assign sequential IDs per category.
    category_counters: dict[str, int] = {}
    for item in raw:
        abbrev = _CATEGORY_ABBREV.get(item.category, item.category[:4])
        n = category_counters.get(abbrev, 0) + 1
        category_counters[abbrev] = n
        item.id = f"ev-{abbrev}-{n:03d}"

    return raw


def write_evidence_json(
    repo_path: Path,
    evidence: list[RepositoryEvidence],
) -> Path:
    """Write ``.agentlint/evidence.json`` and return the output path.

    Args:
        repo_path: Root of the scanned repository.
        evidence:  Evidence list from :func:`collect_evidence`.

    Returns:
        The :class:`~pathlib.Path` of the written file.
    """
    output_dir = Path(repo_path) / ".agentlint"
    output_dir.mkdir(exist_ok=True)

    payload = {
        "agentlint_version": agentlint.__version__,
        "repo_path": str(Path(repo_path).resolve()),
        "evidence": [e.to_dict() for e in evidence],
    }
    output_path = output_dir / "evidence.json"
    output_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return output_path
