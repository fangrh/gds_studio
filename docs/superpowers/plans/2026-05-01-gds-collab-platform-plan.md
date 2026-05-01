# GDS Collab Platform — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a web-based collaboration platform for photonic chip design teams where GDSfactory scripts generate layouts, users file issues against specific elements, and AI agents resolve issues by modifying scripts and rebuilding.

**Architecture:** Modular monolith FastAPI backend with 4 modules (gds, issues, wiki, agent), React SPA frontend with 3 panels, SQLite database, k3s deployment with Argo Workflows, and a pip-installable agent skill package.

**Tech Stack:** Python 3.12 + FastAPI + SQLAlchemy 2.0 + SQLite | React 19 + TypeScript + OpenLayers | k3s + Helm + Argo Workflows + GitHub Actions

**Spec:** `docs/superpowers/specs/2026-05-01-gds-collab-platform-design.md`

---

## Plan Roadmap

This plan is organized into 5 phases. Each phase produces working, testable software:

| Phase | What it delivers | Depends on |
|-------|-----------------|------------|
| Phase 1 | Backend core + GDS API (parsing, indexing, tiles, watcher) | Nothing |
| Phase 2 | Issue + Wiki backend (CRUD, comments, element linking) | Phase 1 |
| Phase 3 | Agent backend + skill package (/replyit) | Phase 2 |
| Phase 4 | React SPA frontend (GDS viewer, Issue panel, Wiki panel) | Phase 1–3 |
| Phase 5 | k3s deployment + CI/CD + Argo Workflows | Phase 1–4 |

---

## Phase 1: Backend Core + GDS Module

### Task 1: Project Scaffold + Git Init

**Files:**
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/requirements.txt`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/conftest.py`
- Create: `.gitignore`

- [ ] **Step 1: Initialize git repo**

```bash
cd "C:/Users/fangr/OneDrive - Aalto University/桌面/aigds"
git init
```

- [ ] **Step 2: Create .gitignore**

Create `.gitignore`:
```
__pycache__/
*.pyc
*.pyo
.env
.venv/
node_modules/
dist/
*.db
*.sqlite
.superpowers/
*.egg-info/
```

- [ ] **Step 3: Create directory structure**

```bash
mkdir -p backend/app/gds backend/app/issues backend/app/wiki backend/app/agent
mkdir -p backend/tests
touch backend/app/__init__.py backend/app/gds/__init__.py backend/app/issues/__init__.py backend/app/wiki/__init__.py backend/app/agent/__init__.py
touch backend/tests/__init__.py
```

- [ ] **Step 4: Create requirements.txt**

Create `backend/requirements.txt`:
```
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy==2.0.35
pydantic==2.9.0
httpx==0.27.0
pytest==8.3.0
pytest-asyncio==0.24.0
klayout==0.29.0
```

- [ ] **Step 5: Create FastAPI main.py**

Create `backend/app/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="GDS Collab Platform", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 6: Create test conftest.py**

Create `backend/tests/conftest.py`:
```python
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
```

- [ ] **Step 7: Write health endpoint test**

Create `backend/tests/test_health.py`:
```python
import pytest


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
```

- [ ] **Step 8: Run test**

```bash
cd backend && python -m pytest tests/test_health.py -v
```
Expected: PASS

- [ ] **Step 9: Commit**

```bash
git add -A
git commit -m "feat: scaffold backend with FastAPI and test setup"
```

---

### Task 2: Database Models + Connection

**Files:**
- Create: `backend/app/db.py`
- Create: `backend/app/models.py`
- Create: `backend/tests/test_db.py`

- [ ] **Step 1: Write failing test for database creation**

Create `backend/tests/test_db.py`:
```python
import pytest
from sqlalchemy import inspect
from app.db import engine, Base, get_db
from app.models import (
    User, GdsScript, GdsBuild, GdsCell, GdsElement,
    Issue, IssueElement, WikiPage, Comment, AgentSession,
)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_all_tables_exist():
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    expected = [
        "users", "gds_scripts", "gds_builds", "gds_cells", "gds_elements",
        "issues", "issue_elements", "wiki_pages", "comments", "agent_sessions",
    ]
    for table in expected:
        assert table in table_names, f"Missing table: {table}"


