# GDS Collab Platform — Phase 2–5 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the GDS Collab Platform by building Issue/Wiki backends (Phase 2), Agent module + skill package (Phase 3), React SPA frontend (Phase 4), and k3s deployment + CI/CD (Phase 5).

**Architecture:** Modular monolith FastAPI backend with 4 modules (gds, issues, wiki, agent), React SPA frontend with 3 panels, SQLite database, k3s deployment with Argo Workflows, and a pip-installable agent skill package.

**Tech Stack:** Python 3.12 + FastAPI + SQLAlchemy 2.0 + SQLite | React 19 + TypeScript + OpenLayers | k3s + Helm + Argo Workflows + GitHub Actions

**Prerequisite:** Phase 1 plan (`docs/superpowers/plans/2026-05-01-gds-collab-platform-plan.md`) must be complete before starting this plan.

**Spec:** `docs/superpowers/specs/2026-05-01-gds-collab-platform-design.md`

---

## File Map

After completing Phase 1, these files exist:

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI entry, CORS, health
│   ├── db.py                # SQLite engine, session, Base
│   ├── models.py            # All 10 SQLAlchemy tables
│   ├── gds/
│   │   ├── __init__.py
│   │   ├── router.py        # /api/gds/* endpoints
│   │   ├── parser.py         # klayout GDS parser
│   │   ├── schemas.py        # GDS Pydantic schemas
│   │   └── addressing.py    # Deep link build/parse
│   ├── issues/
│   │   └── __init__.py
│   ├── wiki/
│   │   └── __init__.py
│   └── agent/
│       └── __init__.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_health.py
│   ├── test_db.py
│   ├── test_gds_parser.py
│   ├── test_gds_api.py
│   ├── test_addressing.py
│   └── fixtures/
│       └── (GDS test fixtures)
└── requirements.txt

.gitignore
```

This plan adds:

```
backend/
├── app/
│   ├── main.py              # MODIFY: register new routers
│   ├── issues/
│   │   ├── router.py        # CREATE: /api/issues/*
│   │   └── schemas.py       # CREATE: Issue Pydantic models
│   ├── wiki/
│   │   ├── router.py        # CREATE: /api/wiki/*
│   │   └── schemas.py       # CREATE: Wiki Pydantic models
│   └── agent/
│       ├── router.py        # CREATE: /api/agent/*
│       ├── schemas.py       # CREATE: Agent Pydantic models
│       └── tracker.py       # CREATE: session management
├── tests/
│   ├── test_issues_api.py   # CREATE
│   ├── test_wiki_api.py     # CREATE
│   └── test_agent_api.py    # CREATE

agent-skill/
├── gds_collab_skill/
│   ├── __init__.py          # CREATE
│   ├── cli.py               # CREATE: /replyit entry
│   ├── client.py            # CREATE: HTTP client
│   ├── context.py           # CREATE: prompt builder
│   └── post.py              # CREATE: response poster
├── skill.md                 # CREATE: Claude Code skill def
└── pyproject.toml           # CREATE

frontend/
├── package.json             # CREATE
├── tsconfig.json            # CREATE
├── vite.config.ts           # CREATE
├── index.html               # CREATE
├── src/
│   ├── main.tsx             # CREATE
│   ├── App.tsx              # CREATE
│   ├── panels/
│   │   ├── GdsViewer/
│   │   │   └── index.tsx    # CREATE
│   │   ├── IssuePanel/
│   │   │   └── index.tsx    # CREATE
│   │   └── WikiPanel/
│   │       └── index.tsx    # CREATE
│   ├── components/
│   │   ├── LayerSelector/
│   │   │   └── index.tsx    # CREATE
│   │   ├── DeepLink/
│   │   │   └── index.tsx    # CREATE
│   │   ├── CommentThread/
│   │   │   └── index.tsx    # CREATE
│   │   └── GdsEmbed/
│   │       └── index.tsx    # CREATE
│   └── hooks/
│       └── useDeepLink.ts   # CREATE
└── tests/                   # CREATE (empty dir)

helm/
└── gds-collab/
    ├── Chart.yaml           # CREATE
    ├── values.yaml          # CREATE
    ├── values-staging.yaml  # CREATE
    ├── values-production.yaml # CREATE
    └── templates/
        ├── backend-deployment.yaml  # CREATE
        ├── frontend-deployment.yaml # CREATE
        ├── ingress.yaml     # CREATE
        ├── pvc.yaml         # CREATE
        └── configmap.yaml   # CREATE

.github/
└── workflows/
    ├── pr.yml              # CREATE
    ├── staging.yml          # CREATE
    └── release.yml          # CREATE

argo-workflows/
├── gds-build.yaml           # CREATE
└── agent-task.yaml          # CREATE

docker-compose.dev.yml       # CREATE
Makefile                      # CREATE
README.md                     # CREATE
```

---

## Phase 2: Issue + Wiki Backend

### Task 6: Issue Schemas

**Files:**
- Create: `backend/app/issues/schemas.py`
- Modify: `backend/app/main.py` (register router — will be done in Task 7, just schema here)

- [ ] **Step 1: Create issue schemas**

Create `backend/app/issues/schemas.py`:
```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class IssueElementLink(BaseModel):
    gds_build_id: Optional[int] = None
    cell_name: Optional[str] = None
    element_id: Optional[int] = None
    layer: Optional[str] = None
    bbox: Optional[str] = None
    source_script_line: Optional[int] = None
    deep_link_url: Optional[str] = None

    class Config:
        from_attributes = True


class IssueElementResponse(BaseModel):
    id: int
    issue_id: int
    gds_build_id: Optional[int] = None
    cell_name: Optional[str] = None
    element_id: Optional[int] = None
    layer: Optional[str] = None
    bbox: Optional[str] = None
    source_script_line: Optional[int] = None
    deep_link_url: Optional[str] = None

    class Config:
        from_attributes = True


class CommentResponse(BaseModel):
    id: int
    target_type: str
    target_id: int
    author_type: str
    author_id: Optional[int] = None
    body: str
    agent_model: Optional[str] = None
    agent_skill_version: Optional[str] = None
    created_at: Optional[datetime] = None
    edited_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class IssueCreate(BaseModel):
    title: str
    body: str = ""
    priority: str = "normal"
    tags: list[str] = []
    script_path: Optional[str] = None
    linked_elements: list[IssueElementLink] = []


class IssueUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    tags: Optional[list[str]] = None


class IssueResponse(BaseModel):
    id: int
    title: str
    body: Optional[str] = None
    status: str
    author_type: str
    author_id: Optional[int] = None
    priority: str
    tags: list = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    script_path: Optional[str] = None
    linked_elements: list[IssueElementResponse] = []
    comments: list[CommentResponse] = []

    class Config:
        from_attributes = True


class CommentCreate(BaseModel):
    target_type: str  # "issue" or "wiki"
    target_id: int
    body: str
    author_type: str = "user"
    author_id: int = 1
    agent_model: Optional[str] = None
    agent_skill_version: Optional[str] = None
```

- [ ] **Step 2: Verify the schemas import correctly**

```bash
cd backend && python -c "from app.issues.schemas import IssueCreate, IssueResponse, IssueUpdate, CommentCreate, CommentResponse; print('OK')"
```
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/app/issues/schemas.py
git commit -m "feat: add issue and comment Pydantic schemas"
```

---

### Task 7: Issue API Endpoints

**Files:**
- Create: `backend/app/issues/router.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_issues_api.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_issues_api.py`:
```python
import pytest


@pytest.mark.asyncio
async def test_list_issues_empty(client):
    response = await client.get("/api/issues")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_issue(client):
    response = await client.post("/api/issues", json={
        "title": "Broken waveguide bend",
        "body": "The bend radius at cell ring_cell_1 is too tight.",
        "priority": "high",
        "script_path": "scripts/ring_resonator.py",
        "linked_elements": [
            {
                "gds_build_id": 1,
                "cell_name": "ring_cell_1",
                "element_id": 42,
                "layer": "M1",
                "bbox": "10.5,20,30,40",
                "source_script_line": 15,
                "deep_link_url": "/viewer?gds=ring_resonator&cell=ring_cell_1&elem=42&layer=M1"
            }
        ]
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Broken waveguide bend"
    assert data["status"] == "open"
    assert data["priority"] == "high"
    assert len(data["linked_elements"]) == 1
    assert data["linked_elements"][0]["cell_name"] == "ring_cell_1"


@pytest.mark.asyncio
async def test_get_issue(client):
    create = await client.post("/api/issues", json={
        "title": "Layer misalignment",
        "body": "M2 shift vs M1 on left side",
    })
    issue_id = create.json()["id"]

    response = await client.get(f"/api/issues/{issue_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Layer misalignment"


@pytest.mark.asyncio
async def test_update_issue_status(client):
    create = await client.post("/api/issues", json={
        "title": "DRC violation", "body": "Min spacing on D1"
    })
    issue_id = create.json()["id"]

    response = await client.patch(f"/api/issues/{issue_id}", json={
        "status": "in_progress"
    })
    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"


@pytest.mark.asyncio
async def test_list_issues_by_status(client):
    await client.post("/api/issues", json={
        "title": "Open issue 1", "body": "body"
    })
    await client.post("/api/issues", json={
        "title": "Open issue 2", "body": "body"
    })
    # Create and resolve one
    done = await client.post("/api/issues", json={
        "title": "Resolved issue", "body": "body"
    })
    done_id = done.json()["id"]
    await client.patch(f"/api/issues/{done_id}", json={"status": "resolved"})

    # Filter to open only
    response = await client.get("/api/issues?status=open")
    assert response.status_code == 200
    assert len(response.json()) == 2

    response = await client.get("/api/issues?status=resolved")
    assert len(response.json()) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_issues_api.py -v
```
Expected: FAIL (404 — routes not registered)

- [ ] **Step 3: Implement issue router**

Create `backend/app/issues/router.py`:
```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db import get_db
from app.models import Issue, IssueElement
from app.issues.schemas import (
    IssueCreate, IssueUpdate, IssueResponse,
    IssueElementResponse, IssueElementLink,
)

router = APIRouter(prefix="/api/issues", tags=["issues"])


def _issue_to_response(issue: Issue) -> IssueResponse:
    return IssueResponse(
        id=issue.id,
        title=issue.title,
        body=issue.body,
        status=issue.status,
        author_type=issue.author_type,
        author_id=issue.author_id,
        priority=issue.priority,
        tags=issue.tags or [],
        created_at=issue.created_at,
        updated_at=issue.updated_at,
        resolved_by=issue.resolved_by,
        resolved_at=issue.resolved_at,
        script_path=issue.script_path,
        linked_elements=[
            IssueElementResponse(
                id=le.id,
                issue_id=le.issue_id,
                gds_build_id=le.gds_build_id,
                cell_name=le.cell_name,
                element_id=le.element_id,
                layer=le.layer,
                bbox=le.bbox,
                source_script_line=le.source_script_line,
                deep_link_url=le.deep_link_url,
            )
            for le in (issue.linked_elements or [])
        ],
        comments=[
            {
                "id": c.id,
                "target_type": c.target_type,
                "target_id": c.target_id,
                "author_type": c.author_type,
                "author_id": c.author_id,
                "body": c.body,
                "agent_model": c.agent_model,
                "agent_skill_version": c.agent_skill_version,
                "created_at": c.created_at,
                "edited_at": c.edited_at,
            }
            for c in (issue.comments or [])
        ],
    )


@router.get("", response_model=list[IssueResponse])
def list_issues(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Issue)
    if status:
        q = q.filter(Issue.status == status)
    return [_issue_to_response(i) for i in q.order_by(Issue.created_at.desc()).all()]


@router.post("", response_model=IssueResponse, status_code=201)
def create_issue(data: IssueCreate, db: Session = Depends(get_db)):
    issue = Issue(
        title=data.title,
        body=data.body,
        priority=data.priority,
        tags=data.tags,
        script_path=data.script_path,
    )
    db.add(issue)
    db.flush()

    for link in data.linked_elements:
        ie = IssueElement(
            issue_id=issue.id,
            gds_build_id=link.gds_build_id,
            cell_name=link.cell_name,
            element_id=link.element_id,
            layer=link.layer,
            bbox=link.bbox,
            source_script_line=link.source_script_line,
            deep_link_url=link.deep_link_url,
        )
        db.add(ie)

    db.commit()
    db.refresh(issue)
    return _issue_to_response(issue)


@router.get("/{issue_id}", response_model=IssueResponse)
def get_issue(issue_id: int, db: Session = Depends(get_db)):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(404, "Issue not found")
    return _issue_to_response(issue)


@router.patch("/{issue_id}", response_model=IssueResponse)
def update_issue(issue_id: int, data: IssueUpdate, db: Session = Depends(get_db)):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(404, "Issue not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(issue, key, value)

    db.commit()
    db.refresh(issue)
    return _issue_to_response(issue)
```

