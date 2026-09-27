# AgentLint — Complete Hackathon Implementation Plan

> **Project tagline:** One repo. Many AI coding agents. One source of truth.
>
> **Purpose of this document:** This is the master implementation specification for building AgentLint phase by phase. A coding AI should be able to follow this file from Phase 0 through Phase 12 and produce the complete hackathon project without inventing major requirements.
>
> **Hackathon:** IBM Bob 2.0 Hackathon (lablab.ai, September 25–27, 2026)
>
> **Primary technology:** IBM Bob 2.0
>
> **MVP stack:** Python 3.11+, Streamlit, pytest, Git/GitHub, Markdown/YAML/JSON parsing, IBM Bob 2.0 IDE.
>
> **Important:** Build the MVP first. Do not spend limited Bob usage on visual polish, CSS, CRUD code, or generic coding tasks that can be completed normally. Reserve Bob for the workflow that demonstrates its unique value: repository understanding, semantic instruction analysis, parallel/subagent investigation, repair reasoning, and verification.

---

# 1. Executive Summary

## 1.1 What AgentLint is

AgentLint is a developer tool that audits the instructions given to AI coding agents and checks whether those instructions still match the repository they are supposed to operate on.

Modern repositories may contain instructions for different AI development tools, for example:

- `AGENTS.md`
- `CLAUDE.md`
- `.github/copilot-instructions.md`
- `.bob/rules-code/AGENTS-code.md`
- `.bob/rules-plan/AGENTS-plan.md`
- `.bob/rules-ask/AGENTS-ask.md`
- optionally Cursor rule files such as `.cursor/rules/*.md` or `.mdc`

These files can drift over time.

Example:

```text
AGENTS.md
- Use npm
- Use Jest

CLAUDE.md
- Use pnpm
- Use Vitest

Actual repository
- packageManager = pnpm
- pnpm-lock.yaml exists
- vitest.config.ts exists
- package.json contains Vitest
```

The problem is not only that two instruction files disagree. The more important problem is that an instruction file may disagree with the **actual repository**.

AgentLint therefore treats the repository as evidence and asks:

1. What do the AI-agent instruction files say?
2. What does the repository actually use?
3. Which instructions contradict each other?
4. Which instructions are stale?
5. Which instructions reference commands, tools, paths, or frameworks that no longer exist?
6. Which rules are duplicated unnecessarily?
7. Which important repository facts are missing from the instructions?
8. What canonical instruction contract should the team use?
9. Can the recommended commands actually run successfully?

IBM Bob 2.0 is used as the semantic reasoning and orchestration layer for the difficult parts of this workflow.

---

# 2. Problem Statement

AI coding agents are increasingly used as software-development partners. A repository can contain different instruction files for different tools, or only one instruction file that gradually becomes stale as the project changes.

This creates several realistic problems:

- one AI agent uses an outdated package manager;
- another assumes the wrong test framework;
- an instruction tells an agent to edit generated files that should not be modified;
- an instruction references a directory that was renamed;
- a test/build/lint command in the instructions no longer exists;
- multiple instruction files repeat the same large blocks of context;
- a repository migrates from Jest to Vitest but `AGENTS.md` still describes Jest;
- a team changes architecture but its coding-agent instructions are not updated.

The result can be:

- inconsistent AI-generated changes;
- additional review and debugging;
- wasted context;
- repeated corrections by developers;
- agents executing outdated commands;
- increased maintenance cost.

AgentLint addresses this as an **application-maintenance / AI-assisted-development workflow**.

---

# 3. Solution Statement

AgentLint creates a repository-grounded consistency layer for AI coding-agent instructions.

The workflow is:

```text
Repository
    |
    v
Discover instruction files
    |
    v
Extract and normalize rules
    |
    +----------------------------+
    |                            |
    v                            v
Instruction evidence        Repository evidence
    |                            |
    +-------------+--------------+
                  |
                  v
         IBM Bob semantic audit
                  |
        +---------+---------+
        |         |         |
        v         v         v
  Rule agent   Repo agent  Validation agent
        |         |         |
        +---------+---------+
                  |
                  v
          Conflict/staleness report
                  |
                  v
        Canonical Agent Contract
                  |
                  v
       Human-reviewed repair plan
                  |
                  v
          Apply approved changes
                  |
                  v
       Deterministic verification
                  |
                  v
            Evidence report
```

The output is not just "AI thinks the files conflict."

The output includes evidence such as:

```text
Finding: Package manager mismatch

Instruction:
AGENTS.md: "Use npm install"

Repository evidence:
package.json -> packageManager: pnpm@...
pnpm-lock.yaml -> present
CI -> pnpm install --frozen-lockfile

Conclusion:
Instruction is stale.

Recommended rule:
Use pnpm.
```

---

# 4. Core Product Principles

The implementation MUST follow these principles.

## 4.1 Repository truth over model opinion

Bob can interpret meaning, but important claims should be supported by evidence found in the repository.

Prefer:

```text
vitest.config.ts exists
package.json contains "vitest"
npm script "test" runs vitest
```

over:

```text
The AI believes the project probably uses Vitest.
```

## 4.2 Human approval before destructive repair

The MVP should never silently rewrite all instruction files.

Default sequence:

```text
Scan -> Explain -> Propose -> User Approves -> Apply -> Verify
```

## 4.3 Deterministic checks where possible

Use normal Python logic for facts that do not need an LLM:

- lockfile detection;
- dependency detection;
- file/path existence;
- package.json scripts;
- config-file detection;
- duplicate text hashes;
- command existence;
- test/build/lint execution.

Use Bob where semantic reasoning is actually helpful:

- interpreting natural-language agent rules;
- deciding whether two differently worded rules mean the same thing;
- deciding whether rules conflict;
- synthesizing a canonical instruction;
- explaining why repository evidence matters;
- coordinating parallel investigation;
- proposing minimal safe repairs.

## 4.4 Evidence before score

Do not show a meaningless "AI health score" without evidence.

Every high-severity finding should contain:

- source instruction;
- source file;
- line or section if possible;
- repository evidence;
- explanation;
- proposed action;
- confidence.

## 4.5 Small, polished MVP before broad compatibility

For the hackathon, support a controlled set of files and conflict categories extremely well instead of pretending to support every agent and programming language.

---

# 5. Hackathon Fit

The official challenge asks participants to create a solution that improves a specific developer workflow, define a problem where time/effort/errors are too high, build a working prototype on a real or sample project, and use Bob features such as Agent mode, parallel tasks, subagents, and document understanding across multiple steps.

AgentLint fits as an **application-maintenance and AI-development-governance workflow**.

## 5.1 Application of Technology

