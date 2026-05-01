# GDS Collab Platform

A web-based collaboration platform for photonic chip design teams. Python scripts using GDSfactory generate GDS layout files. The platform displays layouts, lets users file issues against specific design elements, and enables AI agents to resolve issues by modifying scripts and rebuilding.

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 22+
- Docker (for containerized dev)

### Local Development

```bash
# Install dependencies
make install

# Run backend (terminal 1)
make dev-backend

# Run frontend (terminal 2)
make dev-frontend
```

Open http://localhost:3000.

### Without `make` (Windows / no Makefile)

```bash
# Install dependencies
cd backend && pip install -r requirements.txt
cd ../frontend && npm install
cd ../agent-skill && pip install -e .

# Run backend (terminal 1)
cd backend && uvicorn app.main:app --reload --port 8000

# Run frontend (terminal 2)
cd frontend && npm run dev

# Run tests
cd backend && python -m pytest -v
```

### Docker Compose

```bash
make dev
```

### Agent Skill

```bash
cd agent-skill
pip install -e .
gds-collab-skill --help
```

## Architecture

- **Backend:** FastAPI + SQLAlchemy + SQLite
- **Frontend:** React 19 + TypeScript + OpenLayers
- **GDS Parsing:** klayout
- **Deployment:** k3s + Helm + Argo Workflows
- **CI/CD:** GitHub Actions

## Project Structure

```
├── backend/            # FastAPI backend
│   ├── app/
│   │   ├── gds/        # GDS parsing, viewer, addressing
│   │   ├── issues/     # Issue CRUD, element linking
│   │   ├── wiki/       # Wiki pages, comments
│   │   └── agent/      # Agent session management
│   └── tests/
├── frontend/           # React SPA
│   └── src/
│       ├── panels/     # GDS Viewer, Issue Panel, Wiki Panel
│       ├── components/ # LayerSelector, DeepLink, CommentThread, GdsEmbed
│       └── hooks/      # useDeepLink
├── agent-skill/        # Pip-installable agent skill
├── helm/               # Kubernetes Helm charts
├── argo-workflows/     # Argo Workflow definitions
└── .github/workflows/  # CI/CD pipelines
```

## API Endpoints

### GDS
- `GET /api/gds/scripts` - List scripts
- `POST /api/gds/scripts` - Register script
- `GET /api/gds/scripts/{id}` - Get script
- `GET /api/gds/scripts/{id}/builds` - List builds for script
- `POST /api/gds/builds` - Create build
- `GET /api/gds/builds/{id}` - Get build with cells

### Issues
- `GET /api/issues` - List issues (filter by status)
- `POST /api/issues` - Create issue
- `GET /api/issues/{id}` - Get issue detail
- `PATCH /api/issues/{id}` - Update issue

### Comments
- `POST /api/comments` - Add comment
- `GET /api/comments/issue/{id}` - List issue comments
- `GET /api/comments/wiki/{id}` - List wiki comments

### Wiki
- `GET /api/wiki` - List pages (filter by category)
- `POST /api/wiki` - Create page
- `GET /api/wiki/{slug}` - Get page
- `PATCH /api/wiki/{slug}` - Update page

### Agent
- `GET /api/agent/poll` - Get open issues
- `POST /api/agent/session` - Register session
- `POST /api/agent/claim/{id}` - Claim issue
- `POST /api/agent/build` - Trigger build
- `POST /api/agent/comment` - Post comment
- `POST /api/agent/resolve/{id}` - Resolve issue

## License

MIT
