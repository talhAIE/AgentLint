**IBM Bob 2.0 Integration**

AgentLint leverages IBM Bob 2.0's powerful orchestration and semantic reasoning capabilities to elevate a simple linting tool into an intelligent workflow. While standard deterministic checks handle lockfiles and paths, Bob is used for the critical semantic tasks:

- **Instruction Parsing:** Bob reads raw, natural-language instructions from various agent files and normalizes them into structured rules.
- **Semantic Deduplication & Conflict Detection:** Bob identifies when two differently worded instructions conflict or mean the same thing, which a deterministic regex could never catch.
- **Policy Synthesis:** Using repository evidence, Bob proposes a minimal, safe canonical contract (`policy.yaml`) and a corresponding repair plan.
- **Custom Mode & Skills:** AgentLint includes a custom Bob Mode (`agent-policy-auditor.yaml`) and reusable skills to help human reviewers interact with the generated repair plans and verify findings directly within the Bob IDE.
- **Subagent Parallelization:** Bob orchestrates parallel investigation subagents to analyze distinct parts of the repository evidence against the discovered rules.
