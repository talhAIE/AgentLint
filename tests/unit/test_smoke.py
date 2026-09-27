"""Phase 0 smoke tests.

These tests verify the minimal Phase 0 acceptance criteria:
- `import agentlint` succeeds without error
- `agentlint.__version__` is a non-empty string
"""

import agentlint


def test_import_succeeds() -> None:
    """The agentlint package must be importable."""
    # If import failed, this test would not even run — but let's be explicit.
    assert agentlint is not None


def test_version_is_set() -> None:
    """__version__ must be a non-empty string."""
    assert hasattr(agentlint, "__version__")
    assert isinstance(agentlint.__version__, str)
    assert len(agentlint.__version__) > 0


def test_version_format() -> None:
    """__version__ should follow semver-style major.minor.patch."""
    parts = agentlint.__version__.split(".")
    assert len(parts) == 3, f"Expected 3 version parts, got: {agentlint.__version__!r}"
    for part in parts:
        assert part.isdigit(), f"Version part {part!r} is not numeric"