AgentLint should visibly use IBM Bob 2.0 for:

- `/init` repository context;
- Plan mode during architecture/planning;
- Agent mode during implementation/audit;
- a reusable Bob Skill;
- a custom Bob mode for instruction auditing;
- subagents or parallel investigations;
- document understanding across instruction files;
- repository evidence analysis;
- repair proposals;
- verification;
- optionally `/review` on project changes.

## 5.2 Business Value

Demonstrate concrete reduction in:

- stale AI instructions;
- contradictory rules;
- invalid commands;
- duplicated context;
- manual maintenance effort;
- avoidable developer corrections.

Do NOT invent financial savings.

Use measurable project metrics instead.

## 5.3 Originality

AgentLint is not:

- a generic code reviewer;
- a generic bug fixer;
- a generic testing agent;
- another repository onboarding assistant.

Its focus is the consistency and maintenance of the **instruction layer used by AI coding agents**.

## 5.4 Presentation

The demo must have a very clear before/after story:

```text
BEFORE
Instruction sources: 4
Cross-file conflicts: 3
Repo mismatches: 4
Invalid/stale commands: 2
Duplicate rule groups: 5
Validation checks passing: 1/4

AFTER
Cross-file conflicts: 0
Repo mismatches: 0
Invalid/stale commands: 0
Duplicate rule groups: reduced
Validation checks passing: 4/4
```

Only report metrics the implementation actually measures.

---

# 6. Hackathon Requirements to Satisfy

The final project must be prepared to provide:

- Project Title
- Short Description
- Long Description / Problem & Solution Statement (500 words or less)
- IBM Bob Usage Statement (500 words or less)
- Technology & Category Tags
- Public Code Repository
- IBM Bob Task Session Summary Screenshots
- Demo Application Platform
- Application URL
- Cover Image
- Video Demonstration
- Slide Presentation

Additional official requirements from the supplied challenge:

- repository must be publicly accessible;
- repository must include the code/files where IBM Bob assisted;
- include IBM Bob task-session summary screenshots from each team member;
- demo video must be 3 minutes or less;
- at least 90 seconds of the video should show the solution working;
- video should clearly demonstrate IBM Bob usage;
- submission must be original and MIT-compliant.

Therefore the repository MUST include an MIT `LICENSE`.

---

# 7. Target Users

Primary users:

1. individual developers who use one coding agent and want to detect stale instructions;
2. teams using multiple AI coding agents;
3. maintainers responsible for keeping repository guidance current;
4. engineering teams adopting IBM Bob alongside other development agents.

Important: AgentLint MUST still be useful when the repository has only **one** instruction file.

Example:

```text
Only CLAUDE.md exists.

CLAUDE.md says:
"Use npm."

Repository says:
packageManager = pnpm
pnpm-lock.yaml exists

AgentLint still produces a valid stale-instruction finding.
```

Multiple instruction files add cross-agent conflict detection, but they are NOT required for AgentLint to provide value.

---

# 8. MVP Scope

## 8.1 Supported instruction sources

MVP:

- `AGENTS.md`
- `CLAUDE.md`
- `.github/copilot-instructions.md`
- `.bob/rules-code/AGENTS-code.md`
- `.bob/rules-plan/AGENTS-plan.md`
- `.bob/rules-ask/AGENTS-ask.md`

Optional after MVP:

- `.cursor/rules/*.md`
- `.cursor/rules/*.mdc`
- other configured custom paths.

Never hard-code the design so new source types cannot be added later.

## 8.2 Repository facts to detect

MVP repository evidence:

### Package manager

Detect:

- `pnpm-lock.yaml`
- `yarn.lock`
- `package-lock.json`
- `bun.lock` / `bun.lockb` if supported
- `package.json.packageManager`

### Test framework

Detect evidence for common JS test frameworks:

- Vitest
- Jest
- Playwright
- Cypress

Also support Python test evidence:

- pytest config/dependency
- unittest references as secondary evidence

### Lint/format

Detect:

- ESLint
- Prettier
- Ruff
- Black

### Commands

Extract where available:

- install command
- test command
- lint command
- build command
- format command

Sources:

- `package.json` scripts;
- `pyproject.toml`;
- GitHub Actions;
- Makefile;
- common project docs.

### Runtime/language

Detect obvious evidence:

- Node version (`.nvmrc`, `.node-version`, package engines);
- Python version (`pyproject.toml`, `.python-version`, runtime files).

### Paths

Validate paths explicitly referenced in instruction files.

### Generated/protected paths

MVP can infer only when evidence is explicit, for example:

- comments indicating generated code;
- `codegen` scripts;
- configured generated directories;
- project fixture explicitly included in the demo.

Do not pretend to infer every generated file reliably.

---

# 9. Finding Types

Use these normalized finding types.

## F01 — Cross-Instruction Conflict

Two instruction files give incompatible guidance.

Example:

```text
AGENTS.md -> Use Jest
CLAUDE.md -> Use Vitest
```

## F02 — Instruction vs Repository Mismatch

An instruction disagrees with repository evidence.

Example:

```text
CLAUDE.md -> npm
package.json -> packageManager = pnpm
pnpm-lock.yaml -> present
```

## F03 — Stale Path

Instruction references a path that no longer exists.

Example:

```text
"Add services in src/services/"
```

but `src/services/` does not exist and the project uses `src/modules/`.

## F04 — Invalid/Stale Command

An instruction contains a project command that is not supported by the repository.

Example:

```text
"Run npm run test:unit"
```

but `test:unit` is absent from package scripts.

## F05 — Duplicate Instruction

The same or near-identical instruction appears across multiple files.

MVP:
- exact normalized duplicates deterministically;
- semantic duplicates optionally via Bob.

## F06 — Missing High-Value Context

Bob may identify an important repository convention not represented in agent guidance.

Examples:

- repository clearly uses pnpm but no instruction states the package manager;
- project requires `pnpm lint && pnpm test` before completion but agent guidance lacks definition-of-done.

This finding should be lower confidence unless evidence is clear.

## F07 — Ambiguous Instruction

Example:

```text
"Run tests before finishing."
```

but repository has multiple test suites and no clarification.

This is optional for MVP if time is limited.

---

# 10. Severity Model

Use simple severity levels:

- `critical`
- `high`
- `medium`
- `low`
- `info`

Recommended interpretation:

### Critical

A rule could cause destructive or clearly invalid behavior.

### High

A rule will likely cause incorrect implementation or failed workflow.

### Medium

A rule is stale or inconsistent but does not immediately break the project.

### Low

Duplication, clarity, or maintenance problem.

### Info

Recommended improvement with no current contradiction.

Avoid arbitrary numeric risk scores in the MVP.

---

