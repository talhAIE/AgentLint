"""Evidence sub-package public API.

Phase 2: exposes the top-level evidence collection functions so callers
can use::

    from agentlint.evidence import collect_evidence, write_evidence_json
"""

from agentlint.evidence.repository_truth import collect_evidence, write_evidence_json

__all__ = ["collect_evidence", "write_evidence_json"]
