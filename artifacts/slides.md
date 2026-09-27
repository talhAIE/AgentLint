# Slide 1: The Problem
**Stale AI Instructions**
* Teams use multiple AI coding agents.
* Each agent gets its own instruction file (`AGENTS.md`, `CLAUDE.md`).
* Instructions drift from repository truth.
* Agents generate bad code based on stale guidance.

---
# Slide 2: Why Now?
**The Proliferation of AI Tools**
* Developers no longer just write code; they manage AI agents.
* Inconsistent rules lead to conflicting pull requests.
* Maintaining context manually is impossible as the repository evolves.

---
# Slide 3: The AgentLint Solution
**One source of truth for all agents**
* Discovers all agent instructions.
* Collects evidence from the actual repository (lockfiles, configs).
* Detects conflicts, stale paths, and invalid commands.
* Unifies everything into a canonical policy.

---
# Slide 4: IBM Bob 2.0 Architecture
**Semantic Reasoning Meets Deterministic Validation**
* Deterministic checks handle files, paths, and dependencies.
* **IBM Bob** handles natural language parsing, semantic conflict detection, and policy synthesis.
* Integrated custom Bob Modes and Skills for human-in-the-loop repair.

---
# Slide 5: Live Evidence
**Before vs. After**
* *Before:* 6 conflicting sources, 27 open findings, invalid commands.
* *AgentLint Audit:* Evidence-backed report highlighting exact discrepancies.
* *After:* 0 cross-file conflicts, canonical contract applied, 100% verification pass rate.

---
# Slide 6: Business Value & Future
**Measurable Drift Reduction**
* Reduces developer time spent correcting AI agents.
* Prevents broken builds caused by wrong agent assumptions.
* Future: CI/CD integration, GitHub App, and broader language support.