def test_create_script_and_build():
    from sqlalchemy.orm import Session
    with Session(engine) as session:
        script = GdsScript(
            path="scripts/ring_resonator.py",
            name="ring_resonator",
            description="Ring resonator design",
        )
        session.add(script)
        session.flush()

        build = GdsBuild(
            script_id=script.id,
            gds_path="gds/ring_resonator.gds",
            status="success",
        )
        session.add(build)
        session.commit()

        assert script.id is not None
        assert build.id is not None
        assert build.script_id == script.id
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && python -m pytest tests/test_db.py -v
```
Expected: FAIL (import error — models don't exist yet)

- [ ] **Step 3: Create db.py**

Create `backend/app/db.py`:
```python
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DB_PATH = os.environ.get("GDS_COLLAB_DB", "gds_collab.db")

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 4: Create models.py**

Create `backend/app/models.py`:
```python
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime, ForeignKey,
    JSON, Enum as SAEnum,
)
from sqlalchemy.orm import relationship
from app.db import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(200))


# --- GDS Source Tracking ---

class GdsScript(Base):
    __tablename__ = "gds_scripts"

    id = Column(Integer, primary_key=True)
    path = Column(String(500), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, default="")
    params_json = Column(JSON, default=dict)
    last_modified = Column(DateTime, default=utcnow)
    git_commit = Column(String(40))

    builds = relationship("GdsBuild", back_populates="script", order_by="GdsBuild.created_at.desc()")


class GdsBuild(Base):
    __tablename__ = "gds_builds"

    id = Column(Integer, primary_key=True)
    script_id = Column(Integer, ForeignKey("gds_scripts.id"), nullable=False)
    gds_path = Column(String(500), nullable=False)
    status = Column(String(20), default="pending")  # pending, success, failed
    build_log = Column(Text, default="")
    git_commit = Column(String(40))
    created_at = Column(DateTime, default=utcnow)

    script = relationship("GdsScript", back_populates="builds")
    cells = relationship("GdsCell", back_populates="build")


class GdsCell(Base):
    __tablename__ = "gds_cells"

    id = Column(Integer, primary_key=True)
    build_id = Column(Integer, ForeignKey("gds_builds.id"), nullable=False)
    name = Column(String(200), nullable=False)
    cell_type = Column(String(50), default="cell")
    bbox = Column(String(100))  # "x1,y1,x2,y2"
    layer_count = Column(Integer, default=0)
    element_count = Column(Integer, default=0)

    build = relationship("GdsBuild", back_populates="cells")
    elements = relationship("GdsElement", back_populates="cell")


class GdsElement(Base):
    __tablename__ = "gds_elements"

    id = Column(Integer, primary_key=True)
    cell_id = Column(Integer, ForeignKey("gds_cells.id"), nullable=False)
    element_type = Column(String(50), nullable=False)  # polygon, path, text, reference
    layer = Column(String(20), nullable=False)  # "M1", "D1", etc.
    bbox = Column(String(100))
    path_data = Column(Text, default="")  # serialized geometry
    properties = Column(JSON, default=dict)
    source_line = Column(Integer)  # line in the Python script that created this

    cell = relationship("GdsCell", back_populates="elements")


# --- Collaboration ---

class Issue(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    body = Column(Text, default="")
    status = Column(String(20), default="open")  # open, in_progress, resolved, closed
    author_type = Column(String(20), nullable=False, default="user")
    author_id = Column(Integer, default=1)
    priority = Column(String(10), default="normal")
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    resolved_by = Column(String(50))
    resolved_at = Column(DateTime)
    script_path = Column(String(500))

    linked_elements = relationship("IssueElement", back_populates="issue")
    comments = relationship("Comment", back_populates="issue", order_by="Comment.created_at",
                            primaryjoin="Comment.target_id == Issue.id and Comment.target_type == 'issue'")


class IssueElement(Base):
    __tablename__ = "issue_elements"

    id = Column(Integer, primary_key=True)
    issue_id = Column(Integer, ForeignKey("issues.id"), nullable=False)
    gds_build_id = Column(Integer, ForeignKey("gds_builds.id"))
    cell_name = Column(String(200))
    element_id = Column(Integer)
    layer = Column(String(20))
    bbox = Column(String(100))
    source_script_line = Column(Integer)
    deep_link_url = Column(String(1000))

    issue = relationship("Issue", back_populates="linked_elements")
    build = relationship("GdsBuild")


class WikiPage(Base):
    __tablename__ = "wiki_pages"

    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    slug = Column(String(200), unique=True, nullable=False)
    body = Column(Text, default="")
    category = Column(String(100), default="general")
    tags = Column(JSON, default=list)
    version = Column(Integer, default=1)
    last_editor_type = Column(String(20), default="user")
    last_editor_id = Column(Integer, default=1)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True)
    target_type = Column(String(20), nullable=False)  # "issue" or "wiki"
    target_id = Column(Integer, nullable=False)
    author_type = Column(String(20), nullable=False, default="user")  # "user" or "agent"
    author_id = Column(Integer, default=1)
    body = Column(Text, nullable=False)
    agent_model = Column(String(100))  # e.g. "claude-sonnet-4.6"
    agent_skill_version = Column(String(50))
    created_at = Column(DateTime, default=utcnow)
    edited_at = Column(DateTime)

    issue = relationship(
        "Issue",
        primaryjoin="and_(Comment.target_id == foreign(Issue.id), Comment.target_type == 'issue')",
        viewonly=True,
    )


# --- Agent Tracking ---

class AgentSession(Base):
    __tablename__ = "agent_sessions"

    id = Column(Integer, primary_key=True)
    agent_type = Column(String(50), nullable=False)  # "claude-code", "copilot", etc.
    model = Column(String(100), nullable=False)
    skill_version = Column(String(50))
    started_at = Column(DateTime, default=utcnow)
    ended_at = Column(DateTime)
    issues_processed = Column(Integer, default=0)
    builds_triggered = Column(Integer, default=0)
    status = Column(String(20), default="active")  # active, completed, failed
```