# 11. Canonical Agent Contract

One of the strongest parts of AgentLint is a canonical machine-readable contract.

Create:

```text
.agentlint/policy.yaml
```

Example:

```yaml
version: 1

project:
  name: sample-store

tooling:
  package_manager: pnpm
  test_framework: vitest
  test_command: pnpm test
  lint_command: pnpm lint
  build_command: pnpm build

runtime:
  node: "22"

paths:
  generated:
    - src/generated/**
  protected:
    - migrations/history/**

definition_of_done:
  - pnpm lint
  - pnpm test
  - pnpm build

evidence:
  package_manager:
    - package.json#packageManager
    - pnpm-lock.yaml
  test_framework:
    - package.json#devDependencies.vitest
    - vitest.config.ts
```

Important:

- This file is generated/proposed from repository evidence.
- User approval is required before it becomes the canonical contract.
- The contract is NOT automatically treated as correct merely because Bob wrote it.
- Validation checks must support its claims.

---

# 12. Proposed Repository Structure

```text
agentlint/
├── app.py
├── pyproject.toml
├── requirements.txt
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── AgentLintplan.md
│
├── agentlint/
│   ├── __init__.py
│   ├── cli.py
│   ├── models.py
│   ├── config.py
│   │
│   ├── discovery/
│   │   ├── __init__.py
│   │   ├── instruction_sources.py
│   │   └── repo_files.py
│   │
│   ├── parsing/
│   │   ├── __init__.py
│   │   ├── markdown_rules.py
│   │   ├── json_parser.py
│   │   ├── yaml_parser.py
│   │   └── normalization.py
│   │
│   ├── evidence/
│   │   ├── __init__.py
│   │   ├── package_manager.py
│   │   ├── testing.py
│   │   ├── linting.py
│   │   ├── runtime.py
│   │   ├── commands.py
│   │   ├── paths.py
│   │   └── repository_truth.py
│   │
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── deterministic_rules.py
│   │   ├── conflicts.py
│   │   ├── duplicates.py
│   │   ├── scoring.py
│   │   └── report_builder.py
│   │
│   ├── policy/
│   │   ├── __init__.py
│   │   ├── schema.py
│   │   ├── compiler.py
│   │   ├── diff.py
│   │   └── adapters.py
│   │
│   ├── validation/
│   │   ├── __init__.py
│   │   ├── structural.py
│   │   ├── commands.py
│   │   ├── evidence_check.py
│   │   └── runner.py
│   │
│   └── ui/
│       ├── components.py
│       └── view_models.py
│
├── .bob/
│   ├── commands/
│   │   ├── agentlint-audit.md
│   │   ├── agentlint-repair.md
│   │   └── agentlint-verify.md
│   │
│   ├── skills/
│   │   └── agent-policy-audit/
│   │       └── SKILL.md
│   │
│   └── modes/
│       └── agent-policy-auditor.yaml
│
├── demo_repos/
│   ├── inconsistent-js-repo/
│   ├── single-agent-stale-repo/
│   └── clean-repo/
│
├── artifacts/
│   ├── demo/
│   └── screenshots/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── fixtures/
│   └── golden/
│
└── .github/
    └── workflows/
        ├── test.yml
        └── agentlint.yml
```

Adjust exact Bob mode save location to the format generated/supported by the installed Bob version. Do not invent unsupported Bob configuration syntax; use the Bob UI or current official documentation to create the mode, then commit the resulting YAML.

---

# 13. Data Models

Use dataclasses or Pydantic-style models. Keep external dependencies minimal.

## 13.1 InstructionSource

```python
InstructionSource(
    path: str,
    agent_type: str,
    content_hash: str,
    exists: bool,
)
```

## 13.2 InstructionRule

```python
InstructionRule(
    id: str,
    source_path: str,
    source_agent: str,
    text: str,
    category: str | None,
    normalized_key: str | None,
    normalized_value: str | None,
    line_start: int | None,
    line_end: int | None,
    extraction_method: str,
    confidence: float,
)
```

## 13.3 RepositoryEvidence

```python
RepositoryEvidence(
    id: str,
    category: str,
    key: str,
    value: str,
    source_path: str,
    source_locator: str | None,
    strength: str,  # strong / medium / weak
    explanation: str,
)
```

## 13.4 Finding

```python
Finding(
    id: str,
    type: str,
    severity: str,
    title: str,
    explanation: str,
    instruction_rules: list[str],
    evidence_ids: list[str],
    recommended_action: str,
    confidence: float,
    deterministic: bool,
    status: str,  # open / approved / repaired / ignored
)
```

## 13.5 CanonicalPolicy

Represent `.agentlint/policy.yaml`.

## 13.6 ValidationResult

```python
ValidationResult(
    check_id: str,
    name: str,
    command: str | None,
    passed: bool,
    duration_ms: int | None,
    stdout_excerpt: str | None,
    stderr_excerpt: str | None,
    evidence: list[str],
)
```

---

# 14. Output Files

Every scan should be able to write:

```text
.agentlint/
├── scan.json
├── evidence.json
├── findings.json
├── policy.yaml
├── repair-plan.md
└── verification.json
```

For the hackathon demo, these artifacts are important because they make the system auditable and easy for judges to inspect.

---

# 15. Command-Line Interface

Implement the following CLI:

```bash
agentlint scan <repo-path>
agentlint report <repo-path>
agentlint policy <repo-path>
agentlint validate <repo-path>
agentlint demo
```

Optional:

```bash
agentlint apply <repo-path> --approved
```

Do not implement destructive auto-fix first.

Suggested behavior:

### `agentlint scan`

- discovers instruction files;
- extracts deterministic rules;
- gathers repository evidence;
- performs deterministic checks;
- writes scan/evidence/findings JSON.

### `agentlint report`

- renders human-readable terminal report.

### `agentlint policy`

- produces a candidate canonical policy from deterministic evidence;
- Bob can refine it semantically.

### `agentlint validate`

- validates policy against repository;
- runs approved safe commands.

### `agentlint demo`

- loads packaged sample project and creates a ready-to-show report.

---

# 16. Streamlit Dashboard

Use Streamlit because it is fast to build and easy to deploy.

## 16.1 Page 1 — Overview

Show:

- repository name;
- number of instruction sources;
- open findings;
- conflict count;
- repo mismatch count;
- stale command/path count;
- duplicate groups;
- validation status.

Example:

```text
AgentLint
One repo. Many AI coding agents. One source of truth.

Repository: sample-store

Instruction Sources   4
Conflicts             3
Repo Mismatches       4
Stale Commands        2
Duplicate Groups      5
Validation            1 / 4 passed
```

## 16.2 Page 2 — Instruction Sources

