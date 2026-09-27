---
name: agentlint-repair
description: '# /agentlint-repair'
metadata:
  user-invocable: true
  disable-model-invocation: true
---

# /agentlint-repair

Applies approved AgentLint findings as minimal patches to instruction files.
Requires a completed `/agentlint-audit` run and explicit human approval.

**Usage:** `/agentlint-repair <repo-path>`

If `<repo-path>` is not provided, ask the user for the path before proceeding.

---

## Preconditions

Before starting, verify:
1. `<repo-path>/.agentlint/findings.json` exists
2. `<repo-path>/.agentlint/repair-plan.md` exists (produced by `/agentlint-audit`)

If either file is missing, tell the user to run `/agentlint-audit <repo-path>` first.

---

## Workflow

### Step 1 — Read approved findings

Read `<repo-path>/.agentlint/findings.json` (both `"findings"` and
`"semantic_findings"` keys) and `<repo-path>/.agentlint/repair-plan.md`.

Identify which findings have been approved. A finding is considered approved when:
- The user has explicitly confirmed it in this session, **or**
- The repair-plan.md checklist item is marked `[x]`

If no findings are approved, display the open findings and ask the user which
ones to approve before proceeding. **Do not apply any changes until at least
one finding is explicitly approved.**

### Step 2 — Create or update canonical policy

Read `<repo-path>/.agentlint/evidence.json`.

Create or update `<repo-path>/.agentlint/policy.yaml` with the canonical
contract derived from repository evidence:

```yaml
version: 1

project:
  name: <project name from evidence or directory name>

tooling:
  package_manager: <from evidence>
  test_framework: <from evidence>
  test_command: <from evidence>
  lint_command: <from evidence, if present>
  build_command: <from evidence, if present>

runtime:
  language: <from evidence>

paths:
  generated: []
  protected: []

definition_of_done: []

evidence:
  package_manager:
    - <evidence source path>
  test_framework:
    - <evidence source path>
```

Only include fields for which evidence exists. Do not invent values.

### Step 3 — Preview minimal diffs

For each approved finding, produce a before/after diff preview in the chat.
Show exactly which lines in which instruction files will change.

Example format:
```
File: AGENTS.md  (line 12)
- Use npm for all package operations.
+ Use pnpm for all package operations.
```

**Wait for the user to confirm the diff preview before applying.**

If the user does not confirm, do not apply. Ask: "Shall I apply these changes? [y/N]"

### Step 4 — Apply only approved changes

For each approved finding with a confirmed diff:
- Use `apply_diff` or `search_and_replace` to make the minimal change
- Modify ONLY instruction files and `.agentlint/policy.yaml`
- **Never modify application source code, test files, build configs, or
  any file outside the instruction/policy set**

Allowed edit targets:
- `AGENTS.md`
- `CLAUDE.md`
- `.github/copilot-instructions.md`
- `.bob/**/*.md` (Bob rule files)
- `.cursor/**`
- `.agentlint/policy.yaml`
- `.agentlint/repair-plan.md` (to record applied status)

After each change, update the corresponding repair-plan.md checklist item
from `[ ]` to `[x]`.

### Step 5 — Record repair evidence

After all approved changes are applied, append a `## Repair Summary` section
to `<repo-path>/.agentlint/repair-plan.md`:

```markdown
## Repair Summary

Applied: <ISO timestamp>
Findings repaired: <count>
Files modified: <list>

### Before/After

#### <Finding ID>: <title>
**Before:** <original text>
**After:** <new text>
```

Then tell the user: "Repair complete. Run `/agentlint-verify <repo-path>`
to confirm findings are resolved."

---

## Constraints

- Never edit production code, test files, or build configs
- Never apply a change that was not explicitly approved in this session
- Never auto-approve findings — every repair requires human confirmation
- Never claim repair was successful without running `/agentlint-verify`
