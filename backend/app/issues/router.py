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
        project_id=issue.project_id,
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
    project_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Issue)
    if status:
        q = q.filter(Issue.status == status)
    if project_id:
        q = q.filter(Issue.project_id == project_id)
    return [_issue_to_response(i) for i in q.order_by(Issue.created_at.desc()).all()]


@issue_router.post("", response_model=IssueResponse, status_code=201)
def create_issue(data: IssueCreate, db: Session = Depends(get_db)):
    issue = Issue(
        title=data.title,
        body=data.body,
        priority=data.priority,
        tags=data.tags,
        script_path=data.script_path,
        project_id=data.project_id if hasattr(data, 'project_id') and data.project_id else 1,
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
