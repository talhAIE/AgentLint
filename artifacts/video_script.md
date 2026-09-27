# AgentLint Demo Script

**0:00–0:20 — Hook**
"Teams increasingly use multiple AI coding agents, but those agents can receive different or stale repository instructions. For example, your `AGENTS.md` might say to use `npm`, but your repo actually uses `pnpm`. This leads to broken code."

**0:20–0:40 — Product**
"AgentLint checks your AI-agent instructions against repository truth. It's an intelligent linter that ensures your AI helpers are actually helpful."

**0:40–1:10 — Deterministic Scan**
*(Screen recording: Run `agentlint ui` and open the React dashboard)*
"Here is the AgentLint dashboard. It automatically discovered 6 different instruction files and found 27 open findings, including cross-file conflicts and invalid commands."

**1:10–2:05 — IBM Bob 2.0**
*(Screen recording: Open IBM Bob IDE, show the custom mode and skill)*
"AgentLint uses IBM Bob 2.0 for semantic reasoning. While simple checks are deterministic, Bob reads the natural language instructions, identifies semantic conflicts, and generates a unified Canonical Policy and a safe repair plan based on repository evidence."

**2:05–2:35 — Repair + Verification**
*(Screen recording: Show the Repair Preview and Verification page in the UI)*
"We can review the repair plan. Once approved, the changes are applied, and AgentLint runs a 4-layer verification to ensure the new instructions are consistent with the repository."

**2:35–2:55 — CI / Real User**
*(Screen recording: Show the CI output failing when a bad rule is introduced)*
"If a developer introduces a bad rule later, AgentLint catches it in CI, preventing drift before it happens."

**2:55–3:00 — Close**
"AgentLint gives every coding agent the same repository truth. Thank you."