List every discovered source.

Example:

```text
✓ AGENTS.md
✓ CLAUDE.md
✓ .github/copilot-instructions.md
✓ .bob/rules-code/AGENTS-code.md
```

Show excerpt and parsed rules when selected.

## 16.3 Page 3 — Findings

Filters:

- type;
- severity;
- source file;
- status.

Each finding card:

```text
HIGH — Package manager mismatch

AGENTS.md:
Use npm.

Repository evidence:
package.json -> packageManager=pnpm
pnpm-lock.yaml -> present

Recommendation:
Replace npm instructions with pnpm.

Confidence:
High
```

## 16.4 Page 4 — Repository Truth

Show structured evidence:

- package manager;
- test framework;
- scripts;
- runtime;
- lint/format tools;
- CI commands;
- relevant paths.

## 16.5 Page 5 — Canonical Contract

Render `.agentlint/policy.yaml` in readable form.

Show source evidence for each major policy field.

## 16.6 Page 6 — Repair Preview

Show diff-style proposed changes.

Do not silently apply changes from deployed demo.

## 16.7 Page 7 — Verification

Show:

```text
pnpm lint   PASS
pnpm test   PASS
pnpm build  PASS
policy      PASS
```

For the packaged demo, use real pre-run or local execution results that the code can reproduce.

---

# 17. IBM Bob 2.0 Architecture

Bob must be visibly central to the hackathon workflow.

## 17.1 `/init`

Run Bob `/init` on the AgentLint repository.

Keep:

- root `AGENTS.md`;
- mode-specific `.bob` context files.

Capture screenshots.

## 17.2 Bob Skill

Create:

```text
.bob/skills/agent-policy-audit/SKILL.md
```

Skill goal:

> Audit AI-agent instruction sources against each other and against repository evidence, produce evidence-backed findings, generate a canonical policy proposal, prepare minimal repair patches, and verify the approved result.

Skill rules:

1. Do not edit instructions before evidence collection.
2. Prefer deterministic AgentLint output where available.
3. Every finding must cite both instruction source and repository evidence when applicable.
4. Distinguish:
   - direct contradiction;
   - stale rule;
   - duplicate;
   - missing context;
   - ambiguity.
5. Never claim a command works until executed.
6. Never claim an agent will follow a rule merely because the text was changed.
7. Require human approval before modifying instruction files.
8. After repair, rerun deterministic AgentLint checks.
9. Run relevant project validation commands.
10. Produce before/after evidence.

## 17.3 Custom Bob Mode — Agent Policy Auditor

Create a custom mode through Bob's supported mode UI/configuration.

Purpose:

- read the entire repository;
- analyze instruction files;
- use skills;
- execute AgentLint commands;
- launch subagents;
- edit only approved instruction/policy files during repair.

Recommended tool access:

- Read
- Skill
- Subagent
- Todo/Subtask if supported
- Execute
- Edit with restrictions where practical

If the installed Bob version supports edit regex restrictions, restrict repairs primarily to:

```text
AGENTS.md
CLAUDE.md
.github/copilot-instructions.md
.bob/**
.cursor/**
.agentlint/**
```

Do not let the auditor modify application production code by default.

## 17.4 Bob Slash Commands

### `/agentlint-audit`

Create:

```text
.bob/commands/agentlint-audit.md
```

High-level workflow:

1. run deterministic scan;
2. read `.agentlint/evidence.json`;
3. read instruction files;
4. launch parallel investigation tasks/subagents;
5. synthesize semantic findings;
6. merge deterministic and semantic findings;
7. write `.agentlint/findings.json`;
8. create `.agentlint/repair-plan.md`;
9. do not modify instructions yet.

### `/agentlint-repair`

1. read approved findings;
2. create/update canonical policy;
3. preview minimal diffs;
4. require approval;
5. apply only approved changes;
6. never edit production code.

### `/agentlint-verify`

1. rerun `agentlint scan`;
2. confirm repaired findings disappear;
3. execute safe lint/test/build commands from policy;
4. produce `.agentlint/verification.json`;
5. summarize before/after.

---

# 18. Bob Subagent Roles

The exact subagent mechanism must follow the installed Bob 2.0 capabilities. The main Agent-mode workflow should delegate independent investigation where useful.

Recommended roles:

## A. Instruction Analyst

Inputs:

- all instruction files.

Tasks:

- identify semantic requirements;
- normalize differently worded rules;
- detect direct contradictions;
- identify ambiguous guidance.

Output:

- structured list of rule interpretations;
- potential conflicts.

## B. Repository Reality Analyst

Inputs:

- package config;
- lockfiles;
- test config;
- CI;
- lint/build configs;
- directory structure.

Tasks:

- verify actual tooling;
- verify commands;
- identify strong evidence for repository conventions.

Output:

- evidence-backed repository facts.

## C. Maintenance Analyst

Tasks:

- check referenced paths;
- identify stale file/directory references;
- find duplicated or obsolete sections;
- identify unnecessary repeated context.

## D. Verification Analyst

Tasks:

- review proposed canonical policy;
- check each field against evidence;
- run allowed validation commands;
- challenge unsupported success claims.

Main Bob agent synthesizes the outputs.

---

# 19. Bob Usage Evidence

During development, capture screenshots of:

1. `/init`;
2. Plan mode architecture/design work;
3. Agent mode implementation;
4. Skill creation/use;
5. subagent/parallel audit activity;
6. finding synthesis;
7. repair proposal;
8. verification command/test result;
9. `/review` if used.

Keep screenshots in:

```text
artifacts/screenshots/
```

Use clear filenames:

```text
01-bob-init.png
02-bob-plan-mode.png
03-bob-skill.png
04-bob-subagents.png
05-bob-audit.png
06-bob-repair.png
07-bob-verification.png
```

Never fabricate Bob screenshots.

---

# 20. Implementation Phases

---

# Phase 0 — Scope Lock, Repository Setup, and Hackathon Compliance

## Goal

Create the project skeleton and lock the MVP so the coding agent does not overbuild.

## Tasks

1. Create Git repository.
2. Add MIT `LICENSE`.
3. Add Python project structure.
4. Add `.gitignore`.
5. Add placeholder `README.md`.
6. Add this `AgentLintplan.md`.
7. Add `artifacts/screenshots/`.
8. Create `demo_repos/`.
9. Add basic CI running pytest.
10. Run IBM Bob `/init`.
11. Commit Bob-generated project context files where appropriate.
12. Create `PROGRESS.md` with phase checklist.

## Definition of Done

- project installs;
- `pytest` can run;
- `streamlit run app.py` launches placeholder UI;
- MIT license exists;
- Bob `/init` completed;
- public-repo-safe: no secrets.