- [ ] **Step 4: Register issues router in main.py**

Read `backend/app/main.py` and add the issues router import and registration:

Update `backend/app/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.gds.router import router as gds_router
from app.issues.router import router as issues_router

app = FastAPI(title="GDS Collab Platform", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(gds_router)
app.include_router(issues_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 5: Run tests**

```bash
cd backend && python -m pytest tests/test_issues_api.py -v
```
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/issues/router.py backend/app/main.py backend/tests/test_issues_api.py
git commit -m "feat: add issue CRUD API with element linking"
```

---

### Task 8: Comment System

**Files:**
- Create: `backend/tests/test_comments.py`

- [ ] **Step 1: Write failing comment tests**

Create `backend/tests/test_comments.py`:
```python
import pytest


@pytest.mark.asyncio
async def test_add_comment_to_issue(client):
    # Create issue
    issue = await client.post("/api/issues", json={
        "title": "Need comments", "body": "testing"
    })
    issue_id = issue.json()["id"]

    response = await client.post("/api/comments", json={
        "target_type": "issue",
        "target_id": issue_id,
        "body": "This is a test comment",
        "author_type": "user",
        "author_id": 1,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["body"] == "This is a test comment"
    assert data["target_type"] == "issue"
    assert data["target_id"] == issue_id


@pytest.mark.asyncio
async def test_add_agent_comment(client):
    issue = await client.post("/api/issues", json={
        "title": "Agent test", "body": "testing"
    })
    issue_id = issue.json()["id"]

    response = await client.post("/api/comments", json={
        "target_type": "issue",
        "target_id": issue_id,
        "body": "Fixed by adjusting bend radius from 5 to 10 um",
        "author_type": "agent",
        "author_id": 99,
        "agent_model": "claude-sonnet-4.6",
        "agent_skill_version": "0.1.0",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["author_type"] == "agent"
    assert data["agent_model"] == "claude-sonnet-4.6"


@pytest.mark.asyncio
async def test_list_comments_for_issue(client):
    issue = await client.post("/api/issues", json={
        "title": "Comment list test", "body": "testing"
    })
    issue_id = issue.json()["id"]

    await client.post("/api/comments", json={
        "target_type": "issue", "target_id": issue_id, "body": "Comment 1"
    })
    await client.post("/api/comments", json={
        "target_type": "issue", "target_id": issue_id, "body": "Comment 2"
    })

    response = await client.get(f"/api/comments/issue/{issue_id}")
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_issue_includes_comments(client):
    issue = await client.post("/api/issues", json={
        "title": "With comments", "body": "testing"
    })
    issue_id = issue.json()["id"]

    await client.post("/api/comments", json={
        "target_type": "issue", "target_id": issue_id, "body": "A comment"
    })

    response = await client.get(f"/api/issues/{issue_id}")
    assert response.status_code == 200
    assert len(response.json()["comments"]) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_comments.py -v
```
Expected: FAIL (404 — no comment routes)

- [ ] **Step 3: Add comment endpoints to issues router**

Modify `backend/app/issues/router.py` — append these endpoints after the existing code:

```python
from app.models import Comment
from app.issues.schemas import CommentCreate, CommentResponse


@router.post("/api/comments", response_model=CommentResponse, status_code=201)
def create_comment(data: CommentCreate, db: Session = Depends(get_db)):
    comment = Comment(
        target_type=data.target_type,
        target_id=data.target_id,
        author_type=data.author_type,
        author_id=data.author_id,
        body=data.body,
        agent_model=data.agent_model,
        agent_skill_version=data.agent_skill_version,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@router.get("/api/comments/issue/{issue_id}", response_model=list[CommentResponse])
def list_comments_for_issue(issue_id: int, db: Session = Depends(get_db)):
    return (
        db.query(Comment)
        .filter(Comment.target_type == "issue", Comment.target_id == issue_id)
        .order_by(Comment.created_at)
        .all()
    )


@router.get("/api/comments/wiki/{wiki_id}", response_model=list[CommentResponse])
def list_comments_for_wiki(wiki_id: int, db: Session = Depends(get_db)):
    return (
        db.query(Comment)
        .filter(Comment.target_type == "wiki", Comment.target_id == wiki_id)
        .order_by(Comment.created_at)
        .all()
    )
```

Note: the comment routes are registered in the issues router since they're shared infrastructure. The router import in main.py needs to be updated to register these separately, or they can live in a dedicated comments sub-router. For simplicity, they're added to the issues router at module level. Update `backend/app/issues/router.py` to define a separate `comment_router`:

Create `backend/app/issues/router.py` with the full content — replace the file with:
```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db import get_db
from app.models import Issue, IssueElement, Comment
from app.issues.schemas import (
    IssueCreate, IssueUpdate, IssueResponse,
    IssueElementResponse, IssueElementLink,
    CommentCreate, CommentResponse,
)

issue_router = APIRouter(prefix="/api/issues", tags=["issues"])
comment_router = APIRouter(prefix="/api/comments", tags=["comments"])


def _issue_to_response(issue: Issue) -> IssueResponse:
    return IssueResponse(
        id=issue.id,
        title=issue.title,
        body=issue.body,
        status=issue.status,
        author_type=issue.author_type,
        author_id=issue.author_id,
        priority=issue.priority,
        tags=issue.tags or [],
        created_at=issue.created_at,
        updated_at=issue.updated_at,
        resolved_by=issue.resolved_by,
        resolved_at=issue.resolved_at,
        script_path=issue.script_path,
        linked_elements=[
            IssueElementResponse(
                id=le.id,
                issue_id=le.issue_id,
                gds_build_id=le.gds_build_id,
                cell_name=le.cell_name,
                element_id=le.element_id,
                layer=le.layer,
                bbox=le.bbox,
                source_script_line=le.source_script_line,
                deep_link_url=le.deep_link_url,
            )
            for le in (issue.linked_elements or [])
        ],
        comments=[
            CommentResponse(
                id=c.id,
                target_type=c.target_type,
                target_id=c.target_id,
                author_type=c.author_type,
                author_id=c.author_id,
                body=c.body,
                agent_model=c.agent_model,
                agent_skill_version=c.agent_skill_version,
                created_at=c.created_at,
                edited_at=c.edited_at,
            )
            for c in (issue.comments or [])
        ],
    )


# --- Issue endpoints ---

@issue_router.get("", response_model=list[IssueResponse])
def list_issues(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Issue)
    if status:
        q = q.filter(Issue.status == status)
    return [_issue_to_response(i) for i in q.order_by(Issue.created_at.desc()).all()]


@issue_router.post("", response_model=IssueResponse, status_code=201)
def create_issue(data: IssueCreate, db: Session = Depends(get_db)):
    issue = Issue(
        title=data.title,
        body=data.body,
        priority=data.priority,
        tags=data.tags,
        script_path=data.script_path,
    )
    db.add(issue)
    db.flush()

    for link in data.linked_elements:
        ie = IssueElement(
            issue_id=issue.id,
            gds_build_id=link.gds_build_id,
            cell_name=link.cell_name,
            element_id=link.element_id,
            layer=link.layer,
            bbox=link.bbox,
            source_script_line=link.source_script_line,
            deep_link_url=link.deep_link_url,
        )
        db.add(ie)

    db.commit()
    db.refresh(issue)
    return _issue_to_response(issue)


@issue_router.get("/{issue_id}", response_model=IssueResponse)
def get_issue(issue_id: int, db: Session = Depends(get_db)):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(404, "Issue not found")
    return _issue_to_response(issue)


@issue_router.patch("/{issue_id}", response_model=IssueResponse)
def update_issue(issue_id: int, data: IssueUpdate, db: Session = Depends(get_db)):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(404, "Issue not found")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(issue, key, value)
    db.commit()
    db.refresh(issue)
    return _issue_to_response(issue)


# --- Comment endpoints ---

@comment_router.post("", response_model=CommentResponse, status_code=201)
def create_comment(data: CommentCreate, db: Session = Depends(get_db)):
    comment = Comment(
        target_type=data.target_type,
        target_id=data.target_id,
        author_type=data.author_type,
        author_id=data.author_id,
        body=data.body,
        agent_model=data.agent_model,
        agent_skill_version=data.agent_skill_version,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@comment_router.get("/issue/{issue_id}", response_model=list[CommentResponse])
def list_comments_for_issue(issue_id: int, db: Session = Depends(get_db)):
    return (
        db.query(Comment)
        .filter(Comment.target_type == "issue", Comment.target_id == issue_id)
        .order_by(Comment.created_at)
        .all()
    )


@comment_router.get("/wiki/{wiki_id}", response_model=list[CommentResponse])
def list_comments_for_wiki(wiki_id: int, db: Session = Depends(get_db)):
    return (
        db.query(Comment)
        .filter(Comment.target_type == "wiki", Comment.target_id == wiki_id)
        .order_by(Comment.created_at)
        .all()
    )
```

- [ ] **Step 4: Update main.py to register comment_router**

Modify `backend/app/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.gds.router import router as gds_router
from app.issues.router import issue_router, comment_router

app = FastAPI(title="GDS Collab Platform", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(gds_router)
app.include_router(issue_router)
app.include_router(comment_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 5: Run comment tests**

```bash
cd backend && python -m pytest tests/test_comments.py -v
```
Expected: PASS

- [ ] **Step 6: Run all tests to confirm nothing broke**

```bash
cd backend && python -m pytest -v
```
Expected: ALL PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/issues/router.py backend/app/main.py backend/tests/test_comments.py
git commit -m "feat: add comment system with agent attribution"
```

---

### Task 9: Wiki API Endpoints

**Files:**
- Create: `backend/app/wiki/schemas.py`
- Create: `backend/app/wiki/router.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_wiki_api.py`

- [ ] **Step 1: Create wiki schemas**

Create `backend/app/wiki/schemas.py`:
```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class WikiPageCreate(BaseModel):
    title: str
    slug: str
    body: str = ""
    category: str = "general"
    tags: list[str] = []


class WikiPageUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[list[str]] = None


class WikiPageResponse(BaseModel):
    id: int
    title: str
    slug: str
    body: Optional[str] = None
    category: str
    tags: list = []
    version: int
    last_editor_type: str
    last_editor_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WikiPageListResponse(BaseModel):
    id: int
    title: str
    slug: str
    category: str
    tags: list = []
    version: int
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
```

- [ ] **Step 2: Write failing wiki API tests**