- [ ] **Step 5: Update test conftest to use test database**

Update `backend/tests/conftest.py`:
```python
import os
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ["GDS_COLLAB_DB"] = ":memory:"

from app.db import Base, get_db
from app.main import app

_test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
)
_TestSession = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)


def _override_get_db():
    db = _TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(autouse=True)
def setup_tables():
    Base.metadata.create_all(bind=_test_engine)
    yield
    Base.metadata.drop_all(bind=_test_engine)


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
```

- [ ] **Step 6: Run database tests**

```bash
cd backend && python -m pytest tests/test_db.py -v
```
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/db.py backend/app/models.py backend/tests/conftest.py backend/tests/test_db.py
git commit -m "feat: add SQLAlchemy database models for all 10 tables"
```

---

### Task 3: GDS Parsing Module

**Files:**
- Create: `backend/app/gds/parser.py`
- Create: `backend/tests/test_gds_parser.py`
- Create: `backend/tests/fixtures/simple.py`

- [ ] **Step 1: Create a test GDS script fixture**

Create `backend/tests/fixtures/simple.py`:
```python
"""Simple GDSfactory script that generates a test layout."""
import gdsfactory as gf

c = gf.Component("test_cell")
wg = c << gf.components.straight(length=10, width=0.5)
wg.move((5, 0))
bend = c << gf.components.bend_circular(radius=5)
bend.connect("o1", wg.ports["o2"])
c.write_gds("test_simple.gds")
```

- [ ] **Step 2: Write failing test for GDS parsing**

Create `backend/tests/test_gds_parser.py`:
```python
import pytest
from app.gds.parser import parse_gds, GdsParseResult


def test_parse_result_has_cells():
    """Parser should extract cells from a GDS file."""
    # Use klayout to create a minimal test GDS
    import klayout.db as db

    layout = db.Layout()
    layout.dbu = 0.001
    cell = layout.create_cell("test_cell")
    layer = layout.layer(1, 0)  # layer 1, datatype 0
    cell.shapes(layer).insert(db.Box(0, 0, 1000, 500))
    layout.write("tests/fixtures/test_simple.gds")

    result = parse_gds("tests/fixtures/test_simple.gds")
    assert isinstance(result, GdsParseResult)
    assert len(result.cells) > 0
    assert result.cells[0].name == "test_cell"


