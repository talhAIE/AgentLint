# /agentlint-audit

Runs the full AgentLint audit workflow against a target repository:
deterministic scan followed by Bob semantic investigation and finding synthesis.

**Usage:** `/agentlint-audit <repo-path>`

If `<repo-path>` is not provided, ask the user for the path before proceeding.

---

## Workflow

### Step 1 — Run deterministic scan

Run the deterministic engine against the target repository:

```bash
agentlint scan <repo-path>
```

Read all four output files:
- `<repo-path>/.agentlint/scan.json` — discovered instruction sources
- `<repo-path>/.agentlint/evidence.json` — repository truth evidence
- `<repo-path>/.agentlint/rules.json` — parsed instruction rules
- `<repo-path>/.agentlint/findings.json` — deterministic findings (F01–F05)

Summarize the deterministic findings to the user (count by severity and type)
before proceeding to semantic analysis.

### Step 2 — Read instruction files

Using `read_file`, read every instruction source that exists (from scan.json).
Common locations:
- `<repo-path>/AGENTS.md`
- `<repo-path>/CLAUDE.md`
- `<repo-path>/.github/copilot-instructions.md`
- `<repo-path>/.bob/rules-*/AGENTS*.md`

### Step 3 — Spawn parallel investigation subagents

Use `spawn_subagent` to run the three investigation roles in parallel:

**Subagent A — Instruction Analyst**

Prompt: "You are the Instruction Analyst for AgentLint. Read the following
instruction files and identify: (1) semantic requirements each file asserts,
(2) direct contradictions between files that may not appear as exact text
matches, (3) ambiguous rules that an agent could interpret in conflicting ways.
For each issue found, specify the source file and line range.
Instruction files: [attach content of each file]"

**Subagent B — Repository Reality Analyst**

Prompt: "You are the Repository Reality Analyst for AgentLint. Read the
repository evidence from evidence.json and the raw repository files listed
below. Identify: (1) important project conventions (package manager, test
framework, lint tool, runtime version) not mentioned in any instruction file
(candidate F06 findings), (2) any evidence-backed facts that contradict
instruction claims. Cite the specific evidence item IDs from evidence.json.
Evidence: [attach evidence.json content]"

**Subagent C — Maintenance Analyst**

Prompt: "You are the Maintenance Analyst for AgentLint. Read the instruction
rules from rules.json and the repository directory structure. Identify:
(1) path references in instructions that do not exist in the repository,
(2) duplicate or near-duplicate instruction sections across files that were
not caught as exact matches. Cite rule IDs from rules.json.
Rules: [attach rules.json content]"

Wait for all three subagents to return before proceeding.

### Step 4 — Synthesize semantic findings

Combine the subagent outputs with the deterministic findings. For each new
semantic finding, produce an entry in this exact format:

```json
{
  "title": "...",
  "type": "F06",
  "severity": "medium",
  "instruction_sources": ["<relative-path-to-instruction-file>"],
  "repository_evidence": ["<evidence-id-from-evidence.json>"],
  "reasoning_summary": "<one or two sentences — no chain of thought>",
  "recommended_action": "...",
  "confidence": 0.75,
  "deterministic": false
}
```

Rules for semantic findings:
- `type` must be F06 (missing context) or F07 (ambiguous instruction)
- `confidence` must be between 0.0 and 1.0; use lower values (< 0.7) when
  evidence is indirect
- `reasoning_summary` must cite at least one instruction source OR one evidence ID
- Do not emit a finding for something already covered by a deterministic finding
- Do not store private chain-of-thought; only concise summaries

### Step 5 — Write findings.json

Read the existing `<repo-path>/.agentlint/findings.json`.

Append a `"semantic_findings"` top-level key containing the array of semantic
findings produced in Step 4. **Do not modify the `"findings"` key** — deterministic
results must remain unchanged.

Write the updated file back.

### Step 6 — Write repair-plan.md

Create `<repo-path>/.agentlint/repair-plan.md` with:

```markdown
# AgentLint Repair Plan

Generated: <ISO timestamp>
Repository: <repo-path>
Deterministic findings: <count>
Semantic findings: <count>

## Findings Requiring Action

### [F02-001] <title>
- **Severity:** high
- **Source:** <instruction file>
- **Evidence:** <evidence IDs>
- **Proposed change:** <minimal diff preview>
- **Approval required:** [ ]

... (one section per open finding)

## Findings for Information Only

... (low/info severity findings that need no immediate action)
```

### Step 7 — Present summary to user

Display:
1. Total findings (deterministic + semantic) grouped by type and severity
2. The repair plan location
3. Instructions: "Review `.agentlint/repair-plan.md` and approve items.
   Then run `/agentlint-repair <repo-path>` to apply approved changes."

**Do NOT modify any instruction file in this step.**

---

## Constraints

- Never modify instruction files during an audit — only during `/agentlint-repair`
- Never fabricate evidence IDs; all `repository_evidence` values must come from evidence.json
- Never claim a command works without executing it
- If `agentlint` is not installed, note this and proceed with semantic analysis only;
  mark all findings `"deterministic": false`