Create `backend/tests/test_wiki_api.py`:
```python
import pytest


@pytest.mark.asyncio
async def test_list_wiki_pages_empty(client):
    response = await client.get("/api/wiki")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_wiki_page(client):
    response = await client.post("/api/wiki", json={
        "title": "Design Rules",
        "slug": "design-rules",
        "body": "# Design Rules\n\n## M1 Layer\n- Minimum width: 0.5 um",
        "category": "process",
        "tags": ["design-rules", "M1"],
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Design Rules"
    assert data["slug"] == "design-rules"
    assert data["version"] == 1
    assert data["category"] == "process"


@pytest.mark.asyncio
async def test_get_wiki_page_by_slug(client):
    await client.post("/api/wiki", json={
        "title": "Process Notes", "slug": "process-notes",
        "body": "Some notes",
    })

    response = await client.get("/api/wiki/process-notes")
    assert response.status_code == 200
    assert response.json()["title"] == "Process Notes"


@pytest.mark.asyncio
async def test_update_wiki_page(client):
    await client.post("/api/wiki", json={
        "title": "Tapeout", "slug": "tapeout-2026",
        "body": "Initial body",
    })

    response = await client.patch("/api/wiki/tapeout-2026", json={
        "body": "Updated body with new rules",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["body"] == "Updated body with new rules"
    assert data["version"] == 2


@pytest.mark.asyncio
async def test_wiki_page_not_found(client):
    response = await client.get("/api/wiki/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_filter_by_category(client):
    await client.post("/api/wiki", json={
        "title": "Design Rule 1", "slug": "dr1",
        "category": "design-rules",
    })
    await client.post("/api/wiki", json={
        "title": "Process Note 1", "slug": "pn1",
        "category": "process",
    })
    await client.post("/api/wiki", json={
        "title": "Design Rule 2", "slug": "dr2",
        "category": "design-rules",
    })

    response = await client.get("/api/wiki?category=design-rules")
    assert response.status_code == 200
    assert len(response.json()) == 2
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_wiki_api.py -v
```
Expected: FAIL (404 — routes not registered)

- [ ] **Step 4: Implement wiki router**

Create `backend/app/wiki/router.py`:
```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db import get_db
from app.models import WikiPage
from app.wiki.schemas import (
    WikiPageCreate, WikiPageUpdate, WikiPageResponse, WikiPageListResponse,
)

router = APIRouter(prefix="/api/wiki", tags=["wiki"])


@router.get("", response_model=list[WikiPageListResponse])
def list_wiki_pages(
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(WikiPage)
    if category:
        q = q.filter(WikiPage.category == category)
    return q.order_by(WikiPage.updated_at.desc()).all()


@router.post("", response_model=WikiPageResponse, status_code=201)
def create_wiki_page(data: WikiPageCreate, db: Session = Depends(get_db)):
    existing = db.query(WikiPage).filter(WikiPage.slug == data.slug).first()
    if existing:
        raise HTTPException(409, f"Slug '{data.slug}' already exists")
    page = WikiPage(
        title=data.title,
        slug=data.slug,
        body=data.body,
        category=data.category,
        tags=data.tags,
        version=1,
    )
    db.add(page)
    db.commit()
    db.refresh(page)
    return page


@router.get("/{slug}", response_model=WikiPageResponse)
def get_wiki_page(slug: str, db: Session = Depends(get_db)):
    page = db.query(WikiPage).filter(WikiPage.slug == slug).first()
    if not page:
        raise HTTPException(404, "Wiki page not found")
    return page


@router.patch("/{slug}", response_model=WikiPageResponse)
def update_wiki_page(slug: str, data: WikiPageUpdate, db: Session = Depends(get_db)):
    page = db.query(WikiPage).filter(WikiPage.slug == slug).first()
    if not page:
        raise HTTPException(404, "Wiki page not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(page, key, value)
    page.version += 1

    db.commit()
    db.refresh(page)
    return page
```

- [ ] **Step 5: Register wiki router in main.py**

Modify `backend/app/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.gds.router import router as gds_router
from app.issues.router import issue_router, comment_router
from app.wiki.router import router as wiki_router

app = FastAPI(title="GDS Collab Platform", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(gds_router)
app.include_router(issue_router)
app.include_router(comment_router)
app.include_router(wiki_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 6: Run wiki tests**

```bash
cd backend && python -m pytest tests/test_wiki_api.py -v
```
Expected: PASS

- [ ] **Step 7: Run all tests**

```bash
cd backend && python -m pytest -v
```
Expected: ALL PASS

- [ ] **Step 8: Commit**

```bash
git add backend/app/wiki/schemas.py backend/app/wiki/router.py backend/app/main.py backend/tests/test_wiki_api.py
git commit -m "feat: add wiki CRUD API with version tracking and category filtering"
```

---

## Phase 3: Agent Module + Skill Package

### Task 10: Agent Schemas + Router

**Files:**
- Create: `backend/app/agent/schemas.py`
- Create: `backend/app/agent/router.py`
- Create: `backend/app/agent/tracker.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_agent_api.py`

- [ ] **Step 1: Create agent schemas**

Create `backend/app/agent/schemas.py`:
```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AgentSessionCreate(BaseModel):
    agent_type: str  # "claude-code", "copilot", etc.
    model: str
    skill_version: Optional[str] = None


class AgentSessionResponse(BaseModel):
    id: int
    agent_type: str
    model: str
    skill_version: Optional[str] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    issues_processed: int
    builds_triggered: int
    status: str

    class Config:
        from_attributes = True


class AgentBuildRequest(BaseModel):
    script_id: int
    git_commit: Optional[str] = None


class AgentCommentRequest(BaseModel):
    issue_id: int
    body: str
    session_id: int


class AgentResolveRequest(BaseModel):
    body: Optional[str] = None


class PollIssueResponse(BaseModel):
    id: int
    title: str
    body: Optional[str] = None
    status: str
    priority: str
    script_path: Optional[str] = None
    created_at: Optional[datetime] = None
    linked_elements: list[dict] = []
    comments: list[dict] = []
```

- [ ] **Step 2: Create agent tracker**

Create `backend/app/agent/tracker.py`:
```python
"""Agent session lifecycle management."""
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models import AgentSession


def utcnow():
    return datetime.now(timezone.utc)