def test_parse_extracts_elements():
    """Parser should extract elements (shapes) from cells."""
    import klayout.db as db

    layout = db.Layout()
    layout.dbu = 0.001
    cell = layout.create_cell("element_test")
    layer1 = layout.layer(1, 0)
    layer2 = layout.layer(2, 0)
    cell.shapes(layer1).insert(db.Box(0, 0, 1000, 500))
    cell.shapes(layer2).insert(db.Polygon([db.Point(0, 0), db.Point(500, 0), db.Point(250, 500)]))
    layout.write("tests/fixtures/test_elements.gds")

    result = parse_gds("tests/fixtures/test_elements.gds")
    cell_data = result.cells[0]
    assert cell_data.element_count >= 2


def test_parse_extracts_layers():
    """Parser should identify which layers are present."""
    import klayout.db as db

    layout = db.Layout()
    layout.dbu = 0.001
    cell = layout.create_cell("layer_test")
    layout.layer(1, 0)
    layout.layer(2, 0)
    layout.layer(3, 1)
    cell.shapes(layout.layer(1, 0)).insert(db.Box(0, 0, 100, 100))
    cell.shapes(layout.layer(2, 0)).insert(db.Box(0, 0, 100, 100))
    cell.shapes(layout.layer(3, 1)).insert(db.Box(0, 0, 100, 100))
    layout.write("tests/fixtures/test_layers.gds")

    result = parse_gds("tests/fixtures/test_layers.gds")
    assert len(result.layer_map) >= 3
    assert (1, 0) in result.layer_map
    assert (2, 0) in result.layer_map
    assert (3, 1) in result.layer_map
```

- [ ] **Step 3: Run test to verify it fails**

```bash
cd backend && python -m pytest tests/test_gds_parser.py -v
```
Expected: FAIL (module `app.gds.parser` does not exist)

- [ ] **Step 4: Implement GDS parser**

Create `backend/app/gds/parser.py`:
```python
"""Parse GDS files using klayout and extract cells, elements, layers."""
from dataclasses import dataclass, field
from typing import Optional

import klayout.db as db


@dataclass
class ElementData:
    element_type: str  # "polygon", "box", "path", "text", "reference"
    layer: str  # "1/0" format
    bbox: str  # "x1,y1,x2,y2" in DBU
    path_data: str = ""
    properties: dict = field(default_factory=dict)
    source_line: Optional[int] = None


@dataclass
class CellData:
    name: str
    cell_type: str = "cell"
    bbox: str = ""
    layer_count: int = 0
    element_count: int = 0
    elements: list[ElementData] = field(default_factory=list)


@dataclass
class GdsParseResult:
    cells: list[CellData] = field(default_factory=list)
    layer_map: dict[tuple[int, int], str] = field(default_factory=dict)


def _layer_key(layer_index: int, layout: db.Layout) -> tuple[int, int]:
    info = layout.get_info(layer_index)
    return (info.layer, info.datatype)


def _layer_str(layer_index: int, layout: db.Layout) -> str:
    info = layout.get_info(layer_index)
    return f"{info.layer}/{info.datatype}"


def _bbox_str(box: db.Box) -> str:
    return f"{box.left},{box.bottom},{box.right},{box.top}"


def parse_gds(gds_path: str) -> GdsParseResult:
    """Parse a GDS file and return structured cell/element data."""
    layout = db.Layout()
    layout.read(gds_path)

    result = GdsParseResult()

    # Build layer map
    for i in range(layout.layers()):
        if layout.is_valid_layer(i):
            result.layer_map[_layer_key(i, layout)] = _layer_str(i, layout)

    # Iterate top cells
    for cell_idx in range(layout.cells()):
        cell = layout.cell(cell_idx)
        if cell is None:
            continue

        cell_data = CellData(
            name=cell.name,
            bbox=_bbox_str(cell.dbbox()) if cell.dbbox() else "",
        )

        layers_in_cell = set()

        # Extract shapes
        for li in range(layout.layers()):
            if not layout.is_valid_layer(li):
                continue
            shapes = cell.shapes(li)
            if shapes.is_empty():
                continue
            layers_in_cell.add(li)

            for shape in shapes.each():
                if shape.is_box():
                    el = ElementData(
                        element_type="box",
                        layer=_layer_str(li, layout),
                        bbox=_bbox_str(shape.dbbox()),
                    )
                    cell_data.elements.append(el)
                elif shape.is_polygon():
                    el = ElementData(
                        element_type="polygon",
                        layer=_layer_str(li, layout),
                        bbox=_bbox_str(shape.dbbox()),
                    )
                    cell_data.elements.append(el)
                elif shape.is_path():
                    el = ElementData(
                        element_type="path",
                        layer=_layer_str(li, layout),
                        bbox=_bbox_str(shape.dbbox()),
                    )
                    cell_data.elements.append(el)
                elif shape.is_text():
                    el = ElementData(
                        element_type="text",
                        layer=_layer_str(li, layout),
                        bbox=_bbox_str(shape.dbbox()),
                    )
                    cell_data.elements.append(el)

        # Extract cell references (instances)
        for inst in cell.each_inst():
            ref = ElementData(
                element_type="reference",
                layer="ref",
                bbox=_bbox_str(inst.dbbox()) if inst.dbbox() else "",
                properties={"cell_name": inst.cell.name},
            )
            cell_data.elements.append(ref)

        cell_data.layer_count = len(layers_in_cell)
        cell_data.element_count = len(cell_data.elements)
        result.cells.append(cell_data)

    return result