## Judge Value

Application of Technology + completeness.

---

# Phase 1 — Domain Models and Instruction Discovery

## Goal

Correctly find supported agent instruction files.

## Tasks

Implement:

```text
agentlint/models.py
agentlint/discovery/instruction_sources.py
```

Discovery rules:

- root `AGENTS.md`;
- root `CLAUDE.md`;
- `.github/copilot-instructions.md`;
- `.bob/rules-code/AGENTS-code.md`;
- `.bob/rules-plan/AGENTS-plan.md`;
- `.bob/rules-ask/AGENTS-ask.md`;
- optional cursor rules if enabled.

Support configuration file:

```text
.agentlint/config.yaml
```

Example:

```yaml
extra_instruction_paths:
  - docs/ai-agent-guidance.md
```

Return discovered sources in a stable ordering.

## Tests

- zero instruction files;
- one file;
- multiple files;
- nested configured path;
- unreadable/missing path;
- Bob mode files.

## Definition of Done

```bash
agentlint scan demo_repos/single-agent-stale-repo
```

reports exactly one instruction source and does not fail.

---

# Phase 2 — Repository Truth / Evidence Engine

## Goal

Build deterministic evidence before semantic AI analysis.

## Tasks

Implement detectors.

### Package Manager Detector

Priority evidence:

1. `package.json.packageManager`;
2. lockfiles;
3. CI commands;
4. README only as weaker evidence.

If evidence conflicts, preserve all evidence instead of guessing.

### Test Framework Detector

Look at:

- dependencies/devDependencies;
- config filenames;
- scripts;
- CI.

### Commands Detector

Parse `package.json` scripts.

For Python, parse common `pyproject.toml` fields and configs where practical.

### Lint/Format Detector

Evidence for ESLint, Prettier, Ruff, Black.

### Runtime Detector

Node/Python version evidence.

### Path Detector

Create repository path index for validating referenced paths later.

### CI Evidence

Parse `.github/workflows/*.yml` enough to extract common command strings.

Do not implement a full YAML workflow interpreter.

## Output

`.agentlint/evidence.json`

## Tests

Create fixtures for:

- npm repo;
- pnpm repo;
- Vitest repo;
- Jest repo;
- pytest repo;
- conflicting package-manager evidence.

## Definition of Done

For the inconsistent demo repository, AgentLint correctly identifies:

- pnpm;
- Vitest;
- test command;
- lint/build commands;
- relevant paths.

---

# Phase 3 — Instruction Parsing and Normalization

## Goal

Extract useful, traceable rules from Markdown instructions.

## MVP Approach

Use two layers.

### Layer 1 — Deterministic extraction

Split Markdown into:

- headings;
- bullet items;
- numbered items;
- command blocks;
- imperative sentences where feasible.

Capture line numbers.

Detect explicit keywords/categories:

- package manager;
- test;
- lint;
- build;
- generated;
- do not edit;
- path;
- runtime.

### Layer 2 — Bob semantic interpretation

Bob handles rules that are not easily normalized deterministically.

Important:
The Python parser should still preserve raw text and source line information so Bob findings remain auditable.

## Normalized examples

```text
"Always use pnpm for dependencies."
category=package_manager
key=package_manager
value=pnpm
```

```text
"Tests must be written in Vitest."
category=test_framework
key=test_framework
value=vitest
```

## Tests

- bullets;
- numbered lists;
- headings;
- code blocks;
- blank files;
- duplicate lines;
- mixed prose.

## Definition of Done

UI/CLI can display instruction rules with source file and line location.

---

# Phase 4 — Deterministic Finding Engine

## Goal

Detect high-confidence findings without Bob.

## Implement

### F02 Package Manager Mismatch

Compare explicit agent rule to strong repository evidence.

### F02 Test Framework Mismatch

Compare rule to dependencies/config evidence.

### F03 Stale Paths

Extract obvious path-like strings and confirm existence.

Use conservative matching to avoid false positives.

### F04 Invalid Commands

For package scripts:

- if instruction says `npm run X`, ensure script `X` exists;
- if policy says `pnpm X`, validate against scripts where applicable.

### F05 Exact Duplicate Rules

Normalize whitespace/case/punctuation and hash.

### Cross-file exact contradictions

If normalized key same and value incompatible.

Example:

```text
package_manager=npm
package_manager=pnpm
```

## Output

`.agentlint/findings.json`

## Definition of Done

The packaged inconsistent repo produces known golden findings with no LLM.

## Important

This phase is critical because it gives Bob grounded evidence instead of making the LLM invent every result.

---

# Phase 5 — Sample Repositories and Golden Scenarios

## Goal

Create deterministic demo cases.

## Demo Repository A — `inconsistent-js-repo`

Use a tiny real runnable Node project.

Actual truth:

- pnpm;
- Vitest;
- ESLint;
- build/test/lint scripts.

Deliberately create instruction problems:

`AGENTS.md`:
- says npm;
- says Jest;
- references old `src/services/`.

`CLAUDE.md`:
- says pnpm;
- says Vitest;
- contains one duplicated rule.

Copilot instructions:
- says run nonexistent `test:unit`;
- duplicates definition-of-done.

Bob rules:
- contain stale command.

Expected output:
- package-manager conflicts;
- testing conflict;
- stale path;
- invalid command;
- duplicates.

## Demo Repository B — `single-agent-stale-repo`

Only one `CLAUDE.md`.

It must prove AgentLint is valuable even with one agent file.

Example:

- CLAUDE.md says npm;
- actual project uses pnpm;
- stale directory;
- outdated test command.

## Demo Repository C — `clean-repo`

Correct instructions matching repository.

Expected:

- no high-severity finding;
- validation passes.

## Golden Files

Store expected findings in:

```text
tests/golden/
```

This prevents regressions.

---

# Phase 6 — Bob Skill, Custom Mode, Slash Commands, and Semantic Audit

## Goal

Make IBM Bob a real part of the product workflow.

## Tasks

1. Create Bob Skill.
2. Create custom Agent Policy Auditor mode using supported Bob configuration.
3. Create `/agentlint-audit`.
4. Use Agent mode and parallel/subagent analysis.
5. Read deterministic outputs.
6. Ask subagents to independently inspect:
   - instruction meaning;
   - repository reality;
   - maintenance/staleness.
7. Synthesize semantic findings.
8. Save Bob-enhanced findings in a separate section or JSON field.

## Required Output Rules

Bob finding MUST include:

```json
{
  "title": "...",
  "type": "...",
  "severity": "...",
  "instruction_sources": ["..."],
  "repository_evidence": ["..."],
  "reasoning_summary": "...",
  "recommended_action": "...",
  "confidence": 0.0
}
```

