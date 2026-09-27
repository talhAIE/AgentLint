# Phase 9 — React + FastAPI UI Plan

## Overview

Replace the Streamlit `app.py` placeholder with a production-quality, dark-mode React SPA backed by a FastAPI micro-server.
The React frontend lives in `frontend/`, the Python server in `agentlint/server/`, and both are launched with a single `agentlint ui` CLI command.

### Design Philosophy
- **Terminal-intelligence aesthetic** — deep charcoal/slate background, electric cyan/teal accents.
- **Evidence-first layout** — every finding card shows its source instruction + repository evidence.
- **Human-in-the-loop** — repair actions require explicit approval; nothing writes silently.
- **Demo-safe** — "Load Hackathon Demo" serves pre-generated fixtures from `demo_repos/`; zero runtime dependencies.

---

## Color Palette

| Token | Hex | Usage |
|-------|-----|-------|
| `bg-base` | `#0F1117` | Page background |
| `bg-surface` | `#1A1D27` | Cards, panels |
| `bg-elevated` | `#21253A` | Modals, hover states |
| `border` | `#2E3250` | Card borders, dividers |
| `accent-cyan` | `#22D3EE` | Primary CTA, active nav, links |
| `accent-teal` | `#14B8A6` | Secondary accent, badges |
| `text-primary` | `#E2E8F0` | Body text |
| `text-muted` | `#64748B` | Labels, metadata |
| `severity-critical` | `#EF4444` | Critical findings |
| `severity-high` | `#F97316` | High findings |
| `severity-warn` | `#F59E0B` | Medium findings, warnings |
| `severity-info` | `#6366F1` | Low/info findings |
| `pass-green` | `#22C55E` | PASS status, clean state |

---

## Tech Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Frontend framework | React 18 + Vite | Fast HMR, ESM-native, zero config |
| Styling | Tailwind CSS v3 | Utility-first, custom palette via `tailwind.config.js` |
| Component primitives | shadcn/ui (Radix UI) | Accessible, headless, dark-mode ready |
| Icons | Lucide React | Consistent line-icon set |
| Routing | React Router v6 | SPA navigation, hash-mode for static serving |
| Data fetching | TanStack Query v5 | Cache, loading/error states, background refetch |
| Diff viewer | react-diff-viewer-continued | Repair preview diffs |
| Code highlight | Shiki (via @shikijs/react) | YAML/JSON/Markdown syntax highlighting |
| Charts | Recharts | Finding distribution bar chart on overview |
| Backend | FastAPI + uvicorn | Thin Python wrapper over existing engine |
| API schema | Pydantic v2 (already a dep) | Request/response validation |
| Concurrency | anyio / asyncio | Non-blocking scan subprocess |
| Launcher | `agentlint ui` Typer command | Spawns uvicorn + opens browser |

---

## Project Structure

```
frontend/
  index.html
  vite.config.ts
  tailwind.config.js
  src/
    main.tsx
    App.tsx                  # Router + Layout shell
    api/
      client.ts              # axios base instance
      endpoints.ts           # typed API functions
    components/
      layout/
        Sidebar.tsx          # nav links, demo toggle
        TopBar.tsx           # repo name, scan button, status pill
      common/
        SeverityBadge.tsx
        StatusPill.tsx
        EvidenceTag.tsx
        FindingCard.tsx
        CodeBlock.tsx
    pages/
      OverviewPage.tsx
      SourcesPage.tsx
      FindingsPage.tsx
      EvidencePage.tsx
      PolicyPage.tsx
      RepairPage.tsx
      VerificationPage.tsx

agentlint/server/
  __init__.py
  app.py                     # FastAPI application factory
  routers/
    scan.py                  # POST /scan, GET /scan/status
    artifacts.py             # GET /findings, /evidence, /policy, /repair, /verification
    demo.py                  # GET /demo/repos, POST /demo/load/{repo_name}
  models.py                  # Pydantic response schemas (mirrors agentlint.models)
  fixtures.py                # Loads pre-generated JSON from demo_repos/
```

---

## Sub-Tasks

---

