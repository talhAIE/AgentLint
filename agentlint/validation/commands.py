"""Command validation with allowlist and timeout — Phase 8.

Layer C: Run safe commands from policy definition_of_done with a timeout,
capturing exit code and output excerpt.

Safety contract (mandated by AgentLintplan.md §Phase 8 and AGENTS.md):
  - Only commands in definition_of_done may be executed.
  - A rejection-pattern list blocks destructive commands.
  - Per-command timeout (default 60 s).
  - Execution can be disabled entirely via skip_execution=True.
  - Command is shown to stdout before execution.

Public API:
    run_command_validation(
        policy, repo_path, *, timeout_sec=60, skip_execution=False
    ) -> list[ValidationResult]
"""

from __future__ import annotations

import re
import subprocess
import time
from pathlib import Path

from agentlint.models import CanonicalPolicy, ValidationResult

# ---------------------------------------------------------------------------
# Allowlist / rejection patterns
# ---------------------------------------------------------------------------

# Any command that matches one of these patterns is REJECTED — not run.
# Patterns are matched against the full command string (case-insensitive).
_REJECT_PATTERNS: list[re.Pattern] = [
    # File/directory deletion
    re.compile(r"\brm\b", re.IGNORECASE),
    re.compile(r"\bdel\b", re.IGNORECASE),
    re.compile(r"\brmdir\b", re.IGNORECASE),
    re.compile(r"\bremove-item\b", re.IGNORECASE),
    # Git destructive operations
    re.compile(r"\bgit\s+push\b", re.IGNORECASE),
    re.compile(r"\bgit\s+reset\b", re.IGNORECASE),
    re.compile(r"\bgit\s+clean\b", re.IGNORECASE),
    re.compile(r"\bgit\s+checkout\b", re.IGNORECASE),
    re.compile(r"\bgit\s+rebase\b", re.IGNORECASE),
    re.compile(r"\bgit\s+merge\b", re.IGNORECASE),
    re.compile(r"\bgit\s+commit\b", re.IGNORECASE),
    # Database / formatting destructive ops
    re.compile(r"\bDROP\b", re.IGNORECASE),
    re.compile(r"\bTRUNCATE\b", re.IGNORECASE),
    # Shell pipes to dangerous commands
    re.compile(r"\|\s*sh\b", re.IGNORECASE),
    re.compile(r"\|\s*bash\b", re.IGNORECASE),
    re.compile(r"\|\s*powershell\b", re.IGNORECASE),
    # Wildcard / glob deletion patterns
    re.compile(r"rm\s+-rf?\b", re.IGNORECASE),
    re.compile(r"Remove-Item.*-Recurse", re.IGNORECASE),
    # npm/pnpm/yarn publish/deploy
    re.compile(r"\b(npm|pnpm|yarn)\s+publish\b", re.IGNORECASE),
    re.compile(r"\b(npm|pnpm|yarn)\s+deploy\b", re.IGNORECASE),
]

# Allowed safe command prefixes — only commands whose first token is in this
# set pass the allowlist check (defense-in-depth, positive allowlist).
_ALLOWED_COMMANDS: frozenset[str] = frozenset(
    [
        "npm",
        "pnpm",
        "yarn",
        "npx",
        "node",
        "python",
        "python3",
        "pytest",
        "ruff",
        "flake8",
        "mypy",
        "black",
        "isort",
        "eslint",
        "tsc",
        "tslint",
        "jest",
        "vitest",
        "mocha",
        "cargo",
        "go",
        "make",
        "gradle",
        "./gradlew",
        "mvn",
        "dotnet",
        "bundle",
        "rake",
        "poetry",
        "uv",
        "pip",
    ]
)

_EXCERPT_MAX_CHARS = 500


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _is_safe_command(cmd: str) -> tuple[bool, str]:
    """Check whether *cmd* is safe to execute.

    Returns ``(True, "")`` when safe.
    Returns ``(False, reason)`` when rejected.
    """
    cmd_stripped = cmd.strip()

    # Empty command — reject
    if not cmd_stripped:
        return False, "Command is empty."

    # Check rejection patterns first
    for pattern in _REJECT_PATTERNS:
        if pattern.search(cmd_stripped):
            return False, f"Command rejected: matches destructive pattern {pattern.pattern!r}."

    # Positive allowlist: check the first token
    first_token = cmd_stripped.split()[0].lower()
    # Normalise Windows-style paths (e.g. .\gradlew)
    first_token = first_token.lstrip(".\\./")
    if first_token not in _ALLOWED_COMMANDS and not first_token.startswith("./"):
        return False, (
            f"Command rejected: first token '{first_token}' is not in the "
            "allowed command set. Only build/test/lint commands are permitted."
        )

    return True, ""