Do not store or request private chain-of-thought. Only store concise reasoning summaries/evidence.

## Fail-safe

If Bob semantic analysis is unavailable, AgentLint deterministic scan must still work.

This makes the demo robust.

## Definition of Done

A Bob session can run the audit workflow against `inconsistent-js-repo` and produce evidence-backed additional findings or better explanations without overwriting source instructions.

---

# Phase 7 — Canonical Policy Compiler and Repair Plan

## Goal

Convert evidence into an explicit, reviewable source of truth.

## Tasks

1. Generate candidate `.agentlint/policy.yaml`.
2. Every field should include or be traceable to evidence.
3. Bob reviews ambiguous choices.
4. Generate `repair-plan.md`.
5. Produce per-file patch previews.
6. Require approval before applying.

## Adapter Strategy

Do NOT build a perfect universal translator.

MVP repair should support only well-known target files.

For each target instruction file:

- preserve unrelated content;
- modify only identified stale/conflicting lines where safe;
- otherwise propose manual replacement block.

Prefer minimal diff.

## Example Repair Plan

```text
1. AGENTS.md
   Replace "Use npm" with "Use pnpm".
   Evidence: packageManager + pnpm-lock.yaml.

2. AGENTS.md
   Replace "Use Jest" with "Use Vitest".
   Evidence: vitest dependency + vitest config.

3. CLAUDE.md
   Remove duplicate "Run pnpm lint before finishing."
   Evidence: same rule already present in canonical section.
```

## Definition of Done

User can see:

- original;
- proposed change;
- evidence;
- reason;
- expected effect.

---

# Phase 8 — Verification Engine

## Goal

Prove repairs match repository reality.

This is a major differentiator.

## Verification Layers

### Layer A — Structural Re-scan

After repair:

```bash
agentlint scan .
```

Expected fixed findings should disappear.

### Layer B — Policy Evidence Check

Every high-value policy field must still have evidence.

Example:

```text
policy.package_manager=pnpm
evidence -> packageManager + lockfile
PASS
```

### Layer C — Command Validation

Run safe commands from policy:

```text
pnpm lint
pnpm test
pnpm build
```

or project-specific equivalents.

Rules:

- show command before execution;
- use timeout;
- capture exit code;
- capture small output excerpt;
- never run destructive commands;
- allow user to disable execution.

### Layer D — Instruction Consistency

Confirm supported instruction files no longer contain known contradictions.

## Verification Report

Write:

```text
.agentlint/verification.json
```

and human-readable report.

## Important Claim Discipline

AgentLint may claim:

> "The repaired instruction files are consistent with the evidence and the configured validation commands passed."

AgentLint should NOT claim:

> "Every AI coding agent will now behave perfectly."

That cannot be proven by this MVP.

---

# Phase 9 — Streamlit UI

## Goal

Create a judge-friendly and user-friendly dashboard.

## Tasks

Build all pages listed in Section 16.

Must support two modes:

### Demo Mode

Packaged sample repository.

One click:

```text
Load Hackathon Demo
```

This ensures deployed app is reliable.

### Local Report Mode

User selects/points to a local report directory when running Streamlit locally.

Do not try to clone arbitrary private repos in the deployed MVP.

## UI Priorities

1. evidence clarity;
2. before/after;
3. source traceability;
4. easy judge demo;
5. minimal visual clutter.

## Must-have visual

Before/After comparison card.

Example:

```text
BEFORE                        AFTER

Conflicts        3            0
Repo mismatches  4            0
Stale commands   2            0
Validation       1/4          4/4
```

Do not use fabricated metrics.

---

# Phase 10 — GitHub / CI Integration

## Goal

Make AgentLint feel like a real developer tool.

## MVP GitHub Action

Add workflow that runs:

```bash
agentlint scan .
agentlint validate . --no-execute
```

on pull requests that change:

- supported instruction files;
- package/config files;
- `.bob/**`.

If high-severity deterministic conflict exists:

- fail the check;
- print human-readable report.

Example:

```text
AgentLint: FAIL

High-severity instruction drift detected.

AGENTS.md says: npm
Repository evidence: pnpm
```

## Optional Stretch

Generate a Markdown report for PR comments.

Do not make GitHub API integration a blocker.

## Definition of Done

A sample pull request or local workflow run demonstrates that changing an instruction to a stale value causes CI to fail.

This is strong business-value evidence.

---

# Phase 11 — Testing, Hardening, and Quality

## Goal

Make the project reliable enough for judging.

## Unit Tests

Cover:

- discovery;
- package-manager evidence;
- test-framework evidence;
- command extraction;
- rule normalization;
- conflict detection;
- duplicate detection;
- policy serialization;
- validation.

## Integration Tests

Use demo repos.

Expected:

```text
inconsistent repo -> known findings
single-agent stale repo -> known findings
clean repo -> no high-severity drift
```

## Golden Snapshot Tests

Compare normalized reports.

## Safety Tests

Ensure:

- no writes outside allowed paths;
- path traversal rejected;
- command runner has timeout;
- command allowlist/safety rules;
- secrets not included in reports.

## Performance

For hackathon-sized repos, target quick deterministic scan.

Do not promise enterprise-scale performance without testing.

## Definition of Done

- full test suite passes;
- lint passes;
- demo runs from fresh clone;
- no hardcoded absolute paths;
- no API keys in repository.

---

# Phase 12 — Deployment, Documentation, Demo, and Submission

## Goal

Turn working code into a complete hackathon submission.

## 12.1 README

README must contain:

1. problem;
2. solution;
3. 30-second architecture;
4. why IBM Bob 2.0;
5. features;
6. screenshots;
7. setup;
8. run demo;
9. run against local repo;
10. Bob workflow;
11. project structure;
12. limitations;
13. future work;
14. MIT license.

## 12.2 Deployment

Deploy Streamlit demo.

The deployed app should use bundled sample data or sample repo output.

Do not require judge-owned Bob credentials to see the basic demo.

## 12.3 Public Repository

Confirm:

- public;
- no secrets;
- README works;
- LICENSE;
- Bob files committed;
- sample repo works;
- screenshots visible.

## 12.4 Cover Image

Concept:

```text
AgentLint
One repo. Many AI coding agents. One source of truth.

[AGENTS.md] [CLAUDE.md] [Copilot] [Bob Rules]
                 |
                 v
             AgentLint
                 |
                 v
          Repository Truth
```

## 12.5 Slide Deck

Recommended 6 slides:

1. Problem
2. Why now / real developer workflow
3. AgentLint solution
4. IBM Bob architecture
5. Live evidence / before-after
6. Business value + future