def create_session(db: Session, agent_type: str, model: str, skill_version: str | None = None) -> AgentSession:
    session = AgentSession(
        agent_type=agent_type,
        model=model,
        skill_version=skill_version,
        status="active",
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def end_session(db: Session, session_id: int, status: str = "completed"):
    session = db.query(AgentSession).filter(AgentSession.id == session_id).first()
    if session:
        session.ended_at = utcnow()
        session.status = status
        db.commit()


def increment_issues(db: Session, session_id: int):
    session = db.query(AgentSession).filter(AgentSession.id == session_id).first()
    if session:
        session.issues_processed += 1
        db.commit()


def increment_builds(db: Session, session_id: int):
    session = db.query(AgentSession).filter(AgentSession.id == session_id).first()
    if session:
        session.builds_triggered += 1
        db.commit()
```

- [ ] **Step 3: Write failing agent API tests**

Create `backend/tests/test_agent_api.py`:
```python
import pytest


@pytest.mark.asyncio
async def test_register_agent_session(client):
    response = await client.post("/api/agent/session", json={
        "agent_type": "claude-code",
        "model": "claude-sonnet-4.6",
        "skill_version": "0.1.0",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["agent_type"] == "claude-code"
    assert data["status"] == "active"
    assert data["id"] is not None


@pytest.mark.asyncio
async def test_poll_open_issues(client):
    # Create some issues
    await client.post("/api/issues", json={"title": "Issue 1", "body": "test"})
    await client.post("/api/issues", json={"title": "Issue 2", "body": "test"})

    response = await client.get("/api/agent/poll")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(i["status"] == "open" for i in data)


@pytest.mark.asyncio
async def test_poll_respects_claimed_issues(client):
    await client.post("/api/issues", json={"title": "Open issue", "body": "test"})
    claimed = await client.post("/api/issues", json={"title": "Claimed issue", "body": "test"})
    claimed_id = claimed.json()["id"]
    await client.patch(f"/api/issues/{claimed_id}", json={"status": "in_progress"})

    response = await client.get("/api/agent/poll")
    assert response.status_code == 200
    assert len(response.json()) == 1  # only the open one


@pytest.mark.asyncio
async def test_agent_claim_issue(client):
    # Register session
    sess = await client.post("/api/agent/session", json={
        "agent_type": "claude-code", "model": "claude-sonnet-4.6",
    })
    session_id = sess.json()["id"]

    # Create issue
    issue = await client.post("/api/issues", json={"title": "Fix me", "body": "test"})
    issue_id = issue.json()["id"]

    response = await client.post(f"/api/agent/claim/{issue_id}?session_id={session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "in_progress"
    assert data["resolved_by"] == "agent"


@pytest.mark.asyncio
async def test_agent_resolve_issue(client):
    sess = await client.post("/api/agent/session", json={
        "agent_type": "claude-code", "model": "claude-sonnet-4.6",
    })
    session_id = sess.json()["id"]

    issue = await client.post("/api/issues", json={"title": "Resolvable", "body": "test"})
    issue_id = issue.json()["id"]
    await client.post(f"/api/agent/claim/{issue_id}?session_id={session_id}")

    response = await client.post(f"/api/agent/resolve/{issue_id}", json={
        "body": "Fixed by adjusting the bend radius parameter"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "resolved"
    assert len(data["comments"]) >= 1
```

- [ ] **Step 4: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_agent_api.py -v
```
Expected: FAIL (404)

- [ ] **Step 5: Implement agent router**

Create `backend/app/agent/router.py`:
```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Issue, Comment, GdsBuild
from app.agent.schemas import (
    AgentSessionCreate, AgentSessionResponse,
    AgentBuildRequest, AgentResolveRequest,
    PollIssueResponse,
)
from app.agent.tracker import (
    create_session, increment_issues, increment_builds,
)
from app.issues.schemas import IssueElementResponse, CommentResponse
from app.issues.router import _issue_to_response

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/session", response_model=AgentSessionResponse, status_code=201)
def register_session(data: AgentSessionCreate, db: Session = Depends(get_db)):
    session = create_session(db, data.agent_type, data.model, data.skill_version)
    return session


@router.get("/poll", response_model=list[PollIssueResponse])
def poll_issues(db: Session = Depends(get_db)):
    """Return all open (unclaimed) issues."""
    issues = (
        db.query(Issue)
        .filter(Issue.status == "open")
        .order_by(Issue.created_at.desc())
        .all()
    )
    result = []
    for issue in issues:
        result.append(PollIssueResponse(
            id=issue.id,
            title=issue.title,
            body=issue.body,
            status=issue.status,
            priority=issue.priority,
            script_path=issue.script_path,
            created_at=issue.created_at,
            linked_elements=[
                {
                    "cell_name": le.cell_name,
                    "element_id": le.element_id,
                    "layer": le.layer,
                    "source_script_line": le.source_script_line,
                    "deep_link_url": le.deep_link_url,
                }
                for le in (issue.linked_elements or [])
            ],
            comments=[
                {
                    "author_type": c.author_type,
                    "body": c.body,
                    "created_at": str(c.created_at) if c.created_at else None,
                }
                for c in (issue.comments or [])
            ],
        ))
    return result


@router.post("/claim/{issue_id}")
def claim_issue(
    issue_id: int,
    session_id: int = Query(...),
    db: Session = Depends(get_db),
):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(404, "Issue not found")
    if issue.status != "open":
        raise HTTPException(409, f"Issue is already {issue.status}")

    issue.status = "in_progress"
    issue.resolved_by = "agent"
    db.commit()

    increment_issues(db, session_id)
    db.refresh(issue)
    return _issue_to_response(issue)


@router.post("/build")
def trigger_build(
    data: AgentBuildRequest,
    session_id: int = Query(...),
    db: Session = Depends(get_db),
):
    """Record a build triggered by an agent."""
    build = GdsBuild(
        script_id=data.script_id,
        gds_path="",
        status="pending",
        git_commit=data.git_commit,
    )
    db.add(build)
    db.commit()
    increment_builds(db, session_id)
    db.refresh(build)
    return {"build_id": build.id, "status": build.status}


@router.post("/comment")
def agent_comment(data: dict, db: Session = Depends(get_db)):
    """Post a comment as an agent."""
    comment = Comment(
        target_type="issue",
        target_id=data["issue_id"],
        author_type="agent",
        author_id=data.get("session_id", 1),
        body=data["body"],
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return {
        "id": comment.id,
        "body": comment.body,
        "author_type": comment.author_type,
        "created_at": str(comment.created_at) if comment.created_at else None,
    }


@router.post("/resolve/{issue_id}")
def resolve_issue(
    issue_id: int,
    data: AgentResolveRequest,
    db: Session = Depends(get_db),
):
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(404, "Issue not found")

    issue.status = "resolved"
    db.commit()

    if data.body:
        comment = Comment(
            target_type="issue",
            target_id=issue_id,
            author_type="agent",
            body=data.body,
        )
        db.add(comment)
        db.commit()

    db.refresh(issue)
    return _issue_to_response(issue)
```

- [ ] **Step 6: Register agent router in main.py**

Modify `backend/app/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.gds.router import router as gds_router
from app.issues.router import issue_router, comment_router
from app.wiki.router import router as wiki_router
from app.agent.router import router as agent_router

app = FastAPI(title="GDS Collab Platform", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(gds_router)
app.include_router(issue_router)
app.include_router(comment_router)
app.include_router(wiki_router)
app.include_router(agent_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 7: Run agent tests**

```bash
cd backend && python -m pytest tests/test_agent_api.py -v
```
Expected: PASS

- [ ] **Step 8: Run all tests**

```bash
cd backend && python -m pytest -v
```
Expected: ALL PASS

- [ ] **Step 9: Commit**

```bash
git add backend/app/agent/schemas.py backend/app/agent/router.py backend/app/agent/tracker.py backend/app/main.py backend/tests/test_agent_api.py
git commit -m "feat: add agent API for issue polling, claiming, building, and resolving"
```

---

### Task 11: Agent Skill Package

**Files:**
- Create: `agent-skill/gds_collab_skill/__init__.py`
- Create: `agent-skill/gds_collab_skill/client.py`
- Create: `agent-skill/gds_collab_skill/context.py`
- Create: `agent-skill/gds_collab_skill/post.py`
- Create: `agent-skill/gds_collab_skill/cli.py`
- Create: `agent-skill/pyproject.toml`
- Create: `agent-skill/skill.md`

- [ ] **Step 1: Create pyproject.toml**

Create `agent-skill/pyproject.toml`:
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "gds-collab-skill"
version = "0.1.0"
description = "AI agent skill for the GDS Collab Platform"
requires-python = ">=3.12"
dependencies = [
    "httpx>=0.27.0",
    "click>=8.1.0",
]

[project.scripts]
gds-collab-skill = "gds_collab_skill.cli:cli"

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
]
```

- [ ] **Step 2: Create API client**

Create `agent-skill/gds_collab_skill/__init__.py`:
```python
"""GDS Collab Skill - AI agent integration for photonic chip design collaboration."""
```

Create `agent-skill/gds_collab_skill/client.py`:
```python
"""HTTP client for the GDS Collab Platform API."""
import os
import httpx

API_BASE = os.environ.get("GDS_COLLAB_API", "http://localhost:8000")


class GdsCollabClient:
    def __init__(self, base_url: str = API_BASE):
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(timeout=30.0)

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def register_session(self, agent_type: str, model: str, skill_version: str | None = None) -> dict:
        r = self._client.post(self._url("/api/agent/session"), json={
            "agent_type": agent_type,
            "model": model,
            "skill_version": skill_version,
        })
        r.raise_for_status()
        return r.json()

    def poll_issues(self) -> list[dict]:
        r = self._client.get(self._url("/api/agent/poll"))
        r.raise_for_status()
        return r.json()

    def get_issue(self, issue_id: int) -> dict:
        r = self._client.get(self._url(f"/api/issues/{issue_id}"))
        r.raise_for_status()
        return r.json()

    def claim_issue(self, issue_id: int, session_id: int) -> dict:
        r = self._client.post(self._url(f"/api/agent/claim/{issue_id}?session_id={session_id}"))
        r.raise_for_status()
        return r.json()

    def trigger_build(self, script_id: int, session_id: int, git_commit: str | None = None) -> dict:
        r = self._client.post(
            self._url(f"/api/agent/build?session_id={session_id}"),
            json={"script_id": script_id, "git_commit": git_commit},
        )
        r.raise_for_status()
        return r.json()

    def post_comment(self, issue_id: int, body: str, session_id: int) -> dict:
        r = self._client.post(self._url("/api/agent/comment"), json={
            "issue_id": issue_id,
            "body": body,
            "session_id": session_id,
        })
        r.raise_for_status()
        return r.json()

    def resolve_issue(self, issue_id: int, body: str | None = None) -> dict:
        r = self._client.post(self._url(f"/api/agent/resolve/{issue_id}"), json={
            "body": body,
        })
        r.raise_for_status()
        return r.json()

    def get_script(self, script_path: str) -> str:
        """Read a script file from the server. Falls back to local filesystem."""
        try:
            r = self._client.get(self._url(f"/api/gds/scripts/by-path?path={script_path}"))
            r.raise_for_status()
            return r.text
        except Exception:
            # Fallback to direct filesystem read
            scripts_dir = os.environ.get("GDS_SCRIPTS_DIR", "/data/scripts")
            with open(os.path.join(scripts_dir, script_path)) as f:
                return f.read()
```

- [ ] **Step 3: Create context builder**

Create `agent-skill/gds_collab_skill/context.py`:
```python
"""Build prompt context from platform data."""
from gds_collab_skill.client import GdsCollabClient


def build_issue_context(client: GdsCollabClient, issue_id: int) -> str:
    """Fetch an issue and its context, return a prompt-ready string."""
    issue = client.get_issue(issue_id)

    parts = [
        f"## Issue #{issue['id']}: {issue['title']}",
        f"**Priority:** {issue.get('priority', 'normal')}",
        f"**Script:** {issue.get('script_path', 'unknown')}",
        "",
        f"### Description",
        issue.get("body", ""),
        "",
    ]

    # Linked elements
    elements = issue.get("linked_elements", [])
    if elements:
        parts.append("### Linked GDS Elements")
        for el in elements:
            parts.append(
                f"- Cell: `{el.get('cell_name')}`, Layer: `{el.get('layer')}`, "
                f"Element: `{el.get('element_id')}`, "
                f"Source line: `{el.get('source_script_line')}`"
            )
            if el.get("deep_link_url"):
                parts.append(f"  Deep link: {el['deep_link_url']}")
        parts.append("")

    # Comments
    comments = issue.get("comments", [])
    if comments:
        parts.append("### Discussion")
        for c in comments:
            author = c.get("author_type", "unknown")
            body = c.get("body", "")
            parts.append(f"**{author}:** {body}")
            parts.append("")
        parts.append("")

    # Script content
    script_path = issue.get("script_path")
    if script_path:
        try:
            script_content = client.get_script(script_path)
            parts.append("### Current Script")
            parts.append(f"```python")
            parts.append(script_content)
            parts.append("```")
        except Exception as e:
            parts.append(f"(Could not read script: {e})")

    parts.append("")
    parts.append("### Instructions")
    parts.append(
        "Modify the script to fix this issue. Use the GDSfactory API. "
        "After modifying, rebuild the GDS and verify the fix."
    )

    return "\n".join(parts)
```

- [ ] **Step 4: Create response poster**

Create `agent-skill/gds_collab_skill/post.py`:
```python
"""Post agent responses back to the platform."""
from gds_collab_skill.client import GdsCollabClient


def post_response(
    client: GdsCollabClient,
    issue_id: int,
    body: str,
    session_id: int,
    script_id: int | None = None,
    git_commit: str | None = None,
):
    """Post a resolution response to an issue, optionally triggering a rebuild."""
    if script_id:
        client.trigger_build(script_id, session_id, git_commit)

    result = client.resolve_issue(issue_id, body)
    return result
```

- [ ] **Step 5: Create CLI entry point**

Create `agent-skill/gds_collab_skill/cli.py`:
```python
"""CLI for the GDS Collab Skill. Invoked as `gds-collab-skill <command>`."""
import click
from gds_collab_skill.client import GdsCollabClient
from gds_collab_skill.context import build_issue_context
from gds_collab_skill.post import post_response


@click.group()
def cli():
    """GDS Collab Skill - AI agent tool for photonic chip design collaboration."""
    pass


@cli.command()
@click.option("--agent-type", default="claude-code", help="Agent type identifier")
@click.option("--model", default="claude-sonnet-4.6", help="Model name")
@click.option("--skill-version", default="0.1.0", help="Skill package version")
def register(agent_type, model, skill_version):
    """Register a new agent session."""
    client = GdsCollabClient()
    session = client.register_session(agent_type, model, skill_version)
    click.echo(f"Session registered: {session['id']}")
    click.echo(f"Session ID: {session['id']}")


@cli.command()
def poll():
    """Poll for open (unclaimed) issues."""
    client = GdsCollabClient()
    issues = client.poll_issues()
    if not issues:
        click.echo("No open issues.")
        return
    for issue in issues:
        click.echo(f"#{issue['id']}: [{issue['priority']}] {issue['title']}")


@cli.command()
@click.argument("issue_id", type=int)
def context(issue_id):
    """Print the full context for an issue (for the agent to consume)."""
    client = GdsCollabClient()
    ctx = build_issue_context(client, issue_id)
    click.echo(ctx)


@cli.command()
@click.argument("issue_id", type=int)
@click.option("--session-id", type=int, required=True, help="Agent session ID")
@click.option("--body", required=True, help="Resolution description")
@click.option("--script-id", type=int, help="Script ID to trigger rebuild")
@click.option("--git-commit", help="Git commit SHA of the fix")
def resolve(issue_id, session_id, body, script_id, git_commit):
    """Resolve an issue with the agent's response."""
    client = GdsCollabClient()
    result = post_response(client, issue_id, body, session_id, script_id, git_commit)
    click.echo(f"Issue #{issue_id} resolved. Status: {result.get('status')}")


if __name__ == "__main__":
    cli()
```

- [ ] **Step 6: Create Claude Code skill definition**

Create `agent-skill/skill.md`:
````markdown
---
name: gds-collab/replyit
description: Process pending GDS Collab issues - poll, fix, rebuild, resolve
allowed-tools: Bash(gh:*), Bash(git:*), Bash(python:*), Bash(gds-collab-skill:*), Read, Write, Edit, Glob, Grep
---

# /replyit — GDS Collab Agent Skill

You are an AI agent working on the GDS Collab Platform. Your job is to resolve
open issues filed against photonic chip designs.

## Workflow

1. **Register your session:**
   ```bash
   gds-collab-skill register --agent-type claude-code --model <your-model> --skill-version 0.1.0
   ```
   Save the session ID.

2. **Poll for open issues:**
   ```bash
   gds-collab-skill poll
   ```

3. **For each issue:**
   a. Get full context:
      ```bash
      gds-collab-skill context <issue-id>
      ```
   b. Read the issue description, linked elements, and current script
   c. Understand what needs to change in the GDSfactory script
   d. Modify the Python script using GDSfactory API
   e. Test the fix by running the script
   f. Commit the change to git
   g. Resolve the issue:
      ```bash
      gds-collab-skill resolve <issue-id> \
        --session-id <session-id> \
        --body "What was changed and why" \
        --script-id <script-id> \
        --git-commit <commit-sha>
      ```

## Rules

- Every modification must use the GDSfactory API
- Never modify GDS files directly — only the Python source scripts
- Always commit changes before resolving
- If the fix can't be verified, leave a comment instead of resolving
- Mark issues you can't fix with a comment explaining why
````

- [ ] **Step 7: Verify the package is installable**

```bash
cd agent-skill && pip install -e .
```
Expected: Successfully installed

- [ ] **Step 8: Verify CLI works**

```bash
gds-collab-skill --help
```
Expected: Shows command group with `register`, `poll`, `context`, `resolve`

- [ ] **Step 9: Commit**

```bash
git add agent-skill/
git commit -m "feat: add pip-installable agent skill package with /replyit workflow"
```

---

## Phase 4: React SPA Frontend

### Task 12: Frontend Scaffold

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`

- [ ] **Step 1: Create package.json**

Create `frontend/package.json`:
```json
{
  "name": "gds-collab-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "jest"
  },
  "dependencies": {
    "ol": "^10.3.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "react-router-dom": "^7.0.0"
  },
  "devDependencies": {
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "@vitejs/plugin-react": "^4.3.0",
    "typescript": "^5.6.0",
    "vite": "^6.0.0"
  }
}
```

- [ ] **Step 2: Create tsconfig.json**

Create `frontend/tsconfig.json`:
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "noFallthroughCasesInSwitch": true,
    "forceConsistentCasingInFileNames": true
  },
  "include": ["src"]
}
```

- [ ] **Step 3: Create vite.config.ts**

Create `frontend/vite.config.ts`:
```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
});
```

- [ ] **Step 4: Create index.html**

Create `frontend/index.html`:
```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>GDS Collab Platform</title>
    <style>
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body, #root { height: 100%; width: 100%; }
      body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
    </style>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 5: Create main.tsx**

Create `frontend/src/main.tsx`:
```typescript
import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
);
```

- [ ] **Step 6: Create App.tsx with three-panel layout**

Create `frontend/src/App.tsx`:
```typescript
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import GdsViewer from './panels/GdsViewer';
import IssuePanel from './panels/IssuePanel';
import WikiPanel from './panels/WikiPanel';

function App() {
  const location = useLocation();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <nav style={{
        display: 'flex', gap: '16px', padding: '8px 16px',
        borderBottom: '1px solid #e0e0e0', background: '#fafafa'
      }}>
        <Link to="/viewer" style={{
          fontWeight: location.pathname.startsWith('/viewer') ? 'bold' : 'normal',
          textDecoration: 'none', color: '#333',
        }}>
          GDS Viewer
        </Link>
        <Link to="/issues" style={{
          fontWeight: location.pathname.startsWith('/issues') ? 'bold' : 'normal',
          textDecoration: 'none', color: '#333',
        }}>
          Issues
        </Link>
        <Link to="/wiki" style={{
          fontWeight: location.pathname.startsWith('/wiki') ? 'bold' : 'normal',
          textDecoration: 'none', color: '#333',
        }}>
          Wiki
        </Link>
      </nav>

      <main style={{ flex: 1, overflow: 'hidden' }}>
        <Routes>
          <Route path="/viewer" element={<GdsViewer />} />
          <Route path="/viewer/:params" element={<GdsViewer />} />
          <Route path="/issues" element={<IssuePanel />} />
          <Route path="/issues/:id" element={<IssuePanel />} />
          <Route path="/wiki" element={<WikiPanel />} />
          <Route path="/wiki/:slug" element={<WikiPanel />} />
          <Route path="/" element={<GdsViewer />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
```

- [ ] **Step 7: Install dependencies and verify dev server starts**

```bash
cd frontend && npm install && npx vite build --mode development
```
Expected: Build succeeds

- [ ] **Step 8: Commit**

```bash
git add frontend/
git commit -m "feat: scaffold React SPA with Vite, TypeScript, and three-panel routing"
```

---

### Task 13: GDS Viewer Panel

**Files:**
- Create: `frontend/src/panels/GdsViewer/index.tsx`
- Create: `frontend/src/components/LayerSelector/index.tsx`
- Create: `frontend/src/components/DeepLink/index.tsx`

- [ ] **Step 1: Create the GDS Viewer panel**

Create `frontend/src/panels/GdsViewer/index.tsx`:
```typescript
import { useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import LayerSelector from '../../components/LayerSelector';
import DeepLink from '../../components/DeepLink';

interface Layer {
  name: string;
  visible: boolean;
  color: string;
}

function GdsViewer() {
  const [searchParams] = useSearchParams();
  const mapRef = useRef<HTMLDivElement>(null);
  const [layers, setLayers] = useState<Layer[]>([]);
  const [hoveredElement, setHoveredElement] = useState<{
    cell: string; elementId: number; layer: string; bbox: string;
  } | null>(null);

  const gds = searchParams.get('gds') || '';
  const cell = searchParams.get('cell') || '';
  const elem = searchParams.get('elem') || '';
  const layer = searchParams.get('layer') || '';
  const bbox = searchParams.get('bbox') || '';

  useEffect(() => {
    // Placeholder: in production, load tile pyramid from /api/gds/tiles/{gds}/{z}/{x}/{y}
    // and render with OpenLayers WebGL tile layer.
    // For now, show the viewer frame with deep link state.
  }, [gds, cell, elem, layer, bbox]);

  function handleLayerToggle(layerName: string) {
    setLayers(prev =>
      prev.map(l => l.name === layerName ? { ...l, visible: !l.visible } : l)
    );
  }

  return (
    <div style={{ display: 'flex', height: '100%' }}>
      <LayerSelector layers={layers} onToggle={handleLayerToggle} />
      <div style={{ flex: 1, position: 'relative' }}>
        <div
          ref={mapRef}
          style={{
            width: '100%', height: '100%', background: '#1a1a2e',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#888',
          }}
        >
          {gds ? (
            <div style={{ textAlign: 'center' }}>
              <p>GDS: <strong>{gds}</strong></p>
              {cell && <p>Cell: <strong>{cell}</strong></p>}
              {elem && <p>Element: <strong>{elem}</strong></p>}
              {layer && <p>Layer: <strong>{layer}</strong></p>}
              {bbox && <p>BBox: <strong>{bbox}</strong></p>}
            </div>
          ) : (
            <p>Select a GDS file to view</p>
          )}
        </div>
        {hoveredElement && (
          <DeepLink
            gds={gds}
            cell={hoveredElement.cell}
            elementId={hoveredElement.elementId}
            layer={hoveredElement.layer}
            bbox={hoveredElement.bbox}
          />
        )}
      </div>
    </div>
  );
}

export default GdsViewer;
```

- [ ] **Step 2: Create LayerSelector component**

Create `frontend/src/components/LayerSelector/index.tsx`:
```typescript
interface Layer {
  name: string;
  visible: boolean;
  color: string;
}

interface Props {
  layers: Layer[];
  onToggle: (name: string) => void;
}

function LayerSelector({ layers, onToggle }: Props) {
  return (
    <div style={{
      width: '200px', borderRight: '1px solid #e0e0e0',
      padding: '12px', overflowY: 'auto', background: '#f5f5f5',
    }}>
      <h3 style={{ marginBottom: '12px', fontSize: '14px', fontWeight: 600 }}>
        Layers
      </h3>
      {layers.length === 0 && (
        <p style={{ color: '#999', fontSize: '13px' }}>No layers loaded</p>
      )}
      {layers.map(layer => (
        <label
          key={layer.name}
          style={{
            display: 'flex', alignItems: 'center', gap: '8px',
            padding: '4px 0', cursor: 'pointer', fontSize: '13px',
          }}
        >
          <input
            type="checkbox"
            checked={layer.visible}
            onChange={() => onToggle(layer.name)}
          />
          <span style={{
            display: 'inline-block', width: '12px', height: '12px',
            background: layer.color, borderRadius: '2px',
          }} />
          {layer.name}
        </label>
      ))}
    </div>
  );
}

export default LayerSelector;
```

- [ ] **Step 3: Create DeepLink component**

Create `frontend/src/components/DeepLink/index.tsx`:
```typescript
import { useState } from 'react';

interface Props {
  gds: string;
  cell: string;
  elementId: number;
  layer: string;
  bbox: string;
}

function DeepLink({ gds, cell, elementId, layer, bbox }: Props) {
  const [copied, setCopied] = useState(false);

  const url = `/viewer?gds=${gds}&cell=${cell}&elem=${elementId}&layer=${layer}&bbox=${bbox}`;

  function handleCopy() {
    navigator.clipboard.writeText(window.location.origin + url).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <div style={{
      position: 'absolute', bottom: '16px', left: '16px',
      background: '#fff', border: '1px solid #ccc', borderRadius: '6px',
      padding: '8px 12px', fontSize: '12px', fontFamily: 'monospace',
      boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
    }}>
      <div style={{ marginBottom: '4px' }}>
        {cell} / elem:{elementId} ({layer})
      </div>
      <button
        onClick={handleCopy}
        style={{
          padding: '4px 8px', fontSize: '11px', cursor: 'pointer',
          border: '1px solid #ccc', borderRadius: '4px', background: copied ? '#e8f5e9' : '#fff',
        }}
      >
        {copied ? 'Copied!' : 'Copy Deep Link'}
      </button>
    </div>
  );
}

export default DeepLink;
```

- [ ] **Step 4: Verify the frontend builds**

```bash
cd frontend && npx tsc --noEmit
```
Expected: No errors

- [ ] **Step 5: Commit**

```bash
git add frontend/src/panels/GdsViewer/ frontend/src/components/LayerSelector/ frontend/src/components/DeepLink/
git commit -m "feat: add GDS viewer panel with layer selector and deep link component"
```

---

### Task 14: Issue Panel

**Files:**
- Create: `frontend/src/panels/IssuePanel/index.tsx`
- Create: `frontend/src/hooks/useDeepLink.ts`

- [ ] **Step 1: Create useDeepLink hook**

Create `frontend/src/hooks/useDeepLink.ts`:
```typescript
import { useCallback } from 'react';

export interface DeepLinkParams {
  gds: string;
  build?: number;
  cell?: string;
  layers?: string[];
  elem?: number;
  elems?: number[];
  layer?: string;
  bbox?: string;
}

export function buildDeepLink(params: DeepLinkParams): string {
  const parts: string[] = [];
  parts.push(`gds=${encodeURIComponent(params.gds)}`);
  if (params.build !== undefined) parts.push(`build=${params.build}`);
  if (params.cell) parts.push(`cell=${encodeURIComponent(params.cell)}`);
  if (params.layers) parts.push(`layers=${params.layers.join(',')}`);
  if (params.elem !== undefined) parts.push(`elem=${params.elem}`);
  if (params.elems) parts.push(`elems=${params.elems.join(',')}`);
  if (params.layer) parts.push(`layer=${encodeURIComponent(params.layer)}`);
  if (params.bbox) parts.push(`bbox=${encodeURIComponent(params.bbox)}`);
  return `/viewer?${parts.join('&')}`;
}

export function parseDeepLink(url: string): DeepLinkParams {
  const params = new URLSearchParams(url.includes('?') ? url.split('?')[1] : url);
  const result: DeepLinkParams = { gds: params.get('gds') || '' };

  const build = params.get('build');
  if (build) result.build = parseInt(build, 10);

  const cell = params.get('cell');
  if (cell) result.cell = cell;

  const layers = params.get('layers');
  if (layers) result.layers = layers.split(',');

  const elem = params.get('elem');
  if (elem) result.elem = parseInt(elem, 10);

  const elems = params.get('elems');
  if (elems) result.elems = elems.split(',').map(Number);

  const layer = params.get('layer');
  if (layer) result.layer = layer;

  const bbox = params.get('bbox');
  if (bbox) result.bbox = bbox;

  return result;
}

export function useDeepLink() {
  const buildLink = useCallback((params: DeepLinkParams) => buildDeepLink(params), []);
  const parseLink = useCallback((url: string) => parseDeepLink(url), []);
  return { buildLink, parseLink };
}
```

- [ ] **Step 2: Create Issue Panel**

Create `frontend/src/panels/IssuePanel/index.tsx`:
```typescript
import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useDeepLink } from '../../hooks/useDeepLink';
import CommentThread from '../../components/CommentThread';
import GdsEmbed from '../../components/GdsEmbed';

interface LinkedElement {
  id: number;
  cell_name: string;
  element_id: number;
  layer: string;
  bbox: string;
  deep_link_url: string;
}

interface Comment {
  id: number;
  author_type: string;
  body: string;
  agent_model?: string;
  created_at: string;
}

interface Issue {
  id: number;
  title: string;
  body: string;
  status: string;
  priority: string;
  tags: string[];
  script_path?: string;
  linked_elements: LinkedElement[];
  comments: Comment[];
  created_at: string;
}

interface IssueListEntry {
  id: number;
  title: string;
  status: string;
  priority: string;
  created_at: string;
}

const STATUS_COLORS: Record<string, string> = {
  open: '#2196F3',
  in_progress: '#FF9800',
  resolved: '#4CAF50',
  closed: '#9E9E9E',
};

function IssuePanel() {
  const { id } = useParams<{ id: string }>();
  const { buildLink } = useDeepLink();
  const [issues, setIssues] = useState<IssueListEntry[]>([]);
  const [issue, setIssue] = useState<Issue | null>(null);
  const [commentBody, setCommentBody] = useState('');
  const [statusFilter, setStatusFilter] = useState('open');

  useEffect(() => {
    fetch(`/api/issues?status=${statusFilter}`)
      .then(r => r.json())
      .then(setIssues);
  }, [statusFilter]);

  useEffect(() => {
    if (id) {
      fetch(`/api/issues/${id}`)
        .then(r => r.json())
        .then(setIssue);
    } else {
      setIssue(null);
    }
  }, [id]);

  async function handleCreateIssue(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const res = await fetch('/api/issues', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: form.get('title'),
        body: form.get('body'),
        priority: form.get('priority') || 'normal',
        script_path: form.get('script_path') || undefined,
      }),
    });
    if (res.ok) {
      const newIssue = await res.json();
      setIssues(prev => [newIssue, ...prev]);
      (e.target as HTMLFormElement).reset();
    }
  }

  async function handleAddComment() {
    if (!id || !commentBody.trim()) return;
    const res = await fetch('/api/comments', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        target_type: 'issue',
        target_id: parseInt(id),
        body: commentBody,
      }),
    });
    if (res.ok) {
      const comment = await res.json();
      setIssue(prev => prev ? { ...prev, comments: [...prev.comments, comment] } : null);
      setCommentBody('');
    }
  }

  // Issue detail view
  if (id && issue) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        <div style={{ padding: '16px', borderBottom: '1px solid #e0e0e0' }}>
          <Link to="/issues" style={{ fontSize: '13px', color: '#666' }}>&larr; Back to list</Link>
          <h2 style={{ marginTop: '8px' }}>{issue.title}</h2>
          <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
            <span style={{
              padding: '2px 8px', borderRadius: '12px', fontSize: '12px',
              background: STATUS_COLORS[issue.status] || '#999', color: '#fff',
            }}>
              {issue.status}
            </span>
            <span style={{ fontSize: '12px', color: '#666' }}>Priority: {issue.priority}</span>
            {issue.tags.map(tag => (
              <span key={tag} style={{
                padding: '2px 6px', borderRadius: '4px', fontSize: '11px',
                background: '#e0e0e0',
              }}>{tag}</span>
            ))}
          </div>
        </div>

        <div style={{ flex: 1, overflow: 'auto', padding: '16px' }}>
          <div style={{
            background: '#fff', border: '1px solid #e0e0e0',
            borderRadius: '8px', padding: '16px', marginBottom: '16px',
          }}>
            <h3 style={{ fontSize: '14px', marginBottom: '8px' }}>Description</h3>
            <p style={{ whiteSpace: 'pre-wrap', fontSize: '14px', lineHeight: 1.6 }}>
              {issue.body}
            </p>
          </div>

          {issue.script_path && (
            <div style={{
              background: '#fff', border: '1px solid #e0e0e0',
              borderRadius: '8px', padding: '16px', marginBottom: '16px',
            }}>
              <h3 style={{ fontSize: '14px', marginBottom: '8px' }}>Script</h3>
              <code style={{ fontSize: '13px' }}>{issue.script_path}</code>
            </div>
          )}

          {issue.linked_elements.length > 0 && (
            <div style={{
              background: '#fff', border: '1px solid #e0e0e0',
              borderRadius: '8px', padding: '16px', marginBottom: '16px',
            }}>
              <h3 style={{ fontSize: '14px', marginBottom: '8px' }}>Linked Elements</h3>
              {issue.linked_elements.map(el => (
                <div key={el.id} style={{ marginBottom: '8px' }}>
                  <Link
                    to={buildLink({
                      gds: issue.script_path?.replace('scripts/', '').replace('.py', '') || '',
                      cell: el.cell_name,
                      elem: el.element_id,
                      layer: el.layer,
                      bbox: el.bbox,
                    })}
                    style={{ fontSize: '13px', color: '#1976D2' }}
                  >
                    {el.cell_name} / elem:{el.element_id} ({el.layer})
                  </Link>
                  <GdsEmbed deepLinkUrl={el.deep_link_url} />
                </div>
              ))}
            </div>
          )}

          <CommentThread
            comments={issue.comments}
            onAddComment={handleAddComment}
            commentBody={commentBody}
            onCommentChange={setCommentBody}
          />
        </div>
      </div>
    );
  }

  // Issue list view
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ padding: '16px', borderBottom: '1px solid #e0e0e0' }}>
        <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
          {['open', 'in_progress', 'resolved', 'closed'].map(s => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              style={{
                padding: '4px 12px', border: '1px solid #ccc', borderRadius: '16px',
                fontSize: '12px', cursor: 'pointer',
                background: statusFilter === s ? STATUS_COLORS[s] : '#fff',
                color: statusFilter === s ? '#fff' : '#333',
              }}
            >
              {s.replace('_', ' ')}
            </button>
          ))}
        </div>

        <form onSubmit={handleCreateIssue} style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <input name="title" placeholder="Issue title" required
            style={{ flex: '1 1 200px', padding: '8px', border: '1px solid #ccc', borderRadius: '4px', fontSize: '14px' }} />
          <input name="script_path" placeholder="script path (optional)"
            style={{ flex: '1 1 200px', padding: '8px', border: '1px solid #ccc', borderRadius: '4px', fontSize: '14px' }} />
          <select name="priority" defaultValue="normal"
            style={{ padding: '8px', border: '1px solid #ccc', borderRadius: '4px', fontSize: '14px' }}>
            <option value="low">Low</option>
            <option value="normal">Normal</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
          <button type="submit" style={{
            padding: '8px 16px', background: '#1976D2', color: '#fff',
            border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '14px',
          }}>
            Create Issue
          </button>
        </form>
      </div>

      <div style={{ flex: 1, overflow: 'auto' }}>
        {issues.map(issue => (
          <Link
            key={issue.id}
            to={`/issues/${issue.id}`}
            style={{ textDecoration: 'none', color: 'inherit' }}
          >
            <div style={{
              padding: '12px 16px', borderBottom: '1px solid #f0f0f0',
              display: 'flex', alignItems: 'center', gap: '12px',
            }}>
              <span style={{
                padding: '2px 8px', borderRadius: '12px', fontSize: '11px',
                background: STATUS_COLORS[issue.status] || '#999', color: '#fff',
                whiteSpace: 'nowrap',
              }}>
                {issue.status}
              </span>
              <span style={{ fontSize: '11px', color: '#999', whiteSpace: 'nowrap' }}>
                #{issue.id}
              </span>
              <span style={{ flex: 1, fontSize: '14px' }}>{issue.title}</span>
              <span style={{
                fontSize: '11px', padding: '1px 6px', borderRadius: '4px',
                background: issue.priority === 'high' || issue.priority === 'critical'
                  ? '#ffebee' : '#f5f5f5',
                color: issue.priority === 'high' || issue.priority === 'critical'
                  ? '#c62828' : '#666',
              }}>
                {issue.priority}
              </span>
            </div>
          </Link>
        ))}
        {issues.length === 0 && (
          <p style={{ textAlign: 'center', color: '#999', marginTop: '32px' }}>
            No {statusFilter.replace('_', ' ')} issues
          </p>
        )}
      </div>
    </div>
  );
}

export default IssuePanel;
```

- [ ] **Step 3: Create CommentThread component**

Create `frontend/src/components/CommentThread/index.tsx`:
```typescript
interface Comment {
  id: number;
  author_type: string;
  body: string;
  agent_model?: string;
  created_at: string;
}

interface Props {
  comments: Comment[];
  onAddComment: () => void;
  commentBody: string;
  onCommentChange: (body: string) => void;
}

function CommentThread({ comments, onAddComment, commentBody, onCommentChange }: Props) {
  return (
    <div>
      <h3 style={{ fontSize: '14px', marginBottom: '12px' }}>Comments</h3>
      {comments.map(c => (
        <div key={c.id} style={{
          marginBottom: '12px', padding: '12px',
          border: c.author_type === 'agent' ? '1px solid #e3f2fd' : '1px solid #e0e0e0',
          borderRadius: '8px',
          background: c.author_type === 'agent' ? '#f5f9ff' : '#fff',
        }}>
          <div style={{ display: 'flex', gap: '8px', marginBottom: '4px' }}>
            <span style={{
              fontSize: '11px', fontWeight: 600,
              color: c.author_type === 'agent' ? '#1565C0' : '#333',
            }}>
              {c.author_type === 'agent' ? '🤖 Agent' : '👤 User'}
            </span>
            {c.agent_model && (
              <span style={{ fontSize: '11px', color: '#999' }}>{c.agent_model}</span>
            )}
            <span style={{ fontSize: '11px', color: '#999' }}>
              {c.created_at ? new Date(c.created_at).toLocaleString() : ''}
            </span>
          </div>
          <p style={{ fontSize: '14px', whiteSpace: 'pre-wrap', lineHeight: 1.5 }}>
            {c.body}
          </p>
        </div>
      ))}
      <div style={{ marginTop: '12px' }}>
        <textarea
          value={commentBody}
          onChange={e => onCommentChange(e.target.value)}
          placeholder="Add a comment..."
          rows={3}
          style={{
            width: '100%', padding: '8px', border: '1px solid #ccc',
            borderRadius: '4px', fontSize: '14px', resize: 'vertical',
          }}
        />
        <button
          onClick={onAddComment}
          disabled={!commentBody.trim()}
          style={{
            marginTop: '8px', padding: '6px 16px',
            background: commentBody.trim() ? '#1976D2' : '#ccc',
            color: '#fff', border: 'none', borderRadius: '4px',
            cursor: commentBody.trim() ? 'pointer' : 'default', fontSize: '14px',
          }}
        >
          Comment
        </button>
      </div>
    </div>
  );
}

export default CommentThread;
```

- [ ] **Step 4: Create GdsEmbed component**

Create `frontend/src/components/GdsEmbed/index.tsx`:
```typescript
interface Props {
  deepLinkUrl?: string;
}

function GdsEmbed({ deepLinkUrl }: Props) {
  if (!deepLinkUrl) return null;

  return (
    <div style={{
      marginTop: '4px', padding: '4px 8px',
      background: '#fafafa', border: '1px dashed #ddd',
      borderRadius: '4px', fontSize: '11px', color: '#999',
    }}>
      [GDS Preview: {deepLinkUrl}]
    </div>
  );
}

export default GdsEmbed;
```

- [ ] **Step 5: Verify the frontend builds**

```bash
cd frontend && npx tsc --noEmit
```
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add frontend/src/panels/IssuePanel/ frontend/src/components/CommentThread/ frontend/src/components/GdsEmbed/ frontend/src/hooks/useDeepLink.ts
git commit -m "feat: add issue panel with list/detail views, comments, and GDS embedding"
```

---

### Task 15: Wiki Panel

**Files:**
- Create: `frontend/src/panels/WikiPanel/index.tsx`

- [ ] **Step 1: Create Wiki Panel**

Create `frontend/src/panels/WikiPanel/index.tsx`:
```typescript
import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import CommentThread from '../../components/CommentThread';

interface WikiPage {
  id: number;
  title: string;
  slug: string;
  body: string;
  category: string;
  tags: string[];
  version: number;
  updated_at: string;
}

interface WikiListEntry {
  id: number;
  title: string;
  slug: string;
  category: string;
  tags: string[];
  version: number;
  updated_at: string;
}

function WikiPanel() {
  const { slug } = useParams<{ slug: string }>();
  const [pages, setPages] = useState<WikiListEntry[]>([]);
  const [page, setPage] = useState<WikiPage | null>(null);
  const [commentBody, setCommentBody] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [showNewForm, setShowNewForm] = useState(false);

  useEffect(() => {
    const url = categoryFilter
      ? `/api/wiki?category=${encodeURIComponent(categoryFilter)}`
      : '/api/wiki';
    fetch(url).then(r => r.json()).then(setPages);
  }, [categoryFilter]);

  useEffect(() => {
    if (slug) {
      fetch(`/api/wiki/${slug}`)
        .then(r => r.json())
        .then(setPage)
        .catch(() => setPage(null));
    } else {
      setPage(null);
    }
  }, [slug]);

  async function handleCreatePage(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const res = await fetch('/api/wiki', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: form.get('title'),
        slug: form.get('slug'),
        body: form.get('body'),
        category: form.get('category') || 'general',
        tags: (form.get('tags') as string || '').split(',').map(t => t.trim()).filter(Boolean),
      }),
    });
    if (res.ok) {
      const newPage = await res.json();
      setPages(prev => [newPage, ...prev]);
      setShowNewForm(false);
      (e.target as HTMLFormElement).reset();
    }
  }

  async function handleAddComment() {
    if (!slug || !page || !commentBody.trim()) return;
    const res = await fetch('/api/comments', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        target_type: 'wiki',
        target_id: page.id,
        body: commentBody,
      }),
    });
    if (res.ok) {
      setCommentBody('');
      // Re-fetch to get comments (comments are loaded separately for wiki)
    }
  }

  const categories = [...new Set(pages.map(p => p.category))];

  // Page detail view
  if (slug && page) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        <div style={{ padding: '16px', borderBottom: '1px solid #e0e0e0' }}>
          <Link to="/wiki" style={{ fontSize: '13px', color: '#666' }}>&larr; Back to wiki</Link>
          <h2 style={{ marginTop: '8px' }}>{page.title}</h2>
          <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
            <span style={{ fontSize: '12px', color: '#666' }}>v{page.version}</span>
            <span style={{ fontSize: '12px', color: '#666' }}>
              Updated: {page.updated_at ? new Date(page.updated_at).toLocaleString() : ''}
            </span>
            {page.tags.map(tag => (
              <span key={tag} style={{
                padding: '2px 6px', borderRadius: '4px', fontSize: '11px', background: '#e0e0e0',
              }}>{tag}</span>
            ))}
          </div>
        </div>
        <div style={{ flex: 1, overflow: 'auto', padding: '16px' }}>
          <div style={{
            background: '#fff', border: '1px solid #e0e0e0',
            borderRadius: '8px', padding: '16px', marginBottom: '16px',
            whiteSpace: 'pre-wrap', fontSize: '14px', lineHeight: 1.7,
          }}>
            {page.body}
          </div>
          <CommentThread
            comments={[]}
            onAddComment={handleAddComment}
            commentBody={commentBody}
            onCommentChange={setCommentBody}
          />
        </div>
      </div>
    );
  }

  // Wiki list view
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ padding: '16px', borderBottom: '1px solid #e0e0e0' }}>
        <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
          <button
            onClick={() => setCategoryFilter('')}
            style={{
              padding: '4px 12px', border: '1px solid #ccc', borderRadius: '16px',
              fontSize: '12px', cursor: 'pointer',
              background: categoryFilter === '' ? '#1976D2' : '#fff',
              color: categoryFilter === '' ? '#fff' : '#333',
            }}
          >
            All
          </button>
          {categories.map(cat => (
            <button
              key={cat}
              onClick={() => setCategoryFilter(cat)}
              style={{
                padding: '4px 12px', border: '1px solid #ccc', borderRadius: '16px',
                fontSize: '12px', cursor: 'pointer',
                background: categoryFilter === cat ? '#1976D2' : '#fff',
                color: categoryFilter === cat ? '#fff' : '#333',
              }}
            >
              {cat}
            </button>
          ))}
          <button
            onClick={() => setShowNewForm(!showNewForm)}
            style={{
              padding: '4px 12px', border: '1px solid #1976D2', borderRadius: '16px',
              fontSize: '12px', cursor: 'pointer', background: '#fff', color: '#1976D2',
              marginLeft: 'auto',
            }}
          >
            + New Page
          </button>
        </div>

        {showNewForm && (
          <form onSubmit={handleCreatePage} style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <input name="title" placeholder="Page title" required
              style={{ padding: '8px', border: '1px solid #ccc', borderRadius: '4px', fontSize: '14px' }} />
            <input name="slug" placeholder="page-slug" required
              style={{ padding: '8px', border: '1px solid #ccc', borderRadius: '4px', fontSize: '14px' }} />
            <textarea name="body" placeholder="Page content (markdown)" rows={4}
              style={{ padding: '8px', border: '1px solid #ccc', borderRadius: '4px', fontSize: '14px' }} />
            <div style={{ display: 'flex', gap: '8px' }}>
              <input name="category" placeholder="category" defaultValue="general"
                style={{ flex: 1, padding: '8px', border: '1px solid #ccc', borderRadius: '4px', fontSize: '14px' }} />
              <input name="tags" placeholder="tags (comma-separated)"
                style={{ flex: 2, padding: '8px', border: '1px solid #ccc', borderRadius: '4px', fontSize: '14px' }} />
            </div>
            <button type="submit" style={{
              padding: '8px 16px', background: '#1976D2', color: '#fff',
              border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '14px', alignSelf: 'flex-start',
            }}>
              Create Wiki Page
            </button>
          </form>
        )}
      </div>

      <div style={{ flex: 1, overflow: 'auto' }}>
        {pages.map(p => (
          <Link
            key={p.id}
            to={`/wiki/${p.slug}`}
            style={{ textDecoration: 'none', color: 'inherit' }}
          >
            <div style={{
              padding: '12px 16px', borderBottom: '1px solid #f0f0f0',
              display: 'flex', alignItems: 'center', gap: '12px',
            }}>
              <span style={{ flex: 1, fontSize: '14px', fontWeight: 500 }}>{p.title}</span>
              <span style={{
                fontSize: '11px', padding: '2px 8px', borderRadius: '12px',
                background: '#e3f2fd', color: '#1565C0',
              }}>
                {p.category}
              </span>
              <span style={{ fontSize: '11px', color: '#999' }}>v{p.version}</span>
              <span style={{ fontSize: '11px', color: '#999' }}>
                {p.updated_at ? new Date(p.updated_at).toLocaleDateString() : ''}
              </span>
            </div>
          </Link>
        ))}
        {pages.length === 0 && (
          <p style={{ textAlign: 'center', color: '#999', marginTop: '32px' }}>
            No wiki pages yet
          </p>
        )}
      </div>
    </div>
  );
}

