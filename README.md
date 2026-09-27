# AgentLint

> **One repo. Many AI coding agents. One source of truth.**

AgentLint audits the instruction files given to AI coding agents (`AGENTS.md`, `CLAUDE.md`,
`.github/copilot-instructions.md`, Bob rule files, etc.) and checks whether those instructions
still accurately reflect the actual repository they are supposed to operate on.

Built for the **IBM Bob 2.0 Hackathon** (lablab.ai).

---

## Problem

AI coding agents rely on instruction files to understand a project's toolchain, test commands,
paths, and conventions. These files drift over time — contradicting each other and diverging
from the actual repository. AgentLint detects and helps fix that drift.

## Solution

AgentLint treats the repository as ground truth. It extracts evidence (package manager, test
framework, commands, paths) from real repository files and compares that evidence against every
instruction file to find conflicts, stale references, and missing context.

## Architecture

Coming soon — see `AgentLintplan.md` for the full specification.

## Why IBM Bob 2.0

Coming soon.

## Features

Coming soon.

## Setup

Requires Python 3.11+.

```bash
pip install -e ".[dev]"
```

## Run Demo

```bash
agentlint demo
```

## Run Against a Local Repository

```bash
agentlint scan <repo-path>
```

## Bob Workflow

Coming soon.

## Project Structure

```
agentlint/      Python package (CLI, models, discovery, evidence, parsing, analysis, policy, validation, UI)
demo_repos/     Bundled sample repositories for the demo
tests/          Unit, integration, fixture, and golden-snapshot tests
app.py          Streamlit dashboard
```

## Limitations

This is an MVP built for a hackathon. See `AgentLintplan.md` §24 for a full list of MVP vs
stretch features.

## License

MIT — see `LICENSE`.
