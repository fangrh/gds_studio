"""Sync API endpoints — pull and push between agent and server."""
import json
import os
import shutil
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.auth import verify_token
from app.db import get_db
from app.models import Project, Issue, WikiPage, GdsScript, Comment, IssueElement
from app.sync.schemas import SyncPullResponse, SyncPushResponse

router = APIRouter(prefix="/api/sync", tags=["sync"])

PROJECTS_DIR = os.environ.get("GDS_PROJECTS_DIR", "/data/projects")


def _project_data_dir(project_id: int) -> str:
    d = os.path.join(PROJECTS_DIR, str(project_id))
    os.makedirs(os.path.join(d, "scripts"), exist_ok=True)
    os.makedirs(os.path.join(d, "gds"), exist_ok=True)
    return d


@router.get("/pull", response_model=SyncPullResponse)
def sync_pull(
    since: str | None = None,
    project: Project = Depends(verify_token),
    db: Session = Depends(get_db),
):
    since_dt = None
    if since:
        try:
            since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(400, "Invalid since timestamp")

    issue_q = db.query(Issue).filter(Issue.project_id == project.id)
    if since_dt:
        issue_q = issue_q.filter(Issue.updated_at > since_dt)
    issues = issue_q.all()

    issue_data = []
    for issue in issues:
        issue_data.append({
            "id": issue.id,
            "title": issue.title,
            "body": issue.body,
            "status": issue.status,
            "priority": issue.priority,
            "script_path": issue.script_path,
            "tags": issue.tags or [],
            "created_at": str(issue.created_at) if issue.created_at else None,
            "updated_at": str(issue.updated_at) if issue.updated_at else None,
            "comments": [
                {
                    "id": c.id,
                    "author_type": c.author_type,
                    "body": c.body,
                    "created_at": str(c.created_at) if c.created_at else None,
                }
                for c in (issue.comments or [])
            ],
            "linked_elements": [
                {
                    "cell_name": le.cell_name,
                    "element_id": le.element_id,
                    "layer": le.layer,
                    "source_script_line": le.source_script_line,
                    "deep_link_url": le.deep_link_url,
                }
                for le in (issue.linked_elements or [])
            ],
        })

    wiki_q = db.query(WikiPage).filter(WikiPage.project_id == project.id)
    if since_dt:
        wiki_q = wiki_q.filter(WikiPage.updated_at > since_dt)
    wiki_pages = wiki_q.all()

    wiki_data = [
        {
            "id": wp.id,
            "title": wp.title,
            "slug": wp.slug,
            "body": wp.body,
            "category": wp.category,
            "tags": wp.tags or [],
            "updated_at": str(wp.updated_at) if wp.updated_at else None,
        }
        for wp in wiki_pages
    ]

    now = datetime.now(timezone.utc).isoformat()
    return SyncPullResponse(
        issues=issue_data,
        wiki_updates=wiki_data,
        server_timestamp=now,
    )


@router.post("/push", response_model=SyncPushResponse)
async def sync_push(
    request: Request,
    commit_sha: str = Form(""),
    issue_replies: str = Form("[]"),
    wiki_updates: str = Form("[]"),
    project: Project = Depends(verify_token),
    db: Session = Depends(get_db),
):
    data_dir = _project_data_dir(project.id)

    form = await request.form()
    accepted_scripts = []
    accepted_gds = []
    replied_issues = []
    updated_wiki = []

    for key in form:
        val = form[key]
        if not hasattr(val, "filename"):
            continue
        filename = val.filename
        if not filename:
            continue
        safe_name = os.path.basename(filename)
        if not safe_name:
            continue
        content = await val.read()

        if key.startswith("scripts"):
            dest = os.path.join(data_dir, "scripts", safe_name)
            with open(dest, "wb") as f:
                f.write(content)
            script_name = os.path.splitext(safe_name)[0]
            existing = db.query(GdsScript).filter(
                GdsScript.project_id == project.id,
                GdsScript.path == f"scripts/{safe_name}",
            ).first()
            if existing:
                existing.git_commit = commit_sha or None
            else:
                db.add(GdsScript(
                    project_id=project.id,
                    path=f"scripts/{safe_name}",
                    name=script_name,
                    git_commit=commit_sha or None,
                ))
            accepted_scripts.append(safe_name)

        elif key.startswith("gds_files"):
            dest = os.path.join(data_dir, "gds", safe_name)
            with open(dest, "wb") as f:
                f.write(content)
            accepted_gds.append(safe_name)

    try:
        replies = json.loads(issue_replies)
    except json.JSONDecodeError:
        replies = []

    for reply in replies:
        issue_id = reply.get("issue_id")
        body = reply.get("body", "")
        issue = db.query(Issue).filter(
            Issue.id == issue_id, Issue.project_id == project.id
        ).first()
        if issue:
            comment = Comment(
                target_type="issue",
                target_id=issue_id,
                author_type="agent",
                body=body,
            )
            db.add(comment)
            replied_issues.append(issue_id)

    try:
        wiki_updates_data = json.loads(wiki_updates)
    except json.JSONDecodeError:
        wiki_updates_data = []

    for wu in wiki_updates_data:
        title = wu.get("title", "")
        slug = wu.get("slug", title.lower().replace(" ", "-"))
        body = wu.get("body", "")
        existing = db.query(WikiPage).filter(
            WikiPage.slug == slug, WikiPage.project_id == project.id
        ).first()
        if existing:
            existing.body = body
            existing.title = title
            existing.version = (existing.version or 0) + 1
            existing.last_editor_type = "agent"
        else:
            db.add(WikiPage(
                project_id=project.id,
                title=title,
                slug=slug,
                body=body,
                last_editor_type="agent",
            ))
        updated_wiki.append(slug)

    project.last_sync_at = datetime.now(timezone.utc)
    db.commit()

    now = datetime.now(timezone.utc).isoformat()
    return SyncPushResponse(
        accepted_scripts=accepted_scripts,
        accepted_gds=accepted_gds,
        replied_issues=replied_issues,
        updated_wiki=updated_wiki,
        server_timestamp=now,
    )