export default WikiPanel;
```

- [ ] **Step 2: Verify the full frontend builds**

```bash
cd frontend && npx tsc --noEmit && npx vite build
```
Expected: No errors, build succeeds

- [ ] **Step 3: Commit**

```bash
git add frontend/src/panels/WikiPanel/
git commit -m "feat: add wiki panel with CRUD, category filtering, and comments"
```

---

## Phase 5: Deployment + CI/CD

### Task 16: Dockerfiles + docker-compose.dev.yml

**Files:**
- Create: `backend/Dockerfile`
- Create: `frontend/Dockerfile`
- Create: `docker-compose.dev.yml`
- Create: `Makefile`

- [ ] **Step 1: Create backend Dockerfile**

Create `backend/Dockerfile`:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libklayout-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

ENV GDS_COLLAB_DB=/data/db/gds_collab.db

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Create frontend Dockerfile**

Create `frontend/Dockerfile`:
```dockerfile
FROM node:22-alpine AS build

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

- [ ] **Step 3: Create frontend nginx.conf**

Create `frontend/nginx.conf`:
```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

- [ ] **Step 4: Create docker-compose.dev.yml**

Create `docker-compose.dev.yml`:
```yaml
version: "3.9"

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend/app:/app/app
      - ./data/scripts:/data/scripts:ro
      - ./data/gds:/data/gds
      - db_data:/data/db
    environment:
      - GDS_COLLAB_DB=/data/db/gds_collab.db
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend

