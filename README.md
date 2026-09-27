# AgentLint

> **One repo. Many AI coding agents. One source of truth.**

AgentLint audits the instruction files given to AI coding agents (`AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md`, Bob rule files, etc.) and checks whether those instructions still accurately reflect the actual repository they are supposed to operate on.

Built for the **IBM Bob 2.0 Hackathon** (lablab.ai).

---

## 1. Problem
As teams increasingly adopt AI coding agents, repositories become littered with uncoordinated instruction files. These files inevitably drift from reality. One agent might be told to use `npm` and `Jest`, while the repository actually uses `pnpm` and `Vitest`. When agents act on conflicting or stale instructions, they introduce bugs, break workflows, and waste developer time correcting them.

## 2. Solution
AgentLint treats the repository as evidence. It scans for all agent instructions, normalizes their rules, and then checks them against the actual facts in the repository (such as lockfiles, dependencies, and configuration files). AgentLint surfaces cross-file conflicts, detects invalid commands, flags stale paths, and proposes a unified canonical instruction policy to keep all agents aligned.

## 3. 30-Second Architecture
```text
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
         IBM Bob semantic audit (via Backend API)
                  |
                  v
          Conflict/staleness report
                  |
                  v
        Canonical Agent Contract + React Dashboard
```

## 4. Why IBM Bob 2.0
AgentLint leverages IBM Bob 2.0's powerful orchestration and semantic reasoning capabilities to elevate a simple linting tool into an intelligent workflow:
- **Instruction Parsing:** Bob normalizes natural-language instructions.
- **Semantic Deduplication & Conflict Detection:** Bob identifies when two differently worded instructions conflict or mean the same thing.
- **Policy Synthesis:** Using repository evidence, Bob proposes a minimal, safe canonical contract (`policy.yaml`).

## 5. Features
- **Multi-Source Discovery:** Supports `AGENTS.md`, `CLAUDE.md`, `.bob/rules-*`, and more.
- **Deterministic Evidence Engine:** Automatically detects package managers, test frameworks, lint commands, and active runtimes.
- **Cross-File Conflict Detection:** Finds disagreements between agent instructions.
- **Interactive UI:** A fully-featured React + FastAPI dashboard to view findings, evidence, and apply repair plans.
- **Automated Verification:** Validates that proposed instructions map exactly to commands that run successfully in the repo.

## 6. Screenshots
*(Placeholder — refer to `artifacts/screenshots/` for live Bob IDE session screenshots.)*
* 01-bob-init.png
* 02-dashboard-view.png
* 03-repair-plan.png

## 7. Setup
Requires **Python 3.11+** and **Node.js** (for the UI).

```bash
# Clone the repository
git clone https://github.com/your-username/agentlint.git
cd agentlint

# Install the Python CLI and Backend dependencies
pip install -e ".[dev]"
```

## 8. Run Demo
AgentLint includes a bundled `demo_repos` directory with pre-calculated fixtures. To view the interactive dashboard:

```bash
agentlint ui
```
*This command will automatically install frontend packages, build the React SPA, and launch the FastAPI server on `http://localhost:8000`.*

## 9. Run Against Local Repo
```bash
# Scan a repository to generate findings and evidence
agentlint scan <repo-path>

# Generate a unified policy using IBM Bob
agentlint policy <repo-path>

# Verify that the repository configuration works
agentlint validate <repo-path>
```

## 10. Bob Workflow
AgentLint includes custom Bob modes and skills located in `.bob/`:
- **Commands:** Use `/agentlint-audit`, `/agentlint-repair`, and `/agentlint-verify` directly in the Bob IDE.
- **Custom Mode:** Enable the `agent-policy-auditor` mode to restrict Bob to instruction auditing without modifying production code.
- **Skills:** `agent-policy-audit` skill helps Bob synthesize evidence into a unified contract.

## 11. Project Structure
```text
agentlint/      
  cli.py          # Command line entrypoint
  server/         # FastAPI backend routers
  models.py       # Pydantic data models
  discovery/      # Locates instruction files
  evidence/       # Extracts facts from repo configs
  parsing/        # Normalizes rules
  analysis/       # Determines conflicts & staleness
frontend/         # React + Vite SPA
demo_repos/       # Bundled sample repositories
tests/            # 500+ unit and integration tests
.bob/             # Bob skills, modes, and commands
```

## 12. Limitations
- **MVP Scope:** Designed for the IBM Bob 2.0 hackathon.
- **Supported Languages:** Evidence extraction currently prioritizes JavaScript/TypeScript and Python ecosystems.
- **Generated Code:** Inference for generated paths relies strictly on explicit configurations rather than heuristics.

## 13. Future Work
- Support for `.cursor/rules/*.mdc`.
- Native GitHub App integration for PR checks.
- Enhanced semantic duplicate detection across massive monolithic repositories.
- Expanded evidence extraction for Go, Rust, and Java.

## 14. License
MIT — see [LICENSE](LICENSE).