```

- [ ] **Step 5: Run tests**

```bash
cd backend && python -m pytest tests/test_gds_parser.py -v
```
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/gds/parser.py backend/tests/test_gds_parser.py
git commit -m "feat: add GDS parser module using klayout"
```

---

### Task 4: GDS API Endpoints

**Files:**
- Create: `backend/app/gds/router.py`
- Create: `backend/app/gds/schemas.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_gds_api.py`

- [ ] **Step 1: Create Pydantic schemas**

Create `backend/app/gds/schemas.py`:
```python
from pydantic import BaseModel
from typing import Optional


class ElementResponse(BaseModel):
    id: int
    element_type: str
    layer: str
    bbox: Optional[str] = None
    source_line: Optional[int] = None

    class Config:
        from_attributes = True


class CellResponse(BaseModel):
    id: int
    name: str
    cell_type: str
    bbox: Optional[str] = None
    layer_count: int
    element_count: int
    elements: list[ElementResponse] = []

    class Config:
        from_attributes = True


class BuildResponse(BaseModel):
    id: int
    script_id: int
    gds_path: str
    status: str
    build_log: Optional[str] = None
    git_commit: Optional[str] = None
    cells: list[CellResponse] = []

    class Config:
        from_attributes = True


class ScriptResponse(BaseModel):
    id: int
    path: str
    name: str
    description: Optional[str] = None
    git_commit: Optional[str] = None
    builds: list[BuildResponse] = []

    class Config:
        from_attributes = True


class ScriptCreate(BaseModel):
    path: str
    name: str
    description: str = ""


class BuildCreate(BaseModel):
    script_id: int
    gds_path: str
    git_commit: Optional[str] = None
```

- [ ] **Step 2: Write failing API tests**

Create `backend/tests/test_gds_api.py`:
```python
import pytest


@pytest.mark.asyncio
async def test_list_scripts_empty(client):
    response = await client.get("/api/gds/scripts")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_script(client):
    response = await client.post("/api/gds/scripts", json={
        "path": "scripts/ring_res.py",
        "name": "ring_resonator",
        "description": "Ring resonator",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "ring_resonator"
    assert data["path"] == "scripts/ring_res.py"
    assert data["id"] is not None


@pytest.mark.asyncio
async def test_get_script(client):
    create = await client.post("/api/gds/scripts", json={
        "path": "scripts/test.py", "name": "test",
    })
    script_id = create.json()["id"]

    response = await client.get(f"/api/gds/scripts/{script_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "test"


@pytest.mark.asyncio
async def test_create_build(client):
    create_script = await client.post("/api/gds/scripts", json={
        "path": "scripts/test.py", "name": "test",
    })
    script_id = create_script.json()["id"]

    response = await client.post("/api/gds/builds", json={
        "script_id": script_id,
        "gds_path": "gds/test.gds",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert data["script_id"] == script_id


@pytest.mark.asyncio
async def test_list_builds(client):
    create_script = await client.post("/api/gds/scripts", json={
        "path": "scripts/test.py", "name": "test",
    })
    script_id = create_script.json()["id"]

    await client.post("/api/gds/builds", json={
        "script_id": script_id, "gds_path": "gds/test.gds",
    })

    response = await client.get(f"/api/gds/scripts/{script_id}/builds")
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_get_build_with_cells(client):
    from sqlalchemy.orm import Session
    from app.db import engine
    from app.models import GdsBuild, GdsCell

    # Create script via API
    create_script = await client.post("/api/gds/scripts", json={
        "path": "scripts/test.py", "name": "test",
    })
    script_id = create_script.json()["id"]

    # Create build via API
    create_build = await client.post("/api/gds/builds", json={
        "script_id": script_id, "gds_path": "gds/test.gds",
    })
    build_id = create_build.json()["id"]

    # Insert cell directly (simulating build process)
    with Session(engine) as session:
        cell = GdsCell(
            build_id=build_id, name="test_cell",
            cell_type="cell", bbox="0,0,1000,500",
            layer_count=2, element_count=3,
        )
        session.add(cell)
        session.commit()

    response = await client.get(f"/api/gds/builds/{build_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data["cells"]) == 1
    assert data["cells"][0]["name"] == "test_cell"
```

