from datetime import datetime

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


@router.get("/unreplied")
def unreplied_comments(db: Session = Depends(get_db)):
    """Find issues where the last comment is from a user with no agent reply."""
    issues = db.query(Issue).filter(
        Issue.status != "deleted"
    ).all()

    result = []
    for issue in issues:
        comments = issue.comments or []
        if not comments:
            continue
        sorted_comments = sorted(comments, key=lambda c: c.created_at or datetime.min)
        last_comment = sorted_comments[-1]
        if last_comment.author_type == "user":
            last_agent_time = datetime.min
            for c in sorted_comments:
                if c.author_type == "agent" and c.created_at and c.created_at > last_agent_time:
                    last_agent_time = c.created_at
            user_comments_needing_reply = []
            for c in sorted_comments:
                if c.author_type == "user" and c.created_at and c.created_at > last_agent_time:
                    user_comments_needing_reply.append({
                        "id": c.id,
                        "body": c.body,
                        "created_at": str(c.created_at) if c.created_at else None,
                    })
            if user_comments_needing_reply:
                result.append({
                    "issue_id": issue.id,
                    "issue_title": issue.title,
                    "issue_status": issue.status,
                    "script_path": issue.script_path,
                    "priority": issue.priority,
                    "unreplied_comments": user_comments_needing_reply,
                })
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