## 12.6 3-Minute Video

Target script:

### 0:00–0:20 — Hook

"Teams increasingly use multiple AI coding agents, but those agents can receive different or stale repository instructions."

Show:

```text
AGENTS.md -> npm + Jest
CLAUDE.md -> pnpm + Vitest
Repo -> pnpm + Vitest
```

### 0:20–0:40 — Product

"AgentLint checks AI-agent instructions against repository truth."

### 0:40–1:10 — Deterministic Scan

Show dashboard findings.

### 1:10–2:05 — IBM Bob 2.0

Show actual Bob IDE:

- skill;
- subagent/parallel analysis;
- repository evidence;
- repair plan.

### 2:05–2:35 — Repair + Verification

Show before/after and real commands passing.

### 2:35–2:55 — CI / Real User

Change a rule and show AgentLint CI finding drift.

### 2:55–3:00 — Close

"AgentLint gives every coding agent the same repository truth."

At least 90 seconds must show the actual solution working.

## 12.7 Submission Text

Prepare:

- Short Description
- Problem & Solution Statement <= 500 words
- IBM Bob Usage Statement <= 500 words
- Technology tags

Do this only after final features are implemented so claims match reality.

---

# 21. AI Implementation Protocol

A coding AI following this plan MUST use the following workflow.

## Rule 1 — Implement phases in order

Do not jump directly to UI.

Correct order:

```text
models/discovery
-> evidence
-> parsing
-> deterministic findings
-> demo repos
-> Bob workflow
-> policy/repair
-> verification
-> UI
-> CI
-> hardening
-> submission
```

## Rule 2 — End every phase with tests

Do not mark a phase complete because files exist.

Mark it complete only when acceptance criteria pass.

## Rule 3 — Keep `PROGRESS.md`

Example:

```markdown
- [x] Phase 0
- [x] Phase 1
- [ ] Phase 2
```

Also record:

- commands run;
- tests;
- known issues.

## Rule 4 — Commit each completed phase

Suggested commits:

```text
feat: bootstrap AgentLint project
feat: discover AI agent instruction sources
feat: add repository evidence engine
feat: parse and normalize instruction rules
feat: detect deterministic instruction drift
feat: add hackathon demo repositories
feat: add IBM Bob audit workflow
feat: generate canonical agent policy
feat: add evidence-backed verification
feat: add Streamlit dashboard
feat: add AgentLint pull request check
docs: prepare hackathon submission assets
```

## Rule 5 — No fake functionality

Do not create UI buttons that pretend to call Bob.

If Bob runs in the IDE, the UI should honestly display artifacts generated by the Bob workflow.

If live programmatic Bob integration is later added using an officially supported method, clearly separate it as an extension.

## Rule 6 — No fake metrics

Only display metrics calculated from scan results.

## Rule 7 — No unnecessary dependencies

Prefer standard library + small stable dependencies.

## Rule 8 — Keep Bob usage meaningful

Use Bob for:

- semantic document understanding;
- repository reasoning;
- parallel investigation;
- synthesis;
- repair planning;
- verification reasoning.

Do not spend limited Bob usage generating basic Streamlit layout.

---

# 22. Recommended Technology Stack

## Core

- Python 3.11+
- Typer or argparse for CLI
- PyYAML
- TOML parser (`tomllib` on Python 3.11)
- Streamlit
- pytest

Optional:

- Pydantic if helpful;
- `rapidfuzz` for deterministic near-duplicate detection.

Avoid LangChain unless a concrete need appears.

## Bob

- IBM Bob 2.0 IDE
- Agent mode
- Plan mode
- `/init`
- Skills
- custom modes
- subagents / parallel task delegation
- custom slash commands
- `/review` where useful

## DevOps

- Git
- GitHub
- GitHub Actions
- Streamlit deployment

---

# 23. Bobcoin / Limited-Usage Strategy

Official challenge materials say Bob usage is limited and should be managed.

Therefore:

## Use normal coding tools for:

- Python boilerplate;
- Streamlit layout;
- unit tests that do not need Bob reasoning;
- CSS/presentation;
- documentation formatting.

## Spend Bob usage on:

1. `/init`;
2. architecture planning;
3. Skill/custom mode creation and testing;
4. semantic audit of demo repo;
5. subagent investigation;
6. repair proposal;
7. verification;
8. final Bob review;
9. screenshots/evidence.

Do not assume a fixed Bobcoin cost per task.

Monitor the account balance and stop unnecessary exploratory prompts.

---

# 24. MVP vs Stretch Features

## Must Ship

- instruction discovery;
- single-agent stale instruction detection;
- multi-agent conflict detection;
- repository evidence engine;
- package manager mismatch;
- testing framework mismatch;
- stale path;
- invalid command;
- exact duplicate rule;
- canonical policy;
- repair preview;
- deterministic re-scan;
- command verification;
- Streamlit demo;
- IBM Bob Skill;
- Bob custom workflow;
- Bob subagent evidence;
- public GitHub;
- video/slides/screenshots.

## Ship If Time

- semantic duplicate detection;
- Cursor rules;
- GitHub Action;
- nicer conflict graph;
- Markdown export;
- local repo chooser;
- generated/protected path inference.

## Do NOT Prioritize Before Submission

- authentication;
- database;
- user accounts;
- billing;
- SaaS multi-tenancy;
- full GitHub App;
- support for every language;
- live Claude/Cursor/Copilot APIs;
- complex RAG;
- vector database.

---

# 25. Acceptance Test Scenarios

## Scenario A — Multiple agent files

Input:

```text
AGENTS.md -> npm, Jest
CLAUDE.md -> pnpm, Vitest
repo -> pnpm, Vitest
```

Expected:

- cross-file package-manager conflict;
- repo mismatch for npm;
- test-framework conflict;
- repo mismatch for Jest;
- evidence for pnpm/Vitest;
- policy recommends pnpm/Vitest.

## Scenario B — One agent file

Input:

```text
CLAUDE.md -> npm
repo -> pnpm
```

Expected:

- repo mismatch found;
- no need for second agent file.

## Scenario C — Stale path

Instruction:

```text
Place new services in src/services/
```

Repo:

```text
src/services/ absent
```

Expected:

- stale-path finding with conservative confidence.

## Scenario D — Invalid command

Instruction:

```text
Run pnpm test:unit
```

Package scripts do not contain `test:unit`.

Expected:

- invalid-command finding.

## Scenario E — Clean repository

Instructions and repository agree.

Expected:

- no high-severity findings;
- validation passes.

---

# 26. Success Metrics for Demo

Track metrics that are measurable.

Recommended:

