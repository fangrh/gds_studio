"""Project CRUD endpoints."""
import hashlib
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Project, Issue, WikiPage, GdsScript, IssueElement, Comment
from app.projects.schemas import ProjectCreate, ProjectResponse

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _project_to_response(project: Project, db: Session, include_token: bool = False) -> ProjectResponse:
    issue_count = db.query(func.count(Issue.id)).filter(
        Issue.project_id == project.id, Issue.status != "deleted"
    ).scalar() or 0
    wiki_count = db.query(func.count(WikiPage.id)).filter(
        WikiPage.project_id == project.id
    ).scalar() or 0
    script_count = db.query(func.count(GdsScript.id)).filter(
        GdsScript.project_id == project.id
    ).scalar() or 0

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description or "",
        token=None if not include_token else _get_stored_token(project),
        created_at=project.created_at,
        updated_at=project.updated_at,
        issue_count=issue_count,
        wiki_count=wiki_count,
        script_count=script_count,
    )


def _get_stored_token(project: Project) -> str | None:
    return getattr(project, "_plaintext_token", None)


def _make_token_hash() -> tuple[str, str]:
    token = str(uuid.uuid4())
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    return token, token_hash


@router.post("", response_model=ProjectResponse, status_code=201)
def create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    existing = db.query(Project).filter(Project.name == data.name).first()
    if existing:
        raise HTTPException(409, f"Project '{data.name}' already exists")

    token, token_hash = _make_token_hash()
    project = Project(name=data.name, description=data.description, token_hash=token_hash)
    db.add(project)
    db.commit()
    db.refresh(project)

    project._plaintext_token = token
    return _project_to_response(project, db, include_token=True)


@router.get("", response_model=list[ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    return [_project_to_response(p, db) for p in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    return _project_to_response(project, db)


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")
    if project.name == "main":
        raise HTTPException(400, "Cannot delete the default project")

    db.query(IssueElement).filter(
        IssueElement.issue_id.in_(
            db.query(Issue.id).filter(Issue.project_id == project_id)
        )
    ).delete(synchronize_session="fetch")
    db.query(Comment).filter(
        Comment.target_type == "issue",
        Comment.target_id.in_(
            db.query(Issue.id).filter(Issue.project_id == project_id)
        )
    ).delete(synchronize_session="fetch")
    db.query(Issue).filter(Issue.project_id == project_id).delete()
    db.query(WikiPage).filter(WikiPage.project_id == project_id).delete()
    db.query(GdsScript).filter(GdsScript.project_id == project_id).delete()
    db.delete(project)
    db.commit()


@router.post("/{project_id}/regen-token", response_model=ProjectResponse)
def regenerate_token(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(404, "Project not found")

    token, token_hash = _make_token_hash()
    project.token_hash = token_hash
    db.commit()
    db.refresh(project)

    project._plaintext_token = token
    return _project_to_response(project, db, include_token=True)