### ST-1 — Delete Streamlit, Add FastAPI skeleton

**Status:** `[ ] pending`

**Intent**
Remove `app.py` and Streamlit from the dependency list, add `fastapi` and `uvicorn` to `pyproject.toml`, scaffold the `agentlint/server/` package and its `FastAPI` application factory, and register the `agentlint ui` Typer command in `agentlint/cli.py`.

**Expected Outcomes**
- `app.py` deleted
- `agentlint/server/__init__.py`, `app.py`, `routers/`, `models.py`, `fixtures.py` created
- `pyproject.toml` updated: remove `streamlit`, add `fastapi>=0.111`, `uvicorn[standard]>=0.29`
- `agentlint ui --host 127.0.0.1 --port 8000` command starts uvicorn and opens browser
- `GET /healthz` returns `{"status": "ok"}`

**Todo List**
- [ ] Delete `app.py` from project root
- [ ] Add `fastapi>=0.111`, `uvicorn[standard]>=0.29` to `pyproject.toml` `[project.dependencies]`
- [ ] Remove `streamlit` from `pyproject.toml`
- [ ] Create `agentlint/server/__init__.py` (empty)
- [ ] Create `agentlint/server/app.py` — `create_app()` factory, CORS for `localhost:5173`, `GET /healthz`
- [ ] Create `agentlint/server/models.py` — Pydantic response schemas mirroring `agentlint.models`
- [ ] Create `agentlint/server/fixtures.py` — `load_demo_fixtures(repo_name)` reads `.agentlint/` from `demo_repos/{repo_name}`
- [ ] Create `agentlint/server/routers/__init__.py`, `scan.py`, `artifacts.py`, `demo.py` stubs
- [ ] Add `ui` command to `agentlint/cli.py` that runs `uvicorn agentlint.server.app:create_app --factory`

**Relevant Context**
- `agentlint/cli.py` — existing Typer app, add `ui` command here
- `pyproject.toml` — dependency list and entry points
- `demo_repos/*/` — directories contain `.agentlint/` JSON artifacts for demo mode

---

### ST-2 — FastAPI Artifact Routers

**Status:** `[ ] pending`

**Intent**
Implement all REST endpoints the React frontend will call. The server reads pre-existing `.agentlint/` JSON/YAML artifacts and returns them as structured JSON. No scan logic is re-implemented here — the server only wraps the CLI engine outputs.

**Expected Outcomes**
- `POST /scan` triggers `agentlint scan <repo_path>` as a subprocess, returns job ID
- `GET /scan/status/{job_id}` returns `running | done | error` with progress messages
- `GET /artifacts/findings` returns findings list from `findings.json`
- `GET /artifacts/evidence` returns evidence items from `evidence.json`
- `GET /artifacts/policy` returns policy fields from `policy.yaml`
- `GET /artifacts/repair` returns repair plan text from `repair-plan.md`
- `GET /artifacts/verification` returns verification results from `verification.json`
- `GET /artifacts/sources` returns instruction source list from `scan.json`
- `GET /demo/repos` returns list of 3 demo repo names
- `POST /demo/load/{repo_name}` copies demo fixtures to `.agentlint/` (activates demo data)

**Todo List**
- [ ] Implement `routers/artifacts.py` — each endpoint reads from `.agentlint/` path resolved at startup
- [ ] Implement `routers/scan.py` — async subprocess launch, `asyncio.Queue` for SSE streaming of stdout
- [ ] Implement `routers/demo.py` — list `demo_repos/` and copy fixture `.agentlint/` into active dir
- [ ] Register all routers in `server/app.py`
- [ ] Add error responses: `404` if artifact not found (scan not yet run), `400` for invalid demo name
- [ ] Write `tests/unit/test_server_endpoints.py` — mock filesystem reads, test all routes

**Relevant Context**
- `agentlint/analysis/__init__.py` — `run_deterministic_checks()` for understanding what findings.json contains
- `demo_repos/inconsistent-js-repo/.agentlint/`, `single-agent-stale-repo/.agentlint/`, `clean-repo/.agentlint/` — fixture directories
- `agentlint/models.py` — data model shapes to mirror in `server/models.py`