- instruction sources scanned;
- rules extracted;
- conflicts found;
- repository mismatches found;
- invalid commands found;
- stale paths found;
- duplicate groups found;
- findings repaired;
- validation checks passing;
- instruction bytes/tokens reduced only if calculated correctly.

Good:

```text
Before: 9 open findings
After: 0 high/critical open findings
Validation: 4/4 passed
```

Avoid:

```text
"AgentLint saves companies 70% engineering cost."
```

unless you have real evidence.

---

# 27. Judge-Facing Story

The strongest narrative is:

> AI coding agents are becoming part of the development team, but the instructions controlling them are ordinary repository files that drift like any other documentation. AgentLint treats those instructions as executable development policy. It compares them against the actual repository, uses IBM Bob 2.0 to reason across multiple instruction sources in parallel, proposes a canonical contract, and verifies the repaired guidance with real repository evidence and commands.

This directly demonstrates:

- a specific developer-maintenance problem;
- Bob operating with repository context;
- document understanding;
- parallel/subagent work;
- multi-step workflow;
- measurable before/after evidence.

---

# 28. Risks and Mitigations

## Risk 1 — Idea looks like a simple Markdown comparator

Mitigation:

- repository evidence engine;
- semantic Bob audit;
- canonical policy;
- repair plan;
- verification;
- CI drift prevention.

## Risk 2 — Bob appears peripheral

Mitigation:

- Bob Skill;
- custom Bob mode;
- subagents;
- actual semantic findings;
- Bob-generated repair reasoning;
- video shows Bob workflow.

## Risk 3 — Demo depends on unpredictable LLM output

Mitigation:

- deterministic baseline;
- prepared sample repos;
- golden tests;
- Bob adds semantic value but core demo does not collapse if one response differs.

## Risk 4 — Too much time spent supporting agents

Mitigation:

- limit supported files;
- adapter-based design;
- add agents only after MVP.

## Risk 5 — Claiming cross-agent behavioral verification

Mitigation:

- verify instruction consistency and repository commands;
- do not claim to test Claude/Copilot behavior unless actually integrated.

## Risk 6 — Bobcoins run out

Mitigation:

- implement deterministic core first;
- reserve Bob for high-value audit sessions;
- capture screenshots as soon as successful runs occur.

---

# 29. Final Pre-Submission Checklist

## Product

- [ ] AgentLint deterministic scan works.
- [ ] One-instruction-file case works.
- [ ] Multiple-instruction-file case works.
- [ ] Repository truth evidence works.
- [ ] Canonical policy generated.
- [ ] Repair preview works.
- [ ] Verification works.
- [ ] Clean repo produces clean result.
- [ ] Streamlit demo deployed.

## IBM Bob

- [ ] `/init` used.
- [ ] Bob Skill committed.
- [ ] Custom Bob mode committed/configured.
- [ ] Bob subagents/parallel analysis demonstrated.
- [ ] Bob-assisted files present.
- [ ] Bob task-session screenshots captured.
- [ ] Bob verification shown in video.

## Repository

- [ ] Public.
- [ ] MIT LICENSE.
- [ ] No secrets.
- [ ] README complete.
- [ ] Fresh-clone setup tested.
- [ ] Tests passing.
- [ ] Demo commands documented.

## Submission

- [ ] Project Title.
- [ ] Short Description.
- [ ] Problem & Solution Statement <= 500 words.
- [ ] IBM Bob Usage Statement <= 500 words.
- [ ] Technology tags.
- [ ] Public code repo.
- [ ] Bob screenshots.
- [ ] Demo platform.
- [ ] Application URL.
- [ ] Cover image.
- [ ] <= 3 minute MP4.
- [ ] >= 90 seconds actual demo.
- [ ] Slide deck.

---

# 30. Final Definition of "100% Complete"

AgentLint is complete for this hackathon when a judge can:

1. open the public GitHub repository;
2. understand the problem in under one minute;
3. run the deterministic AgentLint demo;
4. see a repo with stale/conflicting agent instructions;
5. see evidence showing what the repository actually uses;
6. see IBM Bob 2.0 analyze the instruction/repository evidence using the committed Bob workflow;
7. see a proposed canonical policy and repair;
8. see the repaired repository re-scanned;
9. see real lint/test/build or equivalent validation pass;
10. view a deployed dashboard showing the before/after evidence;
11. verify from the repository and video that Bob was meaningfully used;
12. find every required hackathon submission artifact.

The implementation should optimize for **clarity, evidence, reliability, and Bob-specific workflow depth**, not maximum feature count.

---

# 31. Official Source Notes

This plan is grounded in the IBM Bob 2.0 Hackathon material supplied for the project and current IBM Bob documentation.

## Hackathon requirements reflected in this plan

The supplied challenge states that participants should:

- improve a specific developer workflow;
- start from a problem with excessive time, effort, or errors;
- use IBM Bob 2.0 to build a working prototype on a real or sample project;
- leverage Bob capabilities such as Agent mode, parallel tasks, subagents, and document understanding;
- demonstrate measurable workflow impact;
- actively use Bob while managing limited usage.

Judging categories:

- Application of Technology
- Presentation
- Business Value
- Originality

Required deliverables include:

- public repository;
- Bob task-session summary screenshots;
- application URL;
- cover image;
- <=3-minute video with >=90 seconds of the product in action;
- slide presentation;
- <=500-word Problem & Solution Statement;
- <=500-word IBM Bob Usage Statement.

## IBM Bob documentation used for architecture

Current official IBM Bob documentation describes:

- `/init` generating persistent `AGENTS.md` project context;
- Agent mode with Read/Edit/Execute/MCP/Skill/Subtask/Subagent capabilities;
- Plan mode for technical planning;
- reusable Skills;
- custom modes with configurable tool access and file edit restrictions;
- custom slash commands stored in `.bob/commands/`;
- built-in `/review` and `/create-pr`.

Official references:

- https://bob.ibm.com/docs/ide/tutorials/start-a-project
- https://bob.ibm.com/docs/ide/features/modes
- https://bob.ibm.com/docs/ide/tutorials/use-skills
- https://bob.ibm.com/docs/ide/configuration/custom-modes
- https://bob.ibm.com/docs/ide/features/slash-commands
- https://bob.ibm.com/docs/ide/getting-started/quickstart

---

# 32. One-Sentence Build Instruction for a Coding AI

> Implement AgentLint exactly as this phased specification describes: first build a deterministic, evidence-backed scanner that checks AI coding-agent instructions against repository reality; then add IBM Bob 2.0 Skills, custom mode, subagent semantic analysis, human-approved repair generation, verification, Streamlit visualization, CI drift detection, tests, deployment, and all hackathon submission assets—without fabricating metrics, Bob integrations, or unsupported claims.
