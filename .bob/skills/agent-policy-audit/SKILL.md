---
name: agent-policy-audit
description: Use when auditing AI-agent instruction files (AGENTS.md, CLAUDE.md, copilot-instructions.md, Bob rules) against each other and against repository evidence. Guides through evidence collection, deterministic scan, semantic finding synthesis, canonical policy proposal, repair patch preparation, and post-repair verification.
---

# Agent Policy Audit Skill

Audit AI-agent instruction sources against each other and against repository evidence,
produce evidence-backed findings, generate a canonical policy proposal, prepare minimal
repair patches, and verify the approved result.

## Rules (follow strictly, in every session)

1. **Do not edit instructions before evidence collection.** Always run `agentlint scan`
   and read `.agentlint/evidence.json` before proposing any change to any instruction file.

2. **Prefer deterministic AgentLint output where available.** Deterministic findings
   (`deterministic: true` in findings.json) are ground truth. Bob semantic analysis
   supplements them — it does not override them.

3. **Every finding must cite both instruction source and repository evidence** when
   applicable. A finding without evidence references is inadmissible.

4. **Distinguish finding types precisely:**
   - F01 — direct contradiction between two instruction files
   - F02 — instruction disagrees with repository evidence
   - F03 — stale path reference (path no longer exists)
   - F04 — invalid/stale command (script not in repo)
   - F05 — duplicate instruction (same rule in multiple files)
   - F06 — missing high-value context (important repo convention absent from instructions)
   - F07 — ambiguous instruction (too vague to be actionable)

5. **Never claim a command works until it has been executed.** Do not assert that
   `pnpm test` or any other command succeeds without running it and seeing the output.

6. **Never claim an agent will follow a rule merely because the text was changed.**
   Verification requires re-running the deterministic scan and confirming the finding
   disappears from findings.json.

7. **Require human approval before modifying any instruction file.** Present a diff
   preview and wait for explicit confirmation. Never apply changes silently.

8. **After repair, rerun the deterministic AgentLint checks.** The verification step
   must re-run `agentlint scan` and confirm that repaired findings no longer appear.

9. **Run relevant project validation commands** from the canonical policy (e.g.
   `pytest`, `pnpm test`, `pnpm lint`) as part of the verification step.

10. **Produce before/after evidence.** For every repaired finding, record the
    original finding entry and the post-repair scan output so the change is auditable.

## Workflow

### Step 1 — Run deterministic scan

Use `execute_command` to run:
```
agentlint scan <repo-path>
```

This produces:
- `.agentlint/scan.json` — discovered instruction sources
- `.agentlint/evidence.json` — repository truth
- `.agentlint/rules.json` — parsed instruction rules
- `.agentlint/findings.json` — deterministic findings (F01–F05)

Read all four files before proceeding.

### Step 2 — Parallel semantic investigation

Spawn three independent subagents using `spawn_subagent`:

**Subagent A — Instruction Analyst**
- Inputs: all instruction files (read each with `read_file`)
- Tasks: identify semantic requirements; normalize differently worded rules;
  detect direct contradictions not caught deterministically; identify ambiguous guidance
- Output: structured list of rule interpretations and potential conflicts

**Subagent B — Repository Reality Analyst**
- Inputs: package config, lockfiles, test config, CI, lint/build configs, directory structure
- Tasks: verify actual tooling against instruction claims; verify commands work;
  identify strong evidence for conventions not yet in instructions
- Output: evidence-backed repository facts, candidate F06 findings

**Subagent C — Maintenance Analyst**
- Inputs: instruction files, `.agentlint/rules.json`, repository directory listing
- Tasks: check all referenced paths against repo structure; identify stale
  file/directory references; find duplicated or obsolete sections
- Output: candidate F03/F05 additions

### Step 3 — Synthesize and merge findings

Combine deterministic findings from `.agentlint/findings.json` with semantic
findings from subagents. For each semantic finding, produce a JSON object:

```json
{
  "title": "...",
  "type": "F06",
  "severity": "medium",
  "instruction_sources": ["AGENTS.md"],
  "repository_evidence": ["ev-pm-001"],
  "reasoning_summary": "...",
  "recommended_action": "...",
  "confidence": 0.75,
  "deterministic": false
}
```

Do not store or request private chain-of-thought. Only store concise reasoning
summaries with evidence references.

Append semantic findings into `.agentlint/findings.json` under a
`"semantic_findings"` top-level key. Do not overwrite the `"findings"` key
(deterministic results).

### Step 4 — Write repair plan

Write `.agentlint/repair-plan.md` with:
- Summary of all open findings (deterministic + semantic)
- For each finding: the proposed minimal change, a before/after diff preview
- A checklist of items requiring human approval
- Do NOT modify any instruction file yet

### Step 5 — Wait for human approval

Present the repair plan and require explicit approval before proceeding to repair.

Use the `/agentlint-repair` command to apply approved changes.
Use the `/agentlint-verify` command to verify the result.

## Fail-safe

If `agentlint` is not installed or the scan fails, the semantic investigation
(Steps 2–3) can still proceed against instruction files directly. Record that
deterministic scan output is unavailable so findings are marked
`"deterministic": false` and confidence is reduced accordingly.

The project must work without Bob — this skill is an enhancement, not a dependency.