---

### ST-3 — React + Vite Project Scaffold

**Status:** `[ ] pending`

**Intent**
Scaffold the `frontend/` directory with Vite + React + TypeScript, configure Tailwind CSS with the AgentLint color palette, install shadcn/ui primitives, and create the App shell with Sidebar + TopBar layout and all 7 page routes.

**Expected Outcomes**
- `frontend/` contains a working Vite dev server (`npm run dev` on port 5173)
- Tailwind palette tokens defined in `tailwind.config.js` match the color table above
- App shell renders: Sidebar with 7 nav links, TopBar with repo name and scan button
- All 7 page route stubs render (no content yet, just page title + placeholder)
- `npm run build` produces `frontend/dist/` which FastAPI serves as static files at `/`

**Todo List**
- [ ] `npm create vite@latest frontend -- --template react-ts`
- [ ] `cd frontend && npm install tailwindcss@3 postcss autoprefixer`
- [ ] `npx tailwindcss init -p`; write `tailwind.config.js` with full palette token map
- [ ] Install `shadcn/ui`, `lucide-react`, `react-router-dom`, `@tanstack/react-query`, `axios`, `recharts`, `react-diff-viewer-continued`, `@shikijs/react`
- [ ] Create `src/App.tsx` — `BrowserRouter` with `Routes` for all 7 pages
- [ ] Create `Sidebar.tsx` — nav links with Lucide icons, active state highlighting in `accent-cyan`
- [ ] Create `TopBar.tsx` — repo path pill, "Run Scan" button, scan status pill
- [ ] Create 7 page stub components in `src/pages/`
- [ ] Mount static file serving in FastAPI `server/app.py` for `frontend/dist/`
- [ ] Add `"build"` script in `package.json`; update `agentlint ui` command to optionally run build first

**Relevant Context**
- `agentlint/server/app.py` — mount `StaticFiles` at `/` after build
- Color palette defined in the Color Palette table above

---

### ST-4 — Overview & Sources Pages

**Status:** `[ ] pending`

**Intent**
Implement the first two pages: Overview (scan health dashboard) and Instruction Sources (discovered agent files). These are read-only display pages.

**Expected Outcomes**
- **Overview page** shows: repo name, instruction source count, finding counts broken down by severity (Critical / High / Medium / Low / Info), a Recharts horizontal bar chart of finding types (F01–F07), a Before/After comparison card, and verification pass rate badge.
- **Sources page** shows a card list of all discovered instruction files with: file path, agent type, status (found/missing), content hash, and an expandable excerpt of parsed rules.

**Todo List**
- [ ] Create `api/endpoints.ts` — typed functions: `getSources()`, `getFindings()`, `getEvidence()`, `getPolicy()`, `getRepair()`, `getVerification()`
- [ ] Implement `OverviewPage.tsx` — stat cards using TanStack Query to fetch findings and sources; Recharts bar chart; Before/After comparison card
- [ ] Implement `SourcesPage.tsx` — card list per source, expand/collapse parsed rules
- [ ] Create reusable `SeverityBadge.tsx` component (color-coded per palette)
- [ ] Create `StatusPill.tsx` (PASS green / FAIL red / UNKNOWN slate)
- [ ] Wire TanStack Query `QueryClientProvider` in `App.tsx`

**Relevant Context**
- `scan.json` shape: `{ agentlint_version, repo_path, sources: [{path, agent_type, exists, content_hash}] }`
- `findings.json` shape: array of Finding objects with `severity`, `finding_type`, `status`, `confidence`
- `GET /artifacts/sources` → `GET /artifacts/findings` are the two API calls for these pages

---

### ST-5 — Findings & Evidence Pages

**Status:** `[ ] pending`

**Intent**
Implement the two most information-dense pages: Findings (filterable cards per detected issue) and Repository Evidence (structured display of detected repo facts). These pages are the core audit value of the product.

