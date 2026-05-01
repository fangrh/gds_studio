# GDS Collab Platform — Design Spec

**Date:** 2026-05-01
**Status:** Draft
**Scope:** Full platform — GDS viewer, Issue/Wiki collaboration, AI agent integration, CI/CD

## 1. Overview

A web-based collaboration platform for photonic chip design teams (5–20 people). Python scripts using GDSfactory generate GDS layout files. The platform displays these layouts in a WebGL viewer, lets users file issues against specific design elements, and enables AI agents (Claude, GPT, etc.) to read those issues, modify the source scripts, rebuild the GDS, and respond — closing the design-review loop.

**Core workflow:**
```
Python script (source of truth)
  → GDSfactory generates GDS file (build artifact)
    → WebUI displays layout (WebGL viewer)
      → User files issue linked to elements (deep links)
        → Agent reads issue, modifies script, rebuilds GDS
          → WebUI updates, user reviews, cycle continues
```

## 2. Architecture

### 2.1 Modular Monolith Backend

Single FastAPI process with clean module boundaries. Each module owns its router and business logic. Shared SQLAlchemy models in a top-level `models.py`. Designed to be extractable into microservices if needed.

```
backend/app/
├── main.py              # FastAPI entry, CORS, WebSocket mount
├── db.py                # SQLite connection, session management
├── models.py            # SQLAlchemy models (all tables)
├── gds/                 # GDS module
│   ├── router.py        # /api/gds/* endpoints
│   ├── viewer.py        # GDS parsing, WebGL tile generation
│   ├── watcher.py       # Filesystem watcher for .gds and .py files
│   └── addressing.py    # Deep link generation and resolution
├── issues/              # Issue module
│   ├── router.py        # /api/issues/* endpoints
│   └── schemas.py       # Pydantic request/response schemas
├── wiki/                # Wiki module
│   ├── router.py        # /api/wiki/* endpoints
│   └── schemas.py
└── agent/               # Agent integration module
    ├── router.py        # /api/agent/* endpoints
    └── tracker.py       # Session, model, skill version tracking
```

### 2.2 React SPA Frontend

Three-panel layout. Each panel can be opened in a separate browser tab/window, sharing state via URL deep links and WebSocket events.

```
frontend/src/
├── App.tsx              # Main layout router
├── panels/
│   ├── GdsViewer/       # WebGL GDS viewer panel
│   ├── IssuePanel/      # Issue list + detail view
│   └── WikiPanel/       # Wiki page list + editor
├── components/
│   ├── LayerSelector/   # KLayout-style layer visibility picker
│   ├── DeepLink/        # Hover tooltip with click-to-copy URL
│   ├── CommentThread/   # Shared comment component (issues + wiki)
│   └── GdsEmbed/        # Inline mini-viewer for deep links in comments
└── hooks/
    └── useDeepLink.ts   # Resolve deep links to viewer state
```

### 2.3 Agent Skill Package

Standalone pip-installable package. Works with any AI CLI (Claude Code, Copilot, Codex) that can execute Python commands.

```
agent-skill/
├── gds_collab_skill/
│   ├── __init__.py
│   ├── cli.py           # /replyit entry point
│   ├── client.py        # HTTP client for platform API
│   ├── context.py       # Build prompt context from issue
│   └── post.py          # Post response + trigger rebuild
├── skill.md             # Claude Code skill definition
└── pyproject.toml
```

### 2.4 Deployment: k3s + CI/CD

Single-node k3s cluster with staging and production namespaces. CI/CD via GitHub Actions.

```
k3s cluster (single server)
├── Namespace: staging   → backend:stg, frontend:stg, SQLite PVC
├── Namespace: prod      → backend:prod, frontend:prod, SQLite PVC
├── Namespace: system    → Traefik ingress, cert-manager, local registry
└── Argo Workflows       → GDS build pipelines, agent orchestration, batch jobs

Shared volumes:
├── PV: /data/gds/       → GDS build artifacts
├── PV: /data/scripts/   → Python source scripts
└── PV: /data/db/        → SQLite database files (per namespace)
```

