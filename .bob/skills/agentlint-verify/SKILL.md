---
name: agentlint-verify
description: '# /agentlint-verify'
metadata:
  user-invocable: true
  disable-model-invocation: true
---

# /agentlint-verify

Verifies that AgentLint repair was successful by re-running the deterministic
scan, checking that repaired findings are resolved, and running project
validation commands from the canonical policy.

**Usage:** `/agentlint-verify <repo-path>`

If `<repo-path>` is not provided, ask the user for the path before proceeding.

---

## Preconditions

Before starting, verify:
1. `<repo-path>/.agentlint/findings.json` exists (from a prior audit)
2. `<repo-path>/.agentlint/repair-plan.md` exists

If either file is missing, tell the user to run `/agentlint-audit` and
`/agentlint-repair` first.

---

## Workflow

### Step 1 — Re-run deterministic scan

Run the scan against the (now-repaired) repository:

```bash
agentlint scan <repo-path>
```

This overwrites `<repo-path>/.agentlint/findings.json` with a fresh result.
Read the new findings.json immediately after.

### Step 2 — Confirm repaired findings are resolved

Load the pre-repair finding IDs from `repair-plan.md` (items marked `[x]` as applied).

For each repaired finding:
- Check whether a finding of the same `type` with the same `title` substring
  still appears in the new findings.json
- If absent: the repair was successful for this finding — record as RESOLVED
- If still present: the repair was insufficient — record as STILL OPEN and
  explain why

Report the before/after comparison:

```
Before repair: <N> findings  (<X> critical/high, <Y> medium, <Z> low/info)
After repair:  <N> findings  (<X> critical/high, <Y> medium, <Z> low/info)

Resolved:     <list of finding titles>
Still open:   <list of finding titles with explanation>
New findings: <any new findings introduced by the repair>
```

### Step 3 — Run project validation commands

Read `<repo-path>/.agentlint/policy.yaml` if it exists.

Run each command in `definition_of_done` using `execute_command`. For a
Python project this typically means:

```bash
pytest <repo-path>
```

For a Node.js project it may be `pnpm test`, `pnpm lint`, etc.

Only run commands that appear in policy.yaml or in instruction files.
**Never invent or assume commands** — only run what is explicitly documented.

For each command, record:
- exit code
- first 20 lines of stdout
- first 10 lines of stderr (if any)

### Step 4 — Write verification.json

Write `<repo-path>/.agentlint/verification.json`:

```json
{
  "agentlint_version": "<version>",
  "repo_path": "<repo-path>",
  "verified_at": "<ISO timestamp>",
  "pre_repair_finding_count": <N>,
  "post_repair_finding_count": <N>,
  "resolved_findings": ["<finding title>", ...],
  "still_open_findings": ["<finding title>", ...],
  "new_findings": ["<finding title>", ...],
  "validation_commands": [
    {
      "command": "<command string>",
      "exit_code": 0,
      "passed": true,
      "stdout_excerpt": "...",
      "stderr_excerpt": null
    }
  ],
  "overall_passed": true
}
```

`overall_passed` is `true` only when:
- all repaired findings are resolved (still_open_findings is empty)
- all validation commands exited with code 0
- no new high/critical findings were introduced

### Step 5 — Present summary

Display a clear before/after summary to the user.

If `overall_passed` is true:
> "Verification passed. All repaired findings are resolved and project
> validation commands succeeded."

If `overall_passed` is false:
> "Verification failed. See verification.json for details. Re-run
> `/agentlint-repair` to address remaining issues."

---

## Constraints

- Never claim a command succeeded without running it and reading the output
- Never claim a finding is resolved without re-running `agentlint scan`
- Never modify instruction files during verification
- Record all evidence in verification.json — do not rely on memory across sessions