**Expected Outcomes**
- **Findings page** shows:
  - Filter bar: severity dropdown, finding type dropdown, source file dropdown, status toggle
  - Finding cards showing: severity badge, finding ID, type label, affected instruction source, instruction excerpt, supporting evidence tags, recommended action, confidence percentage
  - Clicking a card expands to show full detail including all evidence items
- **Evidence page** shows evidence items grouped by category (package_manager, test_framework, commands, lint_format, runtime, paths, ci) with strength indicator, key/value pairs, and source files

**Todo List**
- [ ] Implement `FindingsPage.tsx` — filter controls using shadcn `Select`, filtered list with `FindingCard`
- [ ] Create `FindingCard.tsx` — collapsible card with all finding fields, evidence tag list
- [ ] Create `EvidenceTag.tsx` — small chip showing evidence category + strength color
- [ ] Implement `EvidencePage.tsx` — grouped accordion sections per category, evidence item rows
- [ ] Add URL-synced filters (React Router `useSearchParams`) so filter state is shareable
- [ ] Link from finding card → evidence page filtered to that evidence ID

**Relevant Context**
- `findings.json` shape: `{ id, finding_type, severity, status, confidence, source_rules: [{path, content}], evidence_ids, recommended_action, explanation }`
- `evidence.json` shape: `{ items: [{category, key, value, source_files, strength, explanation}] }`
- Finding type codes F01–F07 defined in `agentlint/analysis/`

---

### ST-6 — Policy, Repair, and Verification Pages

**Status:** `[ ] pending`

**Intent**
Implement the three action-oriented pages: Canonical Policy (evidence-backed contract), Repair Preview (diff view of proposed changes), and Verification Results (4-layer pass/fail). These complete the full audit workflow in the UI.

**Expected Outcomes**
- **Policy page** shows policy fields rendered as a readable table with source evidence backtrace per field; raw YAML view in a `CodeBlock` component with Shiki syntax highlighting
- **Repair page** shows per-finding diff previews using `react-diff-viewer-continued`; a prominent "Human Approval Required" banner; no apply button (hackathon demo constraint — repair is done via CLI)
- **Verification page** shows 4 verification layers (A: Structural, B: Evidence, C: Commands, D: Consistency) each as a collapsible panel with PASS/FAIL badge and detail messages

**Todo List**
- [ ] Implement `PolicyPage.tsx` — tabbed view: "Readable" table + "Raw YAML" code block
- [ ] Create `CodeBlock.tsx` using Shiki for YAML/JSON highlighting in the dark theme
- [ ] Implement `RepairPage.tsx` — `HumanApprovalBanner` component at top, per-finding diff cards using `react-diff-viewer-continued` in dark mode
- [ ] Implement `VerificationPage.tsx` — 4 accordion panels, each with a `StatusPill` header and collapsible detail list
- [ ] Add "Copy to clipboard" button on CodeBlock for policy YAML

**Relevant Context**
- `policy.yaml` shape: `{ tooling: {package_manager, test_framework, lint_commands, format_commands, runtime}, definition_of_done: {verification_commands}, evidence_trace: {...} }`
- `repair-plan.md` — markdown text with diff blocks per finding; parse into sections by finding ID header
- `verification.json` shape: `{ layers: [{layer_id, name, status, messages: [{level, text}]}] }`

---

### ST-7 — Demo Mode, Polish, and `agentlint ui` Integration

**Status:** `[ ] pending`

**Intent**
Wire up the Demo Mode toggle (loads pre-generated fixtures for the 3 packaged demo repos), add the `agentlint ui` CLI command that builds the frontend if needed and launches FastAPI+uvicorn, and apply final visual polish.

**Expected Outcomes**
- Sidebar contains a "Demo Mode" section with 3 repo buttons: `inconsistent-js-repo`, `single-agent-stale-repo`, `clean-repo`
- Clicking a demo repo calls `POST /demo/load/{repo_name}`, then invalidates all TanStack Query caches to reload all pages
- `agentlint ui` command: checks if `frontend/dist/` exists (builds if not), starts uvicorn on `0.0.0.0:8000`, opens browser to `http://localhost:8000`
- TopBar "Run Scan" button works for local mode (prompts for repo path, calls `POST /scan`)
- Empty-state illustrations shown on each page when no scan has been run yet
- Favicon set to 🔍, page title "AgentLint", footer: "AgentLint v0.1.0 · IBM Bob 2.0 Hackathon · MIT License"
- `README.md` updated with new UI setup instructions (`npm install`, `agentlint ui`)