**CI/CD Pipeline (GitHub Actions):**
- **PR:** lint (ruff + eslint) → unit tests (pytest + jest) → build images → deploy staging → integration tests → block merge until green
- **Tag (vX.Y.Z):** build production images → push to local registry → bump Helm values → deploy to prod (manual approval) → smoke tests → auto-generate changelog

**Argo Workflows:**
- GDS ingestion: file change detected → run GDSfactory → parse GDS → index cells/elements → generate WebGL tiles → update DB → notify frontend via WebSocket
- Agent tasks: /replyit triggers workflow → agent processes issue → rebuild → verify → post response
- Batch processing: DRC checks, simulation queues, layout validation

**Helm chart structure:**
```
helm/
└── gds-collab/
    ├── Chart.yaml
    ├── values.yaml           # Default values
    ├── values-staging.yaml   # Staging overrides
    ├── values-production.yaml # Production overrides
    └── templates/
        ├── backend-deployment.yaml
        ├── frontend-deployment.yaml
        ├── ingress.yaml
        ├── pvc.yaml
        └── configmap.yaml
```

## 3. GDS Viewer Module

### 3.1 Rendering

Client-side WebGL rendering via OpenLayers. The backend parses GDS files and generates a tile pyramid (like map tiles). The frontend loads tiles on demand as the user pans/zooms. OpenLayers is chosen for its proven pan/zoom/tile infrastructure, used in GIS and CAD viewers.

- **Tile generation:** Backend uses klayout's Python module (`klayout.db`) to parse GDS files. Each cell is rendered into tile layers at multiple zoom levels.
- **Layer visibility:** KLayout-style layer selector panel. Each GDS layer (M1, D1, etc.) can be toggled on/off, with configurable colors.
- **Element highlighting:** Deep-linked elements are highlighted with a distinct outline when navigated to.

### 3.2 Script ↔ GDS Mapping

Every GDS file is a build artifact. The `gds_scripts` table tracks which Python script produced which GDS file.

- The file watcher monitors `/data/scripts/*.py` for changes.
- On change, an Argo Workflow runs the script via GDSfactory.
- Output GDS is parsed: every cell and element is indexed with coordinates, layer, element type, and the source script line that created it.
- `source_line` on each element enables the agent to jump directly to the code that produced it.

### 3.3 Deep Links

URL-based deep links enable sharing and cross-referencing between viewer, issues, and wiki.

**Formats:**
```
# Design-level
/viewer?gds=ring_resonator&build=42

# Cell-level
/viewer?gds=ring_resonator&cell=ring_cell_1&layers=M1,D1

# Element-level
/viewer?gds=ring_resonator&cell=ring_cell_1&elem=342&layer=M1&bbox=10.5,20,30,40

# Multi-element
/viewer?gds=ring_resonator&elems=342,343,345&layer=M1
```

**Interaction:** Mouse hover on any element shows a tooltip with the deep link. Click copies to clipboard. Pasting a deep link into an issue or wiki comment renders an inline mini-preview of that element.

### 3.4 Multi-Window Support

Each panel (viewer, issues, wiki) can be opened in its own browser tab. Panels communicate via:
- **Shared URL state:** Deep links navigate any panel to the right context.
- **WebSocket events:** Changes in one panel (e.g., element click in viewer) broadcast to other open panels to highlight the same element.

## 4. Issue Module

### 4.1 Issue Lifecycle

```
open → in_progress (agent claims) → resolved → closed
                                        ↑
                                    reopened (if regression)
```

- **open:** Created by a user, linked to one or more GDS elements.
- **in_progress:** An agent has claimed the issue and is working on it.
- **resolved:** Agent has modified the script, rebuilt, and posted a response. User can verify.
- **closed:** User confirms the fix is correct.
- **reopened:** If a subsequent build regresses the fix.

### 4.2 Element Linking

Issues link to GDS elements via the `issue_elements` join table. Each link stores:
- `gds_build_id`: which build the element belongs to
- `cell_name`: the cell containing the element
- `element_id`: the specific element within the cell
- `layer`: the GDS layer
- `bbox`: bounding box coordinates
- `source_script_line`: line in the Python script that created this element
- `deep_link_url`: pre-built URL for one-click navigation