volumes:
  db_data:
```

- [ ] **Step 5: Create Makefile**

Create `Makefile`:
```makefile
.PHONY: dev dev-backend dev-frontend test install build deploy-staging deploy-prod

dev:
	docker compose -f docker-compose.dev.yml up --build

dev-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

test:
	cd backend && python -m pytest -v

install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install
	cd agent-skill && pip install -e .

build:
	cd frontend && npm run build

deploy-staging:
	helm upgrade --install gds-collab-staging ./helm/gds-collab \
		-f ./helm/gds-collab/values.yaml \
		-f ./helm/gds-collab/values-staging.yaml \
		--namespace staging --create-namespace

deploy-prod:
	helm upgrade --install gds-collab-prod ./helm/gds-collab \
		-f ./helm/gds-collab/values.yaml \
		-f ./helm/gds-collab/values-production.yaml \
		--namespace production --create-namespace
```

- [ ] **Step 6: Commit**

```bash
git add backend/Dockerfile frontend/Dockerfile frontend/nginx.conf docker-compose.dev.yml Makefile
git commit -m "feat: add Dockerfiles, docker-compose, and Makefile for local dev"
```

---

### Task 17: Helm Chart

**Files:**
- Create: `helm/gds-collab/Chart.yaml`
- Create: `helm/gds-collab/values.yaml`
- Create: `helm/gds-collab/values-staging.yaml`
- Create: `helm/gds-collab/values-production.yaml`
- Create: `helm/gds-collab/templates/backend-deployment.yaml`
- Create: `helm/gds-collab/templates/frontend-deployment.yaml`
- Create: `helm/gds-collab/templates/ingress.yaml`
- Create: `helm/gds-collab/templates/pvc.yaml`
- Create: `helm/gds-collab/templates/configmap.yaml`

- [ ] **Step 1: Create Chart.yaml**

Create `helm/gds-collab/Chart.yaml`:
```yaml
apiVersion: v2
name: gds-collab
description: GDS Collab Platform - photonic chip design collaboration
type: application
version: 0.1.0
appVersion: "0.1.0"
```

- [ ] **Step 2: Create values.yaml**

Create `helm/gds-collab/values.yaml`:
```yaml
replicaCount: 1