- [ ] **Step 3: Run test to verify it fails**

```bash
cd backend && python -m pytest tests/test_gds_api.py -v
```
Expected: FAIL (404 — routes not registered)

- [ ] **Step 4: Implement GDS router**

Create `backend/app/gds/router.py`:
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.db import get_db
from app.models import GdsScript, GdsBuild, GdsCell, GdsElement
from app.gds.schemas import (
    ScriptCreate, ScriptResponse, BuildCreate, BuildResponse,
    CellResponse, ElementResponse,
)

router = APIRouter(prefix="/api/gds", tags=["gds"])


@router.get("/scripts", response_model=list[ScriptResponse])
def list_scripts(db: Session = Depends(get_db)):
    return db.query(GdsScript).all()


@router.post("/scripts", response_model=ScriptResponse, status_code=201)
def create_script(data: ScriptCreate, db: Session = Depends(get_db)):
    script = GdsScript(**data.model_dump())
    db.add(script)
    db.commit()
    db.refresh(script)
    return script


@router.get("/scripts/{script_id}", response_model=ScriptResponse)
def get_script(script_id: int, db: Session = Depends(get_db)):
    script = db.query(GdsScript).filter(GdsScript.id == script_id).first()
    if not script:
        raise HTTPException(404, "Script not found")
    return script


@router.get("/scripts/{script_id}/builds", response_model=list[BuildResponse])
def list_builds(script_id: int, db: Session = Depends(get_db)):
    return db.query(GdsBuild).filter(GdsBuild.script_id == script_id).all()


@router.post("/builds", response_model=BuildResponse, status_code=201)
def create_build(data: BuildCreate, db: Session = Depends(get_db)):
    script = db.query(GdsScript).filter(GdsScript.id == data.script_id).first()
    if not script:
        raise HTTPException(404, "Script not found")
    build = GdsBuild(**data.model_dump())
    db.add(build)
    db.commit()
    db.refresh(build)
    return build


@router.get("/builds/{build_id}", response_model=BuildResponse)
def get_build(build_id: int, db: Session = Depends(get_db)):
    build = db.query(GdsBuild).filter(GdsBuild.id == build_id).first()
    if not build:
        raise HTTPException(404, "Build not found")
    return build


@router.get("/builds/{build_id}/cells", response_model=list[CellResponse])
def list_cells(build_id: int, db: Session = Depends(get_db)):
    return db.query(GdsCell).filter(GdsCell.build_id == build_id).all()


@router.get("/cells/{cell_id}/elements", response_model=list[ElementResponse])
def list_elements(cell_id: int, db: Session = Depends(get_db)):
    return db.query(GdsElement).filter(GdsElement.cell_id == cell_id).all()
```

- [ ] **Step 5: Register router in main.py**

Update `backend/app/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.gds.router import router as gds_router