Clicking a linked element in the issue detail view opens the viewer panel and highlights that element.

### 4.3 Comments

GitHub-issue-style threaded comments. Each comment records:
- `author_type`: "user" or "agent"
- `author_id`: references users table or agent_sessions table
- `body`: Markdown content
- `agent_model`: (agent only) which AI model wrote this (e.g., "claude-sonnet-4.6")
- `agent_skill_version`: (agent only) version of the skill package used

Agent comments are visually distinct from user comments in the UI.

## 5. Wiki Module

Wiki pages are persistent documents (no open/closed lifecycle). They support:
- **Markdown body** with embedded GDS deep links (rendered as inline mini-viewers)
- **Comment threads** (same CommentThread component as issues, same comments table with `target_type="wiki"`)
- **Version history**: each edit increments a version counter; diffs are viewable
- **Categories and tags** for organization (e.g., "design rules", "process notes", "tapeout-2026-q3")
- **Author tracking**: `last_editor_type` and `last_editor_id` record who made each edit

## 6. Agent Integration Module

### 6.1 Agent Session Model

Each invocation of `/replyit` creates an `agent_session` record:
- `agent_type`: "claude-code", "copilot", "openai-codex", etc.
- `model`: specific model used (e.g., "claude-sonnet-4.6")
- `skill_version`: pip package version
- `issues_processed`, `builds_triggered`: counters
- `status`: "active", "completed", "failed"

Every agent comment links to its session, providing full traceability.

### 6.2 API Endpoints

```
GET  /api/agent/poll           → list unclaimed issues (status=open, not claimed)
POST /api/agent/claim/{id}     → set issue to in_progress, lock to session
POST /api/agent/build          → trigger Argo rebuild for a script
POST /api/agent/comment        → post agent comment on an issue or wiki page
POST /api/agent/resolve/{id}   → set issue to resolved
GET  /api/agent/session        → register/verify agent session
```

All endpoints are localhost-only (no authentication). The backend checks that requests come from 127.0.0.1.

### 6.3 /replyit Skill Workflow

The skill is defined in `skill.md` for Claude Code. For other agents, it's invoked as a CLI command.

```
1. gds-collab-skill poll          → fetch pending issues
2. For each issue:
   a. Read issue body, comments, linked elements
   b. Read source script (via API or direct file access)
   c. Agent modifies script using GDSfactory API
   d. Commit changes to git
   e. gds-collab-skill build --script <id> --commit <sha>
   f. gds-collab-skill resolve --issue <id> --body "..."
```

Each step is idempotent. If the agent crashes mid-process, the issue remains `in_progress` and another session can pick it up. Stale claims (no activity for 30 minutes) auto-release back to `open`.

### 6.4 Cross-Agent Compatibility

The REST API is the universal contract. The pip package is a convenience wrapper:
- **Claude Code:** Native skill via skill.md
- **Copilot CLI:** Same pip package, invoked via Copilot agent mode
- **OpenAI Codex:** Same pip package, invoked as tool
- **Any agent:** Direct HTTP calls to the API endpoints

All agents produce identical session and comment records, enabling cross-agent performance comparison.

## 7. Data Model

### 7.1 Core Tables

```sql
-- GDS source tracking
gds_scripts (id, path, name, description, params_json, last_modified, git_commit)
gds_builds (id, script_id FK, gds_path, status, build_log, git_commit, created_at)
gds_cells (id, build_id FK, name, cell_type, bbox, layer_count, element_count)
gds_elements (id, cell_id FK, element_type, layer, bbox, path_data, properties, source_line)

-- Collaboration
issues (id, title, body, status, author_type, author_id, priority, tags, created_at, updated_at, resolved_by, resolved_at, script_path)
issue_elements (id, issue_id FK, gds_build_id FK, cell_name, element_id, layer, bbox, source_script_line, deep_link_url)
wiki_pages (id, title, slug, body, category, tags, version, last_editor_type, last_editor_id, created_at, updated_at)
comments (id, target_type, target_id, author_type, author_id, body, agent_model, agent_skill_version, created_at, edited_at)

-- Agent tracking
agent_sessions (id, agent_type, model, skill_version, started_at, ended_at, issues_processed, builds_triggered, status)
users (id, username, display_name)  -- single shared account for research group
```