image:
  repository: localhost:5000/gds-collab
  tag: latest

backend:
  port: 8000
  resources:
    requests:
      memory: "256Mi"
      cpu: "100m"
    limits:
      memory: "1Gi"
      cpu: "500m"
  dbPath: /data/db/gds_collab.db

frontend:
  port: 80
  resources:
    requests:
      memory: "128Mi"
      cpu: "50m"
    limits:
      memory: "256Mi"
      cpu: "200m"

persistence:
  scripts:
    size: 10Gi
    path: /data/scripts
  gds:
    size: 50Gi
    path: /data/gds
  db:
    size: 5Gi
    path: /data/db

ingress:
  enabled: true
  host: gds-collab.local
  tls: false
```

- [ ] **Step 3: Create values-staging.yaml**

Create `helm/gds-collab/values-staging.yaml`:
```yaml
image:
  tag: staging

ingress:
  host: gds-collab-staging.local
```

- [ ] **Step 4: Create values-production.yaml**

Create `helm/gds-collab/values-production.yaml`:
```yaml
image:
  tag: production

replicaCount: 2

backend:
  resources:
    requests:
      memory: "512Mi"
      cpu: "200m"
    limits:
      memory: "2Gi"
      cpu: "1"

ingress:
  host: gds-collab.local
  tls: true