**Todo List**
- [ ] Add demo repo buttons to `Sidebar.tsx`; on click: call `POST /demo/load/{repo}`, then `queryClient.invalidateQueries()`
- [ ] Add empty-state component (`EmptyState.tsx`) shown when artifact endpoints return 404
- [ ] Implement `agentlint ui` Typer command: check `frontend/dist/`, optionally run `npm run build`, spawn uvicorn, call `webbrowser.open`
- [ ] Set favicon and page title in `frontend/index.html`
- [ ] Add license footer to App layout
- [ ] Update `PROGRESS.md` Phase 9 checklist
- [ ] Update `README.md` with new UI section

**Relevant Context**
- `agentlint/cli.py` — add `ui` command alongside existing `scan`, `policy`, `validate`, `demo` commands
- `demo_repos/` — three subdirectories, each with a pre-populated `.agentlint/` directory
- `agentlint/server/fixtures.py` — `load_demo_fixtures()` already scaffolded in ST-1

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│                 Browser (localhost:8000)             │
│                                                     │
│  React SPA (frontend/dist/)                         │
│  ┌──────────┐  ┌──────────────────────────────────┐ │
│  │ Sidebar  │  │  Page Content                    │ │
│  │ Nav +    │  │  TanStack Query → API calls      │ │
│  │ Demo     │  │  shadcn/Radix components         │ │
│  │ toggle   │  │  Recharts / Shiki / Diff viewer  │ │
│  └──────────┘  └──────────────────────────────────┘ │
└───────────────────────┬─────────────────────────────┘
                        │ REST  /api/*
┌───────────────────────▼─────────────────────────────┐
│  FastAPI (agentlint/server/)                        │
│  ┌─────────────────────────────────────────────────┐ │
│  │  routers/artifacts.py  reads .agentlint/*.json  │ │
│  │  routers/scan.py       subprocess agentlint CLI │ │
│  │  routers/demo.py       copies demo fixtures     │ │
│  └─────────────────────────────────────────────────┘ │
│  Serves frontend/dist/ as static files at /         │
└───────────────────────┬─────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────┐
│  .agentlint/ artifacts (produced by CLI engine)     │
│  scan.json · evidence.json · findings.json          │
│  policy.yaml · repair-plan.md · verification.json   │
└─────────────────────────────────────────────────────┘
```

---

## Files to Delete

| File | Reason |
|------|--------|
| `app.py` | Streamlit placeholder replaced by React SPA |
| `agentlint/ui/components.py` | Streamlit stubs replaced by React components |
| `agentlint/ui/view_models.py` | Streamlit stubs replaced; server-side response models move to `agentlint/server/models.py` |

---

## Files to Create

| File | ST |
|------|----|
| `agentlint/server/__init__.py` | ST-1 |
| `agentlint/server/app.py` | ST-1 |
| `agentlint/server/models.py` | ST-1 |
| `agentlint/server/fixtures.py` | ST-1 |
| `agentlint/server/routers/__init__.py` | ST-1 |
| `agentlint/server/routers/scan.py` | ST-2 |
| `agentlint/server/routers/artifacts.py` | ST-2 |
| `agentlint/server/routers/demo.py` | ST-2 |
| `tests/unit/test_server_endpoints.py` | ST-2 |
| `frontend/` (full Vite project) | ST-3 |
| All `src/pages/*.tsx` and components | ST-4, ST-5, ST-6 |

---

## Files to Modify

| File | ST | Change |
|------|----|--------|
| `pyproject.toml` | ST-1 | Remove streamlit, add fastapi + uvicorn |
| `agentlint/cli.py` | ST-1, ST-7 | Add `ui` command |
| `PROGRESS.md` | ST-7 | Mark Phase 9 complete |
| `README.md` | ST-7 | New UI setup section |