app = FastAPI(title="GDS Collab Platform", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(gds_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 6: Run tests**

```bash
cd backend && python -m pytest tests/test_gds_api.py -v
```
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/gds/router.py backend/app/gds/schemas.py backend/app/main.py backend/tests/test_gds_api.py
git commit -m "feat: add GDS API endpoints for scripts, builds, cells, elements"
```

---

### Task 5: Deep Link Addressing

**Files:**
- Create: `backend/app/gds/addressing.py`
- Create: `backend/tests/test_addressing.py`

- [ ] **Step 1: Write failing tests**

Create `backend/tests/test_addressing.py`:
```python
from app.gds.addressing import build_deep_link, parse_deep_link


def test_design_level_link():
    url = build_deep_link(gds="ring_resonator", build=42)
    assert url == "/viewer?gds=ring_resonator&build=42"


def test_cell_level_link():
    url = build_deep_link(gds="ring_resonator", cell="ring_cell_1", layers=["M1", "D1"])
    assert "gds=ring_resonator" in url
    assert "cell=ring_cell_1" in url
    assert "layers=M1,D1" in url


def test_element_level_link():
    url = build_deep_link(
        gds="ring_resonator", cell="ring_cell_1",
        elem=342, layer="M1", bbox="10.5,20,30,40",
    )
    assert "elem=342" in url
    assert "layer=M1" in url
    assert "bbox=10.5,20,30,40" in url


def test_multi_element_link():
    url = build_deep_link(gds="ring_resonator", elems=[342, 343, 345], layer="M1")
    assert "elems=342,343,345" in url


def test_parse_design_link():
    params = parse_deep_link("/viewer?gds=ring_resonator&build=42")
    assert params["gds"] == "ring_resonator"
    assert params["build"] == 42


def test_parse_element_link():
    params = parse_deep_link(
        "/viewer?gds=ring_resonator&cell=ring_cell_1&elem=342&layer=M1&bbox=10.5,20,30,40"
    )
    assert params["gds"] == "ring_resonator"
    assert params["cell"] == "ring_cell_1"
    assert params["elem"] == 342
    assert params["layer"] == "M1"
    assert params["bbox"] == "10.5,20,30,40"


def test_parse_multi_element_link():
    params = parse_deep_link("/viewer?gds=ring_resonator&elems=342,343,345&layer=M1")
    assert params["elems"] == [342, 343, 345]


def test_roundtrip():
    url = build_deep_link(gds="test", cell="c1", elem=10, layer="D1")
    params = parse_deep_link(url)
    assert params["gds"] == "test"
    assert params["cell"] == "c1"
    assert params["elem"] == 10
    assert params["layer"] == "D1"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && python -m pytest tests/test_addressing.py -v
```
Expected: FAIL (module not found)

- [ ] **Step 3: Implement addressing module**

Create `backend/app/gds/addressing.py`:
```python
"""Deep link generation and parsing for GDS viewer state."""
from urllib.parse import urlencode, urlparse, parse_qs


def build_deep_link(
    gds: str,
    build: int | None = None,
    cell: str | None = None,
    layers: list[str] | None = None,
    elem: int | None = None,
    elems: list[int] | None = None,
    layer: str | None = None,
    bbox: str | None = None,
) -> str:
    """Build a deep link URL for the GDS viewer."""
    params: dict[str, str] = {"gds": gds}

    if build is not None:
        params["build"] = str(build)
    if cell is not None:
        params["cell"] = cell
    if layers is not None:
        params["layers"] = ",".join(layers)
    if elem is not None:
        params["elem"] = str(elem)
    if elems is not None:
        params["elems"] = ",".join(str(e) for e in elems)
    if layer is not None:
        params["layer"] = layer
    if bbox is not None:
        params["bbox"] = bbox

    return f"/viewer?{urlencode(params)}"


def parse_deep_link(url: str) -> dict:
    """Parse a deep link URL into its components."""
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)

    result: dict = {}

    if "gds" in qs:
        result["gds"] = qs["gds"][0]
    if "build" in qs:
        result["build"] = int(qs["build"][0])
    if "cell" in qs:
        result["cell"] = qs["cell"][0]
    if "layers" in qs:
        result["layers"] = qs["layers"][0].split(",")
    if "elem" in qs:
        result["elem"] = int(qs["elem"][0])
    if "elems" in qs:
        result["elems"] = [int(x) for x in qs["elems"][0].split(",")]
    if "layer" in qs:
        result["layer"] = qs["layer"][0]
    if "bbox" in qs:
        result["bbox"] = qs["bbox"][0]

    return result