def _excerpt(text: str | None, max_chars: int = _EXCERPT_MAX_CHARS) -> str | None:
    if text is None:
        return None
    return text[:max_chars] if len(text) > max_chars else text


def _run_single_command(
    cmd: str,
    cwd: Path,
    timeout_sec: int,
) -> tuple[int, str | None, str | None, int]:
    """Run *cmd* in *cwd* and return (exit_code, stdout_excerpt, stderr_excerpt, duration_ms)."""
    start = time.monotonic()
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
        duration_ms = int((time.monotonic() - start) * 1000)
        return (
            proc.returncode,
            _excerpt(proc.stdout),
            _excerpt(proc.stderr),
            duration_ms,
        )
    except subprocess.TimeoutExpired:
        duration_ms = int((time.monotonic() - start) * 1000)
        return (
            -1,
            None,
            f"[timeout after {timeout_sec}s]",
            duration_ms,
        )
    except FileNotFoundError as exc:
        duration_ms = int((time.monotonic() - start) * 1000)
        return (
            -1,
            None,
            f"[command not found: {exc}]",
            duration_ms,
        )
    except OSError as exc:
        duration_ms = int((time.monotonic() - start) * 1000)
        return (
            -1,
            None,
            f"[OS error: {exc}]",
            duration_ms,
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_command_validation(
    policy: CanonicalPolicy,
    repo_path: Path | str,
    *,
    timeout_sec: int = 60,
    skip_execution: bool = False,
) -> list[ValidationResult]:
    """Run safe commands from *policy.definition_of_done*.

    Each command is checked against the allowlist before execution.
    When *skip_execution* is ``True``, no subprocess is launched.

    Args:
        policy:         The compiled policy with ``definition_of_done`` commands.
        repo_path:      Working directory for command execution.
        timeout_sec:    Per-command timeout in seconds (default 60).
        skip_execution: When ``True``, commands are listed but not run.

    Returns:
        A :class:`~agentlint.models.ValidationResult` list — one per command
        in ``definition_of_done``.  If no commands are defined, a single
        informational pass result is returned.
    """
    repo_path = Path(repo_path)
    commands = list(policy.definition_of_done)

    if not commands:
        return [
            ValidationResult(
                check_id="layer-c-no-commands",
                name="Command Validation",
                command=None,
                passed=True,
                duration_ms=None,
                stdout_excerpt=(
                    "PASS — no definition_of_done commands defined in policy."
                ),
                stderr_excerpt=None,
                evidence=[],
            )
        ]

    results: list[ValidationResult] = []
    for i, cmd in enumerate(commands, start=1):
        check_id = f"layer-c-cmd-{i:03d}"

        # Safety check
        safe, rejection_reason = _is_safe_command(cmd)
        if not safe:
            results.append(
                ValidationResult(
                    check_id=check_id,
                    name=f"Command Validation: {cmd[:60]}",
                    command=cmd,
                    passed=False,
                    duration_ms=None,
                    stdout_excerpt=f"FAIL — {rejection_reason}",
                    stderr_excerpt=None,
                    evidence=[],
                )
            )
            continue

        if skip_execution:
            results.append(
                ValidationResult(
                    check_id=check_id,
                    name=f"Command Validation: {cmd[:60]}",
                    command=cmd,
                    passed=True,
                    duration_ms=None,
                    stdout_excerpt=f"[execution disabled] would run: {cmd}",
                    stderr_excerpt=None,
                    evidence=[],
                )
            )
            continue

        # Show command before execution (per spec)
        print(f"  [layer-c] running: {cmd}")

        exit_code, stdout_ex, stderr_ex, duration_ms = _run_single_command(
            cmd, repo_path, timeout_sec
        )

        passed = exit_code == 0
        prefix = "PASS" if passed else "FAIL"
        stdout_summary = f"{prefix} (exit {exit_code}) — {cmd[:60]}"
        if stdout_ex:
            stdout_summary = f"{stdout_summary}\n{stdout_ex}"

        results.append(
            ValidationResult(
                check_id=check_id,
                name=f"Command Validation: {cmd[:60]}",
                command=cmd,
                passed=passed,
                duration_ms=duration_ms,
                stdout_excerpt=stdout_summary,
                stderr_excerpt=stderr_ex,
                evidence=[],
            )
        )

    return results