### 7.2 SQLite Strategy

Single SQLite file per namespace (staging gets its own DB, production gets its own). Backup is a file copy. WAL mode enabled for concurrent read/write from the single FastAPI process.

## 8. Authentication

- **Users:** Single shared account with a simple password. Configured via environment variable. No user management UI — just one login for the research group.
- **Agents:** Localhost-only. Backend rejects any request to `/api/agent/*` from non-localhost origins. No token or auth header needed.
- **WebSocket:** Same shared session cookie as the web UI.

## 9. Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Backend | Python 3.12 + FastAPI | Aligns with GDSfactory ecosystem |
| ORM | SQLAlchemy 2.0 | Async-capable, well-supported |
| Database | SQLite (WAL mode) | Zero-ops, file-based backup, sufficient for group scale |
| Frontend | React 19 + TypeScript | Rich ecosystem, type-safe |
| GDS Viewer | WebGL via OpenLayers | Map-like pan/zoom with tile pyramid, proven for CAD/GIS use cases |
| GDS Parsing | klayout Python module | Battle-tested GDS reader |
| Container Orchestration | k3s (single node) | Lightweight Kubernetes, production-grade |
| Ingress | Traefik (k3s built-in) | Auto TLS, simple config |
| CI/CD | GitHub Actions | Standard, free for public repos |
| Workflow Engine | Argo Workflows | GDS build pipelines, agent orchestration |
| Container Registry | Local registry on k3s node | No external dependency |
| Agent Skill | Python pip package | Cross-agent compatible |

## 10. Project Structure

```
gds-collab/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── db.py
│   │   ├── models.py
│   │   ├── gds/
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   ├── viewer.py
│   │   │   ├── watcher.py
│   │   │   └── addressing.py
│   │   ├── issues/
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   └── schemas.py
│   │   ├── wiki/
│   │   │   ├── __init__.py
│   │   │   ├── router.py
│   │   │   └── schemas.py
│   │   └── agent/
│   │       ├── __init__.py
│   │       ├── router.py
│   │       └── tracker.py
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── panels/
│   │   │   ├── GdsViewer/
│   │   │   ├── IssuePanel/
│   │   │   └── WikiPanel/
│   │   ├── components/
│   │   │   ├── LayerSelector/
│   │   │   ├── DeepLink/
│   │   │   ├── CommentThread/
│   │   │   └── GdsEmbed/
│   │   └── hooks/
│   │       └── useDeepLink.ts
│   ├── tests/
│   ├── Dockerfile
│   └── package.json
├── agent-skill/
│   ├── gds_collab_skill/
│   │   ├── __init__.py
│   │   ├── cli.py
│   │   ├── client.py
│   │   ├── context.py
│   │   └── post.py
│   ├── skill.md
│   └── pyproject.toml
├── helm/
│   └── gds-collab/
│       ├── Chart.yaml
│       ├── values.yaml
│       ├── values-staging.yaml
│       ├── values-production.yaml
│       └── templates/
├── .github/
│   └── workflows/
│       ├── pr.yml
│       ├── staging.yml
│       └── release.yml
├── argo-workflows/
│   ├── gds-build.yaml
│   └── agent-task.yaml
├── docker-compose.dev.yml      # Local development (no k3s needed)
├── Makefile
└── README.md
```

## 11. Development Workflow

For local development, a `docker-compose.dev.yml` provides the same backend + frontend setup without k3s. Developers can run the backend with `uvicorn` hot-reload and the frontend with `vite dev`.

**Quick start (local dev):**
```bash
make dev  # starts backend:8000 + frontend:3000 + watches /data/scripts
```

**Quick start (k3s deploy):**
```bash
make deploy-staging   # helm install to k3s staging namespace
make deploy-prod      # helm upgrade production (after approval)
```

**Agent install:**
```bash
pip install gds-collab-skill
# Then in Claude Code: /replyit
```