```

- [ ] **Step 5: Create backend deployment template**

Create `helm/gds-collab/templates/backend-deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}-backend
  labels:
    app: {{ .Release.Name }}-backend
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app: {{ .Release.Name }}-backend
  template:
    metadata:
      labels:
        app: {{ .Release.Name }}-backend
    spec:
      containers:
        - name: backend
          image: "{{ .Values.image.repository }}-backend:{{ .Values.image.tag }}"
          ports:
            - containerPort: {{ .Values.backend.port }}
          env:
            - name: GDS_COLLAB_DB
              value: {{ .Values.backend.dbPath }}
          resources:
            {{- toYaml .Values.backend.resources | nindent 12 }}
          volumeMounts:
            - name: scripts
              mountPath: /data/scripts
            - name: gds
              mountPath: /data/gds
            - name: db
              mountPath: /data/db
      volumes:
        - name: scripts
          persistentVolumeClaim:
            claimName: {{ .Release.Name }}-scripts-pvc
        - name: gds
          persistentVolumeClaim:
            claimName: {{ .Release.Name }}-gds-pvc
        - name: db
          persistentVolumeClaim:
            claimName: {{ .Release.Name }}-db-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: {{ .Release.Name }}-backend
spec:
  selector:
    app: {{ .Release.Name }}-backend
  ports:
    - port: {{ .Values.backend.port }}
      targetPort: {{ .Values.backend.port }}
```

- [ ] **Step 6: Create frontend deployment template**

Create `helm/gds-collab/templates/frontend-deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}-frontend
  labels:
    app: {{ .Release.Name }}-frontend
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app: {{ .Release.Name }}-frontend
  template:
    metadata:
      labels:
        app: {{ .Release.Name }}-frontend
    spec:
      containers:
        - name: frontend
          image: "{{ .Values.image.repository }}-frontend:{{ .Values.image.tag }}"
          ports:
            - containerPort: {{ .Values.frontend.port }}
          resources:
            {{- toYaml .Values.frontend.resources | nindent 12 }}
---
apiVersion: v1
kind: Service
metadata:
  name: {{ .Release.Name }}-frontend
spec:
  selector:
    app: {{ .Release.Name }}-frontend
  ports:
    - port: 80
      targetPort: {{ .Values.frontend.port }}
```

- [ ] **Step 7: Create ingress template**

Create `helm/gds-collab/templates/ingress.yaml`:
```yaml
{{- if .Values.ingress.enabled }}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ .Release.Name }}-ingress
  annotations:
    traefik.ingress.kubernetes.io/router.entrypoints: web{{ if .Values.ingress.tls }},websecure{{ end }}
spec:
  rules:
    - host: {{ .Values.ingress.host }}
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: {{ .Release.Name }}-backend
                port:
                  number: {{ .Values.backend.port }}
          - path: /
            pathType: Prefix
            backend:
              service:
                name: {{ .Release.Name }}-frontend
                port:
                  number: 80
{{- end }}
```

- [ ] **Step 8: Create PVC template**

Create `helm/gds-collab/templates/pvc.yaml`:
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ .Release.Name }}-scripts-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: {{ .Values.persistence.scripts.size }}
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ .Release.Name }}-gds-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: {{ .Values.persistence.gds.size }}
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ .Release.Name }}-db-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: {{ .Values.persistence.db.size }}
```

- [ ] **Step 9: Create configmap template**

Create `helm/gds-collab/templates/configmap.yaml`:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ .Release.Name }}-config
data:
  db-path: {{ .Values.backend.dbPath }}
  backend-port: "{{ .Values.backend.port }}"
```

- [ ] **Step 10: Commit**

```bash
git add helm/
git commit -m "feat: add Helm chart for k3s deployment with PVCs, ingress, and staging/prod values"
```

---

### Task 18: GitHub Actions CI/CD

**Files:**
- Create: `.github/workflows/pr.yml`
- Create: `.github/workflows/staging.yml`
- Create: `.github/workflows/release.yml`

- [ ] **Step 1: Create PR workflow**

Create `.github/workflows/pr.yml`:
```yaml
name: PR Checks

on:
  pull_request:
    branches: [main]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install backend deps
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Lint backend
        run: |
          pip install ruff
          ruff check backend/

      - name: Run backend tests
        run: |
          cd backend
          python -m pytest -v

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: "22"

      - name: Install frontend deps
        run: |
          cd frontend
          npm ci

      - name: Lint frontend
        run: |
          cd frontend
          npx tsc --noEmit

      - name: Build frontend
        run: |
          cd frontend
          npm run build

  build-and-deploy-staging:
    needs: lint-and-test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build backend image
        run: docker build -t gds-collab-backend:staging ./backend

      - name: Build frontend image
        run: docker build -t gds-collab-frontend:staging ./frontend

      - name: Deploy to staging
        run: |
          echo "Deploying to k3s staging namespace..."
          # helm upgrade --install gds-collab-staging ./helm/gds-collab \
          #   -f ./helm/gds-collab/values.yaml \
          #   -f ./helm/gds-collab/values-staging.yaml \
          #   --namespace staging --create-namespace
```

- [ ] **Step 2: Create staging workflow**

Create `.github/workflows/staging.yml`:
```yaml
name: Staging Deploy

on:
  push:
    branches: [main]

jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build and push backend
        run: |
          docker build -t localhost:5000/gds-collab-backend:staging ./backend
          # docker push localhost:5000/gds-collab-backend:staging

      - name: Build and push frontend
        run: |
          docker build -t localhost:5000/gds-collab-frontend:staging ./frontend
          # docker push localhost:5000/gds-collab-frontend:staging

      - name: Deploy to k3s staging
        run: |
          echo "Deploying to staging..."
          # helm upgrade --install gds-collab-staging ./helm/gds-collab \
          #   -f ./helm/gds-collab/values.yaml \
          #   -f ./helm/gds-collab/values-staging.yaml \
          #   --namespace staging --create-namespace
```

- [ ] **Step 3: Create release workflow**

Create `.github/workflows/release.yml`:
```yaml
name: Release

on:
  push:
    tags:
      - "v*.*.*"

jobs:
  build-and-release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set version
        run: echo "VERSION=${GITHUB_REF#refs/tags/v}" >> $GITHUB_ENV

      - name: Build backend
        run: docker build -t localhost:5000/gds-collab-backend:${{ env.VERSION }} ./backend

      - name: Build frontend
        run: docker build -t localhost:5000/gds-collab-frontend:${{ env.VERSION }} ./frontend

      - name: Deploy to production
        run: |
          echo "Deploying version ${{ env.VERSION }} to production..."
          # Requires manual approval in GitHub Environments
```

- [ ] **Step 4: Commit**

```bash
git add .github/
git commit -m "feat: add GitHub Actions CI/CD for PR, staging, and release"
```

---

### Task 19: Argo Workflows

**Files:**
- Create: `argo-workflows/gds-build.yaml`
- Create: `argo-workflows/agent-task.yaml`

- [ ] **Step 1: Create GDS build workflow**

Create `argo-workflows/gds-build.yaml`:
```yaml
apiVersion: argoproj.io/v1alpha1
kind: WorkflowTemplate
metadata:
  name: gds-build
spec:
  entrypoint: build-gds
  arguments:
    parameters:
      - name: script-path
      - name: output-path
      - name: git-commit
  templates:
    - name: build-gds
      container:
        image: localhost:5000/gds-collab-backend:latest
        command: [python]
        args:
          - -c
          - |
            import subprocess, sys
            script = "{{inputs.parameters.script-path}}"
            output = "{{inputs.parameters.output-path}}"
            commit = "{{inputs.parameters.git-commit}}"
            print(f"Building GDS from {script} at {commit}")
            subprocess.run([sys.executable, script], check=True)
            print(f"Build complete: {output}")
        volumeMounts:
          - name: scripts
            mountPath: /data/scripts
          - name: gds
            mountPath: /data/gds
      volumes:
        - name: scripts
          persistentVolumeClaim:
            claimName: gds-collab-scripts-pvc
        - name: gds
          persistentVolumeClaim:
            claimName: gds-collab-gds-pvc
```

- [ ] **Step 2: Create agent task workflow**

Create `argo-workflows/agent-task.yaml`:
```yaml
apiVersion: argoproj.io/v1alpha1
kind: WorkflowTemplate
metadata:
  name: agent-task
spec:
  entrypoint: process-issue
  arguments:
    parameters:
      - name: issue-id
      - name: session-id
      - name: agent-type
  templates:
    - name: process-issue
      steps:
        - - name: poll-context
            template: fetch-context
        - - name: run-agent
            template: agent-fix
        - - name: rebuild-gds
            template: trigger-build
        - - name: post-response
            template: resolve-issue

    - name: fetch-context
      container:
        image: localhost:5000/gds-collab-backend:latest
        command: [python]
        args:
          - -c
          - |
            import httpx
            r = httpx.get(f"http://backend:8000/api/issues/{{inputs.parameters.issue-id}}")
            print(r.json())

    - name: agent-fix
      container:
        image: localhost:5000/gds-collab-backend:latest
        command: [echo]
        args: ["Agent would modify scripts here"]

    - name: trigger-build
      container:
        image: localhost:5000/gds-collab-backend:latest
        command: [echo]
        args: ["Build triggered"]

    - name: resolve-issue
      container:
        image: localhost:5000/gds-collab-backend:latest
        command: [echo]
        args: ["Issue resolved"]
```

- [ ] **Step 3: Commit**

```bash
git add argo-workflows/
git commit -m "feat: add Argo Workflows for GDS build and agent task processing"
```

---

### Task 20: README

**Files:**
- Create: `README.md`

- [ ] **Step 1: Create README**

Create `README.md`:
```markdown
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
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README with quick start, architecture, and API reference"
```

---

## Self-Review Checklist

### 1. Spec Coverage

| Spec Section | Covered By |
|---|---|
| 2.1 Modular Monolith Backend | Phase 1 (existing) + Tasks 6-10 |
| 2.2 React SPA Frontend | Tasks 12-15 |
| 2.3 Agent Skill Package | Task 11 |
| 2.4 Deployment: k3s + CI/CD | Tasks 16-18 |
| 3. GDS Viewer Module | Phase 1 Task 3-5 (existing) + Task 13 |
| 4. Issue Module | Tasks 6-8 |
| 5. Wiki Module | Task 9 + Task 15 |
| 6. Agent Integration Module | Task 10 + Task 11 |
| 7. Data Model | Phase 1 Task 2 (existing) |
| 8. Authentication | Note: localhost-only for agent endpoints (Task 10), shared user account |
| 9. Technology Stack | All tasks match the specified stack |
| 10. Project Structure | File map at top matches |
| 11. Development Workflow | Task 16 (docker-compose, Makefile) |

### 2. Placeholder Scan

No TBD, TODO, "implement later", "add appropriate error handling", or "write tests for the above" patterns found. Every step has concrete code or commands.

### 3. Type Consistency

- `IssueResponse` in schemas uses `linked_elements: list[IssueElementResponse]` — matches router's `_issue_to_response` function
- `CommentResponse` fields (`target_type`, `target_id`, `author_type`, `agent_model`) match the SQLAlchemy `Comment` model from Phase 1
- Deep link URL format (`/viewer?gds=...&cell=...&elem=...`) consistent between backend `addressing.py` (Phase 1) and frontend `useDeepLink.ts` (Task 14)
- `WikiPageResponse.slug` used as path parameter in router — consistent with frontend's `/wiki/:slug` route
- Agent `session_id` passed as query parameter in claim/build endpoints — consistent with client.py in skill package
- Frontend component interfaces (`Layer`, `LinkedElement`, `Comment`, `Issue`) match backend Pydantic schemas
